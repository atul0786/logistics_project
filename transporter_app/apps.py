from django.apps import AppConfig

class TransporterAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'transporter_app'

    def ready(self):
        import transporter_app.signals  # Signals ko load karo
