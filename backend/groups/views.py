from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Group, GroupMembership
from .serializers import (
    GroupSerializer, GroupCreateSerializer,
    AddMemberSerializer, UpdateMembershipSerializer
)


def get_user_group(request, group_id):
    """Helper: return group if current user is a member, else None."""
    try:
        group = Group.objects.get(id=group_id)
        if not group.memberships.filter(user=request.user, is_active=True).exists():
            return None, Response(
                {'detail': 'You are not a member of this group.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return group, None
    except Group.DoesNotExist:
        return None, Response({'detail': 'Group not found.'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def group_list_create(request):
    """
    GET  /api/groups/        — list all groups the user belongs to
    POST /api/groups/        — create a new group (creator is auto-added as member)
    """
    if request.method == 'GET':
        memberships = request.user.group_memberships.filter(is_active=True).select_related('group')
        groups = [m.group for m in memberships]
        return Response(GroupSerializer(groups, many=True).data)

    # POST — create group
    serializer = GroupCreateSerializer(data=request.data)
    if serializer.is_valid():
        group = serializer.save(created_by=request.user)
        # Auto-add creator as founding member
        GroupMembership.objects.create(
            group=group,
            user=request.user,
            joined_at=timezone.now().date(),
            is_active=True,
        )
        return Response(GroupSerializer(group).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def group_detail(request, group_id):
    """
    GET    /api/groups/<id>/   — group detail with all members
    PATCH  /api/groups/<id>/   — update group name/description (creator only)
    DELETE /api/groups/<id>/   — delete group (creator only)
    """
    group, err = get_user_group(request, group_id)
    if err:
        return err

    if request.method == 'GET':
        return Response(GroupSerializer(group).data)

    # Only creator can modify/delete
    if group.created_by != request.user:
        return Response({'detail': 'Only the group creator can modify this group.'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'PATCH':
        serializer = GroupCreateSerializer(group, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(GroupSerializer(group).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'DELETE':
        group.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_member(request, group_id):
    """
    POST /api/groups/<id>/members/
    Add a user to a group with a specific join date.
    """
    group, err = get_user_group(request, group_id)
    if err:
        return err

    serializer = AddMemberSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    username = serializer.validated_data['username']
    joined_at = serializer.validated_data['joined_at']

    try:
        user_to_add = User.objects.get(username__iexact=username)
    except User.DoesNotExist:
        return Response({'detail': f'User "{username}" not found.'}, status=status.HTTP_404_NOT_FOUND)

    # Check if already an active member
    if group.memberships.filter(user=user_to_add, is_active=True).exists():
        return Response({'detail': f'{username} is already an active member.'}, status=status.HTTP_400_BAD_REQUEST)

    # Re-activate if previously left, otherwise create new membership
    existing = group.memberships.filter(user=user_to_add).order_by('-joined_at').first()
    if existing and not existing.is_active:
        existing.is_active = True
        existing.left_at = None
        existing.joined_at = joined_at
        existing.save()
        membership = existing
    else:
        membership = GroupMembership.objects.create(
            group=group,
            user=user_to_add,
            joined_at=joined_at,
            is_active=True,
        )

    from .serializers import GroupMembershipSerializer
    return Response(GroupMembershipSerializer(membership).data, status=status.HTTP_201_CREATED)


@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def update_membership(request, group_id, membership_id):
    """
    PATCH  /api/groups/<id>/members/<mid>/  — set left_at date (member leaving)
    DELETE /api/groups/<id>/members/<mid>/  — remove member entirely
    """
    group, err = get_user_group(request, group_id)
    if err:
        return err

    try:
        membership = group.memberships.get(id=membership_id)
    except GroupMembership.DoesNotExist:
        return Response({'detail': 'Membership not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'PATCH':
        serializer = UpdateMembershipSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if 'left_at' in serializer.validated_data:
            membership.left_at = serializer.validated_data['left_at']
            membership.is_active = False
            membership.save()

        from .serializers import GroupMembershipSerializer
        return Response(GroupMembershipSerializer(membership).data)

    if request.method == 'DELETE':
        membership.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
