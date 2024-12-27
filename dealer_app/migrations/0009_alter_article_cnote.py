from django.db import migrations, models
import django.db.models.deletion
from django.utils import timezone
import uuid

def generate_unique_cnote_number():
    return str(uuid.uuid4())[:8].upper()

def forward_func(apps, schema_editor):
    Article = apps.get_model('dealer_app', 'Article')
    CNotes = apps.get_model('dealer_app', 'CNotes')
    db_alias = schema_editor.connection.alias
    
    # Create CNotes entries for existing CNote IDs with default values
    for article in Article.objects.using(db_alias).all():
        CNotes.objects.using(db_alias).get_or_create(
            id=article.cnote_id,
            defaults={
                'cnote_number': generate_unique_cnote_number(),
                'actual_weight': 0,
                'charged_weight': 0,
                'weight_rate': 0,
                'weight_amount': 0,
                'fix_amount': 0,
                'declared_value': 0,
                'freight': 0,
                'docket_charge': 0,
                'door_delivery_charge': 0,
                'handling_charge': 0,
                'pickup_charge': 0,
                'transhipment_charge': 0,
                'insurance': 0,
                'fuel_surcharge': 0,
                'commission': 0,
                'other_charge': 0,
                'carrier_risk': 0,
                'grand_total': 0,
                'booking_type': 'sundry',
                'delivery_type': 'economy',
                'delivery_method': 'door',
                'risk_type': 'owner',
                'pod_required': 'no',
                'payment_type': 'PAID',
                'status': 'booked',
                'created_at': timezone.now(),
            }
        )

def reverse_func(apps, schema_editor):
    # No reverse operation needed
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('dealer_app', '0008_cnotes'),
    ]

    operations = [
        migrations.RunPython(forward_func, reverse_func),
        migrations.AlterField(
            model_name='article',
            name='cnote',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='articles', to='dealer_app.cnotes'),
        ),
    ]

