from django.contrib import admin
from .models import Expense, ExpenseSplit, Settlement, CurrencyRate


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('description', 'group', 'paid_by', 'amount', 'currency', 'split_type', 'expense_date')
    list_filter = ('currency', 'split_type', 'group', 'is_settlement')
    search_fields = ('description', 'paid_by__username')
    date_hierarchy = 'expense_date'


@admin.register(ExpenseSplit)
class ExpenseSplitAdmin(admin.ModelAdmin):
    list_display = ('expense', 'user', 'share_amount')


@admin.register(Settlement)
class SettlementAdmin(admin.ModelAdmin):
    list_display = ('paid_by', 'paid_to', 'amount', 'currency', 'settlement_date', 'group')
    list_filter = ('currency', 'group')
    date_hierarchy = 'settlement_date'


@admin.register(CurrencyRate)
class CurrencyRateAdmin(admin.ModelAdmin):
    list_display = ('from_currency', 'to_currency', 'rate', 'effective_date', 'fetched_at')
    list_filter = ('from_currency', 'to_currency')
