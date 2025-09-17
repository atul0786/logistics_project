from django.urls import path
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from . import views
from .views import (
    fetch_transporters, custom_login_redirect, get_consignee_data, mf_print,
    get_cities, fetch_cities, send_pickup_request, search_loading_sheets,
    export_excel_template, import_cnotes, view_cnote, search_cnote,
    check_loading_sheet
)
from transporter_app.views import home
from django.shortcuts import redirect

app_name = 'dealer'  # Defines the namespace for this app

urlpatterns = [
    # Dealer-related URLs
    path('create_cnotes/', views.create_cnotes, name='create_cnotes'),
    path('cnote_options/<int:cnote_id>/', views.cnote_options, name='cnote_options'),
    path('list_cnotes/', views.list_cnotes, name='list_cnotes'),
    path('booking_register/', views.booking_register_view, name='booking_register'),
    path('loading_sheet/', views.loading_sheet, name='loading_sheet'),
    path('api/cnote-details/<str:cnote_number>/', views.get_cnote_details, name='get_cnote_details'),
    path('cnote/<int:cnote_id>/update-status/', views.update_cnote_status, name='update_cnote_status'),
    path('cnote-success/<str:cnote_number>/', views.cnote_success, name='cnote_success'),
    path('view-cnote/<str:cnote_number>/', views.view_cnote, name='view_cnote'),
    # path('view-cnote/<str:cnote_number>/', views.view_cnote, name='view_cnote'),  # Duplicate path
    path('api/fetch_pending_cnotes/', views.fetch_pending_cnotes, name='fetch_pending_cnotes'),
    path('api/fetch_transporters/', views.fetch_transporters, name='fetch_transporters'),
    # path('fetch-transporters/', views.fetch_transporters, name='fetch_transporters'),  # Duplicate or conflicting path
    # path('api/fetch_transporters/', views.fetch_transporters, name='fetch_transporters'),  # Duplicate path
    path('search/', views.search, name='search'),
    path('search_cnote/', views.search_cnote, name='search_cnote'),
    # path('search_cnote/', views.search_cnote, name='search_cnote'),  # Duplicate path
    path('api/search_loading_sheets/', views.search_loading_sheets, name='search_loading_sheets'),
    # path('search-loading-sheets/', views.search_loading_sheets, name='search_loading_sheets'),  # Duplicate or conflicting path
    # path('api/search_loading_sheets/', views.search_loading_sheets, name='search_loading_sheets'),  # Duplicate path
    path('mf_print/<int:loading_sheet_number>/', views.mf_print, name='mf_print'),
    # path('mf_print/', views.mf_print, name='mf_print'),  # Duplicate or conflicting path
    # path('mf_print/<str:ls_number>/', views.mf_print, name='mf_print'),  # Duplicate or conflicting path
    path('download_excel/', views.download_excel, name='download_excel'),
    path('cnote/<int:cnote_id>/mark-received/', views.mark_cnote_received, name='mark_cnote_received'),
    path('cnote/<int:cnote_id>/create-delivery/', views.create_delivery, name='create_delivery'),
    path('delivery/<int:delivery_id>/update/', views.update_delivery, name='update_delivery'),
    path('cnote/<int:cnote_id>/cancel/', views.cancel_cnote, name='cancel_cnote'),
    path('get_cities/', views.get_cities, name='get_cities'),
    path('fetch_cities/', views.fetch_cities, name='fetch_cities'),
    # path('fetch_cities/', views.fetch_cities, name='fetch_cities'),  # Duplicate path
    path('send-pickup-request/', views.send_pickup_request, name='send_pickup_request'),
    # path('api/send_pickup_request/', views.send_pickup_request, name='send_pickup_request'),  # Duplicate or conflicting path
    path('api/create_loading_sheet/', views.create_loading_sheet, name='create_loading_sheet'),
    # path('create_loading_sheet/', views.create_loading_sheet, name='create_loading_sheet'),  # Duplicate or conflicting path
    path('api/party-suggestions/', views.party_suggestions, name='party_suggestions'),
    path('import-cnotes/', views.import_cnotes, name='import_cnotes'),
    path('export-excel/', views.export_excel_template, name='export_excel_template'),
    path('get_consignee_data/', views.get_consignee_data, name='get_consignee_data'),
    path('check-loading-sheet/', views.check_loading_sheet, name='check_loading_sheet'),
    path('update_freight/', views.update_freight, name='update_freight'),
    # path('update_freight/', views.update_freight, name='update_freight'),  # Duplicate path
    path('save_cnote/', views.save_cnote, name='save_cnote'),
    # path('save_cnote/', views.save_cnote, name='save_cnote'),  # Duplicate path

    # Transporter-related URLs
    path('transporter/view_pending_pickups/<int:transporter_id>/', views.view_pending_pickups, name='view_pending_pickups'),
    path('transporter/mark_pickup/<int:cnote_id>/', views.mark_pickup, name='mark_pickup'),
    path('transporter/home/', home, name='home'),
    path('list/', views.transporter_list, name='transporter_list'),

    # Authentication URLs
    path('login/', views.custom_login_redirect, name='login'),
    path('login_redirect/', views.custom_login_redirect, name='login_redirect'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # Admin-related URLs
    path('add_dealer/', views.add_dealer, name='add_dealer'),

    # PDF Actions
    path('print_pdf/<int:cnote_id>/', views.print_pdf, name='print_pdf'),
    path('download_pdf/<int:cnote_id>/', views.download_pdf, name='download_pdf'),

    # CNote CRUD Operations
    path('get_cnote/<int:cnote_id>/', views.get_cnote, name='get_cnote'),
    path('update_cnote/<int:cnote_id>/', views.update_cnote, name='update_cnote'),
    path('delete_cnote/<int:cnote_id>/', views.delete_cnote, name='delete_cnote'),

    path('print_with_qr/<str:cnote_number>/', views.print_with_qr, name='print_with_qr'),
    
    path('qr-printer-setting/', views.select_qr_printer, name='select_qr_printer'),
    path('api/save_printers/', views.save_printer_data, name='save_printer_data'),

    path('export-loading-sheet/<int:ls_number>/', views.export_loading_sheet_excel, name='export_loading_sheet_excel'),



]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
