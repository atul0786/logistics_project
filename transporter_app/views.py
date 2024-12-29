import json
from datetime import datetime
import logging
from .models import DeliveryCNote
from decimal import Decimal
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.db.models import Sum
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.views.generic import TemplateView
from dealer_app.models import CNotes, Dealer, LoadingSheetSummary
from .models import Transporter, State, City, PartyMaster, Pickup, TransporterAppReceive
from .forms import StateForm, CityForm, PartyMasterForm
from django.db.models import Sum, Q, Exists, OuterRef
from django.utils import timezone
from datetime import datetime
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from django.shortcuts import render
from dealer_app.models import LoadingSheetSummary, Dealer
from .models import TransporterAppReceive
import logging
import json
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from dealer_app.models import LoadingSheetSummary, LoadingSheetDetail, CNotes
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from .models import ReceivedStatesCnotes
from dealer_app.models import LoadingSheetSummary, LoadingSheetDetail, CNotes
from django.db import transaction
from django.shortcuts import render, get_object_or_404
from dealer_app.models import LoadingSheetSummary, LoadingSheetDetail
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from dealer_app.models import CNotes
from django.views.decorators.csrf import csrf_exempt
from .models import DeliveryCNote, ReceivedStatesCnotes
from dealer_app.models import LoadingSheetDetail, CNotes



logger = logging.getLogger(__name__)

User = get_user_model()  # This will refer to your CustomUser model

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

        # Base query - filter for dispatched and partial_received status
        query = LoadingSheetSummary.objects.filter(status__in=['dispatched', 'partial_received'])

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

        # Order by latest first and limit to 200 records
        query = query.order_by('-created_at')[:200]

        receivables = []
        for sheet in query:
            total_cnotes = sheet.details.count()
            received_cnotes = sheet.details.filter(status='received').count()
            pending_cnotes = total_cnotes - received_cnotes

            receivables.append({
                'srNo': sheet.ls_number,
                'lsNo': sheet.ls_number,
                'lsDateTime': sheet.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'dealer': sheet.dealer.name if sheet.dealer else 'N/A',
                'totalLRs': total_cnotes,
                'pendingLRs': pending_cnotes,
                'totalArt': sheet.total_art,
                'pendingArt': sheet.total_art - received_cnotes  # Assuming each cnote has one article
            })

        # Calculate summary
        summary = {
            'lrCount': query.aggregate(Sum('total_cnote'))['total_cnote__sum'] or 0,
            'totalQuantity': query.aggregate(Sum('total_art'))['total_art__sum'] or 0,
            'totalReceivableWeight': 0,  # This field might need to be added to your model
            'paid': query.aggregate(Sum('total_paid_amount'))['total_paid_amount__sum'] or 0,
            'toPay': query.aggregate(Sum('total_topay_amount'))['total_topay_amount__sum'] or 0,
            'tbb': query.aggregate(Sum('total_tbb_amount'))['total_tbb_amount__sum'] or 0,
        }

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
        
        # Get all loading sheet details without status filter
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

        # Get total counts for the loading sheet
        total_details = LoadingSheetDetail.objects.filter(loading_sheet=loading_sheet)
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
                'status': detail.status
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

import logging

logger = logging.getLogger(__name__)

@login_required
def received_cnote_view(request):
    ls_number = request.GET.get('lsNumber')
    if not ls_number:
        logger.error("No LS number provided in the request.")
        return render(request, 'transporter/RECEIVED_CNOTES.html', {'error': 'No loading sheet number provided.'})

    try:
        loading_sheet_summary = get_object_or_404(LoadingSheetSummary, ls_number=ls_number)
        loading_sheet_details = LoadingSheetDetail.objects.filter(loading_sheet=loading_sheet_summary).select_related('cnote')
        cnotes = CNotes.objects.filter(loadingsheetdetail__loading_sheet=loading_sheet_summary).distinct()

        context = {
            'loading_sheet_summary': loading_sheet_summary,
            'loading_sheet_details': loading_sheet_details,
            'cnotes': cnotes,
        }
        return render(request, 'transporter/RECEIVED_CNOTES.html', context)
    except LoadingSheetSummary.DoesNotExist:
        logger.error(f"Loading sheet with LS number {ls_number} does not exist.")
        return render(request, 'transporter/RECEIVED_CNOTES.html', {'error': 'Loading sheet not found.'})
    except Exception as e:
        logger.error(f"Error fetching loading sheet details: {e}")
        return render(request, 'transporter/RECEIVED_CNOTES.html', {'error': 'An unexpected error occurred while fetching loading sheet details.'})

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
            # Save to DeliveryCNote table
            delivery_cnote = DeliveryCNote(
                lr_number=data['lrNumber'],
                status='Delivered',  # Set status to Delivered
                payment_type=data['paymentType'],
                consignor_name=data['consignor']['name'],
                consignor_address=data['consignor']['address'],
                consignor_contact=data['consignor']['contact'],
                consignor_gst=data['consignor']['gst'],
                consignee_name=data['consignee']['name'],
                consignee_address=data['consignee']['address'],
                consignee_contact=data['consignee']['contact'],
                consignee_gst=data['consignee']['gst'],
                freight_charges=data['charges']['freight'],
                other_charges=data['charges']['other'],
                discount_amount=data['charges']['discount'],
                total_amount=data['charges']['total'],
                delivered_to_name=data['deliveredToName'],
                phone_number=data['phoneNumber'],
                id_proof_type=data['idProofType'],
                id_proof_number=data['idProofNumber'],
                remarks=data.get('remarks', ''),
                delivered_status=True
            )
            delivery_cnote.save()

            # Update status in CNotes table
            cnote = CNotes.objects.get(cnote_number=data['lrNumber'])
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
