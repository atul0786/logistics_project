from django.db import models
from django.contrib.auth.models import AbstractUser 
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import IntegrityError
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.apps import apps
from django.db.models.signals import pre_delete
from django.utils import timezone

class QRPrinterSetting(models.Model):
    dealer = models.OneToOneField('Dealer', on_delete=models.CASCADE)  # ✅ use string 'Dealer'
    printer_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)


# City and State Choices
CITY_CHOICES = [
    ('MUMBAI', 'Mumbai'),
    ('DELHI', 'Delhi'),
    ('BANGALORE', 'Bangalore'),
    ('CHENNAI', 'Chennai'),
    ('KOLKATA', 'Kolkata'),
    ('HYDERABAD', 'Hyderabad'),
    ('PUNE', 'Pune'),
    ('AHMEDABAD', 'Ahmedabad'),
    ('YAVATMAL', 'Yavatmal'),
]

STATE_CHOICES = [
    ('MAHARASHTRA', 'Maharashtra'),
    ('DELHI', 'Delhi'),
    ('KARNATAKA', 'Karnataka'),
    ('TAMIL_NADU', 'Tamil Nadu'),
    ('WEST_BENGAL', 'West Bengal'),
    ('TELANGANA', 'Telangana'),
    ('GUJARAT', 'Gujarat'),
]

class CustomUser(AbstractUser):
    is_dealer = models.BooleanField(default=False)
    is_transporter = models.BooleanField(default=False)
    dealer_name = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.username

class Dealer(models.Model):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE, null=True)
    dealer_id = models.AutoField(primary_key=True)
    dealer_code = models.CharField(max_length=4, unique=True, default="4 DIGIT CODE")
    name = models.CharField(max_length=100)
    company_name = models.CharField(max_length=100, default="Unknown Company")
    contact_person = models.CharField(max_length=100, default="Unknown Contact Person")
    phone_number_1 = models.CharField(max_length=15)
    phone_number_2 = models.CharField(max_length=15, null=True, blank=True)
    mobile_number_1 = models.CharField(max_length=15)
    mobile_number_2 = models.CharField(max_length=15, null=True, blank=True)
    email = models.EmailField(max_length=254, unique=True)
    gstn = models.CharField(max_length=15, null=True, blank=True)
    address = models.TextField(default="Address not provided")
    state = models.CharField(max_length=100, choices=STATE_CHOICES, default='MAHARASHTRA')
    city = models.CharField(max_length=100, choices=CITY_CHOICES, default='MUMBAI')
    branch_service_type = models.CharField(max_length=100, default='--SELECT--')
    location_type = models.CharField(max_length=100)
    pan_no = models.CharField(max_length=10, null=True, blank=True)
    photo = models.ImageField(upload_to='dealer_photos/', null=True, blank=True)
    is_agent_branch = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    #transporter = models.ForeignKey(Transporter, on_delete=models.SET_NULL, null=True, blank=True, related_name='dealers')
    transporter = models.ForeignKey('transporter_app.Transporter', on_delete=models.SET_NULL, null=True, blank=True, related_name='dealers')
    def __str__(self):
        return f"{self.name} ({self.company_name})"

    def save(self, *args, **kwargs):
        self.name = self.name.upper()
        self.city = self.city.upper()
        self.state = self.state.upper()
        super().save(*args, **kwargs)

class DeliveryDestination(models.Model):
    destination_name = models.CharField(max_length=100)
    address = models.TextField()

    def __str__(self):
        return self.destination_name

class DeliveryType(models.Model):
    type_name = models.CharField(max_length=100)

    def __str__(self):
        return self.type_name

class DeliveryMethod(models.Model):
    type_name = models.CharField(max_length=100)

    def __str__(self):
        return self.type_name

class ArtType(models.Model):
    art_type_name = models.CharField(max_length=100)

    def __str__(self):
        return self.art_type_name

class BookingType(models.Model):
    type_name = models.CharField(max_length=100)

    def __str__(self):
        return self.type_name

class CNote(models.Model):
    STATUS_CHOICES = [
        ('booked', 'Booked'),
        ('dispatched', 'Dispatched'),
        ('received', 'Received'),
        ('due_for_delivery', 'Due for Delivery'),
        ('delivered', 'Delivered'),
        ('received_at_godown', 'Received at Godown'),
        ('cancelled', 'Cancelled'),
    ]

    dealer = models.ForeignKey(Dealer, on_delete=models.CASCADE, null=True)
    cnote_number = models.CharField(max_length=100, unique=True, editable=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    booking_type = models.CharField(max_length=50, choices=[('sundry', 'Sundry'), ('other', 'Other')], default='sundry')
    delivery_type = models.CharField(max_length=50, choices=[('economy', 'Economy'), ('express', 'Express')], default='economy')
    delivery_method = models.CharField(max_length=50)
    delivery_destination = models.ForeignKey(DeliveryDestination, on_delete=models.SET_NULL, null=True)
    eway_bill_number = models.CharField(max_length=50, blank=True, null=True)
    manual_date = models.DateField(null=True, blank=True)
    manual_cnote_number = models.CharField(max_length=50, blank=True, null=True)
    manual_cnote_type = models.CharField(max_length=50, blank=True, null=True)
    payment_type = models.CharField(max_length=50, blank=True, null=True)
    consignor_name = models.CharField(max_length=100)
    consignor_mobile = models.CharField(max_length=15)
    consignor_gst = models.CharField(max_length=15, blank=True, null=True)
    consignor_address = models.TextField(blank=True, null=True)
    consignee_name = models.CharField(max_length=100)
    consignee_mobile = models.CharField(max_length=15)
    consignee_gst = models.CharField(max_length=15, blank=True, null=True)
    consignee_address = models.TextField(blank=True, null=True)
    actual_weight = models.DecimalField(max_digits=10, decimal_places=2)
    charged_weight = models.DecimalField(max_digits=10, decimal_places=2)
    weight_rate = models.DecimalField(max_digits=10, decimal_places=2)
    weight_amount = models.DecimalField(max_digits=10, decimal_places=2)
    fix_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    invoice_number = models.CharField(max_length=255, null=True, blank=True)
    declared_value = models.DecimalField(max_digits=15, decimal_places=2)
    risk_type = models.CharField(max_length=50, choices=[('owner', 'Owner'), ('carrier', 'Carrier')])
    pod_required = models.CharField(max_length=3, choices=[('yes', 'Yes'), ('no', 'No')])
    freight = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    docket_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    door_delivery_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    handling_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pickup_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    transhipment_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    insurance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fuel_surcharge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    commission = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    carrier_risk = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='booked')
    status_updated_at = models.DateTimeField(auto_now=True)
    total_art = models.IntegerField(default=0)

    def __str__(self):
        return f"CNote {self.cnote_number} - {self.dealer.dealer_code}"

    def save(self, *args, **kwargs):
        if not self.cnote_number:
            try:
                last_cnote = CNote.objects.filter(dealer=self.dealer).order_by('-id').first()
                if last_cnote:
                    last_number_part = last_cnote.cnote_number.split('-')[-1]
                    new_cnote_number = int(last_number_part) + 1
                else:
                    new_cnote_number = 1
            except (ValueError, IndexError):
                new_cnote_number = 1

            self.cnote_number = f"{self.dealer.dealer_code}-{new_cnote_number:04d}"

        try:
            super().save(*args, **kwargs)
        except IntegrityError:
            self.cnote_number = None
            self.save(*args, **kwargs)
            raise IntegrityError("Could not save CNote due to integrity error.")

    def update_status(self, new_status):
        if new_status in dict(self.STATUS_CHOICES):
            self.status = new_status
            self.status_updated_at = timezone.now()
            self.save()
        else:
            raise ValueError(f"Invalid status: {new_status}")

class CNotes(models.Model):
    STATUS_CHOICES = [
        ('booked', 'Booked'),
        ('dispatched', 'Dispatched'),
        ('received', 'Received'),
        ('due_for_delivery', 'Due for Delivery'),
        ('delivered', 'Delivered'),
        ('received_at_godown', 'Received at Godown'),
        ('cancelled', 'Cancelled'),
    ]

    BOOKING_TYPE_CHOICES = [('sundry', 'Sundry'), ('other', 'Other')]
    DELIVERY_TYPE_CHOICES = [('economy', 'Economy'), ('express', 'Express')]
    RISK_TYPE_CHOICES = [('owner', 'Owner'), ('carrier', 'Carrier')]
    POD_REQUIRED_CHOICES = [('yes', 'Yes'), ('no', 'No')]

    dealer = models.ForeignKey('Dealer', on_delete=models.CASCADE, null=True)
    cnote_number = models.CharField(max_length=100, unique=True, editable=False, db_index=True)
    created_at = models.DateTimeField(default=timezone.now)
    booking_type = models.CharField(max_length=50, choices=BOOKING_TYPE_CHOICES, default='sundry')
    delivery_type = models.CharField(max_length=50, choices=DELIVERY_TYPE_CHOICES, default='economy')
    delivery_method = models.CharField(max_length=50)
    delivery_destination = models.ForeignKey('DeliveryDestination', on_delete=models.SET_NULL, null=True)
    eway_bill_number = models.CharField(max_length=50, blank=True, null=True)
    manual_date = models.DateField(null=True, blank=True)
    manual_cnote_number = models.CharField(max_length=50, blank=True, null=True)
    manual_cnote_type = models.CharField(max_length=50, blank=True, null=True)
    payment_type = models.CharField(max_length=50, blank=True, null=True)
    consignor_name = models.CharField(max_length=100)
    consignor_mobile = models.CharField(max_length=15)
    consignor_gst = models.CharField(max_length=15, blank=True, null=True)
    consignor_address = models.TextField(blank=True, null=True)
    consignee_name = models.CharField(max_length=100)
    consignee_mobile = models.CharField(max_length=15)
    consignee_gst = models.CharField(max_length=15, blank=True, null=True)
    consignee_address = models.TextField(blank=True, null=True)
    actual_weight = models.DecimalField(max_digits=10, decimal_places=2)
    charged_weight = models.DecimalField(max_digits=10, decimal_places=2)
    weight_rate = models.DecimalField(max_digits=10, decimal_places=2)
    weight_amount = models.DecimalField(max_digits=10, decimal_places=2)
    fix_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    invoice_number = models.CharField(max_length=255, null=True, blank=True)
    declared_value = models.DecimalField(max_digits=15, decimal_places=2)
    risk_type = models.CharField(max_length=50, choices=RISK_TYPE_CHOICES)
    pod_required = models.CharField(max_length=3, choices=POD_REQUIRED_CHOICES)
    freight = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    docket_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    door_delivery_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    handling_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pickup_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    transhipment_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    insurance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fuel_surcharge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    commission = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    carrier_risk = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='booked')
    status_updated_at = models.DateTimeField(auto_now=True)
    total_art = models.IntegerField(default=0)

    def __str__(self):
        return f"CNote {self.cnote_number} - {self.dealer.dealer_code}"

    def save(self, *args, **kwargs):
        if not self.cnote_number:
            try:
                last_cnote = CNotes.objects.filter(dealer=self.dealer).order_by('-id').first()
                if last_cnote:
                    last_number_part = last_cnote.cnote_number.split('-')[-1]
                    new_cnote_number = int(last_number_part) + 1
                else:
                    new_cnote_number = 1
            except (ValueError, IndexError):
                new_cnote_number = 1

            self.cnote_number = f"{self.dealer.dealer_code}-{new_cnote_number:04d}"

        try:
            super().save(*args, **kwargs)
        except IntegrityError:
            self.cnote_number = None
            self.save(*args, **kwargs)
            raise IntegrityError("Could not save CNotes due to integrity error.")

    def update_status(self, new_status):
        if new_status in dict(self.STATUS_CHOICES):
            self.status = new_status
            self.status_updated_at = timezone.now()
            self.save()
        else:
            raise ValueError(f"Invalid status: {new_status}")

class Parcel(models.Model):
    cnote = models.ForeignKey('CNotes', on_delete=models.CASCADE)    
    parcel_number = models.IntegerField()
    qr_code_id = models.CharField(max_length=100, unique=True)
    receiver_name = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    from_city = models.CharField(max_length=100)
    
    def __str__(self):
        return self.qr_code_id


class Article(models.Model):
    cnote = models.ForeignKey(CNotes, on_delete=models.CASCADE, related_name='articles')
    article_type = models.CharField(max_length=50)
    art = models.IntegerField(null=True, blank=True)
    art_type = models.ForeignKey('ArtType', on_delete=models.SET_NULL, null=True)
    said_to_contain = models.CharField(max_length=100)
    art_amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Article {self.article_type} for CNotes {self.cnote.cnote_number}"

class Delivery(models.Model):
    cnote = models.ForeignKey(CNote, on_delete=models.CASCADE, null=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    is_successful = models.BooleanField(default=False)

class Branch(models.Model):
    branch_name = models.CharField(max_length=255)
    delivery_destination = models.ForeignKey(DeliveryDestination, on_delete=models.CASCADE)

    def __str__(self):
        return self.branch_name

class LoadingSheetSummary(models.Model):
    LOADING_SHEET_STATUS_CHOICES = [
        ('dispatched', 'Dispatched'),
        ('received', 'Received'),
        ('cancelled', 'Cancelled'),
    ]

    ls_number = models.AutoField(primary_key=True)  # Unique loading sheet number
    dealer = models.ForeignKey(Dealer, on_delete=models.CASCADE)  # Foreign key to Dealer
    #transporter = models.ForeignKey(Transporter, on_delete=models.CASCADE)  # Foreign key to Transporter
    transporter = models.ForeignKey('transporter_app.Transporter', on_delete=models.CASCADE)
    total_cnote = models.IntegerField(default=0)
    total_art = models.IntegerField(default=0)
    total_paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_topay_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_tbb_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_foc_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_manual_paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_manual_topay_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_manual_tbb_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_manual_foc_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=LOADING_SHEET_STATUS_CHOICES, default='dispatched')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Loading Sheet {self.ls_number} - Dealer: {self.dealer.name}, Transporter: {self.transporter.company_name}"
    

    def cancel(self):
        from .models import CNote, LoadingSheetDetail  # Import here to avoid circular import
        
        # Update all associated CNotes
        cnotes = CNote.objects.filter(loading_sheet_details__loading_sheet=self)
        for cnote in cnotes:
            if cnote.status == 'dispatched':
                cnote.status = 'booked'
                cnote.save()
        
        # Update loading sheet status
        self.status = 'cancelled'
        self.save()
        
        # Delete associated LoadingSheetDetails
        LoadingSheetDetail.objects.filter(loading_sheet=self).delete()

    def update_status(self):
        total_cnotes = self.loadingsheetdetail_set.count()
        received_cnotes = self.loadingsheetdetail_set.filter(status='received').count()
        
        if received_cnotes == 0:
            self.status = 'dispatched'
        elif received_cnotes < total_cnotes:
            self.status = 'partial_received'
        else:
            self.status = 'received'
        
        self.save()


class LoadingSheetDetail(models.Model):
    LOADING_SHEET_DETAIL_STATUS_CHOICES = [
        ('dispatched', 'Dispatched'),
        ('received', 'Received'),
        ('cancelled', 'Cancelled'),
    ]

    loading_sheet = models.ForeignKey(LoadingSheetSummary, on_delete=models.CASCADE, related_name='details')
    cnote = models.ForeignKey(CNotes, on_delete=models.CASCADE, related_name='loading_sheet_details')
    consignor_name = models.CharField(max_length=100)
    consignee_name = models.CharField(max_length=100)
    consignor_contact = models.CharField(max_length=15)
    consignee_contact = models.CharField(max_length=15)
    destination = models.CharField(max_length=100)
    art = models.IntegerField()
    payment_type = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=LOADING_SHEET_DETAIL_STATUS_CHOICES, default='dispatched')
    remark = models.TextField(blank=True)

    def __str__(self):
        return f"CNote {self.cnote.cnote_number} in Loading Sheet {self.loading_sheet.ls_number}"

# Signal handlers
def update_cnote_total_art(sender, instance, **kwargs):
    cnote = instance.cnote
    cnote.total_art = cnote.articles.count()
    cnote.save()

def update_loading_sheet_summary(sender, instance, **kwargs):
    loading_sheet = instance.loading_sheet
    loading_sheet.total_cnote = loading_sheet.details.count()
    loading_sheet.total_art = sum(detail.art for detail in loading_sheet.details.all())
    loading_sheet.total_paid_amount = sum(detail.amount for detail in loading_sheet.details.filter(payment_type='PAID'))
    loading_sheet.total_topay_amount = sum(detail.amount for detail in loading_sheet.details.filter(payment_type='TO PAY'))
    loading_sheet.total_tbb_amount = sum(detail.amount for detail in loading_sheet.details.filter(payment_type='TBB'))
    loading_sheet.total_foc_amount = sum(detail.amount for detail in loading_sheet.details.filter(payment_type='FOC'))
    loading_sheet.save()

def update_cnote_status_on_loading_sheet_creation(sender, instance, created, **kwargs):
    if created:
        for detail in instance.details.all():
            detail.cnote.update_status('dispatched')

def update_cnote_status_on_delivery(sender, instance, created, **kwargs):
    if created:
        instance.cnote.update_status('due_for_delivery')
    elif instance.is_successful:
        instance.cnote.update_status('delivered')
    else:
        instance.cnote.update_status('received_at_godown')

def handle_loading_sheet_cancellation(sender, instance, **kwargs):
    if instance.status == 'cancelled':
        instance.details.update(status='cancelled')
        CNote.objects.filter(loading_sheet_details__loading_sheet=instance).update(status='booked')

# Connect signal handlers
post_save.connect(update_cnote_total_art, sender=Article)
post_save.connect(update_loading_sheet_summary, sender=LoadingSheetDetail)
post_save.connect(update_cnote_status_on_loading_sheet_creation, sender=LoadingSheetSummary)
post_save.connect(update_cnote_status_on_delivery, sender=Delivery)
post_save.connect(handle_loading_sheet_cancellation, sender=LoadingSheetSummary)

@receiver(pre_delete, sender=LoadingSheetSummary)
def revert_cnote_status(sender, instance, **kwargs):
    # Get all CNotes associated with this loading sheet
    cnotes = CNote.objects.filter(loading_sheet_details__loading_sheet=instance)
    
    # Update the status of each CNote
    for cnote in cnotes:
        if cnote.status == 'dispatched':
            # Revert the status to 'booked' or the appropriate previous state
            cnote.status = 'booked'
            cnote.save()

    # Delete the loading sheet details
    LoadingSheetDetail.objects.filter(loading_sheet=instance).delete()



class ClientPrinters(models.Model):
    dealer = models.ForeignKey(Dealer, on_delete=models.CASCADE, related_name='client_printers')
    printer_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['dealer', 'printer_name']
    
    def __str__(self):
        return f"{self.dealer.name} - {self.printer_name}"

class QRPrinterSetting(models.Model):
    dealer = models.OneToOneField(Dealer, on_delete=models.CASCADE)
    printer_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.dealer.name} - {self.printer_name}"
