from django.db import models
from django.contrib.auth.models import User


class Group(models.Model):
    """
    A group of people who share expenses.
    e.g., 'Flat 4B' for the flatmates.
    """
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='created_groups'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def active_members(self):
        """Return currently active members of this group."""
        return self.memberships.filter(is_active=True).select_related('user')

    def members_at_date(self, date):
        """
        Return members who were active on a specific date.
        A member is active on a date if:
        - joined_at <= date
        - AND (left_at is NULL OR left_at >= date)
        """
        return self.memberships.filter(
            joined_at__lte=date,
        ).filter(
            models.Q(left_at__isnull=True) | models.Q(left_at__gte=date)
        ).select_related('user')


class GroupMembership(models.Model):
    """
    Tracks when a person joined and left a group.
    Supports membership changes over time (e.g., Meera left end of March,
    Sam joined mid-April).
    """
    group = models.ForeignKey(
        Group, on_delete=models.CASCADE, related_name='memberships'
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='group_memberships'
    )
    joined_at = models.DateField()
    left_at = models.DateField(null=True, blank=True)  # null = still active
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['joined_at']
        unique_together = ['group', 'user', 'joined_at']

    def __str__(self):
        status = 'active' if self.is_active else f'left {self.left_at}'
        return f'{self.user.username} in {self.group.name} ({status})'
