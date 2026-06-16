"""
Management command to create a demo evaluator account.
Idempotent — safe to run multiple times.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Create a demo user (aisha / aisha123) for evaluator convenience.'

    def handle(self, *args, **options):
        username = 'aisha'
        password = 'aisha123'

        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'first_name': 'Aisha',
                'last_name': 'Khan',
                'email': 'aisha@demo.fairshare.app',
            }
        )

        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(
                f'Demo user "{username}" created with password "{password}".'
            ))
        else:
            # Ensure password is always reset to the known demo password
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.WARNING(
                f'Demo user "{username}" already exists — password reset to "{password}".'
            ))
