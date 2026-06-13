from django.urls import path
from . import views

app_name = 'expenses'

urlpatterns = [
    # Exchange rate
    path('exchange-rate/', views.get_exchange_rate, name='exchange_rate'),

    # Group expenses
    path('<int:group_id>/', views.expense_list_create, name='expense_list_create'),
    path('<int:group_id>/<int:expense_id>/', views.expense_detail, name='expense_detail'),

    # Balances
    path('<int:group_id>/balances/', views.group_balances, name='group_balances'),
    path('<int:group_id>/balances/breakdown/', views.user_balance_breakdown, name='user_balance_breakdown'),

    # Settlements
    path('<int:group_id>/settlements/', views.settlement_list_create, name='settlement_list_create'),
    path('<int:group_id>/settlements/<int:settlement_id>/', views.settlement_detail, name='settlement_detail'),
]
