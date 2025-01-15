import json
import logging
import csv
import io
from decimal import Decimal
import datetime
import pandas as pd
from datetime import datetime  # Import the datetime class
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, connection, connections, transaction
from django.db.models import Count, Sum, F, Q, Exists, OuterRef, Prefetch
from django.http import JsonResponse, HttpResponse, FileResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.timezone import make_naive
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_http_methods, require_POST, require_GET
from django.views.generic import TemplateView

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from rest_framework import viewsets, status
from rest_framework.response import Response

from .forms import StateForm, CityForm, PartyMasterForm
from .models import (
    DDMSummary,
    DDMDetails,
    DeliveryCNote,
    ReceivedStatesCnotes,
    Transporter,
    State,
    City,
    PartyMaster,
    Pickup,
    TransporterAppReceive,
    CNote,
)
from .serializers import DDMDetailsSerializer, DDMSummarySerializer
from dealer_app.models import (
    LoadingSheetSummary,
    LoadingSheetDetail,
    CNotes,
    Dealer,
    DeliveryDestination,
    Article,
    ArtType,
)

# Logging configuration
logger = logging.getLogger(__name__)

# User model reference
User = get_user_model()

@login_required
def home(request):
    try:
        transporter = Transporter.objects.get(user=request.user)
        pickup_requests = Pickup.objects.filter(transporter=transporter, status='pending')
        return render(request, 'transporter/home.html', 
                      {
                          'transporter': transporter,
                          'transporter_name': transporter.user.username.title(),
                          'transporter_image': transporter.profile_image.url if transporter.profile_image else 'default_image_url',
                          'pickup_requests': pickup_requests
                      })
    except Transporter.DoesNotExist:
        messages.error(request, "You do not have access to this dashboard. Please contact support.")
        return render(request, 'transporter/home.html')
    except Exception as e:
        messages.error(request, "An unexpected error occurred. Please try again later.")
        logger.error(f"Error in home view: {e}")
        return render(request, 'transporter/home.html')

@login_required
def manage_location(request):
    states = State.objects.all()
    cities = City.objects.all()
    state_form = StateForm()
    city_form = CityForm()

    if request.method == 'POST':
        if 'add_state' in request.POST:
            state_form = StateForm(request.POST)
            if state_form.is_valid():
                state_form.save()
                messages.success(request, "State added successfully!")
                return redirect('transporter:manage_location')
        elif 'add_city' in request.POST:
            city_form = CityForm(request.POST)
            if city_form.is_valid():
                city_form.save()
                messages.success(request, "City added successfully!")
                return redirect('transporter:manage_location')

    context = {
        'states': states,
        'cities': cities,
        'state_form': state_form,
        'city_form': city_form,
    }
    return render(request, 'transporter/manage_location.html', context)

@login_required
def edit_state(request, id):
    state = get_object_or_404(State, id=id)
    if request.method == 'POST':
        form = StateForm(request.POST, instance=state)
        if form.is_valid():
            form.save()
            messages.success(request, "State updated successfully!")
            return redirect('transporter:manage_location')
    else:
        form = StateForm(instance=state)
    return render(request, 'transporter/edit_state.html', {'form': form, 'state': state})

@login_required
def delete_state(request, id):
    state = get_object_or_404(State, id=id)
    if request.method == 'POST':
        state.delete()
        messages.success(request, "State deleted successfully!")
        return redirect('transporter:manage_location')
    return render(request, 'transporter/confirm_delete_state.html', {'state': state})

@login_required
def edit_city(request, id):
    city = get_object_or_404(City, id=id)
    if request.method == 'POST':
        form = CityForm(request.POST, instance=city)
        if form.is_valid():
            form.save()
            messages.success(request, "City updated successfully!")
            return redirect('transporter:manage_location')
    else:
        form = CityForm(instance=city)
    return render(request, 'transporter/edit_city.html', {'form': form, 'city': city})

@login_required
def delete_city(request, id):
    city = get_object_or_404(City, id=id)
    if request.method == 'POST':
        city.delete()
        messages.success(request, "City deleted successfully!")
        return redirect('transporter:manage_location')
    return render(request, 'transporter/confirm_delete_city.html', {'city': city})

@login_required
def party_master(request):
    form = PartyMasterForm()
    return render(request, 'transporter/party_master.html', {'form': form})

@login_required
@require_http_methods(["GET", "POST"])
def add_party(request):
    if request.method == 'POST':
        form = PartyMasterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Party added successfully!")
            return redirect('transporter:party_master')
        else:
            messages.error(request, "There were errors in the form. Please correct them.")
    else:
        form = PartyMasterForm()
    return render(request, 'transporter/party_master.html', {'form': form})

@login_required
@require_http_methods(["GET", "POST"])
def search_party(request):
    if request.method == 'POST':
        search_term = request.POST.get('search_party', '')
        parties = PartyMaster.objects.filter(party_name__icontains=search_term)[:10]
        return render(request, 'transporter/search_results.html', {'parties': parties})
    return render(request, 'transporter/search_party.html')

@login_required
def get_party(request, party_id):
    party = get_object_or_404(PartyMaster, id=party_id)
    form = PartyMasterForm(instance=party)
    return render(request, 'transporter/edit_party.html', {'form': form, 'party': party})

@login_required
def update_party(request, party_id):
    party = get_object_or_404(PartyMaster, id=party_id)
    if request.method == 'POST':
        form = PartyMasterForm(request.POST, instance=party)
        if form.is_valid():
            form.save()
            messages.success(request, "Party updated successfully!")
            return redirect('transporter:party_list')
    else:
        form = PartyMasterForm(instance=party)
    return render(request, 'transporter/edit_party.html', {'form': form, 'party': party})

@login_required
def delete_party(request, party_id):
    party = get_object_or_404(PartyMaster, id=party_id)
    if request.method == 'POST':
        party.delete()
        messages.success(request, "Party deleted successfully!")
        return redirect('transporter:party_list')
    return render(request, 'transporter/confirm_delete_party.html', {'party': party})

@login_required
def save_config(request):
    if request.method == 'POST':
        # Implement your configuration saving logic here
        messages.success(request, "Configuration saved successfully!")
        return redirect('transporter:home')
    return render(request, 'transporter/save_config.html')

def success_page(request):
    return render(request, 'transporter/success.html')

@login_required
def party_list(request):
    parties = PartyMaster.objects.all()
    return render(request, 'transporter/party_list.html', {'parties': parties})

class PartyMasterView(TemplateView):
    template_name = 'transporter/party_master.html'

@login_required
def config_list(request):
    # Implement logic to fetch and display configurations
    return render(request, 'transporter/config_list.html')

@login_required
def get_pickup_requests(request):
    try:
        transporter = Transporter.objects.get(user=request.user)
        pickup_requests = Pickup.objects.filter(transporter=transporter, status='pending')
        data = []
        for pickup in pickup_requests:
            data.append({
                'id': pickup.id,
                'cnote_number': pickup.cnote.cnote_number,
                'created_at': pickup.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'dealer_name': pickup.cnote.dealer.name,
                'consignee_name': pickup.cnote.consignee_name,
                'delivery_address': pickup.cnote.consignee_address,
            })
        return JsonResponse(data, safe=False)
    except Transporter.DoesNotExist:
        logger.error(f"Transporter does not exist for user {request.user.id}")
        return JsonResponse({'error': "Transporter not found."}, status=404)
    except Exception as e:
        logger.error(f"Error fetching pickup requests: {e}")
        return JsonResponse({'error': "An unexpected error occurred."}, status=500)

logger = logging.getLogger(__name__)

@login_required
@ensure_csrf_cookie
def received_view(request):
    return render(request, 'transporter/receive.html')

@login_required
@require_http_methods(["GET"])
def get_dealers_with_loadingsheets(request):
    try:
        dealers = Dealer.objects.filter(
            Exists(LoadingSheetSummary.objects.filter(dealer=OuterRef('pk'), status='dispatched'))
        ).values('dealer_id', 'name').order_by('name')

        return JsonResponse({
            'status': 'success',
            'dealers': list(dealers)
        })
    except Exception as e:
        logger.error(f"Error in get_dealers_with_loadingsheets: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'An error occurred while fetching dealers: {str(e)}'
        }, status=500)
    

logger = logging.getLogger(__name__)

@login_required
@require_http_methods(["GET"])
def fetch_receivables(request):
    try:
        # Get search parameters
        search_type = request.GET.get('searchBy', 'all')
        from_date = request.GET.get('fromDate')
        to_date = request.GET.get('toDate')
        dealer_id = request.GET.get('dealerId')
        ls_number = request.GET.get('lsNumber')

        # Base query - filter for dispatched status only in LoadingSheetSummary
        query = LoadingSheetSummary.objects.filter(status='dispatched')

        # Apply filters based on search parameters
        if search_type == 'dealer' and dealer_id:
            query = query.filter(dealer=dealer_id)
        elif search_type == 'date' and from_date and to_date:
            try:
                from_date = datetime.strptime(from_date, '%Y-%m-%d').date()
                to_date = datetime.strptime(to_date, '%Y-%m-%d').date()
                query = query.filter(created_at__date__range=[from_date, to_date])
            except ValueError:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid date format'
                }, status=400)
        elif search_type == 'lsNumber' and ls_number:
            query = query.filter(ls_number__icontains=ls_number)

        # Order by latest first
        query = query.order_by('-created_at')

        receivables = []
        for sheet in query:
            # Get details for this loading sheet where CNotes are in 'dispatched' status
            details = LoadingSheetDetail.objects.filter(loading_sheet=sheet, status='dispatched')
            
            # Only include this loading sheet if it has CNotes in 'dispatched' status
            if details.exists():
                total_cnotes = details.count()
                total_art = details.aggregate(Sum('art'))['art__sum'] or 0
                
                receivables.append({
                    'srNo': sheet.ls_number,
                    'lsNo': sheet.ls_number,
                    'lsDateTime': sheet.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'dealer': sheet.dealer.name if sheet.dealer else 'N/A',
                    'totalLRs': total_cnotes,
                    'pendingLRs': total_cnotes,  # All are pending as we're only including 'dispatched' status
                    'totalArt': total_art,
                    'pendingArt': total_art
                })

        # Limit to 200 records after filtering
        receivables = receivables[:200]

        # Calculate summary for pending items only
        summary = {
            'lrCount': sum(item['pendingLRs'] for item in receivables),
            'totalQuantity': sum(item['pendingArt'] for item in receivables),
            'totalReceivableWeight': 0,  # This field might need to be added to your model
            'paid': 0,
            'toPay': 0,
            'tbb': 0,
        }

        # Calculate payment type totals from LoadingSheetDetail
        for sheet in query:
            details = LoadingSheetDetail.objects.filter(loading_sheet=sheet, status='dispatched')
            summary['paid'] += details.filter(payment_type='paid').aggregate(Sum('art'))['art__sum'] or 0
            summary['toPay'] += details.filter(payment_type='to_pay').aggregate(Sum('art'))['art__sum'] or 0
            summary['tbb'] += details.filter(payment_type='tbb').aggregate(Sum('art'))['art__sum'] or 0

        return JsonResponse({
            'status': 'success',
            'receivables': receivables,
            'summary': summary
        })
    except Exception as e:
        logger.error(f"Error in fetch_receivables: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'An error occurred while fetching data: {str(e)}'
        }, status=500)

@login_required
@require_http_methods(["POST"])
def receive_shipment(request):
    try:
        data = json.loads(request.body)
        ls_number = data.get('lsNumber')
        
        if not ls_number:
            return JsonResponse({
                'status': 'error',
                'message': 'Loading sheet number is required'
            }, status=400)

        # Get the loading sheet
        loading_sheet = LoadingSheetSummary.objects.get(ls_number=ls_number)
        
        # Check if already received
        if loading_sheet.status != 'dispatched':
            return JsonResponse({
                'status': 'error',
                'message': f'Loading sheet cannot be received (current status: {loading_sheet.status})'
            }, status=400)

        # Update the LoadingSheetSummary status
        loading_sheet.status = 'received'
        loading_sheet.save()

        # Create a new TransporterAppReceive entry
        TransporterAppReceive.objects.create(
            ls_number=loading_sheet.ls_number,
            transporter=request.user.transporter,
            total_lrs=loading_sheet.total_cnote,
            total_art=loading_sheet.total_art,
            total_weight=0,  # This field might need adjustment
            from_branch=getattr(loading_sheet, 'from_branch', 'N/A'),
            to_branch=getattr(loading_sheet, 'to_branch', 'N/A'),
            dealer=loading_sheet.dealer,
            truck_no=getattr(loading_sheet, 'truck_no', 'N/A'),
            ls_date_time=loading_sheet.created_at
        )

        return JsonResponse({
            'status': 'success',
            'message': f'Shipment {ls_number} received successfully'
        })
    except LoadingSheetSummary.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Loading sheet not found'
        }, status=404)
    except Exception as e:
        logger.error(f"Error in receive_shipment: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'An error occurred while receiving the shipment: {str(e)}'
        }, status=500)

logger = logging.getLogger(__name__)

@login_required
@require_http_methods(["GET"])
def get_loading_sheet_details(request, ls_number):
    try:
        logger.info(f"Fetching loading sheet details for LS number: {ls_number}")
        
        # First check if loading sheet exists
        loading_sheet = get_object_or_404(LoadingSheetSummary, ls_number=ls_number)
        
        # Get all loading sheet details
        loading_sheet_details = LoadingSheetDetail.objects.filter(
            loading_sheet=loading_sheet
        ).select_related(
            'cnote',
            'loading_sheet__dealer',
            'loading_sheet__transporter'
        )

        # Log the query for debugging
        logger.debug(f"Query: {loading_sheet_details.query}")
        logger.debug(f"Found {loading_sheet_details.count()} CNotes")

        # Get total counts for the loading sheet (excluding received CNotes)
        total_details = loading_sheet_details.exclude(status='Received')
        total_cnotes = total_details.count()
        total_art = sum(detail.art or 0 for detail in total_details)
        total_amount = sum(detail.amount or 0 for detail in total_details)

        # Prepare loading sheet data
        loading_sheet_data = {
            'ls_no': ls_number,
            'created_at': loading_sheet.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'dealer_name': loading_sheet.dealer.name if loading_sheet.dealer else 'N/A',
            'transporter_name': loading_sheet.transporter.name if loading_sheet.transporter else 'N/A',
            'total_cnotes': total_cnotes,
            'total_articles': total_art,
            'total_amount': total_amount,
        }

        # Prepare LR details
        lr_details = []
        for detail in loading_sheet_details:
            lr_details.append({
                'lr_no': detail.cnote.cnote_number,
                'to': detail.destination or 'N/A',
                'consignee_name': detail.cnote.consignee_name,
                'articles': detail.art or 0,
                'amount': float(detail.amount or 0),
                'cnote_type': detail.payment_type or 'N/A',
                'status': detail.status or 'Pending'  # Ensure status is always set
            })

        logger.info(f"Successfully fetched details for LS {ls_number}: {len(lr_details)} LRs found")
        
        # Log the actual data being sent
        logger.debug(f"Loading sheet data: {loading_sheet_data}")
        logger.debug(f"LR details: {lr_details}")
        
        return JsonResponse({
            'status': 'success',
            'loading_sheet': loading_sheet_data,
            'lr_details': lr_details
        })

    except LoadingSheetSummary.DoesNotExist:
        logger.error(f"Loading sheet not found: {ls_number}")
        return JsonResponse({
            'status': 'error',
            'message': 'Loading sheet not found'
        }, status=404)
    except Exception as e:
        logger.error(f"Error fetching loading sheet details: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'An error occurred while fetching loading sheet details: {str(e)}'
        }, status=500)

@login_required
@require_http_methods(["GET"])
def get_lr_details(request, ls_number):
    try:
        loading_sheet = LoadingSheetSummary.objects.get(ls_number=ls_number)
        cnotes = CNotes.objects.filter(loading_sheet=loading_sheet)
        
        lr_details = []
        for cnote in cnotes:
            lr_details.append({
                'lr_no': cnote.cnote_number,
                'from': cnote.from_location,
                'to': cnote.to_location,
                'amount': float(cnote.total_amount) if cnote.total_amount else 0.0,
                'status': cnote.status,
                'articles': cnote.total_articles,
                'weight': float(cnote.total_weight) if cnote.total_weight else 0.0,
            })

        return JsonResponse({
            'status': 'success',
            'lr_details': lr_details
        })
    except LoadingSheetSummary.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Loading sheet not found'
        }, status=404)
    except Exception as e:
        logger.error(f"Error fetching LR details: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'An error occurred while fetching LR details: {str(e)}'
        }, status=500)

@login_required
@require_http_methods(["POST"])
def record_short_entry(request):
    try:
        data = json.loads(request.body)
        lr_no = data.get('lr_no')
        
        if not lr_no:
            return JsonResponse({
                'status': 'error',
                'message': 'LR number is required'
            }, status=400)

        cnote = CNotes.objects.get(cnote_number=lr_no)
        cnote.status = 'short'
        cnote.save()

        return JsonResponse({
            'status': 'success',
            'message': f'Short entry recorded for LR {lr_no}'
        })
    except CNotes.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'LR not found'
        }, status=404)
    except Exception as e:
        logger.error(f"Error recording short entry: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'An error occurred while recording short entry: {str(e)}'
        }, status=500)

@login_required
@require_http_methods(["POST"])
def record_damage_entry(request):
    try:
        data = json.loads(request.body)
        lr_no = data.get('lr_no')
        
        if not lr_no:
            return JsonResponse({
                'status': 'error',
                'message': 'LR number is required'
            }, status=400)

        cnote = CNotes.objects.get(cnote_number=lr_no)
        cnote.status = 'damaged'
        cnote.save()

        return JsonResponse({
            'status': 'success',
            'message': f'Damage entry recorded for LR {lr_no}'
        })
    except CNotes.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'LR not found'
        }, status=404)
    except Exception as e:
        logger.error(f"Error recording damage entry: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'An error occurred while recording damage entry: {str(e)}'
        }, status=500)

@login_required
@require_http_methods(["POST"])
def record_excess_receive(request):
    try:
        data = json.loads(request.body)
        lr_no = data.get('lr_no')
        quantity = data.get('quantity')
        remarks = data.get('remarks')
        
        if not all([lr_no, quantity]):
            return JsonResponse({
                'status': 'error',
                'message': 'LR number and quantity are required'
            }, status=400)

        cnote = CNotes.objects.get(cnote_number=lr_no)
        cnote.total_articles = int(cnote.total_articles) + int(quantity)
        cnote.remarks = remarks
        cnote.save()

        return JsonResponse({
            'status': 'success',
            'message': f'Excess receive recorded for LR {lr_no}'
        })
    except CNotes.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'LR not found'
        }, status=404)
    except Exception as e:
        logger.error(f"Error recording excess receive: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'An error occurred while recording excess receive: {str(e)}'
        }, status=500)

@login_required
@require_http_methods(["POST"])
def receive_lrs(request):
    try:
        data = json.loads(request.body)
        lr_numbers = data.get('lr_numbers', [])
        remarks = data.get('remarks')
        godown = data.get('godown')
        user = data.get('user')
        
        if not lr_numbers:
            return JsonResponse({
                'status': 'error',
                'message': 'No LRs selected for receiving'
            }, status=400)

        # Update status for all selected LRs
        CNotes.objects.filter(cnote_number__in=lr_numbers).update(
            status='received',
            received_at=timezone.now(),
            received_by=request.user,
            received_remarks=remarks,
            godown=godown
        )

        return JsonResponse({
            'status': 'success',
            'message': f'Successfully received {len(lr_numbers)} LR(s)'
        })
    except Exception as e:
        logger.error(f"Error receiving LRs: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'An error occurred while receiving LRs: {str(e)}'
        }, status=500)

@login_required
def received_cnote_view(request):
    logger.debug(f"Attempting to render RECEIVED_CNOTES.HTML")
    ls_number = request.GET.get('lsNumber')
    if not ls_number:
        return render(request, 'transporter/RECEIVED_CNOTES.HTML', {'error': 'No loading sheet number provided.'})

    try:
        loading_sheet_summary = get_object_or_404(LoadingSheetSummary, ls_number=ls_number)
        loading_sheet_details = LoadingSheetDetail.objects.filter(loading_sheet=loading_sheet_summary).select_related('cnote')
        cnotes = CNotes.objects.filter(loading_sheet_details__loading_sheet=loading_sheet_summary).distinct()

        context = {
            'loading_sheet_summary': loading_sheet_summary,
            'loading_sheet_details': loading_sheet_details,
            'cnotes': cnotes,
        }
        return render(request, 'transporter/RECEIVED_CNOTES.HTML', context)
    except LoadingSheetSummary.DoesNotExist:
        return render(request, 'transporter/RECEIVED_CNOTES.HTML', {'error': 'Loading sheet not found.'})
    except Exception as e:
        return render(request, 'transporter/RECEIVED_CNOTES.HTML', {'error': 'An unexpected error occurred while fetching loading sheet details.'})


logger = logging.getLogger(__name__)

@require_POST
@transaction.atomic
def receive_cnotes(request):
    try:
        data = json.loads(request.body)
        cnotes = data.get('cnotes', [])
        loading_sheet_data = data.get('loadingSheetData', {})
        remarks = data.get('remarks', '')
        godown = data.get('godown', '')
        user = data.get('user', '')

        for lr_no in cnotes:
            # Update ReceivedStatesCnotes
            detail = LoadingSheetDetail.objects.get(cnote__cnote_number=lr_no)
            ReceivedStatesCnotes.objects.create(
                cnote_number=detail.cnote.cnote_number,
                consignor_name=detail.cnote.consignor_name,
                consignee_name=detail.cnote.consignee_name,
                consignor_contact=detail.consignor_contact,
                consignee_contact=detail.consignee_contact,
                articles=detail.art,
                amount=detail.amount,
                ls_number=loading_sheet_data['ls_no'],
                dealer_name=loading_sheet_data['dealer_name'],
                transporter_name=loading_sheet_data['transporter_name'],
                received_at=timezone.now(),
                status='Received',
                remarks=remarks,
                godown=godown,
                received_by=user
            )

            # Update status in dealer_app_cnotes
            CNotes.objects.filter(cnote_number=lr_no).update(status='received')

            # Update status in dealer_app_loadingsheetdetail
            LoadingSheetDetail.objects.filter(cnote__cnote_number=lr_no).update(status='received')

            # Add more status updates for other related tables as needed
            # For example:
            # OtherRelatedModel.objects.filter(cnote__cnote_number=lr_no).update(status='received')

        return JsonResponse({'status': 'success', 'message': f'{len(cnotes)} CNotes received successfully'})
    except Exception as e:
        logger.error(f"Error receiving cnotes: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)



def receive_view(request):
    return render(request, 'receive.html')

logger = logging.getLogger(__name__)

@login_required
def mf_print_view(request, ls_number):
    try:
        # Get the loading sheet
        loading_sheet = get_object_or_404(LoadingSheetSummary, ls_number=ls_number)
        
        # Get all CNotes associated with this loading sheet
        loading_sheet_details = LoadingSheetDetail.objects.filter(
            loading_sheet=loading_sheet
        ).select_related('cnote')
        
        context = {
            'loading_sheet': loading_sheet,
            'loading_sheet_details': loading_sheet_details,
            'dealer': loading_sheet.dealer,
            'transporter': loading_sheet.transporter,
        }
        
        return render(request, 'dealer/mf_print.html', context)
        
    except Exception as e:
        logger.error(f"Error rendering MF Print page: {str(e)}")
        messages.error(request, 'Error loading the print page. Please try again.')
        return redirect('transporter:receive')
    

# transporter_app/views.py


def delivery_cnotes(request):
    return render(request, 'transporter/delivery_cnotes.html')

@require_GET
def search_cnote(request):
    cnote_number = request.GET.get('lrNumber')
    if not cnote_number:
        return JsonResponse({'error': 'LR number is required'}, status=400)

    try:
        cnote = CNotes.objects.get(cnote_number=cnote_number)

        # Try to get the corresponding DeliveryCNote
        try:
            delivery_cnote = DeliveryCNote.objects.get(lr_number=cnote_number)
        except DeliveryCNote.DoesNotExist:
            delivery_cnote = None
        
        # Calculate other charges
        other_charges = cnote.grand_total - cnote.freight if cnote.grand_total and cnote.freight else 0

        # Calculate discount (10% of total charges)
        total_before_discount = cnote.freight + other_charges
        discount = round(total_before_discount * Decimal('0.1'), 2)
        total_after_discount = total_before_discount - discount

        data = {
            'lrNumber': cnote.cnote_number,
            'status': cnote.status,
            'lrType': cnote.payment_type,
            'consignor': {
                'name': cnote.consignor_name,
                'address': cnote.consignor_address,
                'contact': cnote.consignor_mobile,
                'gst': cnote.consignor_gst,
            },
            'consignee': {
                'name': cnote.consignee_name,
                'address': cnote.consignee_address,
                'contact': cnote.consignee_mobile,
                'gst': cnote.consignee_gst,
            },
            'charges': {
                'freight': float(cnote.freight),
                'other': float(other_charges),
                'discount': float(discount),
                'total': float(total_after_discount),
            },
            'weight': {
                'actual': float(cnote.actual_weight),
                'charged': float(cnote.charged_weight),
            },
            'paymentType': cnote.payment_type,
            'deliveryType': cnote.delivery_type,
            'createdAt': cnote.created_at.isoformat() if cnote.created_at else None,
            'statusUpdatedAt': cnote.status_updated_at.isoformat() if cnote.status_updated_at else None,
        }
        # Add delivery details if available
        if delivery_cnote:
            data['deliveryDetails'] = {
                'deliveredToName': delivery_cnote.delivered_to_name,
                'phoneNumber': delivery_cnote.phone_number,
                'idProofType': delivery_cnote.id_proof_type,
                'idProofNumber': delivery_cnote.id_proof_number,
                'remarks': delivery_cnote.remarks,
                'paymentType': delivery_cnote.payment_type,
                'charges': {
                    'freight': float(delivery_cnote.freight_charges),
                    'other': float(delivery_cnote.other_charges),
                    'discount': float(delivery_cnote.discount_amount),
                    'total': float(delivery_cnote.total_amount),
                }
            }
        return JsonResponse(data)
    except CNotes.DoesNotExist:
        return JsonResponse({'error': 'CNotes not found'}, status=404)

@login_required
def ddm_view(request):
    return render(request, 'transporter/ddm.html')


logger = logging.getLogger(__name__)

@csrf_exempt
@require_POST
def submit_delivery(request):
    try:
        data = json.loads(request.body)
        logger.info(f"Received data: {data}")  # Log the incoming data

        with transaction.atomic():
            # Check if the CNotes exists and its current status
            try:
                cnote = CNotes.objects.get(cnote_number=data['lrNumber'])
                if cnote.status == 'Delivered':
                    return JsonResponse({'message': 'CNotes already delivered'}, status=400)
            except CNotes.DoesNotExist:
                return JsonResponse({'error': 'CNotes not found'}, status=404)

            # Update or create DeliveryCNote
            delivery_cnote, created = DeliveryCNote.objects.update_or_create(
                lr_number=data['lrNumber'],
                defaults={
                    'status': 'Delivered',
                    'payment_type': data['paymentType'],
                    'consignor_name': data['consignor']['name'],
                    'consignor_address': data['consignor']['address'],
                    'consignor_contact': data['consignor']['contact'],
                    'consignor_gst': data['consignor']['gst'],
                    'consignee_name': data['consignee']['name'],
                    'consignee_address': data['consignee']['address'],
                    'consignee_contact': data['consignee']['contact'],
                    'consignee_gst': data['consignee']['gst'],
                    'freight_charges': data['charges']['freight'],
                    'other_charges': data['charges']['other'],
                    'discount_amount': data['charges']['discount'],
                    'total_amount': data['charges']['total'],
                    'delivered_to_name': data['deliveredToName'],
                    'phone_number': data['phoneNumber'],
                    'id_proof_type': data['idProofType'],
                    'id_proof_number': data['idProofNumber'],
                    'remarks': data.get('remarks', ''),
                    'delivered_status': True
                }
            )

            # Update status in CNotes table
            cnote.status = 'Delivered'
            cnote.save()

            # Update status in LoadingSheetDetail table
            LoadingSheetDetail.objects.filter(cnote_id=cnote.id).update(status='Delivered')

            # Update status in ReceivedStatesCnotes table
            ReceivedStatesCnotes.objects.filter(cnote_number=data['lrNumber']).update(status='Delivered')

        return JsonResponse({'message': 'Delivery note saved successfully!'}, status=201)
    except Exception as e:
        logger.error(f"Error saving delivery note: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)



def get_destinations(request):
    destinations = DeliveryDestination.objects.filter(
        cnotes__status__in=['received', 'short', 'godown return', 'godown received', 'undelivered']
    ).values_list('destination_name', flat=True).distinct()
    
    destination_list = list(filter(None, destinations))
    
    return JsonResponse(destination_list, safe=False)


logger = logging.getLogger(__name__)

def search_cnotes_for_ddm(request):
    destination = request.GET.get('destination')
    delivery_for = request.GET.get('deliveryFor')
    lr_number = request.GET.get('lrNumber')

    query = CNotes.objects.filter(status__in=['received', 'short', 'godown return', 'godown received', 'undelivered'])

    if destination and destination != "ALL":
        query = query.filter(delivery_destination__destination_name=destination)

    if delivery_for == 'DOOR':
        query = query.filter(delivery_type='DOOR')
    elif delivery_for == 'GODOWN':
        query = query.filter(delivery_type='GODOWN')
    # For 'BOTH', we don't need to filter

    if lr_number:
        query = query.filter(cnote_number__icontains=lr_number)

    results = list(query.values(
    'cnote_number', 
    'consignor_name', 
    'consignee_name', 
    'total_art', 
    'actual_weight', 
    'declared_value', 
    'status',
    delivery_destination_name=F('delivery_destination__destination_name')  # Include the actual name
    ))
    logger.info("Search Results: %s", results)  # Log the results for debugging

    return JsonResponse(results, safe=False)




logger = logging.getLogger(__name__)
@csrf_exempt
@transaction.atomic
def create_delivery_memo(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            logger.info(f"Received data for create_delivery_memo: {data}")

            cnotes = data.get('cnotes', [])
            truck_no = data.get('truckNo', '')
            driver_name = data.get('driverName', '')
            driver_no = data.get('driverNo', '')
            lorry_hire = data.get('lorryHire', 0)
            remarks = data.get('remarks', '')

            if not cnotes:
                return JsonResponse({'status': 'error', 'message': 'No cnotes provided.'}, status=400)

            ddm_no = generate_sequential_ddm_number()
            logger.info(f"Generated DDM number: {ddm_no}")

            # Initialize totals
            total_packages = 0
            total_paid_amount = 0
            total_to_pay_amount = 0
            total_amount = 0

            # Create DDM Summary
            for cnote_number in cnotes:
                cnote = CNotes.objects.get(cnote_number=cnote_number)
                total_packages += cnote.total_art
                total_amount += cnote.grand_total
                if cnote.payment_type == 'paid':
                    total_paid_amount += cnote.grand_total
                elif cnote.payment_type == 'due':
                    total_to_pay_amount += cnote.grand_total

            ddm_summary = DDMSummary.objects.create(
                ddm_no=ddm_no,
                total_cnotes=len(cnotes),
                total_packages=total_packages,
                total_paid_amount=total_paid_amount,
                total_to_pay_amount=total_to_pay_amount,
                total_amount=total_amount,
                creation_date=timezone.now(),
                updated_date=timezone.now(),
                truck_no=truck_no,
                driver_name=driver_name,
                driver_no=driver_no,
                lorry_hire=lorry_hire
            )
            logger.info(f"Created DDM Summary: {ddm_summary.ddm_id}")

            # Create DDM Details for each CNote
            for cnote_number in cnotes:
                cnote = CNotes.objects.get(cnote_number=cnote_number)
                ddm_detail = DDMDetails.objects.create(
                    ddm=ddm_summary,
                    cnote_booking_date=cnote.manual_date,
                    cnote_number=cnote.cnote_number,
                    consignee_name=cnote.consignee_name,
                    contact_number=cnote.consignee_mobile,
                    destination=cnote.delivery_destination,
                    total_pkt=cnote.total_art,
                    amount=cnote.grand_total,
                    payment_type=cnote.payment_type,
                    remark=remarks,
                    dealer_name=cnote.dealer.dealer_code,
                    transporter_name=cnote.consignor_name,
                    status='due delivered',
                    truck_no=truck_no,
                    driver_name=driver_name,
                    driver_no=driver_no,
                    lorry_hire=lorry_hire
                )
                logger.info(f"Created DDM Detail: {ddm_detail.id}")

                # Update status in CNotes
                cnote.status = 'due delivered'
                cnote.save()

                # Update status in LoadingSheetDetail
                LoadingSheetDetail.objects.filter(cnote=cnote).update(status='due delivered')

            return JsonResponse({'status': 'success', 'ddm_no': ddm_no, 'ddm_id': ddm_summary.ddm_id}, status=201)

        except json.JSONDecodeError:
            logger.error("Invalid JSON format in request body.")
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON format.'}, status=400)
        except CNotes.DoesNotExist:
            logger.error("CNote not found.")
            return JsonResponse({'status': 'error', 'message': 'CNote not found.'}, status=404)
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            return JsonResponse({'status': 'error', 'message': 'Internal Server Error.'}, status=500)

@csrf_exempt
def save_ddm_pdf(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            ddm_id = data.get('ddm_id')
            
            ddm_summary = DDMSummary.objects.get(ddm_id=ddm_id)
            ddm_details = DDMDetails.objects.filter(ddm=ddm_summary)

            buffer = io.BytesIO()
            p = canvas.Canvas(buffer, pagesize=letter)

            # Add content to the PDF
            p.drawString(100, 750, f"Door Delivery Memo - {ddm_summary.ddm_no}")
            p.drawString(100, 730, f"Date: {ddm_summary.creation_date.strftime('%Y-%m-%d')}")
            
            y = 700
            for detail in ddm_details:
                p.drawString(100, y, f"CNote: {detail.cnote_number}")
                p.drawString(100, y-15, f"Consignee: {detail.consignee_name}")
                y -= 30

            p.showPage()
            p.save()

            buffer.seek(0)
            return FileResponse(buffer, as_attachment=True, filename=f'DDM-{ddm_summary.ddm_no}.pdf')

        except Exception as e:
            logger.error(f"Error generating PDF: {str(e)}")
            return JsonResponse({'status': 'error', 'message': 'Error generating PDF'}, status=500)
        

class DDMDetailsViewSet(viewsets.ModelViewSet):
    queryset = DDMDetails.objects.all()
    serializer_class = DDMDetailsSerializer

class DDMSummaryViewSet(viewsets.ModelViewSet):
    queryset = DDMSummary.objects.all()
    serializer_class = DDMSummarySerializer

def generate_sequential_ddm_number():
    # Implement your logic to generate a unique sequential DDM number
    # This is a placeholder function
    return "DDM-0001"  # Replace with actual logic to generate a unique number
def generate_sequential_ddm_number():
    with transaction.atomic():
        last_ddm = DDMSummary.objects.select_for_update().order_by('-ddm_id').first()
        
        if last_ddm:
            try:
                last_number = int(last_ddm.ddm_no.split('-')[-1])  # Assuming format is 'DDM-1', 'DDM-2', etc.
                new_number = last_number + 1
            except (ValueError, IndexError):
                raise ValueError(f"Invalid format in DDM number: {last_ddm.ddm_no}")
        else:
            new_number = 1  # Start with 1 if no DDM exists

        while DDMSummary.objects.filter(ddm_no=f"DDM-{new_number}").exists():
            new_number += 1

        return f"DDM-{new_number}"  # Example format: DDM-1, DDM-2, etc.
    
@require_GET
def get_ddm_details(request, ddm_id):
    try:
        ddm_summary = get_object_or_404(DDMSummary, ddm_id=ddm_id)
        ddm_details = DDMDetails.objects.filter(ddm=ddm_summary)

        cnotes_data = []
        total_art = 0
        total_amount = 0

        for detail in ddm_details:
            cnote_data = {
                'cnote_number': detail.cnote_number,
                'consignee_name': detail.consignee_name,
                'consignee_contact': detail.contact_number,
                'delivery_destination': detail.destination,
                'total_art': detail.total_pkt,
                'amount': float(detail.amount),
                'remarks': detail.remark or '',
            }
            cnotes_data.append(cnote_data)
            total_art += detail.total_pkt
            total_amount += detail.amount

        response_data = {
            'ddm_no': ddm_summary.ddm_no,
            'creation_date': ddm_summary.creation_date.strftime('%Y-%m-%d %H:%M:%S'),
            'truck_no': ddm_summary.truck_no,
            'driver_name': ddm_summary.driver_name,
            'driver_no': ddm_summary.driver_no,
            'lorry_hire': float(ddm_summary.lorry_hire),
            'remarks': ddm_summary.remarks or '',
            'cnotes': cnotes_data,
            'total_art': total_art,
            'total_amount': float(total_amount),
        }

        return JsonResponse(response_data)
    except DDMSummary.DoesNotExist:
        return JsonResponse({'error': 'DDM not found'}, status=404)
    except Exception as e:
        logger.error(f"Error in get_ddm_details: {str(e)}")
        return JsonResponse({'error': 'Internal Server Error'}, status=500)



    
@require_GET
def save_ddm_pdf(request, ddm_id):
    # Implement PDF generation logic here
    # For now, we'll just return a success message
    return JsonResponse({'message': 'PDF saved successfully'})


logger = logging.getLogger(__name__)

def ddm_details_view(request):
    try:
        ddm_id = request.GET.get('ddmId')
        if not ddm_id:
            messages.error(request, 'DDM ID is required')
            return redirect('transporter:ddm')

        # Remove 'DDM-' prefix if present
        ddm_id = ddm_id.replace('DDM-', '')
        
        # Get DDM summary
        ddm_summary = get_object_or_404(DDMSummary, ddm_id=ddm_id)
        
        # Get all DDM details
        ddm_details = DDMDetails.objects.filter(ddm=ddm_summary)
        
        total_art = sum(detail.total_pkt for detail in ddm_details)
        total_amount = sum(detail.amount for detail in ddm_details)
        
        context = {
            'ddm_summary': ddm_summary,
            'ddm_details': ddm_details,
            'total_art': total_art,
            'total_amount': total_amount,
            'remarks': ddm_summary.remarks or ''  # Use empty string if remarks is None
        }
        
        return render(request, 'transporter/ddm-details.html', context)
        
    except DDMSummary.DoesNotExist:
        messages.error(request, 'DDM not found')
        return redirect('transporter:ddm')
    except Exception as e:
        logger.error(f"Error in ddm_details_view: {str(e)}")
        messages.error(request, 'Error loading DDM details. Please try again.')
        return redirect('transporter:ddm')

def ddm_settlement(request):
    return render(request, 'transporter/ddm_update.html')  # Ensure the path is correct


logger = logging.getLogger(__name__)

@require_http_methods(["GET"])
def get_ddm_details_for_update(request):
    ddm_no = request.GET.get('ddmNo')
    if not ddm_no:
        return JsonResponse({'error': 'DDM number is required'}, status=400)

    try:
        ddm_summary = get_object_or_404(DDMSummary, ddm_no=ddm_no)
        details = DDMDetails.objects.filter(ddm=ddm_summary)

        data = {
            'ddmNo': ddm_summary.ddm_no,
            'date': ddm_summary.creation_date.isoformat(),
            'totalAmount': float(ddm_summary.total_amount),
            'truckNo': ddm_summary.truck_no,
            'driverName': ddm_summary.driver_name,
            'driverNo': ddm_summary.driver_no,
            'lorryHire': float(ddm_summary.lorry_hire),
            'remarks': ddm_summary.remarks,
            'details': [
                {
                    'id': detail.id,
                    'lrNo': detail.cnote_number,
                    'from': detail.transporter_name,  # Using transporter_name as 'from'
                    'cneeName': detail.consignee_name,
                    'lrType': detail.payment_type,
                    'bookingTotal': float(detail.amount),
                    'art': detail.total_pkt,
                    'rcvDlyAS': detail.status,
                    'deliveryAmount': float(detail.amount),  # Using amount as deliveryAmount
                    'status': detail.status,
                }
                for detail in details
            ]
        }
        logger.info(f"Successfully fetched details for DDM No: {ddm_no}")
        return JsonResponse(data)

    except DDMSummary.DoesNotExist:
        logger.error(f"DDM No {ddm_no} not found")
        return JsonResponse({'error': 'DDM not found'}, status=404)

    except Exception as e:
        logger.error(f"Error fetching DDM details: {str(e)}")
        return JsonResponse({'error': 'An unexpected error occurred'}, status=500)


@csrf_exempt
@require_POST
def update_ddm(request):
    try:
        data = json.loads(request.body)
        id = data.get('id')
        status = data.get('status')
        payment_type = data.get('paymentType')
        reason = data.get('reason', '')

        with transaction.atomic():
            # Update DDM Details
            ddm_detail = DDMDetails.objects.get(id=id)
            ddm_detail.status = status
            ddm_detail.rcv_dly_as = payment_type
            ddm_detail.remark = reason
            ddm_detail.save()

            # Update CNotes status
            cnote = CNotes.objects.get(cnote_number=ddm_detail.cnote_number)
            cnote.status = status
            cnote.save()

            # Update LoadingSheetDetail status
            LoadingSheetDetail.objects.filter(
                cnote=cnote
            ).update(status=status)

            # Update ReceivedStatesCnotes status
            ReceivedStatesCnotes.objects.filter(
                cnote_number=ddm_detail.cnote_number
            ).update(status=status)

            # Update DeliveryCNote if it exists
            DeliveryCNote.objects.filter(
                lr_number=ddm_detail.cnote_number
            ).update(status=status)

        return JsonResponse({
            'status': 'success', 
            'message': 'DDM detail and related records updated successfully'
        })
    except DDMDetails.DoesNotExist:
        return JsonResponse({
            'status': 'error', 
            'message': 'DDM detail not found'
        }, status=404)
    except CNotes.DoesNotExist:
        return JsonResponse({
            'status': 'error', 
            'message': 'CNotes record not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error', 
            'message': str(e)
        }, status=500)

def cnotes_search(request):
    return render(request, 'transporter/cnotes_search.html')

@csrf_exempt
@require_http_methods(["GET", "PUT"])
def cnote_detail(request, cnote_number):
    cnote = get_object_or_404(CNotes, cnote_number=cnote_number)

    if request.method == "GET":
        return get_cnote(request, cnote)
    elif request.method == "PUT":
        return update_cnote(request, cnote)

def get_cnote(request, cnote):
    articles = [
        {
            'article_type': article.article_type,
            'quantity': article.art,
            'description': article.said_to_contain,
            'amount': float(article.art_amount) if article.art_amount else 0
        } for article in cnote.articles.all()
    ]

    status_history = [
        {
            'status': detail.status,
            'status_no': detail.loading_sheet.ls_number,
            'detail': f"LR No.: {cnote.cnote_number}",
            'date': detail.loading_sheet.created_at.strftime('%d-%m-%y %I:%M %p'),
            'on_day': (detail.loading_sheet.created_at.date() - cnote.created_at.date()).days + 1,
            'user': detail.loading_sheet.dealer.name,
            'branch': detail.loading_sheet.dealer.company_name,
            'from': detail.loading_sheet.dealer.city,
            'to': detail.destination,
            'remark': detail.remark,
            'ls_remark': f"LS Number: {detail.loading_sheet.ls_number}"
        } for detail in cnote.loading_sheet_details.all().order_by('-loading_sheet__created_at')
    ]

    response_data = {
        'cnote_number': cnote.cnote_number,
        'created_at': cnote.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'booking_type': cnote.booking_type,
        'delivery_type': cnote.delivery_type,
        'delivery_method': cnote.delivery_method,
        'delivery_destination': cnote.delivery_destination.destination_name if cnote.delivery_destination else None,
        'eway_bill_number': cnote.eway_bill_number,
        'manual_date': cnote.manual_date.strftime('%Y-%m-%d') if cnote.manual_date else None,
        'manual_cnote_number': cnote.manual_cnote_number,
        'manual_cnote_type': cnote.manual_cnote_type,
        'payment_type': cnote.payment_type,
        'consignor_name': cnote.consignor_name,
        'consignor_address': cnote.consignor_address,
        'consignor_mobile': cnote.consignor_mobile,
        'consignor_gst': cnote.consignor_gst,
        'consignee_name': cnote.consignee_name,
        'consignee_address': cnote.consignee_address,
        'consignee_mobile': cnote.consignee_mobile,
        'consignee_gst': cnote.consignee_gst,
        'actual_weight': float(cnote.actual_weight) if cnote.actual_weight else 0,
        'charged_weight': float(cnote.charged_weight) if cnote.charged_weight else 0,
        'weight_rate': float(cnote.weight_rate) if cnote.weight_rate else 0,
        'weight_amount': float(cnote.weight_amount) if cnote.weight_amount else 0,
        'fix_amount': float(cnote.fix_amount) if cnote.fix_amount else 0,
        'invoice_number': cnote.invoice_number,
        'declared_value': float(cnote.declared_value) if cnote.declared_value else 0,
        'risk_type': cnote.risk_type,
        'pod_required': cnote.pod_required,
        'freight': float(cnote.freight) if cnote.freight else 0,
        'docket_charge': float(cnote.docket_charge) if cnote.docket_charge else 0,
        'door_delivery_charge': float(cnote.door_delivery_charge) if cnote.door_delivery_charge else 0,
        'handling_charge': float(cnote.handling_charge) if cnote.handling_charge else 0,
        'pickup_charge': float(cnote.pickup_charge) if cnote.pickup_charge else 0,
        'transhipment_charge': float(cnote.transhipment_charge) if cnote.transhipment_charge else 0,
        'insurance': float(cnote.insurance) if cnote.insurance else 0,
        'fuel_surcharge': float(cnote.fuel_surcharge) if cnote.fuel_surcharge else 0,
        'commission': float(cnote.commission) if cnote.commission else 0,
        'other_charge': float(cnote.other_charge) if cnote.other_charge else 0,
        'carrier_risk': float(cnote.carrier_risk) if cnote.carrier_risk else 0,
        'grand_total': float(cnote.grand_total) if cnote.grand_total else 0,
        'status': cnote.status,
        'status_updated_at': cnote.status_updated_at.strftime('%Y-%m-%d %H:%M:%S'),
        'total_art': cnote.total_art,
        'articles': articles,
        'status_history': status_history,
        'changes_history': []  # Placeholder for changes history
    }

    return JsonResponse(response_data)

def update_cnote(request, cnote):
    try:
        data = json.loads(request.body)

        fields_to_update = [
            'consignor_name', 'consignor_address', 'consignor_mobile', 'consignor_gst',
            'consignee_name', 'consignee_address', 'consignee_mobile', 'consignee_gst',
            'freight', 'door_delivery_charge', 'handling_charge', 'other_charge',
            'delivery_destination', 'eway_bill_number', 'delivery_method'
        ]

        changes = []
        for field in fields_to_update:
            if field in data and getattr(cnote, field) != data[field]:
                old_value = getattr(cnote, field)
                setattr(cnote, field, data[field])
                changes.append({
                    'field': field,
                    'old_value': str(old_value),
                    'new_value': str(data[field]),
                    'user': request.user.username if request.user.is_authenticated else 'Anonymous',
                    'date': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
                })

        cnote.grand_total = (
            float(cnote.freight) +
            float(cnote.door_delivery_charge) +
            float(cnote.handling_charge) +
            float(cnote.other_charge)
        )
        cnote.save()

        updated_data = get_cnote(request, cnote).content
        updated_data = json.loads(updated_data)
        updated_data['changes'] = changes

        return JsonResponse(updated_data)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        return super(CustomJSONEncoder, self).default(obj)

@login_required
def all_booking_register(request):
    return render(request, 'transporter/all_booking_register.html')

@login_required
def booking_register_data(request):
    try:
        logger.info("Starting booking_register_data function")
        
        # Get search parameters from the request
        search_term = request.GET.get('search', '').lower()
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        dealer = request.GET.get('dealer', '').lower()
        from_city = request.GET.get('from_city', '').lower()
        to_city = request.GET.get('to_city', '').lower()
        amount_min = request.GET.get('amount_min')
        amount_max = request.GET.get('amount_max')
        cnote_number = request.GET.get('cnote_number', '').lower()
        ls_number = request.GET.get('ls_number', '').lower()
        ddm_number = request.GET.get('ddm_number', '').lower()

        with connection.cursor() as cursor:
            logger.info("Executing SQL query")
            query = """
                SELECT 
                    c.*,
                    STRING_AGG(DISTINCT a.art_type_id::text, '/') as art_types,
                    STRING_AGG(DISTINCT a.said_to_contain, '/') as said_to_contain,
                    STRING_AGG(DISTINCT a.art_amount::text, '/') as art_amounts,
                    d.name as dealer_name,
                    dd.destination_name as delivery_destination,
                    CASE 
                        WHEN EXISTS (
                            SELECT 1 FROM dealer_app_dealer 
                            WHERE name = d.name
                        ) THEN 'Dealer'
                        ELSE 'Transporter'
                    END as user_type,
                    ls.ls_number as loading_sheet_number,
                    ddm.ddm_no as ddm_number
                FROM dealer_app_cnotes c
                LEFT JOIN dealer_app_article a ON c.id = a.cnote_id
                LEFT JOIN dealer_app_dealer d ON c.dealer_id = d.dealer_id
                LEFT JOIN dealer_app_deliverydestination dd ON c.delivery_destination_id = dd.id
                LEFT JOIN dealer_app_loadingsheetdetail lsd ON c.id = lsd.cnote_id
                LEFT JOIN dealer_app_loadingsheetsummary ls ON lsd.loading_sheet_id = ls.ls_number
                LEFT JOIN transporter_app_ddmdetails ddmd ON c.cnote_number = ddmd.cnote_number
                LEFT JOIN transporter_app_ddmsummary ddm ON ddmd.ddm_id = ddm.ddm_id
                WHERE 1=1
            """
            
            params = []

            if search_term:
                query += """ AND (
                    LOWER(c.cnote_number) LIKE %s OR
                    LOWER(c.consignor_name) LIKE %s OR
                    LOWER(c.consignee_name) LIKE %s OR
                    LOWER(d.name) LIKE %s
                )"""
                params.extend(['%' + search_term + '%'] * 4)

            if date_from:
                query += " AND c.created_at >= %s"
                params.append(date_from)

            if date_to:
                query += " AND c.created_at <= %s"
                params.append(date_to)

            if dealer:
                query += " AND LOWER(d.name) LIKE %s"
                params.append('%' + dealer + '%')

            if from_city:
                query += " AND LOWER(SPLIT_PART(dd.destination_name, ' - ', 1)) LIKE %s"
                params.append('%' + from_city + '%')

            if to_city:
                query += " AND LOWER(SPLIT_PART(dd.destination_name, ' - ', 2)) LIKE %s"
                params.append('%' + to_city + '%')

            if amount_min:
                query += " AND c.grand_total >= %s"
                params.append(float(amount_min))

            if amount_max:
                query += " AND c.grand_total <= %s"
                params.append(float(amount_max))

            if cnote_number:
                query += " AND LOWER(c.cnote_number) LIKE %s"
                params.append('%' + cnote_number + '%')

            if ls_number:
                query += " AND LOWER(ls.ls_number::text) LIKE %s"
                params.append('%' + ls_number + '%')

            if ddm_number:
                query += " AND LOWER(ddm.ddm_no) LIKE %s"
                params.append('%' + ddm_number + '%')

            query += """
                GROUP BY 
                    c.id,
                    d.name,
                    dd.destination_name,
                    ls.ls_number,
                    ddm.ddm_no
                ORDER BY c.created_at DESC
            """

            cursor.execute(query, params)
            cnotes = cursor.fetchall()
            logger.info(f"Fetched {len(cnotes)} records from the database")

        cnotes_data = []
        for index, cnote in enumerate(cnotes):
            logger.debug(f"Processing record {index + 1}")
            cnote_data = dict(zip([col[0] for col in cursor.description], cnote))
            
            art_types = cnote_data.get('art_types')
            said_to_contain = cnote_data.get('said_to_contain')
            art_amounts = cnote_data.get('art_amounts')

            cnote_data['art_types'] = art_types.split('/') if art_types else []
            cnote_data['said_to_contain'] = said_to_contain.split('/') if said_to_contain else []
            cnote_data['art_amounts'] = [float(x) if x and x.replace('.', '').isdigit() else 0 for x in art_amounts.split('/')] if art_amounts else []

            cnote_data['user'] = cnote_data.get('dealer_name') or 'N/A'
            cnote_data['user_type'] = cnote_data.get('user_type') or 'Unknown'
            cnote_data['loading_sheet_number'] = cnote_data.get('loading_sheet_number') or 'N/A'
            cnote_data['ddm_number'] = cnote_data.get('ddm_number') or 'N/A'

            for key, value in cnote_data.items():
                if isinstance(value, Decimal):
                    cnote_data[key] = float(value)
                elif isinstance(value, datetime):
                    cnote_data[key] = value.isoformat()

            cnotes_data.append(cnote_data)

        response_data = {
            'bookings': cnotes_data,
            'transporter_name': request.user.transporter.name if hasattr(request.user, 'transporter') else 'N/A',
            'transporter_city': request.user.transporter.city if hasattr(request.user, 'transporter') else 'N/A'
        }
        json_data = json.dumps(response_data, cls=CustomJSONEncoder)

        return HttpResponse(json_data, content_type='application/json')
    except Exception as e:
        logger.error(f"Error in booking_register_data: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def booking_register_view(request):
    return render(request, 'transporter/booking_register.html')

@login_required
def download_excel(request):
    try:
        logger.info("Starting download_excel function")
        
        with connections['default'].cursor() as cursor:
            cursor.execute("""
                SELECT 
                    c.*,
                    STRING_AGG(DISTINCT a.art_type_id::text, '/') as art_types,
                    STRING_AGG(DISTINCT a.said_to_contain, '/') as said_to_contain,
                    STRING_AGG(DISTINCT a.art_amount::text, '/') as art_amounts,
                    d.name as dealer_name,
                    dd.destination_name as delivery_destination,
                    CASE 
                        WHEN EXISTS (
                            SELECT 1 FROM dealer_app_dealer 
                            WHERE name = d.name
                        ) THEN 'Dealer'
                        ELSE 'Transporter'
                    END as user_type,
                    ls.ls_number as loading_sheet_number,
                    ddm.ddm_no as ddm_number
                FROM dealer_app_cnotes c
                LEFT JOIN dealer_app_article a ON c.id = a.cnote_id
                LEFT JOIN dealer_app_dealer d ON c.dealer_id = d.dealer_id
                LEFT JOIN dealer_app_deliverydestination dd ON c.delivery_destination_id = dd.id
                LEFT JOIN dealer_app_loadingsheetdetail lsd ON c.id = lsd.cnote_id
                LEFT JOIN dealer_app_loadingsheetsummary ls ON lsd.loading_sheet_id = ls.ls_number
                LEFT JOIN transporter_app_ddmdetails ddmd ON c.cnote_number = ddmd.cnote_number
                LEFT JOIN transporter_app_ddmsummary ddm ON ddmd.ddm_id = ddm.ddm_id
                GROUP BY 
                    c.id,
                    d.name,
                    dd.destination_name,
                    ls.ls_number,
                    ddm.ddm_no
                ORDER BY c.created_at DESC
            """)
            columns = [col[0] for col in cursor.description]
            bookings = [dict(zip(columns, row)) for row in cursor.fetchall()]

        logger.info(f"Fetched {len(bookings)} records for Excel download")

        # Process the data
        for booking in bookings:
            booking['art_types'] = booking['art_types'].split('/') if booking['art_types'] else []
            booking['said_to_contain'] = booking['said_to_contain'].split('/') if booking['said_to_contain'] else []
            booking['art_amounts'] = [float(x) if x and x.replace('.', '').isdigit() else 0 for x in booking['art_amounts'].split('/')] if booking['art_amounts'] else []

        # Convert to DataFrame
        df = pd.DataFrame(bookings)

        # Convert timezone-aware datetimes to timezone-naive
        for col in df.select_dtypes(include=['datetime64[ns, UTC]']).columns:
            df[col] = df[col].apply(lambda x: make_naive(x) if x is not pd.NaT else x)

        # Create an HTTP response with the Excel file
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="bookings.xlsx"'

        # Use Pandas to write the DataFrame to the response
        with pd.ExcelWriter(response, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Bookings')

        logger.info("Excel file generated successfully")
        return response
    except Exception as e:
        logger.error(f"Error in download_excel: {str(e)}", exc_info=True)
        return HttpResponse(f"Error generating Excel: {e}", status=500)
