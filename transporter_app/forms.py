from django import forms
from .models import State, City
from .models import PartyMaster


class StateForm(forms.ModelForm):
    class Meta:
        model = State
        fields = ['name', 'capital', 'description']

class CityForm(forms.ModelForm):
    class Meta:
        model = City
        fields = ['name', 'state', 'description']


class PartyMasterForm(forms.ModelForm):
    class Meta:
        model = PartyMaster
        fields = ['party_name', 'display_name', 'is_tbb', 'mobile_number_1', 
                  'mobile_number_2', 'phone_number_1', 'phone_number_2', 'party_code', 
                  'gst_no', 'pan_no', 'email', 'marketing_person', 'party_type', 'country', 
                  'state', 'city', 'pincode', 'address', 'remark']