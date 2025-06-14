from django.db import models
from django.conf import settings
from django.utils import timezone
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from decimal import Decimal

# अन्य मॉडल्स के लिए आयात
from dealer_app.models import CNote, Dealer  # CNote का आयात

class State(models.Model):
    name = models.CharField(max_length=100, unique=True)
    capital = models.CharField(max_length=100)
    description = models.CharField(max_length=255)  # Non-nullable field

    def __str__(self):
        return self.name

class City(models.Model):
    name = models.CharField(max_length=100, unique=True)
    state = models.ForeignKey(State, on_delete=models.CASCADE)  # ForeignKey to State model
    description = models.CharField(max_length=255)  # Non-nullable field

    def __str__(self):
        return self.name

# TransporterProfile model to hold additional information about the transporter
class TransporterProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transporter_profile_user')
    company_name = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=15)
    address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)  # निर्माण समय
    updated_at = models.DateTimeField(auto_now=True)      # अंतिम अपडेट समय

    def __str__(self):
        return self.company_name

# Transporter model to hold transporter information


class Transporter(models.Model):
    id = models.BigAutoField(primary_key=True)
    transporter_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=100)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transporter_user')
    company_name = models.CharField(max_length=100, default="Unknown Company")
    contact_person = models.CharField(max_length=100, default="Unknown Contact Person")
    phone_number_1 = models.CharField(max_length=15)
    phone_number_2 = models.CharField(max_length=15, null=True, blank=True)
    mobile_number_1 = models.CharField(max_length=15)
    mobile_number_2 = models.CharField(max_length=15, null=True, blank=True)
    email = models.EmailField(max_length=254, unique=True)
    gstn = models.CharField(max_length=15, null=True, blank=True)
    address = models.TextField(default="Address not provided")
    state = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    vehicle_number = models.CharField(max_length=20, default="UNKNOWN")
    profile_image = models.ImageField(upload_to='profile_images/', null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'transporter'
        verbose_name = 'Transporter'
        verbose_name_plural = 'Transporters'

    def __str__(self):
        return f"{self.name} (T{self.transporter_id:04d})"

    def save(self, *args, **kwargs):
        if not self.transporter_id:
            last_transporter = Transporter.objects.order_by('-transporter_id').first()
            self.transporter_id = (last_transporter.transporter_id + 1) if last_transporter else 1
        self.name = self.name.upper()
        super().save(*args, **kwargs)

# Pickup model to hold pickup information
class Pickup(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('picked_up', 'Picked Up'),
        ('cancelled', 'Cancelled'),
        # Add more statuses as needed
    ]

    transporter = models.ForeignKey(Transporter, on_delete=models.CASCADE)
    cnote = models.ForeignKey(CNote, on_delete=models.CASCADE)  # CNote ForeignKey defined here
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)  # निर्माण समय
    updated_at = models.DateTimeField(auto_now=True)      # अंतिम अपडेट समय
    dealer = models.ForeignKey(Dealer, on_delete=models.CASCADE)  # Ensure this field is present
    pickup_date = models.DateTimeField(null=True, blank=True, default=timezone.now)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"Pickup {self.id} for {self.cnote}"

    def mark_as_picked_up(self):
        self.status = 'picked_up'
        self.save()

    def cancel(self):
        self.status = 'cancelled'
        self.save()


class PartyMaster(models.Model):
    party_code = models.CharField(max_length=50, null=True, blank=True)  # Optional
    party_name = models.CharField(max_length=255, null=False, blank=False)
    display_name = models.CharField(max_length=255, null=False, blank=False)
    mobile_number_1 = models.CharField(max_length=15)
    mobile_number_2 = models.CharField(max_length=15, blank=True)
    phone_number_1 = models.CharField(max_length=15, blank=True)
    phone_number_2 = models.CharField(max_length=15, blank=True)
    gst_no = models.CharField(max_length=15, null=True, blank=True)  # Optional
    pan_no = models.CharField(max_length=10, null=True, blank=True)  # Optional
    email = models.EmailField(blank=True)
    marketing_person = models.CharField(max_length=255, null=True, blank=True)  # Optional
    party_type = models.CharField(max_length=50)
    country = models.CharField(max_length=50, default="INDIA")
    state = models.CharField(max_length=50, blank=True)
    city = models.CharField(max_length=50)
    pincode = models.CharField(max_length=6)
    address = models.TextField()
    is_tbb = models.BooleanField(default=False)
    remark = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)  # निर्माण समय
    updated_at = models.DateTimeField(auto_now=True)      # अंतिम अपडेट समय

    def __str__(self):
        return f"{self.party_name} ({self.party_code})"
    


class TransporterAppReceive(models.Model):
    ls_number = models.CharField(max_length=50, unique=True)
    received_date = models.DateTimeField(auto_now_add=True)
    transporter = models.ForeignKey(Transporter, on_delete=models.CASCADE)
    total_lrs = models.IntegerField()
    total_art = models.IntegerField()
    total_weight = models.DecimalField(max_digits=10, decimal_places=2)
    from_branch = models.CharField(max_length=100)
    to_branch = models.CharField(max_length=100)
    dealer = models.ForeignKey(Dealer, on_delete=models.SET_NULL, null=True)
    truck_no = models.CharField(max_length=20)
    ls_date_time = models.DateTimeField()

    def __str__(self):
        return f"Received LS: {self.ls_number}"    
    

class ReceivedStatesCnotes(models.Model):
    cnote_number = models.CharField(max_length=255)
    consignor_name = models.CharField(max_length=255)
    consignee_name = models.CharField(max_length=255)
    consignor_contact = models.CharField(max_length=255)
    consignee_contact = models.CharField(max_length=255)
    articles = models.IntegerField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    ls_number = models.CharField(max_length=255)
    dealer_name = models.CharField(max_length=255)
    transporter_name = models.CharField(max_length=255)
    received_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=255, default='Received')
    # Add other fields as necessary
    # New fields
    remarks = models.TextField(blank=True, null=True)
    godown = models.CharField(max_length=255, blank=True, null=True)
    received_by = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"CNotes {self.cnote_number} - {self.status}"
    


class DeliveryCNote(models.Model):
    lr_number = models.CharField(max_length=20)
    status = models.CharField(max_length=50)
    payment_type = models.CharField(max_length=50)  # Add this field
    consignor_name = models.CharField(max_length=100)
    consignor_address = models.TextField()
    consignor_contact = models.CharField(max_length=15)
    consignor_gst = models.CharField(max_length=15)
    consignee_name = models.CharField(max_length=100)
    consignee_address = models.TextField()
    consignee_contact = models.CharField(max_length=15)
    consignee_gst = models.CharField(max_length=15)
    freight_charges = models.DecimalField(max_digits=10, decimal_places=2)
    other_charges = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    delivered_to_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    id_proof_type = models.CharField(max_length=50)
    id_proof_number = models.CharField(max_length=50)
    remarks = models.TextField(null=True, blank=True)
    delivered_status = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.lr_number




class DDMSummary(models.Model):
    ddm_id = models.AutoField(primary_key=True)  # Unique ID for each DDM summary
    ddm_no = models.CharField(max_length=20, unique=True)  # DDM number, must be unique
    total_cnotes = models.IntegerField()
    total_packages = models.IntegerField()
    total_paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_to_pay_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_tbb_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    creation_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    # New fields for loading information
    truck_no = models.CharField(max_length=20, blank=True)
    driver_name = models.CharField(max_length=100, blank=True)
    driver_no = models.CharField(max_length=15, blank=True)
    lorry_hire = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    remarks = models.TextField(blank=True, null=True)  # Add this line
    def __str__(self):
        return f"Summary for DDM {self.ddm_no} (ID: {self.ddm_id})"

    class Meta:
        verbose_name = "Door Delivery Memo Summary"
        verbose_name_plural = "Door Delivery Memo Summaries"


class DDMDetails(models.Model):
    id = models.AutoField(primary_key=True)
    ddm = models.ForeignKey(DDMSummary, on_delete=models.CASCADE, related_name='details', null=True, blank=True)
    cnote_booking_date = models.DateField(null=True, blank=True)
    cnote_number = models.CharField(max_length=20)
    consignee_name = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=20)
    destination = models.CharField(max_length=100)
    total_pkt = models.IntegerField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_type = models.CharField(max_length=20)
    remark = models.TextField(blank=True, null=True)
    creation_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    dealer_name = models.CharField(max_length=100)
    transporter_name = models.CharField(max_length=100)
    status = models.CharField(max_length=20, default='due delivered')
    
    # New fields for loading information
    truck_no = models.CharField(max_length=20, blank=True)
    driver_name = models.CharField(max_length=100, blank=True)
    driver_no = models.CharField(max_length=15, blank=True)
    lorry_hire = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"DDM Detail for CNote {self.cnote_number} (DDM ID: {self.ddm.ddm_id if self.ddm else 'N/A'})"

    class Meta:
        verbose_name = "Door Delivery Memo Details"
        verbose_name_plural = "Door Delivery Memo Details"



User = get_user_model()

class Bill(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    )
    
    bill_number = models.CharField(max_length=20, unique=True)
    dealer = models.ForeignKey('dealer_app.Dealer', on_delete=models.CASCADE)
    transporter = models.ForeignKey('transporter_app.Transporter', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_bills')
    from_date = models.DateField(null=True, blank=True)
    to_date = models.DateField(null=True, blank=True)
    bill_month = models.IntegerField(null=True, blank=True)
    bill_year = models.IntegerField(null=True, blank=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gst_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=18.00)
    gst_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    remarks = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Bill {self.bill_number} - {self.dealer.name}"
    
    def save(self, *args, **kwargs):
        # Ensure gst_percentage is a Decimal
        if not isinstance(self.gst_percentage, Decimal):
            self.gst_percentage = Decimal(str(self.gst_percentage))
        # Calculate GST and total amount if not already set
        if not self.gst_amount or not self.total_amount:
            self.gst_amount = self.subtotal * (self.gst_percentage / Decimal('100'))
            self.total_amount = self.subtotal + self.gst_amount
        super().save(*args, **kwargs)

class BillItem(models.Model):
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='items')
    cnote = models.ForeignKey('dealer_app.CNotes', on_delete=models.CASCADE)
    cnote_number = models.CharField(max_length=50)
    created_date = models.DateField()
    payment_type = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    consignee_name = models.CharField(max_length=255)
    total_art = models.IntegerField()
    
    def __str__(self):
        return f"Bill Item {self.cnote_number} for {self.bill.bill_number}"
    
    class Meta:
        unique_together = ('bill', 'cnote')
