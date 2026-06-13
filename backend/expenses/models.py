from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal


class Expense(models.Model):
    """
    An expense paid by one person, split among group members.
    Supports multiple split types: equal, unequal, percentage, share.
    """
    SPLIT_TYPE_CHOICES = [
        ('equal', 'Equal'),
        ('unequal', 'Unequal'),
        ('percentage', 'Percentage'),
        ('share', 'Share (Ratio)'),
    ]

    CURRENCY_CHOICES = [
        ('INR', 'Indian Rupee'),
        ('USD', 'US Dollar'),
    ]

    group = models.ForeignKey(
        'groups.Group', on_delete=models.CASCADE, related_name='expenses'
    )
    paid_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='expenses_paid'
    )
    description = models.CharField(max_length=500)
    amount = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    currency = models.CharField(
        max_length=3, choices=CURRENCY_CHOICES, default='INR'
    )
    split_type = models.CharField(
        max_length=20, choices=SPLIT_TYPE_CHOICES, default='equal'
    )
    expense_date = models.DateField()
    notes = models.TextField(blank=True, default='')
    is_settlement = models.BooleanField(
        default=False,
        help_text='True if this is a payment/settlement, not an expense'
    )

    # For tracking CSV import origin
    import_row_number = models.IntegerField(
        null=True, blank=True,
        help_text='CSV row number if imported from file'
    )
    import_report = models.ForeignKey(
        'importer.ImportReport', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='created_expenses'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-expense_date', '-created_at']

    def __str__(self):
        return f'{self.description} - {self.currency} {self.amount} by {self.paid_by.username}'

    @property
    def amount_in_inr(self):
        """
        Convert amount to INR for balance calculations.
        Uses stored exchange rate from CurrencyRate table.
        """
        if self.currency == 'INR':
            return self.amount
        # Look up the exchange rate for the expense date
        rate = CurrencyRate.get_rate(self.currency, 'INR', self.expense_date)
        return (self.amount * rate).quantize(Decimal('0.01'))


class ExpenseSplit(models.Model):
    """
    How an expense is split among participants.
    Each row represents one person's share of one expense.
    """
    expense = models.ForeignKey(
        Expense, on_delete=models.CASCADE, related_name='splits'
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='expense_splits'
    )
    share_amount = models.DecimalField(
        max_digits=12, decimal_places=2,
        help_text='Calculated amount this user owes for this expense'
    )
    share_value = models.DecimalField(
        max_digits=12, decimal_places=4, null=True, blank=True,
        help_text='Raw value: percentage (e.g., 30.0), ratio (e.g., 2), or fixed amount'
    )

    class Meta:
        unique_together = ['expense', 'user']

    def __str__(self):
        return f'{self.user.username} owes {self.share_amount} for {self.expense.description}'


class Settlement(models.Model):
    """
    A direct payment from one person to another to settle debts.
    Not an expense — this reduces balances without creating new splits.
    """
    CURRENCY_CHOICES = [
        ('INR', 'Indian Rupee'),
        ('USD', 'US Dollar'),
    ]

    group = models.ForeignKey(
        'groups.Group', on_delete=models.CASCADE, related_name='settlements'
    )
    paid_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='settlements_made'
    )
    paid_to = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='settlements_received'
    )
    amount = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    currency = models.CharField(
        max_length=3, choices=CURRENCY_CHOICES, default='INR'
    )
    settlement_date = models.DateField()
    notes = models.TextField(blank=True, default='')

    # For tracking CSV import origin
    import_row_number = models.IntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-settlement_date', '-created_at']

    def __str__(self):
        return f'{self.paid_by.username} → {self.paid_to.username}: {self.currency} {self.amount}'


class CurrencyRate(models.Model):
    """
    Stores exchange rates fetched from ExchangeRate-API.
    Caches rates by date to avoid excessive API calls.
    """
    from_currency = models.CharField(max_length=3)
    to_currency = models.CharField(max_length=3)
    rate = models.DecimalField(max_digits=12, decimal_places=4)
    effective_date = models.DateField()
    fetched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['from_currency', 'to_currency', 'effective_date']
        ordering = ['-effective_date']

    def __str__(self):
        return f'{self.from_currency} → {self.to_currency}: {self.rate} ({self.effective_date})'

    @classmethod
    def get_rate(cls, from_currency, to_currency, date=None):
        """
        Get exchange rate, checking cache first, then API, then fallback.
        """
        from django.conf import settings
        from django.utils import timezone
        import requests
        from decimal import Decimal

        if from_currency == to_currency:
            return Decimal('1.0')

        if date is None:
            date = timezone.now().date()

        # Check cache first
        cached = cls.objects.filter(
            from_currency=from_currency,
            to_currency=to_currency,
            effective_date=date
        ).first()

        if cached:
            return cached.rate

        # Try API
        api_key = settings.EXCHANGE_RATE_API_KEY
        if api_key:
            try:
                url = f'{settings.EXCHANGE_RATE_API_BASE_URL}/{api_key}/pair/{from_currency}/{to_currency}'
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('result') == 'success':
                        rate = Decimal(str(data['conversion_rate']))
                        # Cache the rate
                        cls.objects.update_or_create(
                            from_currency=from_currency,
                            to_currency=to_currency,
                            effective_date=date,
                            defaults={'rate': rate}
                        )
                        return rate
            except (requests.RequestException, KeyError, ValueError):
                pass  # Fall through to default

        # Fallback to default rate
        if from_currency == 'USD' and to_currency == 'INR':
            return Decimal(str(settings.DEFAULT_USD_TO_INR_RATE))
        elif from_currency == 'INR' and to_currency == 'USD':
            return Decimal('1') / Decimal(str(settings.DEFAULT_USD_TO_INR_RATE))

        return Decimal('1.0')  # Unknown pair fallback
