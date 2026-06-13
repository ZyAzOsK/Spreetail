from django.contrib import admin
from .models import ImportReport, ImportAnomaly


@admin.register(ImportReport)
class ImportReportAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'group', 'imported_by', 'status', 'total_rows', 'anomaly_count', 'imported_at')
    list_filter = ('status', 'group')


@admin.register(ImportAnomaly)
class ImportAnomalyAdmin(admin.ModelAdmin):
    list_display = ('import_report', 'row_number', 'anomaly_type', 'severity', 'resolution')
    list_filter = ('anomaly_type', 'severity', 'resolution')
    search_fields = ('description',)
