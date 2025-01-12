from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    CustomUser, Dealer, CNote, BookingType, DeliveryType, 
    DeliveryDestination, ArtType, Article, LoadingSheetSummary, LoadingSheetDetail
)
from transporter_app.models import Transporter

class CustomUserAdmin(UserAdmin):
    model = CustomUser    
    list_display = ('username', 'email', 'dealer_name', 'is_dealer', 'is_transporter', 'is_staff')
    search_fields = ('username', 'email', 'dealer_name')
    list_filter = ('is_dealer', 'is_transporter', 'is_staff', 'is_active')
    ordering = ('username',)
    list_per_page = 20

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'dealer_name')}),
        ('Permissions', {'fields': ('is_dealer', 'is_transporter', 'is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}), 
        ('Important dates', {'fields': ('last_login', 'date_joined')}), 
    )

@admin.register(Dealer)
class DealerAdmin(admin.ModelAdmin):
    list_display = ('dealer_id', 'dealer_code', 'user', 'name', 'company_name', 'email', 'phone_number_1', 'state', 'city', 'branch_service_type', 'created_at', 'get_transporter_name')
    search_fields = ('dealer_id', 'dealer_code', 'name', 'company_name', 'email')
    list_filter = ('state', 'city', 'branch_service_type', 'created_at')
    ordering = ('name',)
    list_per_page = 20

    def get_transporter_name(self, obj):
        return obj.transporter.name if obj.transporter else '-'
    get_transporter_name.short_description = 'Transporter'

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "transporter":
            kwargs["queryset"] = Transporter.objects.all().order_by('name')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if 'transporter' in form.cleaned_data:
            if form.cleaned_data['transporter'] is None:
                obj.transporter = None
        super().save_model(request, obj, form, change)

class CNotesForm(forms.ModelForm):
    class Meta:
        model = CNote
        fields = [
            'dealer', 'booking_type', 'delivery_type', 'delivery_method', 'delivery_destination',
            'eway_bill_number', 'consignor_name', 'consignor_mobile', 'consignor_gst', 'consignor_address',
            'consignee_name', 'consignee_mobile', 'consignee_gst', 'consignee_address',
            'actual_weight', 'charged_weight', 'weight_rate', 'weight_amount', 'fix_amount',
            'invoice_number', 'declared_value', 'risk_type', 'pod_required',
            'freight', 'docket_charge', 'door_delivery_charge', 'handling_charge',
            'pickup_charge', 'transhipment_charge', 'insurance', 'fuel_surcharge',
            'commission', 'other_charge', 'carrier_risk', 'grand_total',
            'payment_type', 'manual_date', 'manual_cnote_number', 'manual_cnote_type',
            'total_art', 'status'
        ]
        widgets = {
            'consignor_address': forms.Textarea(attrs={'rows': 3, 'cols': 40}),
            'consignee_address': forms.Textarea(attrs={'rows': 3, 'cols': 40}),
        }

@admin.register(CNote)
class CNotesAdmin(admin.ModelAdmin):
    form = CNoteForm
    list_display = ('id', 'cnote_number', 'dealer', 'booking_type', 'delivery_type', 'consignor_name', 'consignee_name', 'payment_type', 'status', 'created_at')
    search_fields = ('cnote_number', 'dealer__name', 'consignor_name', 'consignee_name')
    list_filter = ('created_at', 'booking_type', 'delivery_type', 'payment_type', 'status')
    ordering = ('-created_at',)
    list_per_page = 20
    

    fieldsets = (
        ('Basic Information', {
            'fields': ('dealer', 'booking_type', 'delivery_type', 'delivery_method', 'delivery_destination', 'eway_bill_number', 'status')
        }),
        ('Consignor Information', {
            'fields': ('consignor_name', 'consignor_mobile', 'consignor_gst', 'consignor_address')
        }),
        ('Consignee Information', {
            'fields': ('consignee_name', 'consignee_mobile', 'consignee_gst', 'consignee_address')
        }),
        ('Weight and Amount', {
            'fields': ('actual_weight', 'charged_weight', 'weight_rate', 'weight_amount', 'fix_amount', 'total_art')
        }),
        ('Invoice and Value', {
            'fields': ('invoice_number', 'declared_value', 'risk_type', 'pod_required')
        }),
        ('Charges', {
            'fields': ('freight', 'docket_charge', 'door_delivery_charge', 'handling_charge',
                       'pickup_charge', 'transhipment_charge', 'insurance', 'fuel_surcharge',
                       'commission', 'other_charge', 'carrier_risk', 'grand_total')
        }),
        ('Payment Information', {
            'fields': ('payment_type', 'manual_date', 'manual_cnote_number', 'manual_cnote_type')
        }),
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['delivery_destination'].queryset = DeliveryDestination.objects.all()
        return form

class ArticleInline(admin.TabularInline):
    model = Article
    extra = 1

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('cnote', 'article_type', 'art', 'art_type', 'said_to_contain', 'art_amount')
    search_fields = ('cnote__cnote_number', 'article_type', 'said_to_contain')
    list_filter = ('article_type', 'art_type')
    list_per_page = 20

@admin.register(BookingType)
class BookingTypeAdmin(admin.ModelAdmin):
    list_display = ('type_name',)
    search_fields = ('type_name',)
    list_per_page = 20

@admin.register(DeliveryType)
class DeliveryTypeAdmin(admin.ModelAdmin):
    list_display = ('type_name',)
    search_fields = ('type_name',)
    list_per_page = 20

@admin.register(DeliveryDestination)
class DeliveryDestinationAdmin(admin.ModelAdmin):
    list_display = ('destination_name', 'address')
    search_fields = ('destination_name', 'address')
    list_per_page = 20

@admin.register(ArtType)
class ArtTypeAdmin(admin.ModelAdmin):
    list_display = ('art_type_name',)
    search_fields = ('art_type_name',)
    list_per_page = 20

@admin.register(LoadingSheetSummary)
class LoadingSheetSummaryAdmin(admin.ModelAdmin):
    list_display = ('ls_number', 'transporter', 'total_cnote', 'total_art', 'total_paid_amount', 'total_topay_amount', 'total_tbb_amount', 'total_foc_amount', 'status', 'created_at')
    search_fields = ('ls_number', 'transporter__name')
    list_filter = ('status', 'created_at')
    ordering = ('-created_at',)
    list_per_page = 20
    actions = ['cancel_loading_sheet']

    def cancel_loading_sheet(self, request, queryset):
        for loading_sheet in queryset:
            # Get all CNotes associated with this loading sheet
            cnotes = CNote.objects.filter(loading_sheet_details__loading_sheet=loading_sheet)
            
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

        self.message_user(request, f"{queryset.count()} loading sheet(s) have been cancelled.")

    cancel_loading_sheet.short_description = "Cancel selected loading sheets"







@admin.register(LoadingSheetDetail)
class LoadingSheetDetailAdmin(admin.ModelAdmin):
    list_display = ('loading_sheet', 'cnote', 'consignor_name', 'consignee_name', 'destination', 'art', 'payment_type', 'amount', 'status')
    search_fields = ('loading_sheet__ls_number', 'cnote__cnote_number', 'consignor_name', 'consignee_name')
    list_filter = ('status', 'payment_type')
    ordering = ('loading_sheet', 'cnote')
    list_per_page = 20

admin.site.register(CustomUser, CustomUserAdmin)
