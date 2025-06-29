from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.forms import inlineformset_factory
from .models import CNote, Dealer, DeliveryDestination, DeliveryType, ArtType, BookingType, Article
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Fieldset, ButtonHolder, Submit
from .models import CNotes, Article  # Make sure you're importing CNotes

# Login form for dealer users
class DealerLoginForm(AuthenticationForm):
    username = forms.CharField(max_length=30)
    password = forms.CharField(widget=forms.PasswordInput)

class CNoteForm(forms.ModelForm):
    class Meta:
        model = CNote
        fields = '__all__'


# Form for creating and editing CNotes
class CNoteForm(forms.ModelForm):
    PAYMENT_TYPE_CHOICES = [
        ('PAID', 'Paid'),
        ('TOPAY', 'To Pay'),
        ('TBB', 'TBB'),
        ('FOC', 'FOC'),
        ('MANUAL', 'Manual'),
    ]

    booking_type = forms.ModelChoiceField(
        queryset=BookingType.objects.all(), 
        empty_label="Select Booking Type"
    )   
    delivery_type = forms.ModelChoiceField(
        queryset=DeliveryType.objects.all(), 
        empty_label="Select Delivery Type"
    )
    delivery_method = forms.ChoiceField(
        choices=[('door', 'Door Delivery'), ('godown', 'Godown Delivery')],
        initial='door'
    )
    delivery_destination = forms.ModelChoiceField(
        queryset=DeliveryDestination.objects.all(),
        empty_label="Select Delivery Destination"
    )
    payment_type = forms.ChoiceField(choices=PAYMENT_TYPE_CHOICES, required=True)
    manual_cnote_type = forms.ChoiceField(choices=PAYMENT_TYPE_CHOICES[:4], required=False)
    manual_cnote_number = forms.CharField(max_length=50, required=False)
    manual_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = CNote
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'id-cnoteForm'
        self.helper.form_method = 'post'
        self.helper.form_action = 'submit_cnote'
        self.helper.layout = Layout(
            Fieldset(
                'Booking Details',
                Field('booking_type', css_class='form-control'),
                Field('delivery_type', css_class='form-control'),
                Field('delivery_method', css_class='form-control'),
                Field('delivery_destination', css_class='form-control'),
                Field('eway_bill_number', css_class='form-control'),
                Field('payment_type', css_class='form-control'),
            ),
            Fieldset(
                'Manual Entry Details',
                Field('manual_cnote_type', css_class='form-control'),
                Field('manual_cnote_number', css_class='form-control'),
                Field('manual_date', css_class='form-control'),
                css_id='manual-entry-fields',
                css_class='hidden',
            ),
            Fieldset(
                'Consignor Details',
                Field('consignor_name', css_class='form-control'),
                Field('consignor_mobile', css_class='form-control'),
                Field('consignor_gst', css_class='form-control'),
                Field('consignor_address', css_class='form-control small-input'),
            ),
            Fieldset(
                'Consignee Details',
                Field('consignee_name', css_class='form-control'),
                Field('consignee_mobile', css_class='form-control'),
                Field('consignee_gst', css_class='form-control'),
                Field('consignee_address', css_class='form-control'),
            ),
            Fieldset(
                'Shipment Details',
                Field('actual_weight', css_class='form-control'),
                Field('charged_weight', css_class='form-control'),
                Field('weight_rate', css_class='form-control'),
                Field('weight_amount', css_class='form-control'),
                Field('fix_amount', css_class='form-control'),
                Field('invoice_number', css_class='form-control'),
                Field('declared_value', css_class='form-control'),
                Field('risk_type', css_class='form-control'),
                Field('pod_required', css_class='form-control'),
            ),
            Fieldset(
                'Charges',
                Field('freight', css_class='form-control'),
                Field('docket_charge', css_class='form-control'),
                Field('door_delivery_charge', css_class='form-control'),
                Field('handling_charge', css_class='form-control'),
                Field('pickup_charge', css_class='form-control'),
                Field('transhipment_charge', css_class='form-control'),
                Field('insurance', css_class='form-control'),
                Field('fuel_surcharge', css_class='form-control'),
                Field('commission', css_class='form-control'),
                Field('other_charge', css_class='form-control'),
                Field('carrier_risk', css_class='form-control'),
                Field('grand_total', css_class='form-control'),
            ),
            ButtonHolder(
                Submit('submit', 'Submit', css_class='btn btn-primary')
            )
        )

    def clean(self):
        cleaned_data = super().clean()
        payment_type = cleaned_data.get('payment_type')
        manual_cnote_type = cleaned_data.get('manual_cnote_type')
        manual_cnote_number = cleaned_data.get('manual_cnote_number')
        manual_date = cleaned_data.get('manual_date')

        if payment_type == 'MANUAL':
            if not manual_cnote_type:
                self.add_error('manual_cnote_type', 'This field is required for manual entries.')
            if not manual_cnote_number:
                self.add_error('manual_cnote_number', 'This field is required for manual entries.')
            if not manual_date:
                self.add_error('manual_date', 'This field is required for manual entries.')
        return cleaned_data

class ArticleForm(forms.ModelForm):
    art_type = forms.ModelChoiceField(
        queryset=ArtType.objects.all(), 
        empty_label="Select Art Type"
    )
    class Meta:
        model = Article
        fields = ['article_type', 'art', 'art_type', 'said_to_contain', 'art_amount']

ArticleFormSet = inlineformset_factory(
    CNotes, Article, form=ArticleForm,
    extra=1, can_delete=True, can_delete_extra=True
)

class DealerForm(forms.ModelForm):
    class Meta:
        model = Dealer
        fields = [
            'name', 'company_name', 'contact_person', 'phone_number_1', 'phone_number_2', 
            'mobile_number_1', 'mobile_number_2', 'email', 'gstn', 'address', 
            'state', 'city', 'branch_service_type', 'location_type', 'pan_no', 'photo'
        ]

        widgets = {
            'city': forms.Select(attrs={'class': 'form-control'}),
            'state': forms.Select(attrs={'class': 'form-control'}),
            'branch_service_type': forms.Select(attrs={'class': 'form-control'}),
            'location_type': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['state'].queryset = DeliveryDestination.objects.all()
        self.fields['city'].queryset = DeliveryDestination.objects.all()
        self.fields['branch_service_type'].queryset = DeliveryType.objects.all()
        self.fields['location_type'].queryset = DeliveryType.objects.all()

# Set the template pack for crispy forms (e.g., bootstrap4)
CRISPY_TEMPLATE_PACK = 'bootstrap4'



from django import forms

class QRPrinterSelectionForm(forms.Form):
    printer_name = forms.ChoiceField(label="Select QR Printer", choices=[])

    def __init__(self, *args, **kwargs):
        printers = kwargs.pop('printers', [])
        super().__init__(*args, **kwargs)

        # ✅ Add "No QR Printer" at the top
        printers.insert(0, "❌ No QR Printer (Use A4 Sheet)")

        self.fields['printer_name'].choices = [(p, p) for p in printers]
