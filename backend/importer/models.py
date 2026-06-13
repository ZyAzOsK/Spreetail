from django.db import models
from django.contrib.auth.models import User


class ImportReport(models.Model):
    """
    A record of a CSV import operation.
    Tracks how many rows were processed, how many anomalies found,
    and the overall status of the import.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('in_review', 'In Review'),
        ('completed', 'Completed'),
        ('partial', 'Partially Imported'),
        ('cancelled', 'Cancelled'),
    ]

    group = models.ForeignKey(
        'groups.Group', on_delete=models.CASCADE, related_name='import_reports'
    )
    imported_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='imports'
    )
    file_name = models.CharField(max_length=255)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending'
    )
    total_rows = models.IntegerField(default=0)
    successful_rows = models.IntegerField(default=0)
    skipped_rows = models.IntegerField(default=0)
    anomaly_count = models.IntegerField(default=0)

    # Store the raw CSV content for reference
    raw_csv_content = models.TextField(blank=True, default='')

    imported_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-imported_at']

    def __str__(self):
        return f'Import {self.file_name} ({self.status}) - {self.imported_at.strftime("%Y-%m-%d %H:%M")}'


class ImportAnomaly(models.Model):
    """
    A single data problem detected during CSV import.
    Each anomaly is surfaced to the user for review.
    
    Resolution flow:
    1. Detected during parsing → status='detected'
    2. User reviews → status changes to 'approved', 'modified', or 'skipped'
    3. Applied during import finalization
    """
    ANOMALY_TYPE_CHOICES = [
        ('duplicate', 'Duplicate Entry'),
        ('missing_field', 'Missing Required Field'),
        ('format_error', 'Format Error'),
        ('math_error', 'Mathematical Error'),
        ('name_mismatch', 'Name Mismatch/Variant'),
        ('date_error', 'Date Format Error'),
        ('negative_amount', 'Negative Amount'),
        ('zero_amount', 'Zero Amount'),
        ('membership_violation', 'Membership Violation'),
        ('misclassification', 'Misclassified Entry'),
        ('conflicting_data', 'Conflicting Data'),
        ('rounding', 'Rounding Issue'),
        ('currency_missing', 'Missing Currency'),
        ('other', 'Other'),
    ]

    RESOLUTION_CHOICES = [
        ('pending', 'Pending Review'),
        ('auto_fixed', 'Auto-Fixed'),
        ('user_approved', 'User Approved'),
        ('user_modified', 'User Modified'),
        ('skipped', 'Skipped'),
    ]

    SEVERITY_CHOICES = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ]

    import_report = models.ForeignKey(
        ImportReport, on_delete=models.CASCADE, related_name='anomalies'
    )
    row_number = models.IntegerField(
        help_text='CSV row number (1-indexed, including header)'
    )
    anomaly_type = models.CharField(max_length=30, choices=ANOMALY_TYPE_CHOICES)
    severity = models.CharField(
        max_length=10, choices=SEVERITY_CHOICES, default='warning'
    )
    field_name = models.CharField(
        max_length=50, blank=True, default='',
        help_text='The CSV column where the anomaly was found'
    )
    description = models.TextField(
        help_text='Human-readable description of the problem'
    )
    original_value = models.TextField(
        blank=True, default='',
        help_text='The original value from the CSV'
    )
    suggested_value = models.TextField(
        blank=True, default='',
        help_text='The suggested corrected value'
    )
    suggested_action = models.TextField(
        blank=True, default='',
        help_text='Description of the suggested resolution'
    )

    # Resolution
    resolution = models.CharField(
        max_length=20, choices=RESOLUTION_CHOICES, default='pending'
    )
    resolved_value = models.TextField(
        blank=True, default='',
        help_text='The final value after user review'
    )
    user_notes = models.TextField(
        blank=True, default='',
        help_text='Notes added by user during review'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['row_number', 'created_at']
        verbose_name_plural = 'Import anomalies'

    def __str__(self):
        return f'Row {self.row_number}: {self.anomaly_type} - {self.description[:50]}'
