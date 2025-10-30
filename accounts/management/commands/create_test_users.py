from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import UserProfile


class Command(BaseCommand):
    help = 'Create test users with different roles for testing authentication system'

    def handle(self, *args, **options):
        # Create admin user
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@example.com',
                'first_name': 'Admin',
                'last_name': 'User',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            admin_user.userprofile.role = 'ADMIN'
            admin_user.userprofile.save()
            self.stdout.write(self.style.SUCCESS(f'Created admin user: admin/admin123'))
        else:
            self.stdout.write(self.style.WARNING(f'Admin user already exists'))

        # Create leadership user
        leadership_user, created = User.objects.get_or_create(
            username='leader',
            defaults={
                'email': 'leader@example.com',
                'first_name': 'Team',
                'last_name': 'Leader',
            }
        )
        if created:
            leadership_user.set_password('leader123')
            leadership_user.save()
            leadership_user.userprofile.role = 'LEADERSHIP'
            leadership_user.userprofile.save()
            self.stdout.write(self.style.SUCCESS(f'Created leadership user: leader/leader123'))
        else:
            self.stdout.write(self.style.WARNING(f'Leadership user already exists'))

        # Create team member user
        member_user, created = User.objects.get_or_create(
            username='member',
            defaults={
                'email': 'member@example.com',
                'first_name': 'Team',
                'last_name': 'Member',
            }
        )
        if created:
            member_user.set_password('member123')
            member_user.save()
            member_user.userprofile.role = 'TEAM_MEMBER'
            member_user.userprofile.save()
            self.stdout.write(self.style.SUCCESS(f'Created team member user: member/member123'))
        else:
            self.stdout.write(self.style.WARNING(f'Team member user already exists'))

        self.stdout.write(self.style.SUCCESS('Test users creation completed!'))