from django.urls import path
from . import views

app_name = 'groups'

urlpatterns = [
    path('', views.group_list_create, name='group_list_create'),
    path('<int:group_id>/', views.group_detail, name='group_detail'),
    path('<int:group_id>/members/', views.add_member, name='add_member'),
    path('<int:group_id>/members/<int:membership_id>/', views.update_membership, name='update_membership'),
]
