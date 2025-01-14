from rest_framework import serializers
from .models import State, Transporter  # Ensure you import the necessary models

class StateSerializer(serializers.ModelSerializer):
    class Meta:
        model = State
        fields = '__all__'  # or specify the fields you want to include

class TransporterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transporter
        fields = '__all__'  # or specify the fields you want to include


from rest_framework import serializers
from .models import DDMDetails, DDMSummary

class DDMDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DDMDetails
        fields = '__all__'


class DDMSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = DDMSummary
        fields = '__all__'
