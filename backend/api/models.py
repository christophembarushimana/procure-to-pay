from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q

class User(AbstractUser):
    ROLE_CHOICES = [
        ('staff', 'Staff'),
        ('approver_level_1', 'Approver Level 1'),
        ('approver_level_2', 'Approver Level 2'),
        ('finance', 'Finance'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='staff')
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

class PurchaseRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requests_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    proforma = models.FileField(upload_to='proformas/', null=True, blank=True)
    proforma_data = models.JSONField(null=True, blank=True)
    
    purchase_order = models.FileField(upload_to='purchase_orders/', null=True, blank=True)
    purchase_order_data = models.JSONField(null=True, blank=True)
    
    receipt = models.FileField(upload_to='receipts/', null=True, blank=True)
    receipt_data = models.JSONField(null=True, blank=True)
    receipt_validation = models.JSONField(null=True, blank=True)
    
    level_1_approved = models.BooleanField(default=False)
    level_1_approver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='level_1_approvals')
    level_1_approved_at = models.DateTimeField(null=True, blank=True)
    
    level_2_approved = models.BooleanField(default=False)
    level_2_approver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='level_2_approvals')
    level_2_approved_at = models.DateTimeField(null=True, blank=True)
    
    rejected_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='rejections')
    rejected_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(
                check=Q(status='pending') | Q(status='approved') | Q(status='rejected'),
                name='valid_status'
            )
        ]
    
    def __str__(self):
        return f"{self.title} - {self.status}"
    
    def can_approve_level_1(self, user):
        return (
            self.status == 'pending' and
            not self.level_1_approved and
            user.role == 'approver_level_1'
        )
    
    def can_approve_level_2(self, user):
        return (
            self.status == 'pending' and
            self.level_1_approved and
            not self.level_2_approved and
            user.role == 'approver_level_2'
        )
    
    def can_reject(self, user):
        return (
            self.status == 'pending' and
            user.role in ['approver_level_1', 'approver_level_2']
        )