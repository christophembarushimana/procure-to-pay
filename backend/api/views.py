from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.db import transaction
from django.utils import timezone
from .models import User, PurchaseRequest
from .serializers import (
    UserSerializer, RegisterSerializer, PurchaseRequestSerializer,
    PurchaseRequestCreateSerializer, ApprovalSerializer, 
    RejectionSerializer, ReceiptUploadSerializer
)
from .document_processor import (
    extract_proforma_data, generate_purchase_order, validate_receipt
)

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data)

class PurchaseRequestViewSet(viewsets.ModelViewSet):
    queryset = PurchaseRequest.objects.all()
    serializer_class = PurchaseRequestSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = PurchaseRequest.objects.all()
        
        if user.role == 'staff':
            queryset = queryset.filter(created_by=user)
        elif user.role == 'approver_level_1':
            queryset = queryset.filter(status='pending')
        elif user.role == 'approver_level_2':
            queryset = queryset.filter(status='pending', level_1_approved=True)
        
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'create':
            return PurchaseRequestCreateSerializer
        return PurchaseRequestSerializer
    
    def create(self, request):
        if request.user.role != 'staff':
            return Response(
                {'error': 'Only staff can create purchase requests'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            purchase_request = serializer.save()
            
            if purchase_request.proforma:
                try:
                    proforma_data = extract_proforma_data(purchase_request.proforma)
                    purchase_request.proforma_data = proforma_data
                    purchase_request.save()
                except Exception as e:
                    pass
            
            return Response(
                PurchaseRequestSerializer(purchase_request).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, pk=None):
        purchase_request = self.get_object()
        
        if request.user != purchase_request.created_by:
            return Response(
                {'error': 'You can only update your own requests'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if purchase_request.status != 'pending':
            return Response(
                {'error': 'Cannot update non-pending requests'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = PurchaseRequestCreateSerializer(
            purchase_request, data=request.data, partial=True
        )
        if serializer.is_valid():
            purchase_request = serializer.save()
            
            if 'proforma' in request.data and purchase_request.proforma:
                try:
                    proforma_data = extract_proforma_data(purchase_request.proforma)
                    purchase_request.proforma_data = proforma_data
                    purchase_request.save()
                except Exception as e:
                    pass
            
            return Response(PurchaseRequestSerializer(purchase_request).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['patch'])
    def approve(self, request, pk=None):
        purchase_request = self.get_object()
        user = request.user
        
        with transaction.atomic():
            purchase_request = PurchaseRequest.objects.select_for_update().get(pk=pk)
            
            if purchase_request.status != 'pending':
                return Response(
                    {'error': 'Request is not pending'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if user.role == 'approver_level_1' and not purchase_request.level_1_approved:
                purchase_request.level_1_approved = True
                purchase_request.level_1_approver = user
                purchase_request.level_1_approved_at = timezone.now()
                purchase_request.save()
                
                return Response({
                    'message': 'Level 1 approval successful',
                    'request': PurchaseRequestSerializer(purchase_request).data
                })
            
            elif user.role == 'approver_level_2' and purchase_request.level_1_approved and not purchase_request.level_2_approved:
                purchase_request.level_2_approved = True
                purchase_request.level_2_approver = user
                purchase_request.level_2_approved_at = timezone.now()
                purchase_request.status = 'approved'
                
                po_data = generate_purchase_order(purchase_request)
                purchase_request.purchase_order_data = po_data
                
                purchase_request.save()
                
                return Response({
                    'message': 'Level 2 approval successful - Request approved and PO generated',
                    'request': PurchaseRequestSerializer(purchase_request).data,
                    'purchase_order': po_data
                })
            
            else:
                return Response(
                    {'error': 'You cannot approve this request at this stage'},
                    status=status.HTTP_403_FORBIDDEN
                )
    
    @action(detail=True, methods=['patch'])
    def reject(self, request, pk=None):
        purchase_request = self.get_object()
        user = request.user
        
        serializer = RejectionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            purchase_request = PurchaseRequest.objects.select_for_update().get(pk=pk)
            
            if purchase_request.status != 'pending':
                return Response(
                    {'error': 'Request is not pending'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if user.role not in ['approver_level_1', 'approver_level_2']:
                return Response(
                    {'error': 'Only approvers can reject requests'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            purchase_request.status = 'rejected'
            purchase_request.rejected_by = user
            purchase_request.rejected_at = timezone.now()
            purchase_request.rejection_reason = serializer.validated_data['reason']
            purchase_request.save()
            
            return Response({
                'message': 'Request rejected',
                'request': PurchaseRequestSerializer(purchase_request).data
            })
    
    @action(detail=True, methods=['post'])
    def submit_receipt(self, request, pk=None):
        purchase_request = self.get_object()
        
        if request.user != purchase_request.created_by:
            return Response(
                {'error': 'Only the request creator can submit receipts'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if purchase_request.status != 'approved':
            return Response(
                {'error': 'Can only submit receipts for approved requests'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = ReceiptUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        purchase_request.receipt = serializer.validated_data['receipt']
        
        if purchase_request.purchase_order_data:
            try:
                validation_result = validate_receipt(
                    purchase_request.receipt,
                    purchase_request.purchase_order_data
                )
                purchase_request.receipt_validation = validation_result
            except Exception as e:
                purchase_request.receipt_validation = {
                    'is_valid': False,
                    'error': str(e)
                }
        
        purchase_request.save()
        
        return Response({
            'message': 'Receipt submitted successfully',
            'validation': purchase_request.receipt_validation,
            'request': PurchaseRequestSerializer(purchase_request).data
        })