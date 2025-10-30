from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('TEAM_MEMBER', 'Team Member'),
        ('LEADERSHIP', 'Leadership'),
        ('ADMIN', 'Administrator'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='TEAM_MEMBER')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"
    
    def is_admin(self):
        """Check if user has admin role"""
        return self.role == 'ADMIN'
    
    def is_leadership(self):
        """Check if user has leadership or admin role"""
        return self.role in ['LEADERSHIP', 'ADMIN']
    
    def is_team_member(self):
        """Check if user has team member role"""
        return self.role == 'TEAM_MEMBER'
    
    def can_approve_requests(self):
        """Check if user can approve training requests"""
        return self.is_leadership()
    
    def can_manage_users(self):
        """Check if user can manage other users"""
        return self.is_admin()
    
    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Automatically create UserProfile when User is created"""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save UserProfile when User is saved"""
    if hasattr(instance, 'userprofile'):
        instance.userprofile.save()
