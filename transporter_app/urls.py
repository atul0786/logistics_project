from django.urls import path
from . import views
from django.views.generic import TemplateView
from .views import received_cnote_view
from .views import receive_cnotes

from django.urls import path
from . import views
from django.views.generic import TemplateView

app_name = 'transporter'

print("Loading transporter_app URLs...")

urlpatterns = [
    # Home and basic views
    path('home/', views.home, name='home'),
    path('manage-location/', views.manage_location, name='manage_location'),
    path("logout/", auth_views.LogoutView.as_view(next_page='/login/'), name="logout"),

    
    # Party management
    path('party-master/', views.party_master, name='party_master'),
    path('add-party/', views.add_party, name='add_party'),
    path('search-party/', views.search_party, name='search_party'),
    path('get-party/<int:party_id>/', views.get_party, name='get_party'),
    path('update-party/<int:party_id>/', views.update_party, name='update_party'),
    path('delete-party/<int:party_id>/', views.delete_party, name='delete_party'),
    path('edit-party/<int:party_id>/', views.edit_party, name='edit_party'),
    path('get-party-master-records/', views.get_party_master_records, name='get_party_master_records'),
    
    # Location management
    path('edit-state/<int:id>/', views.edit_state, name='edit_state'),
    path('delete-state/<int:id>/', views.delete_state, name='delete_state'),
    path('add-city/', views.add_city, name='add_city'),
    path('edit-city/<int:id>/', views.edit_city, name='edit_city'),
    path('delete-city/<int:id>/', views.delete_city, name='delete_city'),
    
    # Configuration
    path('save-config/', views.save_config, name='save_config'),
    
    # Pickup requests
    path('api/get_pickup_requests/', views.get_pickup_requests, name='get_pickup_requests'),
    
    # Receive functionality
    path('receive/', views.received_view, name='receive'),
    path('api/receivables/', views.fetch_receivables, name='fetch_receivables'),
    path('api/receive-shipment/', views.receive_shipment, name='receive_shipment'),
    path('api/dealers-with-loadingsheets/', views.get_dealers_with_loadingsheets, name='get_dealers_with_loadingsheets'),
    path('receive/RECEIVED_CNOTES.HTML', views.received_cnote_view, name='received_cnote'),
    path('api/receive-cnotes/', views.receive_cnotes, name='receive_cnotes'),
    
    # Loading sheet details
    path('api/loading-sheet/<str:ls_number>/', views.get_loading_sheet_details, name='get_loading_sheet_details'),
    path('api/lr-details/<str:ls_number>/', views.get_lr_details, name='get_lr_details'),
    path('api/short-entry/', views.record_short_entry, name='record_short_entry'),
    path('api/damage-entry/', views.record_damage_entry, name='record_damage_entry'),
    path('api/excess-receive/', views.record_excess_receive, name='record_excess_receive'),
    path('api/receive-lrs/', views.receive_lrs, name='receive_lrs'),
    
    # Print functionality
    path('mf_print/<str:ls_number>/', views.mf_print_view, name='mf_print'),
    
    # Delivery functionality
    path('delivery-cnotes/', views.delivery_cnotes, name='delivery_cnotes'),
    path('api/search-cnote/', views.search_cnote, name='search_cnote'),
    path('api/submit-delivery/', views.submit_delivery, name='submit_delivery'),
    
    # DDM (Door Delivery Memo) functionality
    path('ddm/', views.ddm_view, name='ddm'),
    path('api/get-destinations/', views.get_destinations, name='get_destinations'),
    path('api/search-cnotes-for-ddm/', views.search_cnotes_for_ddm, name='search_cnotes_for_ddm'),
    path('api/create-delivery-memo/', views.create_delivery_memo, name='create_delivery_memo'),
    path('api/save-ddm-pdf/', views.save_ddm_pdf, name='save_ddm_pdf'),
    path('api/get-ddm-details/<str:ddm_id>/', views.get_ddm_details, name='get_ddm_details'),
    path('api/save-ddm-pdf/<str:ddm_id>/', views.save_ddm_pdf, name='save_ddm_pdf'),
    path('ddm-details/', views.ddm_details_view, name='ddm_details'),
    
    # DDM settlement
    path('ddm-settlement/', views.ddm_settlement, name='ddm_settlement'),
    path('api/update-ddm/', views.update_ddm, name='update_ddm'),
    path('api/ddm-details-for-update/', views.get_ddm_details_for_update, name='get_ddm_details_for_update'),
    
    # CNotes search and management
    path('cnotes-search/', views.cnotes_search, name='cnotes_search'),
    path('api/cnotes/<str:cnote_number>/', views.cnote_detail, name='cnote_detail'),
    path('api/cnotes/<str:cnote_number>/update/', views.update_cnote, name='update_cnote'),
    
    # Booking register - FIXED URLS
    path('all-booking-register/', views.all_booking_register, name='all_booking_register'),
    path('booking-register/', views.booking_register_view, name='booking_register'),
    path('booking-register-data/', views.booking_register_data, name='booking_register_data'),
    path('booking_register_data/', views.booking_register_data, name='booking_register_data_alt'),  # Alternative URL
    path('download-excel/', views.download_excel, name='download_excel'),
    path('download_excel/', views.download_excel, name='download_excel_alt'),  # Alternative URL
    
    # User management
    path('add-user/', views.add_user, name='add_user'),
    path('export-dealers-template/', views.export_dealers_template, name='export_dealers_template'),
    path('import-dealers/', views.import_dealers, name='import_dealers'),
    path('view-users/', views.view_users, name='view_users'),
    path('fetch-users/', views.fetch_users, name='fetch_users'),
    path('reset-password/', views.reset_password, name='reset_password'),
    
    # Billing functionality
    path('billing/', views.billing, name='billing'),
    path('save-bill/', views.save_bill, name='save_bill'),
    path('bills/', views.bill_list, name='bill_list'),
    path('bill/<int:bill_id>/', views.bill_detail, name='bill_detail'),
    path('cancel-bill/<int:bill_id>/', views.cancel_bill, name='cancel_bill'),
    path('bill/<int:bill_id>/update/', views.update_bill, name='update_bill'),
    path('bill/<int:bill_id>/available-cnotes/', views.available_cnotes, name='available_cnotes'),
    path('bill/<int:bill_id>/add-cnote/', views.add_cnote_to_bill, name='add_cnote_to_bill'),
    path('bill/<int:bill_id>/remove-cnote/', views.remove_cnote_from_bill, name='remove_cnote_from_bill'),
    path('bill/<int:bill_id>/print/', views.bill_print, name='bill_print'),
    path('bill-manage/', views.bill_manage, name='bill_manage'),
    
    # API endpoints
    path('dealers/', views.dealer_list, name='dealer_list'),
    path('dashboard-summary/', views.dashboard_summary, name='dashboard_summary'),
]
