from django.urls import path
from . import views

app_name = 'importer'

urlpatterns = [
    # Step 1: Upload CSV
    path('<int:group_id>/upload/', views.upload_csv, name='upload_csv'),

    # List past imports for a group
    path('<int:group_id>/reports/', views.list_reports, name='list_reports'),

    # Step 2: Get report for review
    path('<int:group_id>/reports/<int:report_id>/', views.get_report, name='get_report'),

    # Step 3: Resolve individual anomaly
    path(
        '<int:group_id>/reports/<int:report_id>/anomalies/<int:anomaly_id>/',
        views.resolve_anomaly,
        name='resolve_anomaly',
    ),

    # Bulk approve auto-fixed anomalies
    path(
        '<int:group_id>/reports/<int:report_id>/approve-auto/',
        views.resolve_all_auto,
        name='resolve_all_auto',
    ),

    # Step 4: Finalize import
    path(
        '<int:group_id>/reports/<int:report_id>/finalize/',
        views.finalize_import,
        name='finalize_import',
    ),
]
