from rest_framework import serializers
from .models import Dealer, Transporter, CNote, Manifest, ManifestItem

# Dealer Serializer
class DealerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dealer
        fields = '__all__'

# Transporter Serializer
class TransporterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transporter
        fields = '__all__'

# CNote Serializer
class CNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = CNote
        fields = '__all__'

# Manifest Serializer
class ManifestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Manifest
        fields = '__all__'

# Manifest Item Serializer
class ManifestItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ManifestItem
        fields = '__all__'
