from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .views import fetch_transporters, custom_login_redirect, mf_print
from transporter_app.views import home as home
from django.conf import settings
from django.conf.urls.static import static
from .views import get_cities
from .views import fetch_cities
from transporter_app.views import home as home
from django.shortcuts import redirect
from .views import send_pickup_request
from .views import search_loading_sheets
from .views import view_cnote, search_cnote
from .views import export_excel_template
from .views import import_cnotes  # ✅ Correct import


app_name = 'dealer'  # Defines the namespace for this app

urlpatterns = [
    # Dealer-related URLs
    #path('create_cnote/', views.create_cnote, name='create_cnote'),
    path('create_cnotes/', views.create_cnotes, name='create_cnotes'),

    path('cnote_options/<int:cnote_id>/', views.cnote_options, name='cnote_options'),
    path('list_cnotes/', views.list_cnotes, name='list_cnotes'),
    path('booking_register/', views.booking_register_view, name='booking_register'),
    path('loading_sheet/', views.loading_sheet, name='loading_sheet'),  
    path('api/cnote-details/<str:cnote_number>/', views.get_cnote_details, name='get_cnote_details'),
    path('cnote/<int:cnote_id>/update-status/', views.update_cnote_status, name='update_cnote_status'),
    path('cnote-success/<str:cnote_number>/', views.cnote_success, name='cnote_success'),
    path('view_cnote/<str:cnote_number>/', views.view_cnote, name='view_cnote'),
    path('api/fetch_pending_cnotes/', views.fetch_pending_cnotes, name='fetch_pending_cnotes'),
    #path('fetch-transporters/', views.fetch_transporters, name='fetch_transporters'),
    path('api/fetch_transporters/', views.fetch_transporters, name='fetch_transporters'),
    path('search/', views.search, name='search'),  # Add this line
    path('search_cnote/', search_cnote, name='search_cnote'),  # Ensure this line is present

    #path('api/search_loading_sheets/', views.search_loading_sheet, name='search_loading_sheets'),
    #path('search-loading-sheet/', search_loading_sheet, name='search_loading_sheet'),
    #path('search-loading-sheets/', views.search_loading_sheets, name='search_loading_sheets'),
    path('api/search_loading_sheets/', views.search_loading_sheets, name='search_loading_sheets'),
    #path('mf_print/', views.mf_print, name='mf_print'),
    #path('mf_print/<str:ls_number>/', views.mf_print, name='mf_print'),
    path('dealer/mf_print/<int:loading_sheet_number>/', views.mf_print, name='mf_print'),
    path('mf_print/<str:loading_sheet_number>/', views.mf_print, name='mf_print'),

   
    #path('api/fetch_transporters/', views.fetch_transporters, name='fetch_transporters'),
    path('cnote/<int:cnote_id>/mark-received/', views.mark_cnote_received, name='mark_cnote_received'),
    path('cnote/<int:cnote_id>/create-delivery/', views.create_delivery, name='create_delivery'),
    path('delivery/<int:delivery_id>/update/', views.update_delivery, name='update_delivery'),
    path('cnote/<int:cnote_id>/cancel/', views.cancel_cnote, name='cancel_cnote'),
    path('get_cities/', get_cities, name='get_cities'),  # Add this line
    #path('fetch-cities/', fetch_cities, name='fetch_cities'),
    path('fetch_cities/', views.fetch_cities, name='fetch_cities'),


    
    #path('api/send_pickup_request/', views.send_pickup_request, name='send_pickup_request'),  # Added this line
    path('send-pickup-request/', views.send_pickup_request, name='send_pickup_request'),    
    #path('create-loading-sheet/', views.create_loading_sheet, name='loading_sheet'),
   #path('loading-sheet/<int:ls_number>/', views.loading_sheet_detail, name='loading_sheet_detail'),
    #path('cancel-loading-sheet/<int:ls_number>/', views.cancel_loading_sheet, name='cancel_loading_sheet'),
    #path('update-cnote-status/<int:cnote_id>/', views.update_cnote_status, name='update_cnote_status'),
    #path('loading-sheets/', views.loading_sheet_list, name='loading_sheet_list'),

    #path('create_loading_sheet/', views.create_loading_sheet, name='create_loading_sheet'),
    #path('create_loading_sheet/', views.create_loading_sheet, name='create_loading_sheet'),
    path('api/create_loading_sheet/', views.create_loading_sheet, name='create_loading_sheet'),

    #path('api/fetch_pending_cnotes/', views.fetch_pending_cnotes, name='fetch_pending_cnotes'),
    #path('api/fetch_transporters/', views.fetch_transporters, name='fetch_transporters'),
    #path('api/create_loading_sheet/', views.create_loading_sheet, name='create_loading_sheet'),

    path('api/party-suggestions/', views.party_suggestions, name='party_suggestions'),
    #path('api/save-party/', views.save_party, name='save_party'),





    # Transporter-related URLs
    path('transporter/view_pending_pickups/<int:transporter_id>/', views.view_pending_pickups, name='view_pending_pickups'),
    path('transporter/mark_pickup/<int:cnote_id>/', views.mark_pickup, name='mark_pickup'),

    # Authentication URLs
    path('login/', custom_login_redirect, name='login'),  # Point to custom login redirect view
    path('login_redirect/', custom_login_redirect, name='login_redirect'),  # Ensure only one login_redirect path
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # Admin-related URLs
    path('add_dealer/', views.add_dealer, name='add_dealer'),

    # PDF actions
    path('print_pdf/<int:cnote_id>/', views.print_pdf, name='print_pdf'),
    path('download_pdf/<int:cnote_id>/', views.download_pdf, name='download_pdf'),

    # CNote CRUD operations
    path('get_cnote/<int:cnote_id>/', views.get_cnote, name='get_cnote'),
    path('update_cnote/<int:cnote_id>/', views.update_cnote, name='update_cnote'),
    path('delete_cnote/<int:cnote_id>/', views.delete_cnote, name='delete_cnote'),

    # Transporter Dashboard
    #path('dashboard/', transporter_dashboard, name='transporter_dashboard'),  # Transporter dashboard view
    path('transporter/home/', home, name='home'),
    #path('api/get_pickup_requests/', views.get_pickup_requests, name='get_pickup_requests'),
    path('list/', views.transporter_list, name='transporter_list'),

    path('import-cnotes/', import_cnotes, name='import_cnotes'),
    path('export-excel/', export_excel_template, name='export_excel_template'),
    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
