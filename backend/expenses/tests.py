"""
Basic API smoke tests for Phase 2 endpoints.
Tests: register, login, group create, add member, expense create, balances, settlement.
"""
import json
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status

from groups.models import Group, GroupMembership
from expenses.models import Expense, ExpenseSplit, Settlement


class AuthAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register(self):
        response = self.client.post('/api/auth/register/', {
            'username': 'aisha',
            'email': 'aisha@test.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        self.assertEqual(response.data['user']['username'], 'aisha')

    def test_login(self):
        User.objects.create_user('rohan', password='testpass123')
        response = self.client.post('/api/auth/login/', {
            'username': 'rohan',
            'password': 'testpass123',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('user', response.data)

    def test_me_requires_auth(self):
        response = self.client.get('/api/auth/me/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_authenticated(self):
        user = User.objects.create_user('priya', password='testpass123')
        self.client.force_authenticate(user=user)
        response = self.client.get('/api/auth/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'priya')


class GroupAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.aisha = User.objects.create_user('aisha', email='a@t.com', password='pass')
        self.rohan = User.objects.create_user('rohan', email='r@t.com', password='pass')
        self.client.force_authenticate(user=self.aisha)

    def test_create_group(self):
        response = self.client.post('/api/groups/', {
            'name': 'Flat 4B',
            'description': 'Our flat group',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Flat 4B')
        # Creator should be auto-added as member
        group = Group.objects.get(name='Flat 4B')
        self.assertTrue(group.memberships.filter(user=self.aisha, is_active=True).exists())

    def test_add_member(self):
        group = Group.objects.create(name='Flat 4B', created_by=self.aisha)
        GroupMembership.objects.create(group=group, user=self.aisha, joined_at='2026-01-01', is_active=True)

        response = self.client.post(f'/api/groups/{group.id}/members/', {
            'username': 'rohan',
            'joined_at': '2026-02-01',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(group.memberships.filter(user=self.rohan, is_active=True).exists())

    def test_non_member_cannot_access_group(self):
        group = Group.objects.create(name='Private', created_by=self.rohan)
        GroupMembership.objects.create(group=group, user=self.rohan, joined_at='2026-01-01', is_active=True)

        response = self.client.get(f'/api/groups/{group.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ExpenseAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.aisha = User.objects.create_user('aisha', password='pass')
        self.rohan = User.objects.create_user('rohan', password='pass')
        self.priya = User.objects.create_user('priya', password='pass')

        self.group = Group.objects.create(name='Flat 4B', created_by=self.aisha)
        for user, date in [(self.aisha, '2026-01-01'), (self.rohan, '2026-01-01'), (self.priya, '2026-01-01')]:
            GroupMembership.objects.create(group=self.group, user=user, joined_at=date, is_active=True)

        self.client.force_authenticate(user=self.aisha)

    def test_create_equal_expense(self):
        response = self.client.post(f'/api/expenses/{self.group.id}/', {
            'description': 'Grocery run',
            'amount': '900.00',
            'currency': 'INR',
            'split_type': 'equal',
            'expense_date': '2026-03-10',
            'paid_by_username': 'aisha',
            'split_with': ['aisha', 'rohan', 'priya'],
            'split_details': {},
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check splits: 3 people, 900/3 = 300 each
        expense = Expense.objects.get(description='Grocery run')
        splits = {s.user.username: s.share_amount for s in expense.splits.all()}
        self.assertEqual(splits['aisha'], Decimal('300.00'))
        self.assertEqual(splits['rohan'], Decimal('300.00'))
        self.assertEqual(splits['priya'], Decimal('300.00'))

    def test_create_share_expense(self):
        """Scooter rental: Rohan and Dev took bigger ones (share 2), others share 1."""
        response = self.client.post(f'/api/expenses/{self.group.id}/', {
            'description': 'Scooter rental',
            'amount': '3600.00',
            'currency': 'INR',
            'split_type': 'share',
            'expense_date': '2026-03-10',
            'paid_by_username': 'priya',
            'split_with': ['aisha', 'rohan', 'priya'],
            'split_details': {'aisha': '1', 'rohan': '2', 'priya': '1'},
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        expense = Expense.objects.get(description='Scooter rental')
        splits = {s.user.username: s.share_amount for s in expense.splits.all()}
        # Total shares: 4, per share: 900
        self.assertEqual(splits['aisha'], Decimal('900.00'))
        self.assertEqual(splits['rohan'], Decimal('1800.00'))
        self.assertEqual(splits['priya'], Decimal('900.00'))

    def test_balances(self):
        """After Aisha pays 900 split equally 3 ways, Rohan and Priya owe 300 each."""
        expense = Expense.objects.create(
            group=self.group,
            paid_by=self.aisha,
            description='Test',
            amount=Decimal('900.00'),
            currency='INR',
            split_type='equal',
            expense_date='2026-03-10',
        )
        for user, amount in [(self.aisha, 300), (self.rohan, 300), (self.priya, 300)]:
            ExpenseSplit.objects.create(expense=expense, user=user, share_amount=amount)

        response = self.client.get(f'/api/expenses/{self.group.id}/balances/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        balances = {b['username']: Decimal(b['balance']) for b in response.data['balances']}
        self.assertEqual(balances['aisha'], Decimal('600.00'))   # owed 600
        self.assertEqual(balances['rohan'], Decimal('-300.00'))   # owes 300
        self.assertEqual(balances['priya'], Decimal('-300.00'))   # owes 300


class SplitEngineTest(TestCase):
    """Unit tests for the split calculation engine."""

    def test_equal_split_remainder_goes_to_payer(self):
        from expenses.split_engine import calculate_equal_split
        # 100 / 3 = 33.33... remainder goes to first (payer)
        splits = calculate_equal_split(Decimal('100.00'), [1, 2, 3])
        self.assertEqual(splits[1], Decimal('33.34'))  # payer gets remainder
        self.assertEqual(splits[2], Decimal('33.33'))
        self.assertEqual(splits[3], Decimal('33.33'))
        self.assertEqual(sum(splits.values()), Decimal('100.00'))

    def test_percentage_split_normalizes_110_pct(self):
        from expenses.split_engine import calculate_percentage_split
        # 30+30+30+20 = 110, should normalize to sum=total
        splits = calculate_percentage_split(
            Decimal('2200.00'),
            {1: Decimal('30'), 2: Decimal('30'), 3: Decimal('30'), 4: Decimal('20')}
        )
        self.assertEqual(sum(splits.values()), Decimal('2200.00'))

    def test_negative_amount_refund(self):
        from expenses.split_engine import calculate_equal_split
        # -30 USD refund split among 4 people
        splits = calculate_equal_split(Decimal('-30.00'), [1, 2, 3, 4])
        self.assertEqual(sum(splits.values()), Decimal('-30.00'))
        for uid, amt in splits.items():
            self.assertTrue(amt <= 0, f'Expected negative or zero, got {amt}')
