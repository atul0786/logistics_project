from django.contrib import admin
from .models import Transporter

from django.contrib import admin
from .models import State, City, PartyMaster
from .models import Pickup


@admin.register(Transporter)
class TransporterAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'company_name', 'contact_person', 'phone_number_1', 'email', 'city', 'profile_image','state')
    list_display_links = ('id', 'name')  # Allow clicking on both ID and name
    search_fields = ('id', 'name', 'company_name', 'email')
    list_filter = ('state', 'city')
    ordering = ('name',)
    list_per_page = 20

    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'name', 'company_name', 'contact_person')
        }),
        ('Contact Information', {
            'fields': ('phone_number_1', 'phone_number_2', 'mobile_number_1', 'mobile_number_2', 'email')
        }),
        ('Address Information', {
            'fields': ('address', 'state', 'city')
        }),
        ('Additional Information', {
            'fields': ('gstn', 'vehicle_number','profile_image')
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:  # If editing an existing object
            return ('transporter_id',) + self.readonly_fields
        return self.readonly_fields

    def save_model(self, request, obj, form, change):
        if not change:  # If this is a new object
            obj.user = request.user
        super().save_model(request, obj, form, change)


admin.site.register(State)
admin.site.register(City)
admin.site.register(PartyMaster)
admin.site.register(Pickup)
