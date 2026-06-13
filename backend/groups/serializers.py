from django.contrib.auth.models import User
from rest_framework import serializers

from accounts.serializers import UserSerializer
from .models import Group, GroupMembership


class GroupMembershipSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = GroupMembership
        fields = ('id', 'user', 'joined_at', 'left_at', 'is_active')


class GroupSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    memberships = GroupMembershipSerializer(many=True, read_only=True)
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = ('id', 'name', 'description', 'created_by', 'memberships', 'member_count', 'created_at')
        read_only_fields = ('id', 'created_by', 'created_at')

    def get_member_count(self, obj):
        return obj.memberships.filter(is_active=True).count()


class GroupCreateSerializer(serializers.ModelSerializer):
    """Lightweight serializer for creating a group."""
    class Meta:
        model = Group
        fields = ('id', 'name', 'description')
        read_only_fields = ('id',)


class AddMemberSerializer(serializers.Serializer):
    username = serializers.CharField()
    joined_at = serializers.DateField()

    def validate_username(self, value):
        try:
            User.objects.get(username__iexact=value)
        except User.DoesNotExist:
            raise serializers.ValidationError(f'User "{value}" not found.')
        return value


class UpdateMembershipSerializer(serializers.Serializer):
    left_at = serializers.DateField(required=False, allow_null=True)
    is_active = serializers.BooleanField(required=False)
