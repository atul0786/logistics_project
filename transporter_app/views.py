import json
import logging
import csv
import io
from decimal import Decimal
from django.db import IntegrityError
import datetime
import pandas as pd
from datetime import datetime  # Import the datetime class
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib import messages
import json
from decimal import Decimal
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.utils import timezone
from datetime import datetime
import logging
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
from dealer_app.models import CustomUser  # Replace `your_app_name` with your app's actual name
from dealer_app.models import Dealer, CNotes, Article  # Correct imports
from transporter_app.models import Bill, BillItem
from django.shortcuts import render
from django.http import HttpResponse
from .models import Bill, BillItem  # Adjust model imports based on your project
from django.template.loader import get_template  # Import get_template
from io import BytesIO
from django.http import FileResponse
import os
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
    
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .forms import CityForm
from .models import City

@login_required
def add_city(request):
    if request.method == 'POST':
        form = CityForm(request.POST)
        if form.is_valid():
            city = form.save()
            return JsonResponse({'city': {
                'id': city.id,
                'name': city.name,
                'state': city.state.id,
                'description': city.description
            }})
        return JsonResponse({'error': form.errors.as_json()}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=400)
    
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

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from .models import City, State
from .forms import CityForm
from django.db.models import ProtectedError

@login_required
def edit_city(request, id):
    """
    Handle GET requests to fetch city data for editing and POST requests to update a city.
    Returns JSON with city data or validation errors.
    """
    city = get_object_or_404(City, id=id)
    if request.method == 'GET':
        return JsonResponse({
            'city': {
                'id': city.id,
                'name': city.name,
                'state': city.state.id,
                'description': city.description
            }
        })
    elif request.method == 'POST':
        form = CityForm(request.POST, instance=city)
        if form.is_valid():
            city = form.save()
            return JsonResponse({
                'city': {
                    'id': city.id,
                    'name': city.name,
                    'state': city.state.id,
                    'description': city.description
                }
            })
        return JsonResponse({'error': form.errors.as_json()}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@login_required
def delete_city(request, id):
    """
    Handle POST requests to delete a city.
    Returns JSON indicating success or error.
    """
    if request.method == 'POST':
        city = get_object_or_404(City, id=id)
        try:
            city.delete()
            return JsonResponse({'message': 'City deleted successfully'})
        except ProtectedError:
            return JsonResponse({'error': 'Cannot delete city because it is linked to other records (e.g., CNotes or Delivery Destinations).'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=400)

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

@require_http_methods(["GET"])
def get_party_master_records(request):
    records = PartyMaster.objects.all().values()
    return JsonResponse(list(records), safe=False, encoder=DjangoJSONEncoder)

@require_http_methods(["GET"])
def get_party(request, party_id):
    try:
        party = PartyMaster.objects.get(id=party_id)
        data = {
            'id': party.id,
            'party_code': party.party_code,
            'party_name': party.party_name,
            'display_name': party.display_name,
            'mobile_number_1': party.mobile_number_1,
            'mobile_number_2': party.mobile_number_2,
            'phone_number_1': party.phone_number_1,
            'phone_number_2': party.phone_number_2,
            'gst_no': party.gst_no,
            'pan_no': party.pan_no,
            'email': party.email,
            'marketing_person': party.marketing_person,
            'party_type': party.party_type,
            'country': party.country,
            'state': party.state,
            'city': party.city,
            'pincode': party.pincode,
            'address': party.address,
            'is_tbb': party.is_tbb,
            'remark': party.remark,
            'created_at': party.created_at.isoformat(),
            'updated_at': party.updated_at.isoformat(),
        }
        return JsonResponse(data)
    except PartyMaster.DoesNotExist:
        return JsonResponse({'error': 'Party not found'}, status=404)

@require_http_methods(["POST"])
def delete_party(request, party_id):
    try:
        party = PartyMaster.objects.get(id=party_id)
        party.delete()
        return JsonResponse({
            'success': True,
            'message': 'Party successfully deleted'
        })
    except PartyMaster.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Party not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

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

@require_http_methods(["GET", "POST"])
def edit_party(request, party_id):
    try:
        party = PartyMaster.objects.get(id=party_id)
        
        if request.method == "GET":
            data = {
                'id': party.id,
                'party_code': party.party_code,
                'party_name': party.party_name,
                'display_name': party.display_name,
                'mobile_number_1': party.mobile_number_1,
                'mobile_number_2': party.mobile_number_2,
                'phone_number_1': party.phone_number_1,
                'phone_number_2': party.phone_number_2,
                'gst_no': party.gst_no,
                'pan_no': party.pan_no,
                'email': party.email,
                'marketing_person': party.marketing_person,
                'party_type': party.party_type,
                'country': party.country,
                'state': party.state,
                'city': party.city,
                'pincode': party.pincode,
                'address': party.address,
                'is_tbb': party.is_tbb,
                'remark': party.remark,
            }
            return JsonResponse(data)
        
        elif request.method == "POST":
            data = json.loads(request.body)
            for key, value in data.items():
                setattr(party, key, value)
            party.save()
            return JsonResponse({
                'success': True,
                'message': 'Party successfully updated'
            })
    
    except PartyMaster.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Party not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


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
    """
    Create a Delivery Memo (DDM) with associated details for given CNotes.
    Returns a JSON response with the DDM number and ID on success.
    """
    if request.method != 'POST':
        logger.warning(f"Invalid request method: {request.method}")
        return JsonResponse({'status': 'error', 'message': 'Method not allowed.'}, status=405)

    try:
        # Parse request body
        data = json.loads(request.body)
        logger.info(f"Received data for create_delivery_memo: {data}")

        # Extract and validate required fields
        cnotes = data.get('cnotes', [])
        truck_no = data.get('truckNo', '').strip()
        driver_name = data.get('driverName', '').strip()
        driver_no = data.get('driverNo', '').strip()
        lorry_hire = data.get('lorryHire', 0)
        remarks = data.get('remarks', '').strip()

        # Validate inputs
        if not cnotes:
            logger.error("No CNotes provided in the request.")
            return JsonResponse({'status': 'error', 'message': 'At least one CNote number is required.'}, status=400)

        if not isinstance(cnotes, list):
            logger.error("CNotes must be provided as a list.")
            return JsonResponse({'status': 'error', 'message': 'CNotes must be a list.'}, status=400)

        if not truck_no:
            logger.error("Truck number is required.")
            return JsonResponse({'status': 'error', 'message': 'Truck number is required.'}, status=400)

        # Generate DDM number
        ddm_no = generate_sequential_ddm_number()
        logger.info(f"Generated DDM number: {ddm_no}")

        # Fetch all CNotes in one query with related dealer and delivery_destination
        cnote_numbers_set = set(cnotes)  # Remove duplicates
        cnotes_qs = CNotes.objects.select_related('dealer', 'delivery_destination').filter(
            cnote_number__in=cnote_numbers_set
        )

        # Check if all requested CNotes exist
        found_cnotes = {cnote.cnote_number: cnote for cnote in cnotes_qs}
        missing_cnotes = cnote_numbers_set - set(found_cnotes.keys())
        if missing_cnotes:
            logger.error(f"CNotes not found: {missing_cnotes}")
            return JsonResponse(
                {'status': 'error', 'message': f"CNotes not found: {', '.join(missing_cnotes)}"},
                status=404
            )

        # Initialize totals for DDM Summary
        total_packages = 0
        total_paid_amount = 0
        total_to_pay_amount = 0
        total_amount = 0

        # Calculate totals
        for cnote_number in cnotes:
            cnote = found_cnotes[cnote_number]
            total_packages += cnote.total_art or 0
            total_amount += cnote.grand_total or 0
            if cnote.payment_type == 'paid':
                total_paid_amount += cnote.grand_total or 0
            elif cnote.payment_type == 'due':
                total_to_pay_amount += cnote.grand_total or 0

        # Create DDM Summary
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

        # Create DDM Details for each CNote (Standard Approach)
        for cnote_number in cnotes:
            cnote = found_cnotes[cnote_number]
            logger.info(
                f"Processing CNote {cnote_number}, destination: {cnote.delivery_destination}, "
                f"booking_date: {cnote.created_at.date()}"
            )

            # Handle None values with fallbacks and use destination_name
            destination = (
                getattr(cnote.delivery_destination, 'destination_name', 'Unknown')
                if cnote.delivery_destination else 'Unknown'
            )
            consignee_name = cnote.consignee_name or ''
            contact_number = cnote.consignee_mobile or ''
            payment_type = cnote.payment_type or 'PAID'
            dealer_name = cnote.dealer.dealer_code if cnote.dealer else 'N/A'
            transporter_name = cnote.consignor_name or ''

            # Create DDM Detail
            ddm_detail = DDMDetails.objects.create(
                ddm=ddm_summary,
                cnote_booking_date=cnote.created_at.date(),  # Use created_at.date() to avoid NULL
                cnote_number=cnote.cnote_number,
                consignee_name=consignee_name,
                contact_number=contact_number,
                destination=destination,
                total_pkt=cnote.total_art or 0,
                amount=cnote.grand_total or 0,
                payment_type=payment_type,
                remark=remarks,
                dealer_name=dealer_name,
                transporter_name=transporter_name,
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

        # Optional: Bulk Creation Approach for DDM Details (Uncomment to use)
        """
        ddm_details_list = []
        for cnote_number in cnotes:
            cnote = found_cnotes[cnote_number]
            logger.info(
                f"Processing CNote {cnote_number}, destination: {cnote.delivery_destination}, "
                f"booking_date: {cnote.created_at.date()}"
            )

            # Handle None values with fallbacks and use destination_name
            destination = (
                getattr(cnote.delivery_destination, 'destination_name', 'Unknown')
                if cnote.delivery_destination else 'Unknown'
            )
            consignee_name = cnote.consignee_name or ''
            contact_number = cnote.consignee_mobile or ''
            payment_type = cnote.payment_type or 'PAID'
            dealer_name = cnote.dealer.dealer_code if cnote.dealer else 'N/A'
            transporter_name = cnote.consignor_name or ''

            ddm_details_list.append(
                DDMDetails(
                    ddm=ddm_summary,
                    cnote_booking_date=cnote.created_at.date(),
                    cnote_number=cnote.cnote_number,
                    consignee_name=consignee_name,
                    contact_number=contact_number,
                    destination=destination,
                    total_pkt=cnote.total_art or 0,
                    amount=cnote.grand_total or 0,
                    payment_type=payment_type,
                    remark=remarks,
                    dealer_name=dealer_name,
                    transporter_name=transporter_name,
                    status='due delivered',
                    truck_no=truck_no,
                    driver_name=driver_name,
                    driver_no=driver_no,
                    lorry_hire=lorry_hire
                )
            )

        # Bulk create DDM Details
        if ddm_details_list:
            created_ddm_details = DDMDetails.objects.bulk_create(ddm_details_list)
            logger.info(f"Created {len(created_ddm_details)} DDM Details in bulk.")

        # Update statuses after bulk creation
        for cnote_number in cnotes:
            cnote = found_cnotes[cnote_number]
            cnote.status = 'due delivered'
            cnote.save()
            LoadingSheetDetail.objects.filter(cnote=cnote).update(status='due delivered')
        """

        return JsonResponse(
            {
                'status': 'success',
                'ddm_no': ddm_no,
                'ddm_id': ddm_summary.ddm_id,
                'message': 'Delivery Memo created successfully.'
            },
            status=201
        )

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON format in request body: {str(e)}")
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON format.'}, status=400)

    except ValueError as e:
        logger.error(f"Value error in request processing: {str(e)}")
        return JsonResponse({'status': 'error', 'message': f'Invalid data: {str(e)}'}, status=400)

    except Exception as e:
        logger.error(f"Unexpected error in create_delivery_memo: {str(e)}", exc_info=True)
        return JsonResponse(
            {'status': 'error', 'message': 'Internal Server Error. Please contact support.'},
            status=500
        )

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
    


logger = logging.getLogger(__name__)

@require_GET
def get_ddm_details(request, ddm_id):
    try:
        # ✅ Fetch DDM Summary
        ddm_summary = get_object_or_404(DDMSummary, ddm_id=ddm_id)

        # ✅ Fetch all related DDM Details
        ddm_details = DDMDetails.objects.filter(ddm=ddm_summary)

        cnotes_data = []
        total_art = 0
        total_amount = 0

        for detail in ddm_details:
            try:
                # ✅ Step 1: Fetch CNote
                cnote = CNotes.objects.get(cnote_number=detail.cnote_number)
                cnote_date = cnote.created_at.date().strftime('%Y-%m-%d') if cnote.created_at else "N/A"
                
                # ✅ Step 2: Get total_art from dealer_app_article
                total_packets = Article.objects.filter(cnote_id=cnote.id).aggregate(total_art=Sum('art'))['total_art'] or 0
                
                # ✅ Step 3: Fetch Payment Type from CNotes table
                payment_type = cnote.payment_type if cnote.payment_type else "N/A"
                
                logger.info(f"Total PKG for {detail.cnote_number}: {total_packets} (From: dealer_app_article)")
            
            except CNotes.DoesNotExist:
                logger.warning(f"CNotes Not Found: {detail.cnote_number}")
                cnote_date = "N/A"
                total_packets = 0  # Default to 0
                payment_type = "N/A"  # Default Payment Type

            cnote_data = {
                'cnote_number': detail.cnote_number,
                'date': cnote_date,
                'consignee_name': detail.consignee_name,
                'consignee_contact': detail.contact_number,
                'delivery_destination': detail.destination,
                'total_art': total_packets,  # ✅ Now correctly calculated!
                'amount': float(detail.amount) if detail.amount else 0,
                'cn_type': payment_type,  # ✅ Correctly fetched CN Type
                'remarks': detail.remark or '',
            }
            cnotes_data.append(cnote_data)
            total_art += total_packets
            total_amount += detail.amount if detail.amount else 0

        # ✅ Fix `creation_date`
        creation_date = ddm_summary.creation_date.strftime('%Y-%m-%d') if ddm_summary.creation_date else "N/A"

        response_data = {
            'ddm_no': ddm_summary.ddm_no,
            'creation_date': creation_date,
            'truck_no': ddm_summary.truck_no,
            'driver_name': ddm_summary.driver_name,
            'driver_no': ddm_summary.driver_no,
            'lorry_hire': float(ddm_summary.lorry_hire) if ddm_summary.lorry_hire else 0,
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

        # Remove 'DDM-' prefix if present (More flexible)
        ddm_id = ddm_id.replace('DDM-', '') if ddm_id.startswith('DDM-') else ddm_id

        # Get DDM summary
        ddm_summary = get_object_or_404(DDMSummary, ddm_id=ddm_id)

        # Get all DDM details
        ddm_details = DDMDetails.objects.filter(ddm=ddm_summary)

        # Ensure `None` values don’t cause errors
        total_art = sum(detail.total_pkt or 0 for detail in ddm_details)
        total_amount = sum(detail.amount or 0 for detail in ddm_details)

        context = {
            'ddm_summary': ddm_summary,
            'ddm_details': ddm_details,
            'total_art': total_art,
            'total_amount': total_amount,
            'remarks': ddm_summary.remarks or '',  # Use empty string if None
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
    
# Import models
from dealer_app.models import (
    CustomUser, Dealer, CNotes, Article, LoadingSheetSummary, 
    LoadingSheetDetail, DeliveryDestination, ArtType
)
from transporter_app.models import (
    DDMSummary, DDMDetails, DeliveryCNote, ReceivedStatesCnotes,
    Transporter, State, City, PartyMaster, Pickup, TransporterAppReceive,
    CNote, Bill, BillItem
)
from .forms import StateForm, CityForm, PartyMasterForm
from .serializers import DDMDetailsSerializer, DDMSummarySerializer

# Set up logging
logger = logging.getLogger(__name__)
User = get_user_model()

class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle Decimal and datetime objects"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        return super(CustomJSONEncoder, self).default(obj)

@login_required
def all_booking_register(request):
    """Render the all booking register page"""
    try:
        return render(request, 'transporter/all_booking_register.html')
    except Exception as e:
        logger.error(f"Error rendering all booking register page: {str(e)}")
        messages.error(request, "Error loading the booking register page.")
        return redirect('transporter:home')

@login_required
def booking_register_data(request):
    """
    Fetch booking register data with optimized queries and proper error handling
    """
    try:
        logger.info("Starting booking_register_data function")
        
        # Get search parameters
        search_params = {
            'search': request.GET.get('search', '').strip().lower(),
            'date_from': request.GET.get('date_from'),
            'date_to': request.GET.get('date_to'),
            'dealer': request.GET.get('dealer', '').strip().lower(),
            'from_city': request.GET.get('from_city', '').strip().lower(),
            'to_city': request.GET.get('to_city', '').strip().lower(),
            'amount_min': request.GET.get('amount_min'),
            'amount_max': request.GET.get('amount_max'),
            'cnote_number': request.GET.get('cnote_number', '').strip().lower(),
            'ls_number': request.GET.get('ls_number', '').strip().lower(),
            'ddm_number': request.GET.get('ddm_number', '').strip().lower(),
        }

        # Build optimized query using Django ORM instead of raw SQL
        cnotes_query = CNotes.objects.select_related(
            'dealer', 'delivery_destination'
        ).prefetch_related(
            'articles__art_type',
            'loading_sheet_details__loading_sheet',
            'ddm_details__ddm'
        )

        # Apply filters
        cnotes_query = apply_booking_filters(cnotes_query, search_params)
        
        # Limit results for performance (max 1000 records)
        cnotes = cnotes_query.order_by('-created_at')[:1000]
        
        # Process data
        cnotes_data = []
        for cnote in cnotes:
            try:
                cnote_data = process_cnote_data(cnote)
                cnotes_data.append(cnote_data)
            except Exception as e:
                logger.warning(f"Error processing CNotes {cnote.cnote_number}: {str(e)}")
                continue

        logger.info(f"Successfully processed {len(cnotes_data)} records")
        
        # Get transporter info
        transporter_info = get_transporter_info(request.user)
        
        response_data = {
            'bookings': cnotes_data,
            'transporter_name': transporter_info['name'],
            'transporter_city': transporter_info['city'],
            'total_records': len(cnotes_data)
        }
        
        return JsonResponse(response_data, encoder=CustomJSONEncoder)
        
    except Exception as e:
        logger.error(f"Error in booking_register_data: {str(e)}", exc_info=True)
        return JsonResponse({
            'error': 'An error occurred while fetching booking data',
            'message': str(e)
        }, status=500)

def apply_booking_filters(query, params):
    """Apply filters to the booking query"""
    
    # Date range filter
    if params['date_from']:
        try:
            from_date = datetime.strptime(params['date_from'], '%Y-%m-%d').date()
            query = query.filter(created_at__date__gte=from_date)
        except ValueError:
            logger.warning(f"Invalid from_date format: {params['date_from']}")
    
    if params['date_to']:
        try:
            to_date = datetime.strptime(params['date_to'], '%Y-%m-%d').date()
            query = query.filter(created_at__date__lte=to_date)
        except ValueError:
            logger.warning(f"Invalid to_date format: {params['date_to']}")
    
    # Search term filter
    if params['search']:
        query = query.filter(
            Q(cnote_number__icontains=params['search']) |
            Q(consignor_name__icontains=params['search']) |
            Q(consignee_name__icontains=params['search']) |
            Q(dealer__name__icontains=params['search'])
        )
    
    # Dealer filter
    if params['dealer']:
        query = query.filter(dealer__name__icontains=params['dealer'])
    
    # Amount range filters
    if params['amount_min']:
        try:
            min_amount = float(params['amount_min'])
            query = query.filter(grand_total__gte=min_amount)
        except (ValueError, TypeError):
            logger.warning(f"Invalid amount_min: {params['amount_min']}")
    
    if params['amount_max']:
        try:
            max_amount = float(params['amount_max'])
            query = query.filter(grand_total__lte=max_amount)
        except (ValueError, TypeError):
            logger.warning(f"Invalid amount_max: {params['amount_max']}")
    
    # CNotes number filter
    if params['cnote_number']:
        query = query.filter(cnote_number__icontains=params['cnote_number'])
    
    # Loading sheet number filter
    if params['ls_number']:
        query = query.filter(loading_sheet_details__loading_sheet__ls_number__icontains=params['ls_number'])
    
    # DDM number filter
    if params['ddm_number']:
        query = query.filter(ddm_details__ddm__ddm_no__icontains=params['ddm_number'])
    
    return query.distinct()

def process_cnote_data(cnote):
    """Process individual CNotes data"""
    
    # Get articles data
    articles = cnote.articles.all()
    art_types = []
    said_to_contain = []
    art_amounts = []
    total_articles = 0
    
    for article in articles:
        art_type_name = article.art_type.art_type_name if article.art_type else 'N/A'
        art_types.append(art_type_name)
        
        contain_info = f"{article.said_to_contain or 'N/A'} ({article.art or 0})"
        said_to_contain.append(contain_info)
        
        art_amounts.append(float(article.art_amount or 0))
        total_articles += article.art or 0
    
    # Get loading sheet info
    loading_sheet_detail = cnote.loading_sheet_details.first()
    loading_sheet_number = loading_sheet_detail.loading_sheet.ls_number if loading_sheet_detail else 'N/A'
    
    # Get DDM info
    ddm_detail = cnote.ddm_details.first()
    ddm_number = ddm_detail.ddm.ddm_no if ddm_detail else 'N/A'
    
    # Determine user type
    user_type = 'Dealer' if cnote.dealer else 'Unknown'
    
    return {
        'id': cnote.id,
        'cnote_number': cnote.cnote_number,
        'booking_type': cnote.booking_type or 'N/A',
        'delivery_destination': cnote.delivery_destination.destination_name if cnote.delivery_destination else 'N/A',
        'consignor_name': cnote.consignor_name or 'N/A',
        'consignee_name': cnote.consignee_name or 'N/A',
        'payment_type': cnote.payment_type or 'N/A',
        'grand_total': float(cnote.grand_total or 0),
        'created_at': cnote.created_at.isoformat() if cnote.created_at else None,
        'eway_bill_number': cnote.eway_bill_number or 'N/A',
        'actual_weight': float(cnote.actual_weight or 0),
        'charged_weight': float(cnote.charged_weight or 0),
        'weight_rate': float(cnote.weight_rate or 0),
        'weight_amount': float(cnote.weight_amount or 0),
        'fix_amount': float(cnote.fix_amount or 0),
        'invoice_number': cnote.invoice_number or 'N/A',
        'declared_value': float(cnote.declared_value or 0),
        'risk_type': cnote.risk_type or 'N/A',
        'pod_required': cnote.pod_required or 'N/A',
        'freight': float(cnote.freight or 0),
        'docket_charge': float(cnote.docket_charge or 0),
        'door_delivery_charge': float(cnote.door_delivery_charge or 0),
        'handling_charge': float(cnote.handling_charge or 0),
        'pickup_charge': float(cnote.pickup_charge or 0),
        'transhipment_charge': float(cnote.transhipment_charge or 0),
        'insurance': float(cnote.insurance or 0),
        'fuel_surcharge': float(cnote.fuel_surcharge or 0),
        'commission': float(cnote.commission or 0),
        'other_charge': float(cnote.other_charge or 0),
        'carrier_risk': cnote.carrier_risk or 'N/A',
        'delivery_type': cnote.delivery_type or 'N/A',
        'delivery_method': cnote.delivery_method or 'N/A',
        'status': cnote.status or 'N/A',
        'total_art': total_articles,
        'art_types': art_types,
        'said_to_contain': said_to_contain,
        'art_amounts': art_amounts,
        'consignor_gst': cnote.consignor_gst or 'N/A',
        'consignee_gst': cnote.consignee_gst or 'N/A',
        'user': cnote.dealer.name if cnote.dealer else 'N/A',
        'user_type': user_type,
        'loading_sheet_number': loading_sheet_number,
        'ddm_number': ddm_number,
    }

def get_transporter_info(user):
    """Get transporter information for the current user"""
    try:
        if hasattr(user, 'transporter'):
            transporter = user.transporter
            return {
                'name': transporter.name or 'N/A',
                'city': transporter.city or 'N/A'
            }
    except Exception as e:
        logger.warning(f"Could not get transporter info: {str(e)}")
    
    return {'name': 'GoodWayExpress', 'city': 'Yavatmal'}

@login_required
def booking_register_view(request):
    """Render the booking register view page"""
    try:
        return render(request, 'transporter/booking_register.html')
    except Exception as e:
        logger.error(f"Error rendering booking register view: {str(e)}")
        messages.error(request, "Error loading the booking register page.")
        return redirect('transporter:home')

@login_required
def download_excel(request):
    """
    Download booking register data as Excel file with improved performance
    """
    try:
        logger.info("Starting Excel download")
        
        # Get the same filtered data as the main view
        search_params = {
            'search': request.GET.get('search', '').strip().lower(),
            'date_from': request.GET.get('date_from'),
            'date_to': request.GET.get('date_to'),
            'dealer': request.GET.get('dealer', '').strip().lower(),
            'from_city': request.GET.get('from_city', '').strip().lower(),
            'to_city': request.GET.get('to_city', '').strip().lower(),
            'amount_min': request.GET.get('amount_min'),
            'amount_max': request.GET.get('amount_max'),
            'cnote_number': request.GET.get('cnote_number', '').strip().lower(),
            'ls_number': request.GET.get('ls_number', '').strip().lower(),
            'ddm_number': request.GET.get('ddm_number', '').strip().lower(),
        }
        
        # Build query
        cnotes_query = CNotes.objects.select_related(
            'dealer', 'delivery_destination'
        ).prefetch_related(
            'articles__art_type',
            'loading_sheet_details__loading_sheet',
            'ddm_details__ddm'
        )
        
        cnotes_query = apply_booking_filters(cnotes_query, search_params)
        cnotes = cnotes_query.order_by('-created_at')[:5000]  # Limit for Excel export
        
        # Process data for Excel
        excel_data = []
        for cnote in cnotes:
            try:
                cnote_data = process_cnote_data(cnote)
                # Flatten arrays for Excel
                cnote_data['art_types'] = ' / '.join(cnote_data['art_types']) if cnote_data['art_types'] else 'N/A'
                cnote_data['said_to_contain'] = ' / '.join(cnote_data['said_to_contain']) if cnote_data['said_to_contain'] else 'N/A'
                cnote_data['art_amounts'] = ' / '.join([str(amt) for amt in cnote_data['art_amounts']]) if cnote_data['art_amounts'] else 'N/A'
                excel_data.append(cnote_data)
            except Exception as e:
                logger.warning(f"Error processing CNotes {cnote.cnote_number} for Excel: {str(e)}")
                continue
        
        if not excel_data:
            return JsonResponse({'error': 'No data available for export'}, status=404)
        
        # Create DataFrame
        df = pd.DataFrame(excel_data)
        
        # Convert datetime columns
        datetime_columns = ['created_at']
        for col in datetime_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Create HTTP response
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="booking_register_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
        
        # Write to Excel
        with pd.ExcelWriter(response, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Booking Register')
            
            # Auto-adjust column widths
            worksheet = writer.sheets['Booking Register']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        logger.info(f"Excel file generated successfully with {len(excel_data)} records")
        return response
        
    except Exception as e:
        logger.error(f"Error in download_excel: {str(e)}", exc_info=True)
        return JsonResponse({
            'error': 'Error generating Excel file',
            'message': str(e)
        }, status=500)

# Additional utility functions for better code organization

def validate_date_range(date_from, date_to):
    """Validate date range parameters"""
    try:
        if date_from:
            from_date = datetime.strptime(date_from, '%Y-%m-%d').date()
        if date_to:
            to_date = datetime.strptime(date_to, '%Y-%m-%d').date()
        
        if date_from and date_to and from_date > to_date:
            raise ValueError("From date cannot be greater than to date")
        
        return True
    except ValueError as e:
        logger.warning(f"Date validation error: {str(e)}")
        return False

def get_booking_summary(cnotes_data):
    """Calculate booking summary statistics"""
    try:
        total_records = len(cnotes_data)
        total_amount = sum(item.get('grand_total', 0) for item in cnotes_data)
        
        paid_amount = sum(
            item.get('grand_total', 0) 
            for item in cnotes_data 
            if item.get('payment_type', '').upper() == 'PAID'
        )
        
        to_pay_amount = sum(
            item.get('grand_total', 0) 
            for item in cnotes_data 
            if item.get('payment_type', '').upper() == 'TO PAY'
        )
        
        return {
            'total_records': total_records,
            'total_amount': total_amount,
            'paid_amount': paid_amount,
            'to_pay_amount': to_pay_amount,
            'average_amount': total_amount / total_records if total_records > 0 else 0
        }
    except Exception as e:
        logger.error(f"Error calculating booking summary: {str(e)}")
        return {
            'total_records': 0,
            'total_amount': 0,
            'paid_amount': 0,
            'to_pay_amount': 0,
            'average_amount': 0
        }


from django.db import IntegrityError


@login_required
def add_user(request):
    if request.method == "POST":
        role = request.POST.get('role')
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')
        name = request.POST.get('name')
        phone_number = request.POST.get('phone_number')
        address = request.POST.get('address')
        state = request.POST.get('state')
        city = request.POST.get('city')
        dealer_code = request.POST.get('dealer_code', '').strip()

        if role == "dealer":
            if not dealer_code or len(dealer_code) != 4:
                return JsonResponse({'success': False, 'message': 'Dealer code must be exactly 4 characters.'}, status=400)

        if not email:
            return JsonResponse({'success': False, 'message': 'Email is required.'}, status=400)

        try:
            with transaction.atomic():
                if CustomUser.objects.filter(username=username).exists():
                    return JsonResponse({'success': False, 'message': 'Username already exists.'}, status=400)
                if CustomUser.objects.filter(email=email).exists():
                    return JsonResponse({'success': False, 'message': 'Email already exists.'}, status=400)

                user = CustomUser.objects.create_user(
                    username=username,
                    password=password,
                    email=email
                )

                if role == "dealer":
                    user.is_dealer = True
                    user.save()
                    Dealer.objects.create(
                        user=user,
                        dealer_code=dealer_code,
                        name=name,
                        mobile_number_1=phone_number,
                        address=address,
                        state=state,
                        city=city,
                        email=email
                    )
                elif role == "transporter":
                    user.is_transporter = True
                    user.save()
                    Transporter.objects.create(
                        user=user,
                        name=name,
                        mobile_number_1=phone_number,
                        address=address,
                        state=state,
                        city=city,
                        email=email
                    )
                else:
                    return JsonResponse({'success': False, 'message': 'Invalid role selected.'}, status=400)

                return JsonResponse({'success': True, 'message': f"{role.capitalize()} added successfully!"}, status=201)

        except IntegrityError as e:
            if 'dealer_app_dealer_email_key' in str(e):
                return JsonResponse({'success': False, 'message': 'This email is already associated with a dealer.'}, status=400)
            else:
                return JsonResponse({'success': False, 'message': f"Database integrity error: {str(e)}"}, status=500)
        except Exception as e:
            return JsonResponse({'success': False, 'message': f"Error: {str(e)}"}, status=500)

    return render(request, 'transporter/add_user.html')




import pandas as pd
from django.http import HttpResponse

@login_required
def export_dealers_template(request):
    columns = ["Dealer Code", "Name", "Username", "Password", "Email", "Phone Number", "Address", "State", "City"]
    df = pd.DataFrame(columns=columns)
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="dealers_template.xlsx"'
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Dealers Template')
    return response


import pandas as pd
from django.contrib.auth.models import User

@login_required
def import_dealers(request):
    if request.method == "POST" and request.FILES.get("dealer_file"):
        try:
            file = request.FILES["dealer_file"]
            df = pd.read_excel(file)

            required_columns = ["Dealer Code", "Name", "Username", "Password", "Email", "Phone Number", "Address", "State", "City"]
            if not all(col in df.columns for col in required_columns):
                return JsonResponse({'success': False, 'message': 'Invalid file format.'}, status=400)

            with transaction.atomic():
                for _, row in df.iterrows():
                    dealer_code = str(row["Dealer Code"]).strip()
                    if not dealer_code or len(dealer_code) != 4:
                        return JsonResponse({'success': False, 'message': f'Invalid dealer code: {dealer_code}. Must be exactly 4 characters.'}, status=400)

                    if CustomUser.objects.filter(username=row["Username"]).exists():
                        return JsonResponse({'success': False, 'message': f'Username already exists: {row["Username"]}'}, status=400)
                    if CustomUser.objects.filter(email=row["Email"]).exists():
                        return JsonResponse({'success': False, 'message': f'Email already exists: {row["Email"]}'}, status=400)

                    user = CustomUser.objects.create_user(
                        username=row["Username"],
                        email=row["Email"],
                        password=row["Password"],
                        is_dealer=True
                    )

                    Dealer.objects.create(
                        user=user,
                        dealer_code=dealer_code,
                        name=row["Name"],
                        mobile_number_1=row["Phone Number"],
                        address=row["Address"],
                        state=row["State"],
                        city=row["City"],
                        email=row["Email"]
                    )

            return JsonResponse({'success': True, 'message': 'Dealers imported successfully!'}, status=201)
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)
    return JsonResponse({'success': False, 'message': 'Invalid request.'}, status=400)


def dealer_billing(request):
    dealers = Dealer.objects.all()  # Fetch all dealers
    dealer_id = request.GET.get('dealer_id')  # Get dealer ID from request (if provided)

    # Filter CNotes based on dealer and excluding cancelled status
    cnotes = CNotes.objects.filter(status__exclude='cancelled')

    if dealer_id:
        cnotes = cnotes.filter(dealer_id=dealer_id)  # Filter for a specific dealer

    # Aggregating billing amounts
    billing_data = cnotes.values(
        'dealer__dealer_code', 'dealer__dealer_name'
    ).annotate(
        total_freight=Sum('freight'),
        total_charges=Sum('grand_total')
    )

    return render(request, 'billing.html', {'dealers': dealers, 'billing_data': billing_data})


logger = logging.getLogger(__name__)

@login_required
def billing(request):
    logger.info("📢 billing view called")
    
    dealers = Dealer.objects.all()
    selected_dealer = request.GET.get('dealer', '')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    month = request.GET.get('month')
    selected_state = request.GET.get('state', 'all')
    
    logger.info(f"Request params: dealer={selected_dealer}, from_date={from_date}, to_date={to_date}, month={month}, state={selected_state}")
    
    cnotes = None
    
    if selected_dealer or from_date or to_date or month:
        # Exclude CNotes that are already billed (present in BillItem) and not cancelled
        billed_cnote_ids = BillItem.objects.values_list('cnote_id', flat=True)
        cnotes = CNotes.objects.filter(~Q(status='cancelled')).exclude(id__in=billed_cnote_ids)
        
        if selected_dealer:
            try:
                dealer = Dealer.objects.get(name=selected_dealer)
                cnotes = cnotes.filter(dealer=dealer)
                logger.info(f"Filtered by dealer: {selected_dealer}, count: {cnotes.count()}")
            except Dealer.DoesNotExist:
                messages.error(request, f"Dealer '{selected_dealer}' not found.")
                cnotes = CNotes.objects.none()
        
        if from_date and to_date:
            try:
                from_date_obj = timezone.make_aware(datetime.strptime(from_date, '%Y-%m-%d'))
                to_date_obj = timezone.make_aware(datetime.strptime(to_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59))
                cnotes = cnotes.filter(created_at__gte=from_date_obj, created_at__lte=to_date_obj)
                logger.info(f"Filtered by date range: {from_date} to {to_date}, count: {cnotes.count()}")
            except ValueError:
                messages.error(request, "Invalid date format. Please use YYYY-MM-DD.")
                cnotes = CNotes.objects.none()
        
        elif month:
            try:
                month_int = int(month)
                current_year = timezone.now().year
                cnotes = cnotes.filter(created_at__year=current_year, created_at__month=month_int)
                logger.info(f"Filtered by month: {month}, count: {cnotes.count()}")
            except ValueError:
                messages.error(request, "Invalid month value.")
                cnotes = CNotes.objects.none()
        
        if selected_state and selected_state.lower() != "all":
            cnotes = cnotes.filter(dealer__state=selected_state)
            logger.info(f"Filtered by state: {selected_state}, count: {cnotes.count()}")
        
        if cnotes.exists():
            cnotes = cnotes.select_related('dealer', 'delivery_destination').prefetch_related('articles')
            
            for cnote in cnotes:
                articles = Article.objects.filter(cnote=cnote)
                cnote.total_art = articles.aggregate(total_sum=Sum('art'))['total_sum'] or 0
                
                art_types = []
                said_to_contain_list = []
                art_amounts = []
                
                for article in articles:
                    art_type_name = article.art_type.art_type_name if article.art_type else 'N/A'
                    art_types.append(art_type_name)
                    
                    said_to_contain = f"{article.said_to_contain or 'N/A'} ({article.art or 0})"
                    said_to_contain_list.append(said_to_contain)
                    
                    art_amount = str(article.art_amount) if article.art_amount else '0'
                    art_amounts.append(art_amount)
                
                cnote.art_types_display = ' / '.join(art_types) if art_types else 'N/A'
                cnote.said_to_contain_display = ' / '.join(said_to_contain_list) if said_to_contain_list else 'N/A'
                cnote.art_amounts_display = ' / '.join(art_amounts) if art_amounts else '0'
    
    context = {
        'dealers': dealers,
        'selected_dealer': selected_dealer,
        'selected_from_date': from_date,
        'selected_to_date': to_date,
        'selected_month': month,
        'selected_state': selected_state,
        'cnotes': cnotes,
        'months': range(1, 13),
    }
    
    return render(request, 'transporter/billing.html', context)

def generate_bill_number():
    """Generate a sequential bill number in the format INV/MMYY/NNNN"""
    today = timezone.now()
    month_year = today.strftime('%m%y')
    
    prefix = f"INV/{month_year}/"
    latest_bill = Bill.objects.filter(bill_number__startswith=prefix).order_by('-bill_number').first()
    
    if latest_bill:
        try:
            last_number = int(latest_bill.bill_number.split('/')[-1])
            new_number = last_number + 1
        except (ValueError, IndexError):
            new_number = 1
    else:
        new_number = 1
    
    return f"{prefix}{new_number:04d}"

@login_required
def save_bill(request):
    if request.method != 'POST':
        logger.warning(f"Invalid request method for bill creation: {request.method}")
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

    try:
        # Parse JSON data
        data = json.loads(request.body)
        logger.info(f"Received bill save request with data: {data}")

        dealer_name = data.get('dealer_name')
        cnote_ids = [int(id_str) for id_str in data.get('cnote_ids', [])]
        from_date = data.get('from_date')
        to_date = data.get('to_date')
        month = data.get('month')
        gst_percentage = Decimal(str(data.get('gst_percentage', 18)))

        # Validate required fields
        if not dealer_name or not cnote_ids:
            logger.warning("Missing required fields: dealer_name or cnote_ids")
            return JsonResponse(
                {'status': 'error', 'message': 'Dealer and CNotes are required'},
                status=400
            )

        # Fetch dealer
        try:
            dealer = Dealer.objects.get(name=dealer_name)
            logger.info(f"Found dealer: {dealer_name}")
        except Dealer.DoesNotExist:
            logger.error(f"Dealer not found: {dealer_name}")
            return JsonResponse(
                {'status': 'error', 'message': f'Dealer {dealer_name} not found'},
                status=404
            )

        # Validate CNotes existence
        cnotes = CNotes.objects.filter(id__in=cnote_ids)
        if len(cnotes) != len(cnote_ids):
            found_ids = set(cnote.id for cnote in cnotes)
            missing_ids = set(cnote_ids) - found_ids
            logger.error(f"Some CNotes not found. Missing IDs: {missing_ids}")
            return JsonResponse({
                'status': 'error',
                'message': f'Some CNotes were not found. Missing IDs: {missing_ids}',
                'missing_ids': list(missing_ids)
            }, status=404)
        logger.info(f"Found {len(cnotes)} CNotes matching provided IDs")

        # Validate CNotes are not used in active/pending bills
        used_cnotes = BillItem.objects.filter(
            cnote_id__in=cnote_ids,
            bill__status__in=['active', 'pending']
        ).select_related('bill', 'cnote')
        if used_cnotes.exists():
            used_cnote_details = [
                f"CNote {item.cnote.cnote_number} (ID: {item.cnote_id}) used in bill {item.bill.bill_number}"
                for item in used_cnotes
            ]
            logger.error(f"CNotes already used: {used_cnote_details}")
            return JsonResponse({
                'status': 'error',
                'message': 'Some CNotes are already used in active or pending bills',
                'used_cnotes': used_cnote_details
            }, status=400)

        # Calculate subtotal
        subtotal = sum(cnote.grand_total for cnote in cnotes)
        logger.info(f"Calculated subtotal: {subtotal}")

        # Generate bill number
        bill_number = generate_bill_number()
        logger.info(f"Generated bill number: {bill_number}")

        # Get Transporter instance for the logged-in user
        try:
            transporter = request.user.transporter_user
            logger.info(f"Found transporter for user {request.user.username}: {transporter}")
            logger.info(f"Transporter ID: {transporter.id}")
        except AttributeError:
            logger.error(f"No Transporter associated with user {request.user.username}")
            return JsonResponse({
                'status': 'error',
                'message': 'No Transporter associated with this user. Please contact the administrator.'
            }, status=400)

        # Create Bill and BillItems within a transaction
        with transaction.atomic():
            # Create Bill
            bill = Bill.objects.create(
                bill_number=bill_number,
                dealer=dealer,
                transporter=transporter,
                created_by=request.user,
                from_date=from_date if from_date else None,
                to_date=to_date if to_date else None,
                bill_month=month if month else None,
                bill_year=timezone.now().year,
                subtotal=subtotal,
                gst_percentage=gst_percentage,
                status='pending'
            )
            logger.info(f"Created bill with ID: {bill.id}")
            logger.info(f"Bill transporter: {bill.transporter}")

            # Create BillItems
            for cnote in cnotes:
                BillItem.objects.create(
                    bill=bill,
                    cnote=cnote,
                    cnote_number=cnote.cnote_number,
                    created_date=cnote.created_at.date(),
                    payment_type=cnote.payment_type or 'N/A',
                    amount=cnote.grand_total,
                    consignee_name=cnote.consignee_name,
                    total_art=cnote.total_art
                )
            logger.info(f"Created {len(cnotes)} bill items for bill {bill_number}")

        return JsonResponse({
            'status': 'success',
            'message': 'Bill saved successfully',
            'bill_number': bill_number,
            'bill_id': bill.id
        })

    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON data received'}, status=400)

    except ValueError as e:
        logger.error(f"Invalid ID or GST format: {str(e)}")
        return JsonResponse(
            {'status': 'error', 'message': 'Invalid CNote ID or GST percentage format'},
            status=400
        )

    except Exception as e:
        logger.error(f"Unexpected error saving bill: {str(e)}", exc_info=True)
        return JsonResponse(
            {'status': 'error', 'message': f'Error saving bill: {str(e)}'},
            status=500
        )

@login_required
def cancel_bill(request, bill_id):
    if request.method != 'POST':
        logger.warning(f"Invalid request method for bill cancellation: {request.method}")
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

    try:
        with transaction.atomic():  # Ensure atomicity for database operations
            # Fetch bill using get_object_or_404 for cleaner error handling
            bill = get_object_or_404(Bill, id=bill_id)

            # Check if bill is in pending status
            if bill.status != 'pending':
                logger.warning(f"Attempt to cancel non-pending bill {bill.bill_number} with status {bill.status}")
                return JsonResponse(
                    {'status': 'error', 'message': 'Only pending bills can be cancelled'},
                    status=400
                )

            # Delete all related BillItem entries to free up CNotes
            deleted_count = BillItem.objects.filter(bill=bill).delete()[0]
            logger.info(f"Deleted {deleted_count} BillItem entries for bill {bill.bill_number}")

            # Update bill status to cancelled
            bill.status = 'cancelled'
            bill.save()
            logger.info(f"Bill {bill.bill_number} cancelled successfully")

            return JsonResponse({
                'status': 'success',
                'message': f'Bill {bill.bill_number} cancelled successfully. {deleted_count} CNote(s) freed.'
            })

    except Bill.DoesNotExist:
        # This is technically redundant due to get_object_or_404, but kept for clarity
        logger.error(f"Bill with ID {bill_id} not found")
        return JsonResponse({'status': 'error', 'message': 'Bill not found'}, status=404)

    except Exception as e:
        logger.error(f"Error cancelling bill {bill_id}: {str(e)}", exc_info=True)
        return JsonResponse({'status': 'error', 'message': f'Error cancelling bill: {str(e)}'}, status=500)

@login_required
def bill_list(request):
    bills = Bill.objects.all().order_by('-created_at')

    # Filtering
    dealer = request.GET.get('dealer')
    status = request.GET.get('status')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    month = request.GET.get('month')
    year = request.GET.get('year')
    invoice_no = request.GET.get('invoice_no')

    if dealer:
        bills = bills.filter(dealer__name__icontains=dealer)
        logger.info(f"Filtered bills by dealer: {dealer}, count: {bills.count()}")

    if status:
        bills = bills.filter(status=status)
        logger.info(f"Filtered bills by status: {status}, count: {bills.count()}")

    if from_date:
        try:
            from_date_obj = timezone.make_aware(datetime.strptime(from_date, '%Y-%m-%d'))
            bills = bills.filter(created_at__gte=from_date_obj)
            logger.info(f"Filtered bills by from_date: {from_date}, count: {bills.count()}")
        except ValueError:
            return JsonResponse({'status': 'error', 'message': 'Invalid from date format'}, status=400)

    if to_date:
        try:
            to_date_obj = timezone.make_aware(datetime.strptime(to_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59))
            bills = bills.filter(created_at__lte=to_date_obj)
            logger.info(f"Filtered bills by to_date: {to_date}, count: {bills.count()}")
        except ValueError:
            return JsonResponse({'status': 'error', 'message': 'Invalid to date format'}, status=400)

    if month:
        try:
            bills = bills.filter(bill_month=int(month))
            logger.info(f"Filtered bills by month: {month}, count: {bills.count()}")
        except ValueError:
            return JsonResponse({'status': 'error', 'message': 'Invalid month format'}, status=400)

    if year:
        try:
            bills = bills.filter(bill_year=int(year))
            logger.info(f"Filtered bills by year: {year}, count: {bills.count()}")
        except ValueError:
            return JsonResponse({'status': 'error', 'message': 'Invalid year format'}, status=400)

    if invoice_no:
        bills = bills.filter(bill_number__icontains=invoice_no)
        logger.info(f"Filtered bills by invoice_no: {invoice_no}, count: {bills.count()}")

    # Pagination
    items_per_page = 10
    paginator = Paginator(bills, items_per_page)
    page_number = request.GET.get('page', 1)

    try:
        page_obj = paginator.page(page_number)
    except Exception as e:
        logger.error(f"Pagination error: {str(e)}")
        page_obj = paginator.page(1)

    # Prepare data for JSON response
    bills_data = []
    for bill in page_obj:
        bills_data.append({
            'id': bill.id,
            'bill_number': bill.bill_number,
            'created_at': bill.created_at.isoformat(),
            'dealer': {
                'name': bill.dealer.name
            },
            'total_amount': float(bill.total_amount),
            'items_count': bill.items.count(),
            'status': bill.status
        })

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'results': bills_data,
            'total_pages': paginator.num_pages
        })

    # For non-AJAX requests, render the template
    context = {
        'bills': page_obj,
    }
    return render(request, 'transporter/bill_manage.html', context)


@login_required
def bill_detail(request, bill_id):
    bill = Bill.objects.select_related('dealer').get(id=bill_id)
    items = BillItem.objects.filter(bill=bill)
    response = {
        'id': bill.id,
        'bill_number': bill.bill_number,
        'created_at': bill.created_at.isoformat(),
        'dealer': {
            'name': bill.dealer.name,
            'address': bill.dealer.address,
            'gstn': bill.dealer.gstn,  # Corrected field
            'phone_number_1': bill.dealer.phone_number_1,
            'email': bill.dealer.email
        },
        'status': bill.status,
        'items': [{
            'id': item.id,
            'cnote_number': item.cnote_number,
            'created_date': item.created_date.isoformat(),
            'payment_type': item.payment_type,
            'amount': float(item.amount)
        } for item in items],
        'subtotal': float(bill.subtotal),
        'gst_percentage': float(bill.gst_percentage),
        'gst_amount': float(bill.gst_amount),
        'total_amount': float(bill.total_amount)
    }
    return JsonResponse(response)    

logger = logging.getLogger(__name__)

@login_required
def update_bill(request, bill_id):
    if request.method not in ['POST', 'PUT']:
        logger.warning(f"Invalid request method for bill update: {request.method}")
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

    try:
        # Parse JSON data
        data = json.loads(request.body)
        logger.info(f"Received update request for bill ID {bill_id}: {data}")

        # Extract fields from frontend payload
        created_at = data.get('created_at')
        status = data.get('status')
        dealer_data = data.get('dealer', {})
        dealer_name = dealer_data.get('name') if dealer_data else None
        items = data.get('items', [])
        cnote_ids = [int(item['id']) for item in items if 'id' in item and item['id']]  # Extract CNote IDs

        # Fetch bill
        bill = get_object_or_404(Bill, id=bill_id)
        logger.info(f"Found bill: {bill.bill_number}, status={bill.status}, dealer={bill.dealer.name}, items_count={bill.items.count()}")

        # Validate bill status
        if bill.status != 'pending':
            logger.warning(f"Cannot update bill {bill.bill_number}: status is {bill.status}")
            return JsonResponse({'status': 'error', 'message': 'Only pending bills can be updated'}, status=400)

        # Validate dealer
        if dealer_name:
            try:
                dealer = Dealer.objects.get(name=dealer_name)
                logger.info(f"Dealer set to: {dealer.name}")
            except Dealer.DoesNotExist:
                logger.error(f"Dealer not found: {dealer_name}")
                return JsonResponse({'status': 'error', 'message': f'Dealer {dealer_name} not found'}, status=404)
        else:
            dealer = bill.dealer
            logger.info(f"No dealer_name provided, keeping dealer: {dealer.name}")

        # Validate CNotes
        if cnote_ids:
            logger.info(f"Processing cnote_ids: {cnote_ids}")
            # Fetch CNotes without strict dealer validation
            cnotes = CNote.objects.filter(id__in=cnote_ids)
            cnote_details = [(cnote.id, cnote.cnote_number, cnote.dealer.name if cnote.dealer else 'None') for cnote in cnotes]
            logger.info(f"Found CNotes: {cnote_details}")

            if len(cnotes) != len(cnote_ids):
                found_ids = set(cnote.id for cnote in cnotes)
                missing_ids = set(cnote_ids) - found_ids
                logger.error(f"CNotes not found: {missing_ids}")
                return JsonResponse({
                    'status': 'error',
                    'message': f'Some CNotes not found: {missing_ids}',
                    'missing_ids': list(missing_ids)
                }, status=404)

            # Check if CNotes are used in other active/pending bills
            used_cnotes = BillItem.objects.filter(
                cnote_id__in=cnote_ids,
                bill__status__in=['active', 'pending'],
                bill__id__ne=bill_id
            ).select_related('bill', 'cnote')
            if used_cnotes.exists():
                used_details = [f"CNote {item.cnote.cnote_number} in bill {item.bill.bill_number}" for item in used_cnotes]
                logger.error(f"CNotes already used: {used_details}")
                return JsonResponse({
                    'status': 'error',
                    'message': 'Some CNotes are used in other active/pending bills',
                    'used_cnotes': used_details
                }, status=400)

            # Warn if dealer mismatch but proceed
            for cnote in cnotes:
                if cnote.dealer and cnote.dealer != dealer:
                    logger.warning(f"CNote {cnote.cnote_number} (ID: {cnote.id}) belongs to dealer {cnote.dealer.name}, not {dealer.name}")
                elif not cnote.dealer:
                    logger.warning(f"CNote {cnote.cnote_number} (ID: {cnote.id}) has no dealer assigned")
        else:
            cnotes = bill.items.all()
            logger.info(f"No cnote_ids provided, keeping {len(cnotes)} existing items")

        # Update bill in transaction
        with transaction.atomic():
            # Update bill fields
            if created_at:
                try:
                    bill.created_at = timezone.make_aware(datetime.strptime(created_at, '%Y-%m-%d'))
                    logger.info(f"Set created_at: {bill.created_at}")
                except ValueError as e:
                    logger.error(f"Invalid created_at format: {created_at}, error: {str(e)}")
                    return JsonResponse({'status': 'error', 'message': f'Invalid created_at format: {created_at}'}, status=400)
            else:
                logger.info(f"No created_at provided, keeping: {bill.created_at}")

            if status in ['pending', 'paid', 'cancelled']:
                bill.status = status
                logger.info(f"Set status: {bill.status}")
            else:
                logger.info(f"No valid status provided, keeping: {bill.status}")

            if dealer_name:
                bill.dealer = dealer
                logger.info(f"Set dealer: {dealer.name}")

            # Update BillItems
            if cnote_ids:
                deleted_count = BillItem.objects.filter(bill=bill).delete()[0]
                logger.info(f"Deleted {deleted_count} BillItems")
                for cnote in cnotes:
                    item_data = next((item for item in items if item['id'] == cnote.id), {})
                    BillItem.objects.create(
                        bill=bill,
                        cnote=cnote,
                        cnote_number=cnote.cnote_number,
                        created_date=cnote.created_at.date(),
                        payment_type=item_data.get('payment_type', cnote.payment_type or 'N/A'),
                        amount=Decimal(str(item_data.get('amount', cnote.grand_total))),
                        consignee_name=cnote.consignee_name,
                        total_art=cnote.total_art
                    )
                logger.info(f"Created {len(cnotes)} new BillItems")
            else:
                logger.info(f"No items to update, keeping existing BillItems")

            # Recalculate totals
            bill.subtotal = sum(item.amount for item in bill.items.all())
            bill.gst_amount = bill.subtotal * (bill.gst_percentage / Decimal('100'))
            bill.total_amount = bill.subtotal + bill.gst_amount
            logger.info(f"Recalculated totals: subtotal={bill.subtotal}, gst_amount={bill.gst_amount}, total_amount={bill.total_amount}")

            # Save and verify
            logger.info(f"Before save: bill_id={bill.id}, status={bill.status}, dealer={bill.dealer.name}, subtotal={bill.subtotal}, items={bill.items.count()}")
            bill.save()
            bill.refresh_from_db()
            logger.info(f"After save: bill_id={bill.id}, status={bill.status}, dealer={bill.dealer.name}, subtotal={bill.subtotal}, items={bill.items.count()}")

        # Prepare response
        bill_data = {
            'id': bill.id,
            'bill_number': bill.bill_number,
            'created_at': bill.created_at.isoformat(),
            'dealer': {'name': bill.dealer.name},
            'items': [
                {
                    'id': item.id,
                    'cnote_number': item.cnote_number,
                    'created_date': item.created_date.isoformat(),
                    'amount': float(item.amount),
                    'payment_type': item.payment_type
                } for item in bill.items.all()
            ],
            'subtotal': float(bill.subtotal),
            'gst_percentage': float(bill.gst_percentage),
            'gst_amount': float(bill.gst_amount),
            'total_amount': float(bill.total_amount),
            'status': bill.status
        }

        logger.info(f"Bill {bill.bill_number} updated successfully: {bill_data}")
        response = JsonResponse({'status': 'success', 'bill': bill_data})
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return response

    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'}, status=400)
    except ValueError as e:
        logger.error(f"Value error: {str(e)}")
        return JsonResponse({'status': 'error', 'message': f'Invalid input: {str(e)}'}, status=400)
    except Exception as e:
        logger.error(f"Unexpected error updating bill {bill_id}: {str(e)}", exc_info=True)
        return JsonResponse({'status': 'error', 'message': f'Error: {str(e)}'}, status=500) 
@login_required
def available_cnotes(request, bill_id):
    try:
        bill = Bill.objects.get(id=bill_id)
        # Fetch CNotes for the bill's dealer that are not associated with any bill
        used_cnote_ids = BillItem.objects.values_list('cnote_id', flat=True)
        cnotes = CNotes.objects.filter(
            dealer=bill.dealer
        ).exclude(id__in=used_cnote_ids)

        cnotes_data = [
            {
                'id': cnote.id,
                'cnote_number': cnote.cnote_number,
                'created_at': cnote.created_at.isoformat(),
                'grand_total': float(cnote.grand_total),
                'payment_type': cnote.payment_type
            } for cnote in cnotes
        ]

        return JsonResponse({'cnotes': cnotes_data})
    except Bill.DoesNotExist:
        logger.error(f"Bill with ID {bill_id} not found")
        return JsonResponse({'status': 'error', 'message': 'Bill not found'}, status=404)
    except Exception as e:
        logger.error(f"Error fetching available CNotes: {str(e)}", exc_info=True)
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    

@login_required
@require_POST
def add_cnote_to_bill(request, bill_id):
    try:
        bill = Bill.objects.get(id=bill_id)
        data = json.loads(request.body)
        cnote_id = data.get('cnote_id')

        cnote = CNotes.objects.get(id=cnote_id)
        if cnote.dealer != bill.dealer:
            return JsonResponse({'status': 'error', 'message': 'CNote does not belong to the bill\'s dealer'}, status=400)

        # Check if the CNote is already associated with a bill
        if BillItem.objects.filter(cnote=cnote).exists():
            return JsonResponse({'status': 'error', 'message': 'CNote is already associated with a bill'}, status=400)

        # Create a new BillItem
        bill_item = BillItem.objects.create(
            bill=bill,
            cnote=cnote,
            cnote_number=cnote.cnote_number,
            created_date=cnote.created_at.date(),
            payment_type=cnote.payment_type or 'N/A',
            amount=cnote.grand_total,
            consignee_name=cnote.consignee_name,
            total_art=cnote.total_art
        )

        # Update bill totals
        bill.subtotal = sum(item.amount for item in bill.items.all())
        bill.gst_amount = bill.subtotal * (bill.gst_percentage / Decimal('100'))
        bill.total_amount = bill.subtotal + bill.gst_amount
        bill.save()

        bill_data = {
            'id': bill.id,
            'bill_number': bill.bill_number,
            'created_at': bill.created_at.isoformat(),
            'dealer': {
                'name': bill.dealer.name
            },
            'items': [
                {
                    'id': item.id,
                    'cnote_number': item.cnote_number,
                    'created_date': item.created_date.isoformat(),
                    'amount': float(item.amount),
                    'payment_type': item.payment_type
                } for item in bill.items.all()
            ],
            'subtotal': float(bill.subtotal),
            'gst_percentage': float(bill.gst_percentage),
            'gst_amount': float(bill.gst_amount),
            'total_amount': float(bill.total_amount),
            'status': bill.status
        }

        logger.info(f"CNote {cnote.cnote_number} added to bill {bill.bill_number}")
        return JsonResponse({'status': 'success', 'bill': bill_data})
    except Bill.DoesNotExist:
        logger.error(f"Bill with ID {bill_id} not found")
        return JsonResponse({'status': 'error', 'message': 'Bill not found'}, status=404)
    except CNotes.DoesNotExist:
        logger.error(f"CNote with ID {cnote_id} not found")
        return JsonResponse({'status': 'error', 'message': 'CNote not found'}, status=404)
    except Exception as e:
        logger.error(f"Error adding CNote to bill: {str(e)}", exc_info=True)
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    

@login_required
@require_POST
def remove_cnote_from_bill(request, bill_id):
    try:
        bill = Bill.objects.get(id=bill_id)
        data = json.loads(request.body)
        cnote_id = data.get('cnote_id')

        bill_item = BillItem.objects.get(bill=bill, cnote_id=cnote_id)
        bill_item.delete()

        # Update bill totals
        bill.subtotal = sum(item.amount for item in bill.items.all())
        bill.gst_amount = bill.subtotal * (bill.gst_percentage / Decimal('100'))
        bill.total_amount = bill.subtotal + bill.gst_amount
        bill.save()

        bill_data = {
            'id': bill.id,
            'bill_number': bill.bill_number,
            'created_at': bill.created_at.isoformat(),
            'dealer': {
                'name': bill.dealer.name
            },
            'items': [
                {
                    'id': item.id,
                    'cnote_number': item.cnote_number,
                    'created_date': item.created_date.isoformat(),
                    'amount': float(item.amount),
                    'payment_type': item.payment_type
                } for item in bill.items.all()
            ],
            'subtotal': float(bill.subtotal),
            'gst_percentage': float(bill.gst_percentage),
            'gst_amount': float(bill.gst_amount),
            'total_amount': float(bill.total_amount),
            'status': bill.status
        }

        logger.info(f"CNote removed from bill {bill.bill_number}")
        return JsonResponse({'status': 'success', 'bill': bill_data})
    except Bill.DoesNotExist:
        logger.error(f"Bill with ID {bill_id} not found")
        return JsonResponse({'status': 'error', 'message': 'Bill not found'}, status=404)
    except BillItem.DoesNotExist:
        logger.error(f"BillItem with CNote ID {cnote_id} not found in bill {bill_id}")
        return JsonResponse({'status': 'error', 'message': 'CNote not found in this bill'}, status=404)
    except Exception as e:
        logger.error(f"Error removing CNote from bill: {str(e)}", exc_info=True)
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    

@login_required
def dealer_list(request):
    try:
        dealers = Dealer.objects.all()
        dealers_data = [
            {
                'name': dealer.name
            } for dealer in dealers
        ]
        return JsonResponse(dealers_data, safe=False)
    except Exception as e:
        logger.error(f"Error fetching dealers: {str(e)}", exc_info=True)
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    


@login_required
def dashboard_summary(request):
    try:
        bills = Bill.objects.all()

        # Filtering
        month = request.GET.get('month')
        year = request.GET.get('year')
        dealer = request.GET.get('dealer')

        if month:
            bills = bills.filter(bill_month=int(month))
        if year:
            bills = bills.filter(bill_year=int(year))
        if dealer:
            bills = bills.filter(dealer__name__icontains=dealer)

        # Summary calculations
        active_bills = bills.filter(status__in=['pending', 'paid']).count()
        cancelled_bills = bills.filter(status='cancelled').count()
        total_bills = bills.count()
        total_amount = float(sum(bill.total_amount for bill in bills.filter(status__in=['pending', 'paid'])))

        # Dealer summary
        dealer_summary = {}
        for bill in bills.filter(status__in=['pending', 'paid']):
            dealer_name = bill.dealer.name
            if dealer_name not in dealer_summary:
                dealer_summary[dealer_name] = {
                    'count': 0,
                    'total_amount': 0.0
                }
            dealer_summary[dealer_name]['count'] += 1
            dealer_summary[dealer_name]['total_amount'] += float(bill.total_amount)

        dealer_summary_data = [
            {
                'dealer': dealer,
                'count': summary['count'],
                'total_amount': summary['total_amount'],
                'average_amount': summary['total_amount'] / summary['count'] if summary['count'] > 0 else 0
            }
            for dealer, summary in dealer_summary.items()
        ]

        return JsonResponse({
            'active_bills': active_bills,
            'cancelled_bills': cancelled_bills,
            'total_bills': total_bills,
            'total_amount': total_amount,
            'dealer_summary': dealer_summary_data
        })
    except Exception as e:
        logger.error(f"Error fetching dashboard summary: {str(e)}", exc_info=True)
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
@login_required
def bill_manage(request):
    """
    View to render the bill management page.
    """
    try:
        logger.info(f"User {request.user.username} accessed the bill management page")
        return render(request, 'transporter/bill_manage.html', {})
    except Exception as e:
        logger.error(f"Error rendering bill management page: {str(e)}", exc_info=True)
        return render(request, 'transporter/bill_manage.html', {'error': 'An error occurred while loading the page'})


def bill_print(request, bill_id):
    try:
        bill = Bill.objects.select_related('dealer').get(id=bill_id)
        items = BillItem.objects.filter(bill=bill)
        
        context = {
            'bill': bill,
            'items': items,
            'dealer': bill.dealer,
        }
        
        template = get_template('transporter/bill_print.html')  # Use get_template
        html = template.render(context)
        
        if request.GET.get('download', False):
            from weasyprint import HTML
            pdf_file = BytesIO()
            HTML(string=html).write_pdf(pdf_file)
            pdf_file.seek(0)
            response = FileResponse(pdf_file, as_attachment=True, filename=f'bill_{bill.bill_number}.pdf')
            return response
        
        return HttpResponse(html)
    
    except Bill.DoesNotExist:
        return HttpResponse("Bill not found", status=404)
    except Exception as e:
        return HttpResponse(f"Error generating bill: {str(e)}", status=500)
    
# transporter_app/views.py
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model  # Import get_user_model
from .models import Dealer, Transporter

# Get the active user model (CustomUser in your case)
User = get_user_model()

@login_required
def reset_password(request):
    """
    Handle password reset for a specific user.
    """
    if request.method == "GET":
        username = request.GET.get("username")
        if not username:
            return redirect('transporter:view_users')
        try:
            User.objects.get(username=username)  # Use the dynamic User model
            return render(request, 'transporter/reset_password.html', {'username': username})
        except User.DoesNotExist:
            return redirect('transporter:view_users')

    elif request.method == "POST":
        username = request.POST.get("username")
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        if new_password != confirm_password:
            return JsonResponse({"success": False, "message": "Passwords do not match."})

        try:
            user = User.objects.get(username=username)  # Use the dynamic User model
            user.set_password(new_password)
            user.save()
            return JsonResponse({"success": True, "message": "Password reset successfully."})
        except User.DoesNotExist:
            return JsonResponse({"success": False, "message": "User not found."})
        except Exception as e:
            return JsonResponse({"success": False, "message": f"Error resetting password: {str(e)}"})

@login_required
def view_users(request):
    """
    Render the view_users.html template to display all users.
    """
    return render(request, 'transporter/view_users.html')  # Corrected template path

@login_required
def fetch_users(request):
    """
    Fetch all Dealer and Transporter records and return them as JSON.
    """
    try:
        # Fetch all dealers
        dealers = Dealer.objects.all()
        dealer_data = [
            {
                "role": "Dealer",
                "dealer_code": dealer.dealer_code,
                "username": dealer.user.username if dealer.user else '-',
                "name": dealer.name,
                "company_name": dealer.company_name,
                "email": dealer.email,
                "phone_number_1": dealer.phone_number_1,
                "phone_number_2": dealer.phone_number_2 or '-',
                "mobile_number_1": dealer.mobile_number_1,
                "mobile_number_2": dealer.mobile_number_2 or '-',
                "address": dealer.address,
                "state": dealer.state,
                "city": dealer.city,
            }
            for dealer in dealers
        ]

        # Fetch all transporters
        transporters = Transporter.objects.all()
        transporter_data = [
            {
                "role": "Transporter",
                "transporter_id": f"T{transporter.transporter_id:04d}",
                "username": transporter.user.username if transporter.user else '-',
                "name": transporter.name,
                "company_name": transporter.company_name,
                "email": transporter.email,
                "phone_number_1": transporter.phone_number_1,
                "phone_number_2": transporter.phone_number_2 or '-',
                "mobile_number_1": transporter.mobile_number_1,
                "mobile_number_2": transporter.mobile_number_2 or '-',
                "address": transporter.address,
                "state": transporter.state,
                "city": transporter.city,
            }
            for transporter in transporters
        ]

        # Combine the data
        users = dealer_data + transporter_data

        if not users:
            return JsonResponse({"success": False, "message": "No users found."})

        return JsonResponse({"success": True, "users": users})
    except Exception as e:
        return JsonResponse({"success": False, "message": f"Error fetching users: {str(e)}"})
