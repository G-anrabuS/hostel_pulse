"""
Management command to clear OAuth associations
"""
from django.core.management.base import BaseCommand
from social_django.models import UserSocialAuth


class Command(BaseCommand):
    help = 'Clear all OAuth associations to allow re-authentication with new scopes'

    def handle(self, *args, **options):
        count = UserSocialAuth.objects.all().count()
        UserSocialAuth.objects.all().delete()
        self.stdout.write(
            self.style.SUCCESS(f'Successfully deleted {count} OAuth association(s)')
        )
        self.stdout.write(
            self.style.SUCCESS('You can now sign in again with new permissions!')
        )
