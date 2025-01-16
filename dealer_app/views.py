from django.shortcuts import render, redirect, get_object_or_404   
from django.contrib.auth.decorators import login_required, user_passes_test   
from django.contrib.auth import login, authenticate   
from django.contrib import messages   
from django.http import HttpResponseForbidden, HttpResponseRedirect, JsonResponse, HttpResponse   
from django.views.decorators.csrf import csrf_protect   
from django.core.paginator import Paginator   
from rest_framework.decorators import api_view   
from rest_framework.response import Response   
from django.template.loader import get_template
from django.http import JsonResponse
from transporter_app.models import City, Pickup
import json
from django.db import transaction
from io import BytesIO   
from xhtml2pdf import pisa   
from functools import wraps  
from .models import BookingType, CNotes, DeliveryDestination, Dealer, CNote, Article, ArtType
import logging   
from django.http import JsonResponse
from transporter_app.models import Transporter
from django.db import connection
from django.views.decorators.http import require_POST
from django.shortcuts import render, get_object_or_404
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import CNote  # यदि आप CNote मॉडल का उपयोग कर रहे हैं
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from .models import CNote
from transporter_app.models import Pickup  # Import Pickup from transporter_app
from django.urls import reverse
from django.db.models import Count
from django.http import JsonResponse
from .models import CNote
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
#from .models import Transporter, Pickup  # Assuming you have these models
from django.shortcuts import render, get_object_or_404
from .models import Dealer, CNote  # Make sure these models are correctly imported
from transporter_app.models import Transporter, Pickup  # Import Pickup from transporter_app
from django.contrib.auth import authenticate, login as auth_login
from django.shortcuts import redirect, render
from django.contrib import messages
from transporter_app.models import Transporter
from transporter_app.models import Transporter  # Make sure this import is correct
import logging
from django.http import JsonResponse
from transporter_app.models import City  # सही आयात
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import CNote  # Ensure your models are imported correctly
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.utils import timezone
from .models import CNote
from .models import CNotes
from transporter_app.models import Pickup
import logging
from transporter_app.models import Transporter  # Transporter मॉडल का सही आयात
from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from xml.etree.ElementTree import Element, SubElement, tostring
from .models import BookingType, DeliveryDestination, Dealer, CNote, Article, ArtType, LoadingSheetSummary, LoadingSheetDetail
import logging
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from .models import CNote, LoadingSheetSummary, LoadingSheetDetail
from transporter_app.models import Transporter
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import Http404
from .models import CNotes
from django.shortcuts import get_object_or_404
from django.db import connection
from django.http import JsonResponse
from transporter_app.models import PartyMaster
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
import json
import logging
from django.views.decorators.http import require_GET, require_POST





# Set up logging   
logger = logging.getLogger(__name__)   

@login_required
def render_to_pdf(template_src, context_dict):   
    template = get_template(template_src)   
    html = template.render(context_dict)   
    result = BytesIO()   
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)   
    if not pdf.err:   
        return result.getvalue()   
    return None 
  
def user_owns_cnote(view_func):
    @wraps(view_func)
    def wrapper(request, cnote_id, *args, **kwargs):
        # Get the CNote object using the provided cnote_id
        cnote = get_object_or_404(CNote, id=cnote_id)
        
        # Check if the dealer associated with the CNote is the same as the logged-in user
        if cnote.dealer.user != request.user:
            return HttpResponseForbidden("You do not have permission to access this CNote.")
        
        # Call the original view function
        return view_func(request, cnote_id, *args, **kwargs)
    
    return wrapper


logger = logging.getLogger(__name__)


def custom_login_redirect(request):

    if request.method == 'POST':

        user_type = request.POST.get('user_type')

        username = request.POST.get('username')

        password = request.POST.get('password')

        

        logger.info(f"Login attempt - User Type: {user_type}, Username: {username}")

        

        # First, check if the user exists and credentials are correct

        user = authenticate(request, username=username, password=password)

        

        if user is not None:

            logger.info(f"User  authenticated successfully: {user.username}")

            

            # Debug query to check user flags

            with connection.cursor() as cursor:

                cursor.execute("""

                    SELECT is_dealer, is_transporter, is_active, is_staff 

                    FROM dealer_app_customuser 

                    WHERE username = %s

                """, [username])

                row = cursor.fetchone()

                if row:

                    logger.info(f"User  flags - is_dealer: {row[0]}, is_transporter: {row[1]}, is_active: {row[2]}, is_staff: {row[3]}")

                else:

                    logger.error(f"No user flags found for username: {username}")


            if user_type == 'dealer':

                # Check if user is marked as dealer in CustomUser  model

                if not user.is_dealer:

                    logger.warning(f"User  {username} attempted dealer login but is_dealer=False")

                    messages.error(request, 'Your account is not authorized as a dealer.')

                    return render(request, 'registration/login.html')

                

                # Check if there's an associated Dealer record

                try:

                    dealer = Dealer.objects.select_related('user').get(user=user)

                    logger.info(f"Found dealer record for user {username}: {dealer.name}")

                    login(request, user)

                    logger.info(f"Dealer login successful: {username}")

                    return redirect('dealer:create_cnotes')

                except Dealer.DoesNotExist:

                    logger.error(f"No Dealer record found for user {username} despite is_dealer=True")

                    messages.error(request, 'Dealer account not properly configured. Please contact support.')

                    return render(request, 'registration/login.html')

                

            elif user_type == 'transporter':

                # Check if user is marked as transporter in CustomUser  model

                if not user.is_transporter:

                    logger.warning(f"User  {username} attempted transporter login but is_transporter=False")

                    messages.error(request, 'Your account is not authorized as a transporter.')

                    return render(request, 'registration/login.html')

                

                # Check if there's an associated Transporter record

                try:

                    transporter = Transporter.objects.select_related('user').get(user=user)

                    logger.info(f"Found transporter record for user {username}")

                    login(request, user)

                    logger.info(f"Transporter login successful: {username}")

                    return redirect('transporter:home')

                except Transporter.DoesNotExist:

                    logger.error(f"No Transporter record found for user {username} despite is_transporter=True")

                    messages.error(request, 'Transporter account not properly configured. Please contact support.')

                    return render(request, 'registration/login.html')

            else:

                logger.warning(f"Invalid user type specified: {user_type}")

                messages.error(request, 'Invalid account type selected.')

        else:

            logger.warning(f"Authentication failed for username: {username}")

            messages.error(request, 'Invalid username or password.')


    return render(request, 'registration/login.html')    
@login_required
def login_redirect(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user_type = request.POST.get('user_type')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            print("Authenticated user:", user.username)  # Debug statement
            # Redirect based on user type
            if user_type == 'dealer':
                return redirect('dealer:create_cnotes')  # Redirect to dealer page
            elif user_type == 'transporter':
                return redirect('transporter:home')  # Use the namespace here
        else:
            print("Authentication failed for user:", username)  # Debugging output
            messages.error(request, 'Invalid username or password.')

    return render(request, 'registration/login.html')

@login_required  
@user_owns_cnote  
def get_cnote(request, cnote_id):  
    try:  
        cnote = CNote.objects.get(id=cnote_id)  
        articles = Article.objects.filter(cnote=cnote)  
        cnote_data = {  
            'id': cnote.id,  
            'booking_type': cnote.booking_type,  
            'delivery_destination': cnote.delivery_destination,  
            'consignee_name': cnote.consignee_name,  
            'payment_type': cnote.payment_type,  
            'grand_total': cnote.grand_total,  
            'created_at': cnote.created_at.strftime('%Y-%m-%d %H:%M:%S'),  
            'articles': [  
                {  
                    'article_type': article.article_type,  
                    'art': article.art,  
                    'art_type': article.art_type,  
                    'said_to_cont': article .said_to_cont,  
                    'art_amt': article.art_amt  
                } for article in articles  
            ]  
        }  
        return JsonResponse({'status': 'success', 'data': cnote_data})  
    except CNote.DoesNotExist:  
        logger.warning(f"CNote not found: {cnote_id}")  
        return JsonResponse({'status': 'error', 'message': 'CNote not found'}, status=404)  
    except Exception as e:  
        logger.error(f"Error getting CNote: {str(e)}")  
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)  

@login_required  
def list_cnotes(request):  
    try:  
        cnotes = CNote.objects.filter(dealer__user=request.user).order_by('-created_at')  
        paginator = Paginator(cnotes, 10)  
        page_number = request.GET.get('page')  
        page_obj = paginator.get_page(page_number)  
        cnotes_data = [  
            {  
                'id': cnote.id,  
                'booking_type': cnote.booking_type,  
                'delivery_destination': cnote.delivery_destination,  
                'consignee_name': cnote.consignee_name,  
                'payment_type': cnote.payment_type,  
                'grand_total': cnote.grand_total,  
                'created_at': cnote.created_at.strftime('%Y-%m-%d %H:%M:%S')  
            } for cnote in page_obj  
        ]  
        return JsonResponse({'status': 'success', 'data': cnotes_data, 'count': paginator.count})  
    except Exception as e:  
        logger.error(f"Error getting CNotes: {str(e)}")  
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)  

@login_required  
@user_owns_cnote  
def update_cnote(request, cnote_id):  
    cnote = get_object_or_404(CNote, id=cnote_id) 
    if request.method == 'POST':  
        # Access form data using request.POST  
        dealer_id = request.POST.get('dealer_id')  
        booking_type = request.POST.get('booking_type')  
        delivery_type = request.POST.get('delivery_type')  
        delivery_method = request.POST.get('delivery_method')  
        delivery_destination = request.POST.get('delivery_destination')  
        ewayBillNumber = request.POST.get('ewayBillNumber')  
        consignor_name = request.POST.get('consignor_name')  
        consignor_mobile = request.POST.get('consignor_mobile')  
        consignor_gst = request.POST.get('consignor_gst')  
        consignor_address = request.POST.get('consignor_address')  
        consignee_name = request.POST.get('consignee_name')  
        consignee_mobile = request.POST.get('consignee_mobile')  
        consignee_gst = request.POST.get('consignee_gst')  
        consignee_address = request.POST.get('consignee_address')  
        article = request.POST.get('article')  
        art = request.POST.get('art')  
        art_type = request.POST.get('art_type')  
        said_to_cont = request.POST.get('said_to_cont')  
        art_amt = request.POST.get('art_amt')  
        actual_weight = request.POST.get('actual_weight')  
        charged_weight = request.POST.get('charged_weight')  
        weight_rate = request.POST.get('weight_rate')  
        weight_amount = request.POST.get('weight_amount')  
        fix_amount = request.POST.get('fix_amount')  
        invoice_number = request.POST.get('invoice_number')  
        declared_value = request.POST.get('declared_value')  
        risk_type = request.POST.get('risk_type')  
        pod_required = request.POST.get('pod_required')  
        freight = request.POST.get('freight')  
        docket_charge = request.POST.get('docket_charge')  
        door_delivery_charge = request.POST.get('door_delivery_charge')  
        handling_charge = request.POST.get('handling_charge')  
        pickup_charge = request.POST.get('pickup_charge')  
        transhipment_charge = request.POST.get('transhipment_charge')  
        insurance = request.POST.get('insurance')  
        fuel_surcharge = request.POST.get('fuel_surcharge')  
        commission = request.POST.get('commission')  
        other_charge = request.POST.get('other_charge')  
        carrier_risk = request.POST.get('carrier_risk')  
        grand_total = request.POST.get('grand_total')  

        # Update the CNote object and save it to the database  
        cnote.dealer = Dealer.objects.get(id=dealer_id)  
        cnote.booking_type = booking_type  
        cnote.delivery_type = delivery_type  
        cnote.delivery_method = delivery_method  
        cnote .delivery_destination = delivery_destination  
        cnote.ewayBillNumber = ewayBillNumber  
        cnote.consignor_name = consignor_name  
        cnote.consignor_mobile = consignor_mobile  
        cnote.consignor_gst = consignor_gst  
        cnote.consignor_address = consignor_address  
        cnote.consignee_name = consignee_name  
        cnote.consignee_mobile = consignee_mobile  
        cnote.consignee_gst = consignee_gst  
        cnote.consignee_address = consignee_address  
        cnote.article = article  
        cnote.art = art  
        cnote.art_type = art_type  
        cnote.said_to_cont = said_to_cont  
        cnote.art_amt = art_amt  
        cnote.actual_weight = actual_weight  
        cnote.charged_weight = charged_weight  
        cnote.weight_rate = weight_rate  
        cnote.weight_amount = weight_amount  
        cnote.fix_amount = fix_amount  
        cnote.invoice_number = invoice_number  
        cnote.declared_value = declared_value  
        cnote.risk_type = risk_type  
        cnote.pod_required = pod_required  
        cnote.freight = freight  
        cnote.docket_charge = docket_charge 
        cnote.door_delivery_charge = door_delivery_charge  
        cnote.handling_charge = handling_charge  
        cnote.pickup_charge = pickup_charge  
        cnote.transhipment_charge = transhipment_charge  
        cnote.insurance = insurance  
        cnote.fuel_surcharge = fuel_surcharge  
        cnote.commission = commission  
        cnote.other_charge = other_charge  
        cnote.carrier_risk = carrier_risk  
        cnote.grand_total = grand_total  
        cnote.save()  
        messages.success(request, 'CNote updated successfully.')  
        return redirect('dealer:dealer_cnotes')  
    else:  
        return render(request, 'dealer/update_cnote.html', {'cnote': cnote})  

@login_required  
@user_owns_cnote  
def delete_cnote(request, cnote_id):  
    cnote = get_object_or_404(CNote, id=cnote_id)  
    if request.method == 'POST':  
        cnote.delete()  
        messages.success(request, 'CNote deleted successfully.')  
        return redirect('dealer:dealer_cnotes')  
    return render(request, 'dealer/confirm_delete.html', {'cnote': cnote})  

import logging

logger = logging.getLogger(__name__)

@login_required
@require_POST
@transaction.atomic
def create_loading_sheet(request):
    try:
        data = json.loads(request.body)
        transporter_id = data.get('transporter_id')
        cnote_ids = data.get('cnote_ids', [])

        logger.info(f"Creating loading sheet for transporter {transporter_id} with CNotes: {cnote_ids}")

        transporter = get_object_or_404(Transporter, id=transporter_id)
        dealer = request.user.dealer

        loading_sheet = LoadingSheetSummary.objects.create(
            dealer=dealer,
            transporter=transporter,
            city=dealer.city,
            total_cnote_number=len(cnote_ids),
            state=dealer.state,
            status='dispatched'
        )

        logger.info(f"Created LoadingSheetSummary with ID: {loading_sheet.ls_number}")

        total_package = 0
        total_paid_amount = 0
        total_to_pay_amount = 0

        for cnote_id in cnote_ids:
            try:
                cnote = CNotes.objects.select_for_update().get(pk=cnote_id)
                if cnote.status in ['booked', 'received_at_godown']:
                    LoadingSheetDetail.objects.create(
                        loading_sheet=loading_sheet,
                        cnote=cnote,
                        consignor_name=cnote.consignor_name,
                        consignee_name=cnote.consignee_name,
                        consignor_contact=cnote.consignor_mobile,
                        consignee_contact=cnote.consignee_mobile,
                        destination=str(cnote.delivery_destination),
                        art=cnote.total_art,
                        payment_type=cnote.payment_type,
                        amount=cnote.grand_total,
                        status='dispatched'
                    )
                    logger.info(f"Created LoadingSheetDetail for CNotes {cnote.cnote_number}")
                    
                    # Update CNotes status to 'dispatched'
                    cnote.status = 'dispatched'
                    cnote.save()
                    logger.info(f"Updated CNotes {cnote.cnote_number} status to 'dispatched'")

                    total_package += cnote.articles.count()
                    if cnote.payment_type == 'PAID':
                        total_paid_amount += cnote.grand_total
                    else:
                        total_to_pay_amount += cnote.grand_total
                else:
                    logger.warning(f"CNotes {cnote.cnote_number} status is not eligible for dispatch")
            except CNotes.DoesNotExist:
                logger.warning(f"CNotes with ID {cnote_id} does not exist")
                continue
            except Exception as e:
                logger.error(f"Error processing CNotes {cnote_id}: {str(e)}")
                continue

        loading_sheet.total_package = total_package
        loading_sheet.total_paid_amount = total_paid_amount
        loading_sheet.total_to_pay_amount = total_to_pay_amount
        loading_sheet.save()

        logger.info(f"Loading sheet {loading_sheet.ls_number} updated with totals")

        return JsonResponse({
            'message': 'Loading sheet created successfully',
            'loading_sheet_id': loading_sheet.ls_number
        })

    except Exception as e:
        logger.error(f"Error creating loading sheet: {str(e)}")
        return JsonResponse({
            'error': str(e)
        }, status=400)

@login_required
@require_POST
@transaction.atomic
def cancel_loading_sheet(request, loading_sheet_id):
    try:
        loading_sheet = get_object_or_404(LoadingSheetSummary, ls_number=loading_sheet_id, dealer=request.user.dealer)
        
        # Get all CNotes associated with this loading sheet
        cnotes = CNotes.objects.filter(loading_sheet_details__loading_sheet=loading_sheet)
        
        # Update the status of each CNote back to 'booked'
        for cnote in cnotes:
            if cnote.status == 'dispatched':
                cnote.status = 'booked'
                cnote.save()
                logger.info(f"CNotes {cnote.cnote_number} status reverted to 'booked'")
        
        # Update the loading sheet status
        loading_sheet.status = 'cancelled'
        loading_sheet.save()
        
        # Delete the loading sheet details
        LoadingSheetDetail.objects.filter(loading_sheet=loading_sheet).delete()
        
        logger.info(f"Loading sheet {loading_sheet_id} cancelled successfully")
        
        return JsonResponse({
            'success': True,
            'message': 'Loading sheet cancelled successfully.'
        })
    except Exception as e:
        logger.error(f"Error cancelling loading sheet {loading_sheet_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@login_required
def update_cnote_status(request, cnote_id):
    cnote = get_object_or_404(CNotes, id=cnote_id)
    new_status = request.POST.get('status')
    if new_status:
        cnote.status = new_status
        cnote.save()
        messages.success(request, f'CNotes status updated to: {new_status}')
    else:
        messages.error(request, 'Invalid status')
    return redirect('dealer:create_cnotes')
# ... other views ...

@login_required
def mark_cnote_received(request, cnote_id):
    cnote = get_object_or_404(CNotes, id=cnote_id)
    cnote.update_status('received')  # Update status to received
    messages.success(request, 'CNotes marked as received')
    return redirect('transporter:cnote_detail', cnote_id=cnote.id)

@login_required
def create_delivery(request, cnote_id):
    cnote = get_object_or_404(CNotes, id=cnote_id)
    Delivery.objects.create(cnote=cnote)  # Create a new delivery record
    cnote.update_status('due_for_delivery')  # Update status to due for delivery
    messages.success(request, 'Delivery created and CNotes marked as due for delivery')
    return redirect('transporter:delivery_list')

@login_required
def update_delivery(request, delivery_id):
    delivery = get_object_or_404(Delivery, id=delivery_id)
    if request.method == 'POST':
        is_successful = request.POST.get('is_successful') == 'true'
        delivery.is_successful = is_successful
        delivery.delivered_at = timezone.now() if is_successful else None
        delivery.save()
        status = 'delivered' if is_successful else 'received_at_godown'
        messages.success(request , f'Delivery updated and CNotes marked as {status}')
    return redirect('transporter:delivery_list')

@login_required
def cancel_cnote(request, cnote_id):
    cnote = get_object_or_404(CNotes, id=cnote_id)
    if cnote.status != 'cancelled':
        cnote.update_status('cancelled')
        messages.success(request, 'CNotes cancelled successfully')
    else:
        messages.error(request, 'This CNotes is already cancelled')
    return redirect('dealer:cnote_detail', cnote_id=cnote.id)

@login_required
def loading_sheet(request):
    dealer = request.user.dealer  # Get the dealer associated with the logged-in user
    cnotes = CNotes.objects.filter(dealer=dealer, status__in=['booked', 'received'])
    destinations = DeliveryDestination.objects.filter(id__in=cnotes.values('delivery_destination'))

    # Fetch all transporters to pass to the template
    transporters = Transporter.objects.all()  # Fetch all transporters

    context = {
        'available_cnotes': cnotes,
        'destinations': destinations,
        'dealer': dealer,  # Ensure dealer is included in the context
        'transporters': transporters  # Pass transporters to the template
    }

    if request.method == 'POST':
        cnote_ids = request.POST.getlist('cnote_ids')  # Get the list of CNotes IDs
        transporter_id = request.POST.get('transporter_id')

        if not cnote_ids:
            messages.error(request, 'Please select at least one CNotes for the loading sheet.')
            return redirect('dealer:loading_sheet')

        if not transporter_id:
            messages.error(request, 'Please select a transporter.')
            return redirect('dealer:loading_sheet')

        try:
            transporter = Transporter.objects.get(id=transporter_id)
        except Transporter.DoesNotExist:
            messages.error(request, 'Invalid transporter selected.')
            return redirect('dealer:loading_sheet')

        # Create loading sheet logic here...

        messages.success(request, 'Loading sheet created successfully.')
        return redirect('dealer:loading_sheet_detail', loading_sheet_id=loading_sheet.id)

    return render(request, 'dealer/loading_sheet.html', context)

@login_required
def booking_register_view(request):
    # Get the logged-in dealer
    try:
        dealer = request.user.dealer
    except AttributeError:
        # If the user is not a dealer, show an error or redirect
        return redirect('login')

    # Filter CNotes for the logged-in dealer
    dealer_cnotes = CNotes.objects.filter(dealer=dealer).order_by('-created_at')
    
    # Get article data for each CNotes
    article_data = []
    for cnote in dealer_cnotes:
        try:
            articles = Article.objects.filter(cnote=cnote)
            
            # Safely collect article data with proper null checks
            art_types = []
            said_to_contain_list = []
            art_amounts = []
            total_art = 0
            
            for article in articles:
                # Handle art_type safely - use the actual art type name from the selection
                try:
                    art_type_name = article.art_type.art_type_name if article.art_type else 'N/A'
                    # Convert database value to display value
                    if art_type_name == 'type1':
                        art_type_name = 'SMALL BOX'
                    elif art_type_name == 'type2':
                        art_type_name = 'BIG BOX'
                    art_types.append(art_type_name)
                except AttributeError:
                    art_types.append('N/A')
                
                # Handle said_to_contain safely
                try:
                    art_value = str(article.art) if article.art is not None else '0'
                    said_to_contain = str(article.said_to_contain) if article.said_to_contain else 'N/A'
                    said_to_contain_list.append(f'{said_to_contain} - {art_value}')
                except AttributeError:
                    said_to_contain_list.append('N/A - 0')
                
                # Handle art_amount safely
                try:
                    art_amount = str(article.art_amount) if article.art_amount is not None else '0'
                    art_amounts.append(art_amount)
                except AttributeError:
                    art_amounts.append('0')
                
                # Calculate total_art safely
                try:
                    total_art += article.art if article.art is not None else 0
                except AttributeError:
                    pass
            
            # Create article data dictionary with safe default values
            article_entry = {
                'cnote_id': cnote.id,
                'articles': articles,
                'total_art': total_art,
                'art_types': '/'.join(art_types),
                'said_to_contain': '/'.join(said_to_contain_list),
                'art_amounts': '/'.join(art_amounts),
                'cnote_number': getattr(cnote, 'cnote_number', 'N/A'),
                'booking_type': getattr(cnote, 'booking_type', 'N/A'),
                'delivery_destination': getattr(cnote, 'delivery_destination', 'N/A'),
                'consignor_name': getattr(cnote, 'consignor_name', 'N/A'),
                'consignee_name': getattr(cnote, 'consignee_name', 'N/A'),
                'payment_type': getattr(cnote, 'payment_type', 'N/A'),
                'grand_total': getattr(cnote, 'grand_total', 0),
                'created_at': getattr(cnote, 'created_at', None),
                'eway_bill_number': getattr(cnote, 'eway_bill_number', 'N/A'),
                'actual_weight': getattr(cnote, 'actual_weight', 0),
                'charged_weight': getattr(cnote, 'charged_weight', 0),
                'weight_rate': getattr(cnote, 'weight_rate', 0),
                'weight_amount': getattr(cnote, 'weight_amount', 0),
                'fix_amount': getattr(cnote, 'fix_amount', 0),
                'invoice_number': getattr(cnote, 'invoice_number', 'N/A'),
                'declared_value': getattr(cnote, 'declared_value', 0),
                'risk_type': getattr(cnote, 'risk_type', 'N/A'),
                'pod_required': getattr(cnote, 'pod_required', 'N/A'),
                'freight': getattr(cnote, 'freight', 0),
                'docket_charge': getattr(cnote, 'docket_charge', 0),
                'door_delivery_charge': getattr(cnote, 'door_delivery_charge', 0),
                'handling_charge': getattr(cnote, 'handling_charge', 0),
                'pickup_charge': getattr(cnote, 'pickup_charge', 0),
                'transhipment_charge': getattr(cnote, 'transhipment_charge', 0),
                'insurance': getattr(cnote, 'insurance', 0),
                'fuel_surcharge': getattr(cnote, 'fuel_surcharge', 0),
                'commission': getattr(cnote, 'commission', 0),
                'other_charge': getattr(cnote, 'other_charge', 0),
                'carrier_risk': getattr(cnote, 'carrier_risk', 0),
                'delivery_type': getattr(cnote, 'delivery_type', 'N/A'),
                'delivery_method': getattr(cnote, 'delivery_method', 'N/A'),
                'status': getattr(cnote, 'status', 'N/A'),
                'consignor_gst': getattr(cnote, 'consignor_gst', 'N/A'),
                'consignee_gst': getattr(cnote, 'consignee_gst', 'N/A'),
            }
            
            article_data.append(article_entry)
            
        except Exception as e:
            # Log the error and continue with the next CNotes
            logger.error(f"Error processing CNotes {cnote.id}: {str(e)}")
            continue

    # Pass the required data to the template
    context = {
        'dealer': dealer,
        'dealer_cnotes': dealer_cnotes,
        'article_data': article_data,
    }

    return render(request, 'dealer/booking_register.html', context)

@login_required
def cnote_options(request, cnote_id):
    cnote = get_object_or_404(CNotes, id=cnote_id)
    if request.method == 'POST':
        option = request.POST.get('option')
        if option == 'pdf':
            pdf_file = render_to_pdf('dealer/cnote_pdf.html', {'cnote': cnote})
            response = HttpResponse(pdf_file, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="cnote_{cnote_id}.pdf"'
            return response
        elif option == 'print':
            return redirect('create_cnotes')  # Adjust as needed
    return render(request, 'dealer/cnote_options.html', {'cnote': cnote})


@login_required
def view_pending_pickups(request, transporter_id):
    # Get the transporter object based on the ID
    transporter = get_object_or_404(Transporter, id=transporter_id)

    # Fetch the pending pickups for this transporter
    pending_pickups = Pickup.objects.filter(transporter=transporter, status='pending')

    # Render the template with the pending pickups
    return render(request, 'dealer/view_pending_pickups.html', {
        'transporter': transporter,
        'pending_pickups': pending_pickups
    })



@login_required
def view_pending_pickups(request, transporter_id):
    # Get the transporter object based on the ID
    transporter = get_object_or_404(Transporter, id=transporter_id)

    # Fetch the pending pickups for this transporter
    pending_pickups = Pickup.objects.filter(transporter=transporter, status='pending')

    # Render the template with the pending pickups
    return render(request, 'dealer/view_pending_pickups.html', {
        'transporter': transporter,
        'pending_pickups': pending_pickups
    })




@login_required
def view_pickups(request):
    pickups = Pickup.objects.all()  # Get all pickups
    return render(request, 'dealer/view_pickups.html', {'pickups': pickups})




def mark_pickup(request, cnote_id):
    # Logic to mark the pickup
    pickup = get_object_or_404(Pickup, cnote_id=cnote_id)
    # Update the pickup status or any other logic you need
    pickup.status = 'picked_up'  # Example status update
    pickup.save()
    return render(request, 'dealer/pickup_marked.html', {'pickup': pickup})

def add_dealer(request):
    # यहाँ पर डीलर जोड़ने की लॉजिक डालें
    return render(request, 'dealer/add_dealer.html')  # डीलर जोड़ने का टेम्पलेट


def print_pdf(request, cnote_id):
    # यहाँ पर PDF प्रिंट करने की लॉजिक डालें
    return render(request, 'dealer/print_pdf.html', {'cnote_id': cnote_id})  # PDF प्रिंट करने का टेम्पलेट


def download_pdf(request, cnote_id):
    # यहाँ पर PDF डाउनलोड करने की लॉजिक डालें
    cnote = CNotes.objects.get(id=cnote_id)  # उदाहरण के लिए, CNotes मॉडल से डेटा प्राप्त करना
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="cnote_{cnote_id}.pdf"'
    
    # यहाँ पर PDF जनरेट करने की लॉजिक डालें
    # उदाहरण के लिए, आप ReportLab या किसी अन्य लाइब्रेरी का उपयोग कर सकते हैं

    return response  # PDF फ़ाइल को वापस करें


@login_required
def get_cnote_details(request, cnote_number):
    cnote = get_object_or_404(CNotes, cnote_number=cnote_number)
    data = {
        'cnote_number': cnote.cnote_number,
        'created_at': cnote.created_at.isoformat(),
        'payment_type': cnote.payment_type,
        'booking_type': cnote.booking_type,
        'delivery_type': cnote.delivery_type,
        'delivery_method': cnote.delivery_method,
        'delivery_destination': cnote.delivery_destination,
        'eway_bill_number': cnote.eway_bill_number,
        'consignor_name': cnote.consignor_name,
        'consignor_mobile': cnote.consignor_mobile,
        'consignor_gst': cnote.consignor_gst,
        'consignor_address': cnote.consignor_address,
        'consignee_name': cnote.consignee_name,
        'consignee_mobile': cnote.consignee_mobile,
        'consignee_gst': cnote.consignee_gst,
        'consignee_address': cnote.consignee_address,
        'articles': [
            {
                'name': article.name,
                'quantity': article.quantity,
                'type': article.type,
                'said_to_contain': article.said_to_contain,
                'amount': float(article.amount)
            } for article in cnote.articles.all()
        ],
        'freight': float(cnote.freight),
        'docket_charge': float(cnote.docket_charge),
        'door_delivery_charge': float(cnote.door_delivery_charge),
        'handling_charge': float(cnote.handling_charge),
        'other_charge': float(cnote.other_charge),
        'grand_total': float(cnote.grand_total),
        'dealer': {
            'logo_url': cnote.dealer.logo.url if cnote.dealer.logo else None
        }
    }
    return JsonResponse(data)

@login_required
def cnote_success(request, cnote_number):
    try:
        # Directly fetch the CNotes object with related articles
        cnote = CNotes.objects.prefetch_related('articles').get(cnote_number=cnote_number)
        return render(request, 'dealer/cnote_success.html', {'cnote': cnote})
    except CNotes.DoesNotExist:
        messages.error(request, 'CNote not found.')
        return redirect('dealer:create_cnotes')
        
@login_required
def view_cnote(request, cnote_number):
    print(f"Searching for CNotes with number: {cnote_number}")
    try:
        cnote = CNotes.objects.get(cnote_number=cnote_number)
        print(f"CNotes found: {cnote}")
        return render(request, 'dealer/view_cnote.html', {'cnote': cnote})
    except CNotes.DoesNotExist:
        print(f"CNotes with number {cnote_number} does not exist")
        raise Http404("CNotes does not exist")
    

# dealer_app/views.py

logger = logging.getLogger(__name__)

@login_required
def fetch_pending_cnotes(request):
    dealer = request.user.dealer
    cnotes = CNotes.objects.filter(
        dealer=dealer, 
        status__in=['booked', 'received_at_godown']
    ).values(
        'id', 'created_at', 'cnote_number', 'delivery_destination__destination_name',
        'consignor_name', 'consignee_name', 'total_art', 'actual_weight', 
        'charged_weight', 'booking_type', 'freight', 'grand_total'
    )
    
    # Convert queryset to list and ensure total_art is not None
    cnotes_list = list(cnotes)
    for cnote in cnotes_list:
        if cnote['total_art'] is None:
            cnote['total_art'] = 0
            
    return JsonResponse(cnotes_list, safe=False)

logger = logging.getLogger(__name__)
@csrf_exempt
def fetch_transporters(request):
    transporters = Transporter.objects.all()
    
    # Create XML structure
    root = Element('transporters')
    for transporter in transporters:
        transporter_elem = SubElement(root, 'transporter')
        transporter_elem.set('id', str(transporter.id))
        name_elem = SubElement(transporter_elem, 'name')
        name_elem.text = transporter.name

    # Convert XML to string
    xml_str = tostring(root, encoding='unicode')
    
    # Return XML response
    return HttpResponse(xml_str, content_type='application/xml')

@login_required
def home(request):
    # Logic specific to the dealer dashboard
    return render(request, 'transporter_app/home.html')  # Adjust the template path as needed


def get_cities(request):
    if request.is_ajax():
        cities = City.objects.values_list('name', flat=True)
        return JsonResponse(list(cities), safe=False)
    return JsonResponse([], safe=False)

def fetch_cities(request):
    # Get all city names from the City model
    cities = City.objects.values_list('name', flat=True)
    return JsonResponse(list(cities), safe=False)

logger = logging.getLogger(__name__)

@login_required
@csrf_exempt
def send_pickup_request(request):
    if request.method == 'POST':
        logger.debug("Received POST request for sending pickup request.")
        logger.debug(f"POST data: {request.POST}")
        
        transporter_name = request.POST.get('transporter_name')
        cnote_ids = request.POST.get('cnote_ids', '')

        logger.debug(f"Transporter name: {transporter_name}, CNotes IDs: {cnote_ids}")

        if not transporter_name:
            messages.error(request, 'No transporter name provided.')
            logger.warning("No transporter name provided.")
            return redirect('dealer:loading_sheet')

        if isinstance(cnote_ids, str):
            cnote_ids = [id.strip() for id in cnote_ids.split(',') if id.strip()]
        
        if not cnote_ids:
            messages.error(request, 'No valid CNotes IDs provided.')
            logger.warning("No valid CNotes IDs provided.")
            return redirect('dealer:loading_sheet')

        try:
            transporter = Transporter.objects.get(name=transporter_name)
        except Transporter.DoesNotExist:
            messages.error(request, f'Transporter with name "{transporter_name}" does not exist.')
            logger.warning(f"Transporter with name '{transporter_name}' does not exist.")
            return redirect('dealer:loading_sheet')

        dealer = request.user.dealer
        
        try:
            loading_sheet_summary = LoadingSheetSummary.objects.create(
                dealer=dealer,
                transporter=transporter,
                total_cnote=len(cnote_ids),
                status='dispatched'
            )

            valid_cnote_ids = []
            total_art = 0
            total_paid_amount = total_topay_amount = total_tbb_amount = total_foc_amount = 0

            for cnote_id in cnote_ids:
                try:
                    cnote = CNotes.objects.get(id=int(cnote_id))
                    if cnote.status in ['booked', 'received_at_godown']:  # Update: Added status check
                        valid_cnote_ids.append(cnote_id)

                        LoadingSheetDetail.objects.create(
                            loading_sheet=loading_sheet_summary,
                            cnote=cnote,
                            consignor_name=cnote.consignor_name,
                            consignee_name=cnote.consignee_name,
                            consignor_contact=cnote.consignor_mobile,
                            consignee_contact=cnote.consignee_mobile,
                            destination=str(cnote.delivery_destination),
                            art=cnote.total_art,
                            payment_type=cnote.payment_type,
                            amount=cnote.grand_total,
                            status='dispatched'
                        )

                    cnote.status = 'dispatched'
                    cnote.save()
                    logger.info(f"CNotes {cnote_id} status updated to 'dispatched'")

                    total_art += cnote.total_art
                    if cnote.payment_type == 'PAID':
                        total_paid_amount += cnote.grand_total
                    elif cnote.payment_type == 'TO PAY':
                        total_topay_amount += cnote.grand_total
                    elif cnote.payment_type == 'TBB':
                        total_tbb_amount += cnote.grand_total
                    elif cnote.payment_type == 'FOC':
                        total_foc_amount += cnote.grand_total

                    logger.debug(f"LoadingSheetDetail created for CNotes ID: {cnote_id}")
                except ValueError:
                    logger.warning(f"Invalid CNotes ID format: {cnote_id}")
                except CNotes.DoesNotExist:
                    logger.warning(f"CNotes with ID {cnote_id} does not exist")
                except Exception as e:
                    logger.error(f"Error processing CNotes {cnote_id}: {str(e)}")

            loading_sheet_summary.total_art = total_art
            loading_sheet_summary.total_paid_amount = total_paid_amount
            loading_sheet_summary.total_topay_amount = total_topay_amount
            loading_sheet_summary.total_tbb_amount = total_tbb_amount
            loading_sheet_summary.total_foc_amount = total_foc_amount
            loading_sheet_summary.save()

            logger.info(f"Loading sheet {loading_sheet_summary.ls_number} created successfully")

            messages.success(request, f'Loading sheet {loading_sheet_summary.ls_number} created successfully!')

            # Redirect to the mf_print.html page using ls_number
            return redirect('dealer:mf_print', loading_sheet_number=loading_sheet_summary.ls_number)
        
        except Exception as e:
            logger.error(f"Error creating loading sheet: { str(e)}")
            messages.error(request, f'Error creating loading sheet: {str(e)}')
            return redirect('dealer:loading_sheet')

    messages.error(request, 'Invalid request method.')
    return redirect('dealer:loading_sheet')

@login_required
def accept_loading_sheet(request, sheet_id):
    loading_sheet = get_object_or_404(LoadingSheet, id=sheet_id)
    for cnote in loading_sheet.cnotes.all():
        cnote.status = 'received'
        cnote.save()
    messages.success(request, 'CNotes acknowledged by transporter.')
    return redirect('transporter:home')

@login_required
def mark_as_delivered(request, cnote_id):
    cnote = get_object_or_404(CNotes, id=cnote_id)
    Delivery.objects.create(cnote=cnote, is_successful=True)
    messages.success(request, 'CNotes marked as delivered.')
    return redirect('transporter:delivery_list')

@login_required
def transporter_list(request):
    # Fetch all transporters
    transporters = Transporter.objects.all()

    # Render the template with the correct path
    return render(request, 'transporter/transporter_list.html', {'transporters': transporters})

@login_required
def search(request):
    dealer = request.user.dealer  # Fetch the logged-in dealer's information
    return render(request, 'dealer/search.html', {'dealer': dealer})  # Pass dealer info to the template



@login_required
def search_loading_sheets(request):
        # Get the logged-in dealer
    try:
        dealer = request.user.dealer
    except AttributeError:
        # If the user is not a dealer, show an error or redirect
        return redirect('login')

    if request.method == 'POST':
        search_type = request.POST.get('type')
        query = request.POST.get('query', '').strip()
        
        if search_type == 'ls':
            dealer = request.user.dealer
            if query:
                # Search for a specific loading sheet
                loading_sheets = LoadingSheetSummary.objects.filter(
                    dealer=dealer,
                    ls_number__icontains=query
                )
            else:
                # Show all loading sheets for the dealer
                loading_sheets = LoadingSheetSummary.objects.filter(dealer=dealer)
            
            results = loading_sheets.order_by('-created_at')
        else:
            results = []
    else:
        results = []
    
    return render(request, 'dealer/search.html', {
        'results': results,
        'query': query if 'query' in locals() else '',
    })

logger = logging.getLogger(__name__)

@login_required
def mf_print(request, loading_sheet_number):
    try:
        # Get the loading sheet
        loading_sheet = get_object_or_404(LoadingSheetSummary, ls_number=loading_sheet_number)
        
        # Get all CNotes associated with this loading sheet
        loading_sheet_details = LoadingSheetDetail.objects.filter(
            loading_sheet=loading_sheet
        ).select_related('cnote')
        
        # Get the dealer associated with the loading sheet
        dealer = loading_sheet.dealer
        
        context = {
            'loading_sheet': loading_sheet,
            'loading_sheet_details': loading_sheet_details,
            'dealer': dealer,
            'transporter': loading_sheet.transporter,
        }
        
        return render(request, 'dealer/mf_print.html', context)
        
    except Exception as e:
        logger.error(f"Error rendering MF Print page: {str(e)}")
        messages.error(request, 'Error loading the print page. Please try again.')
        return redirect('dealer:loading_sheet')
    
@login_required
@require_POST
def cancel_loading_sheet(request, loading_sheet_id):
    try:
        loading_sheet = get_object_or_404(LoadingSheetSummary, ls_number=loading_sheet_id, dealer=request.user.dealer)
        
        # Get all CNotes associated with this loading sheet
        cnotes = CNotes.objects.filter(loading_sheet_details__loading_sheet=loading_sheet)
        
        # Update the status of each CNote
        for cnote in cnotes:
            if cnote.status == 'dispatched':
                # Revert the status to 'booked' or the appropriate previous state
                cnote.status = 'booked'
                cnote.save()
        
        # Update the loading sheet status
        loading_sheet.status = 'cancelled'
        loading_sheet.save()
        
        # Delete the loading sheet details
        LoadingSheetDetail.objects.filter(loading_sheet=loading_sheet).delete()
        
        return JsonResponse({'success': True, 'message': 'Loading sheet cancelled successfully.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

logger = logging.getLogger(__name__)
@login_required
def create_cnotes(request):
    # Get the logged-in dealer
    dealer = request.user.dealer  # Assuming you have a OneToOneField relationship
    
    logger = logging.getLogger(__name__)
    logger.info("Create CNotes view called.")
    
    try:
        dealer = Dealer.objects.get(user=request.user)
        logger.info(f"Dealer: {dealer}")
    except Dealer.DoesNotExist:
        logger.error('Dealer not found.')
        return JsonResponse({'success': False, 'error': 'Dealer not found.'})
     
    # Fetch the last CNote created by the dealer
    last_cnote = CNotes.objects.filter(dealer=dealer).order_by('-created_at').first()

    if request.method == 'POST':
        logger.info("POST request received.")
        logger.info(f"POST data: {request.POST}")

        try:
            # Process charge fields with explicit mapping
            charge_fields = {
                'freight': 'freight',
                'docket_charge': 'docket_charge',
                'door_delivery_charge': 'door_delivery_charge',
                'handling_charge': 'handling_charge',
                'pickup_charge': 'pickup_charge',
                'transhipment_charge': 'transhipment_charge',
                'insurance': 'insurance',
                'fuel_surcharge': 'fuel_surcharge',
                'commission': 'commission',
                'other_charge': 'other_charge',
                'carrier_risk': 'carrier_risk',
                'grand_total': 'grand_total'
            }
            
            charges = {}
            for field, db_field in charge_fields.items():
                try:
                    value = request.POST.get(field, '0')
                    charges[db_field] = float(value)
                    logger.info(f"Processed {field}: {charges[db_field]}")
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error converting {field}: {str(e)}")
                    charges[db_field] = 0.0

            # Create CNotes object with all fields
            cnote = CNotes(
                dealer=dealer,
                booking_type=request.POST.get('booking_type'),
                delivery_type=request.POST.get('delivery_type'),
                delivery_method=request.POST.get('delivery_method'),
                delivery_destination=DeliveryDestination.objects.get_or_create(
                    destination_name=request.POST.get('delivery_destination')
                )[0],
                eway_bill_number=request.POST.get('ewayBillNumber'),
                consignor_name=request.POST.get('consignor_name'),
                consignor_mobile=request.POST.get('consignor_mobile'),
                consignor_gst=request.POST.get('consignorGST'),
                consignor_address=request.POST.get('consignorAddress'),
                consignee_name=request.POST.get('consignee_name'),
                consignee_mobile=request.POST.get('consignee_mobile'),
                consignee_gst=request.POST.get('consigneeGST'),
                consignee_address=request.POST.get('consigneeAddress'),
                actual_weight=float(request.POST.get('actual_weight', 0)),
                charged_weight=float(request.POST.get('charged_weight', 0)),
                weight_rate=float(request.POST.get('weight_rate', 0)),
                weight_amount=float(request.POST.get('weight_amount', 0)),
                fix_amount=float(request.POST.get('fix_amount', 0)),
                invoice_number=request.POST.get('invoice_number'),
                declared_value=float(request.POST.get('declared_value', 0)),
                risk_type=request.POST.get('risk_type'),
                pod_required=request.POST.get('pod_required'),
                payment_type=request.POST.get('paymentType'),
                **charges  # Unpack all charge fields
            )
            
            # Save the CNotes object
            cnote.save()
            logger.info(f"CNotes saved successfully. ID: {cnote.id}")

            # Process article details from the new format
            articles_data = []
            index = 0
            while True:
                article_type = request.POST.get(f'articles[{index}][article]')
                if article_type is None:
                    break
                
                art = request.POST.get(f'articles[{index}][art]')
                art_type = request.POST.get(f'articles[{index}][artType]')
                said_to_contain = request.POST.get(f'articles[{index}][saidToContain]')
                per_pkt_amt = request.POST.get(f'articles[{index}][perPktAmt]', '0')
                total_amt = request.POST.get(f'articles[{index}][totalAmt]', '0')
                
                articles_data.append({
                    'article_type': article_type,
                    'art': art,
                    'art_type': art_type,
                    'said_to_contain': said_to_contain,
                    'art_amount': float(total_amt)  # Using total_amt as art_amount
                })
                index += 1

            # Create Article objects
            for article_data in articles_data:
                Article.objects.create(
                    cnote=cnote,
                    article_type=article_data['article_type'],
                    art=article_data['art'],
                    art_type=ArtType.objects.get_or_create(
                        art_type_name=article_data['art_type']
                    )[0],
                    said_to_contain=article_data['said_to_contain'],
                    art_amount=article_data['art_amount']
                )
                logger.info(f"Created article: {article_data}")

            # Return success response with redirect URL
            return JsonResponse({
                'success': True,
                'message': f'CNotes created successfully with number: {cnote.cnote_number}',
                'redirect_url': reverse('dealer:cnote_success', kwargs={'cnote_number': cnote.cnote_number})
            })

        except Exception as e:
            logger.error(f"Error saving CNotes: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': f'Error creating CNotes: {str(e)}'
            })

    # GET request - render the form
    context = {
        'dealer': request.user.dealer,
        'destinations': DeliveryDestination.objects.all(),
        'cities': City.objects.all(),
        'last_cnote': last_cnote,  # Pass the last CNote to the template
        'dealer': dealer,
    }
    return render(request, 'dealer/create_cnotes.html', context)


@login_required
def search_cnote(request):
    cnote_number = request.GET.get('cnote_number')
    if cnote_number:
        try:
            cnote = get_object_or_404(CNotes, cnote_number=cnote_number)
            return render(request, 'dealer/view_cnote.html', {'cnote': cnote})
        except CNotes.DoesNotExist:
            messages.error(request, 'CNote not found.')
            return redirect('dealer:create_cnotes')  # Redirect back to the create CNotes page
    messages.error(request, 'Please enter a CNote number.')
    return redirect('dealer:create_cnotes')  # Redirect if no CNote number is provided





# Set up logging
logger = logging.getLogger(__name__)

@require_GET
def party_suggestions(request):
    try:
        query = request.GET.get('query', '').upper()
        logger.info(f"Received party suggestion query: {query}")
        
        if len(query) >= 2:
            parties = PartyMaster.objects.filter(
                Q(party_name__istartswith=query) |
                Q(party_code__istartswith=query) |
                Q(display_name__istartswith=query) |
                Q(mobile_number_1__istartswith=query) |
                Q(gst_no__istartswith=query)
            )[:10]
            
            if not parties.exists():
                logger.info(f"No parties found for query: {query}")
                return JsonResponse([], safe=False)
            
            data = [{
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
                'remark': party.remark
            } for party in parties]
            
            logger.info(f"Found {len(data)} matching parties")
            return JsonResponse(data, safe=False)
        
        return JsonResponse([], safe=False)
        
    except Exception as e:
        logger.exception(f"Error in party_suggestions: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_POST
def save_party(request):
    try:
        logger.info("Received request to save party.")
        data = json.loads(request.body)
        logger.info(f"Request data: {data}")
        
        party_name = data.get('party_name', '').strip().upper()
        
        if not party_name:
            return JsonResponse({
                'success': False, 
                'error': 'Party name is required'
            }, status=400)
        
        logger.info(f"Attempting to save/update party: {party_name}")
        
        # Generate a unique party code if not provided
        party_code = data.get('party_code', '').strip().upper()
        if not party_code:
            last_party = PartyMaster.objects.order_by('-party_code').first()
            if last_party and last_party.party_code.startswith('P'):
                last_number = int(last_party.party_code[1:])
                party_code = f"P{last_number + 1:04d}"
            else:
                party_code = "P0001"
        
        defaults = {
            'display_name': data.get('display_name', party_name).strip().upper(),
            'mobile_number_1': data.get('mobile_number_1', '').strip(),
            'mobile_number_2': data.get('mobile_number_2', '').strip(),
            'phone_number_1': data.get('phone_number_1', '').strip(),
            'phone_number_2': data.get('phone_number_2', '').strip(),
            'gst_no': data.get('gst_no', '').strip().upper(),
            'pan_no': data.get('pan_no', '').strip().upper(),
            'email': data.get('email', '').strip().lower(),
            'marketing_person': data.get('marketing_person', '').strip().upper(),
            'party_type': data.get('party_type', 'CUSTOMER').strip().upper(),
            'country': data.get('country', 'INDIA').strip().upper(),
            'state': data.get('state', '').strip().upper(),
            'city': data.get('city', '').strip().upper(),
            'pincode': data.get('pincode', '').strip(),
            'address': data.get('address', '').strip().```python
            .upper(),
            'is_tbb': data.get('is_tbb', False),
            'remark': data.get('remark', '').strip().upper()
        }
        
        try:
            party = PartyMaster.objects.get(party_code=party_code)
            for key, value in defaults.items():
                setattr(party, key, value)
            party.party_name = party_name
            party.save()
            created = False
        except PartyMaster.DoesNotExist:
            party = PartyMaster.objects.create(
                party_code=party_code,
                party_name=party_name,
                **defaults
            )
            created = True
        
        logger.info(f"Successfully {'created' if created else 'updated'} party: {party_name}")
        return JsonResponse({
            'success': True,
            'message': f"Party {'created' if created else 'updated'} successfully",
            'party_code': party.party_code
        })
        
    except json.JSONDecodeError:
        logger.error("Invalid JSON data received")
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
        
    except Exception as e:
        logger.exception(f"Error in save_party: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

def generate_unique_party_code():
    last_party = PartyMaster.objects.order_by('-party_code').first()
    if last_party:
        last_number = int(last_party.party_code[1:])
        new_number = last_number + 1
    else:
        new_number = 1
    return f"P{new_number:04d}"
