import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings
from expenses.models import CurrencyRate

print(f"API Key from settings: {settings.EXCHANGE_RATE_API_KEY}")

print("\nFetching USD to INR exchange rate...")
rate = CurrencyRate.get_rate('USD', 'INR')
print(f"Rate returned: {rate}")
