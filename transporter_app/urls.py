from django.urls import path
from . import views
from django.views.generic import TemplateView
from .views import received_cnote_view
from .views import receive_cnotes




app_name = 'transporter'

print("Loading transporter_app URLs...")

urlpatterns = [
    path('home/', views.home, name='home'),
    path('manage-location/', views.manage_location, name='manage_location'),
    path('party-master/', views.party_master, name='party_master'),
    path('add-party/', views.add_party, name='add_party'),
    path('search-party/', views.search_party, name='search_party'),
    path('get-party/<int:party_id>/', views.get_party, name='get_party'),
    path('update-party/<int:party_id>/', views.update_party, name='update_party'),
    path('delete-party/<int:party_id>/', views.delete_party, name='delete_party'),
    path('save-config/', views.save_config, name='save_config'),
    path('api/get_pickup_requests/', views.get_pickup_requests, name='get_pickup_requests'),
    path('receive/', views.received_view, name='receive'),
    path('api/receivables/', views.fetch_receivables, name='fetch_receivables'),
    path('api/receive-shipment/', views.receive_shipment, name='receive_shipment'),
    path('api/dealers-with-loadingsheets/', views.get_dealers_with_loadingsheets, name='get_dealers_with_loadingsheets'),
    
    # Updated URL pattern to match the exact filename
    path('receive/RECEIVED_CNOTES.HTML', views.received_cnote_view, name='received_cnote'),

    path('api/receive-cnotes/', views.receive_cnotes, name='receive_cnotes'),
    path('receive/', views.receive_view, name='receive'),

    path('api/loading-sheet/<str:ls_number>/', views.get_loading_sheet_details, name='get_loading_sheet_details'),
    path('api/lr-details/<str:ls_number>/', views.get_lr_details, name='get_lr_details'),
    path('api/short-entry/', views.record_short_entry, name='record_short_entry'),
    path('api/damage-entry/', views.record_damage_entry, name='record_damage_entry'),
    path('api/excess-receive/', views.record_excess_receive, name='record_excess_receive'),
    path('api/receive-lrs/', views.receive_lrs, name='receive_lrs'),

    path('mf_print/<str:ls_number>/', views.mf_print_view, name='mf_print'),

    path('edit-state/<int:id>/', views.edit_state, name='edit_state'),
    path('delete-state/<int:id>/', views.delete_state, name='delete_state'),
    path('edit-city/<int:id>/', views.edit_city, name='edit_city'),
    path('delete-city/<int:id>/', views.delete_city, name='delete_city'),

    path('delivery-cnotes/', views.delivery_cnotes, name='delivery_cnotes'),
    path('api/search-cnote/', views.search_cnote, name='search_cnote'),
    path('ddm/', views.ddm_view, name='ddm'),
    path('api/get-destinations/', views.get_destinations, name='get_destinations'),
    path('api/search-cnotes-for-ddm/', views.search_cnotes_for_ddm, name='search_cnotes_for_ddm'),

    path('api/submit-delivery/', views.submit_delivery, name='submit_delivery'),
    path('api/create-delivery-memo/', views.create_delivery_memo, name='create_delivery_memo'),
    path('api/save-ddm-pdf/', views.save_ddm_pdf, name='save_ddm_pdf'),

    path('api/submit-delivery/', views.submit_delivery, name='submit_delivery'),
    path('api/get-ddm-details/<str:ddm_id>/', views.get_ddm_details, name='get_ddm_details'),
    path('api/save-ddm-pdf/<str:ddm_id>/', views.save_ddm_pdf, name='save_ddm_pdf'),
     
     # Add the new URL pattern for ddm-details.html
    #path('ddm-details/', TemplateView.as_view(template_name='transporter/ddm-details.html'), name='ddm_details'),

    path('ddm-details/', views.ddm_details_view, name='ddm_details'),
    path('ddm-settlement/', views.ddm_settlement, name='ddm_settlement'),
    path('api/update-ddm/', views.update_ddm, name='update_ddm'),
    path('api/ddm-details-for-update/', views.get_ddm_details_for_update, name='get_ddm_details_for_update'),

    
    path('cnotes-search/', views.cnotes_search, name='cnotes_search'),

    
]
