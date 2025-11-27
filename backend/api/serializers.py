from rest_framework import serializers
from .models import User, PurchaseRequest

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'first_name', 'last_name']
        read_only_fields = ['id']

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'role', 'first_name', 'last_name']
    
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            role=validated_data.get('role', 'staff'),
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        return user

class PurchaseRequestSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    level_1_approver_name = serializers.CharField(source='level_1_approver.get_full_name', read_only=True)
    level_2_approver_name = serializers.CharField(source='level_2_approver.get_full_name', read_only=True)
    rejected_by_name = serializers.CharField(source='rejected_by.get_full_name', read_only=True)
    
    class Meta:
        model = PurchaseRequest
        fields = '__all__'
        read_only_fields = [
            'created_by', 'created_at', 'updated_at', 'status',
            'level_1_approved', 'level_1_approver', 'level_1_approved_at',
            'level_2_approved', 'level_2_approver', 'level_2_approved_at',
            'rejected_by', 'rejected_at', 'purchase_order', 'purchase_order_data',
            'proforma_data', 'receipt_data', 'receipt_validation'
        ]

class PurchaseRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseRequest
        fields = ['title', 'description', 'amount', 'proforma']
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)

class ApprovalSerializer(serializers.Serializer):
    pass

class RejectionSerializer(serializers.Serializer):
    reason = serializers.CharField(required=True)

class ReceiptUploadSerializer(serializers.Serializer):
    receipt = serializers.FileField(required=True)