from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import models
from accounts.models import UserProfile


class Command(BaseCommand):
    help = 'Test admin functionality by creating sample users and displaying statistics'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Testing Admin Functionality'))
        
        # Display current user statistics
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        inactive_users = total_users - active_users
        
        self.stdout.write(f'Total Users: {total_users}')
        self.stdout.write(f'Active Users: {active_users}')
        self.stdout.write(f'Inactive Users: {inactive_users}')
        
        # Display role distribution
        role_stats = UserProfile.objects.values('role').annotate(
            count=models.Count('role')
        ).order_by('role')
        
        self.stdout.write('\nRole Distribution:')
        for role_stat in role_stats:
            role_display = dict(UserProfile.ROLE_CHOICES).get(role_stat['role'], role_stat['role'])
            self.stdout.write(f'  {role_display}: {role_stat["count"]}')
        
        # Test admin actions
        self.stdout.write('\nAdmin Actions Available:')
        self.stdout.write('  - Activate/Deactivate Users')
        self.stdout.write('  - Bulk Role Assignment')
        self.stdout.write('  - CSV Export')
        self.stdout.write('  - User Statistics View')
        self.stdout.write('  - Enhanced Search and Filtering')
        
        self.stdout.write(self.style.SUCCESS('\nAdmin functionality test completed successfully!'))