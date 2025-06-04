from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from transporter_app.models import City
from dealer_app.models import DeliveryDestination
import logging

logger = logging.getLogger(__name__)

# Ye variable old city name store karega
city_old_name = {}

@receiver(pre_save, sender=City)
def store_old_name(sender, instance, **kwargs):
    try:
        old_instance = City.objects.get(pk=instance.pk)
        city_old_name[instance.pk] = old_instance.name
    except City.DoesNotExist:
        city_old_name[instance.pk] = None

@receiver(post_save, sender=City)
def sync_city_to_delivery_destination(sender, instance, created, **kwargs):
    try:
        if created:
            # Naya city bana, to DeliveryDestination mein add karo
            DeliveryDestination.objects.create(
                destination_name=instance.name,
                address=f"Default address for {instance.name}"
            )
            logger.info(f"Created DeliveryDestination for City: {instance.name}")
        else:
            # City update hua, to DeliveryDestination update karo
            old_name = city_old_name.get(instance.pk)
            if old_name and old_name != instance.name:
                DeliveryDestination.objects.filter(destination_name=old_name).update(
                    destination_name=instance.name
                )
                logger.info(f"Updated DeliveryDestination from {old_name} to {instance.name}")
            else:
                DeliveryDestination.objects.get_or_create(
                    destination_name=instance.name,
                    defaults={'address': f'Default address for {instance.name}'}
                )
            city_old_name.pop(instance.pk, None)
    except Exception as e:
        logger.error(f"Error syncing City to DeliveryDestination: {str(e)}")
