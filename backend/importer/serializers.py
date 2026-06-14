from rest_framework import serializers
from .models import ImportReport, ImportAnomaly


class ImportAnomalySerializer(serializers.ModelSerializer):
    class Meta:
        model = ImportAnomaly
        fields = (
            'id', 'row_number', 'anomaly_type', 'severity',
            'field_name', 'description', 'original_value',
            'suggested_value', 'suggested_action',
            'resolution', 'resolved_value', 'user_notes',
            'created_at', 'resolved_at',
        )
        read_only_fields = ('id', 'created_at')


class ImportReportSerializer(serializers.ModelSerializer):
    imported_by_username = serializers.CharField(
        source='imported_by.username', read_only=True
    )
    pending_anomalies = serializers.SerializerMethodField()

    class Meta:
        model = ImportReport
        fields = (
            'id', 'group', 'imported_by_username', 'file_name',
            'status', 'total_rows', 'successful_rows', 'skipped_rows',
            'anomaly_count', 'pending_anomalies', 'imported_at', 'completed_at',
        )
        read_only_fields = fields

    def get_pending_anomalies(self, obj):
        return obj.anomalies.filter(resolution='pending').count()
