from decimal import Decimal
from django.contrib.auth.models import User
from rest_framework import serializers

from accounts.serializers import UserSerializer
from .models import Expense, ExpenseSplit, Settlement, CurrencyRate


class ExpenseSplitSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = ExpenseSplit
        fields = ('id', 'user', 'share_amount', 'share_value')


class ExpenseSerializer(serializers.ModelSerializer):
    paid_by = UserSerializer(read_only=True)
    splits = ExpenseSplitSerializer(many=True, read_only=True)
    amount_in_inr = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Expense
        fields = (
            'id', 'group', 'paid_by', 'description', 'amount', 'currency',
            'split_type', 'expense_date', 'notes', 'is_settlement',
            'import_row_number', 'splits', 'amount_in_inr', 'created_at',
        )
        read_only_fields = ('id', 'paid_by', 'created_at', 'amount_in_inr')


class SplitDetailField(serializers.DictField):
    """Accepts {username_or_id: value} pairs for split details."""
    child = serializers.DecimalField(max_digits=12, decimal_places=4)


class ExpenseCreateSerializer(serializers.ModelSerializer):
    """
    Used for creating/updating expenses.
    split_with: list of usernames to include in the split
    split_details: {username: value} for unequal/percentage/share splits
    """
    paid_by_username = serializers.CharField(write_only=True, required=False)
    split_with = serializers.ListField(child=serializers.CharField(), write_only=True)
    split_details = serializers.DictField(child=serializers.DecimalField(max_digits=12, decimal_places=4), required=False, write_only=True, default=dict)

    class Meta:
        model = Expense
        fields = (
            'id', 'description', 'amount', 'currency', 'split_type',
            'expense_date', 'notes', 'is_settlement',
            'paid_by_username', 'split_with', 'split_details',
        )
        read_only_fields = ('id',)

    def validate_currency(self, value):
        valid = [c[0] for c in Expense.CURRENCY_CHOICES]
        if value not in valid:
            raise serializers.ValidationError(f'Currency must be one of {valid}.')
        return value

    def validate_amount(self, value):
        # Allow negative amounts (refunds) - handled as reversals
        return value

    def validate(self, attrs):
        split_type = attrs.get('split_type', 'equal')
        split_details = attrs.get('split_details', {})

        if split_type in ('unequal', 'percentage', 'share') and not split_details:
            raise serializers.ValidationError({
                'split_details': f'split_details is required for split_type={split_type}'
            })

        return attrs


class SettlementSerializer(serializers.ModelSerializer):
    paid_by = UserSerializer(read_only=True)
    paid_to = UserSerializer(read_only=True)

    class Meta:
        model = Settlement
        fields = ('id', 'group', 'paid_by', 'paid_to', 'amount', 'currency', 'settlement_date', 'notes', 'created_at')
        read_only_fields = ('id', 'paid_by', 'created_at')


class SettlementCreateSerializer(serializers.ModelSerializer):
    paid_to_username = serializers.CharField(write_only=True)

    class Meta:
        model = Settlement
        fields = ('id', 'amount', 'currency', 'settlement_date', 'notes', 'paid_to_username')
        read_only_fields = ('id',)

    def validate_paid_to_username(self, value):
        try:
            User.objects.get(username__iexact=value)
        except User.DoesNotExist:
            raise serializers.ValidationError(f'User "{value}" not found.')
        return value


class CurrencyRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CurrencyRate
        fields = ('from_currency', 'to_currency', 'rate', 'effective_date', 'fetched_at')
