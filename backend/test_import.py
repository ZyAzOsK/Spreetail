import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test.client import RequestFactory
from django.core.files.uploadedfile import SimpleUploadedFile
from groups.models import Group
from importer.views import upload_csv, finalize_import
from django.contrib.auth.models import User

# Ensure users exist with correct dates
users_data = [
    ('Aisha', '2026-01-01', None),
    ('Rohan', '2026-01-01', None),
    ('Priya', '2026-01-01', None),
    ('Meera', '2026-01-01', '2026-03-31'),
    ('Dev', '2026-01-01', None),
    ('Sam', '2026-04-08', None),
]

for username, joined, left in users_data:
    u, _ = User.objects.get_or_create(username=username)

group, _ = Group.objects.get_or_create(name='Test Group')
for username, joined, left in users_data:
    u = User.objects.get(username=username)
    group.memberships.update_or_create(
        user=u, 
        defaults={'joined_at': joined, 'left_at': left, 'is_active': not bool(left)}
    )

factory = RequestFactory()

csv_content = open('../Expenses Export.csv', 'rb').read()
file = SimpleUploadedFile('Expenses Export.csv', csv_content, content_type='text/csv')

request = factory.post('/api/import/1/upload/', {'file': file})
request.user = User.objects.get(username='Aisha')

response = upload_csv(request, group.id)
print("Upload Response:", response.status_code)
data = response.data
print(f"Total: {data['total_rows']}, Auto-OK: {data['auto_ok']}, Needs Review: {data['needs_review']}")

report_id = data['report_id']

# Simulate user accepting all auto-decisions
row_decisions = {}
for r in data['rows']:
    if not r['skip']:
        row_decisions[r['row_number']] = 'settlement' if r['is_settlement'] else ('import' if r['is_valid'] else 'skip')

print(f"Finalizing with decisions: {row_decisions}")
request = factory.post(f'/api/import/1/reports/{report_id}/finalize/', {'row_decisions': row_decisions}, content_type='application/json')
request.user = User.objects.get(username='Aisha')
request.data = {'row_decisions': row_decisions}

response = finalize_import(request, group.id, report_id)
print("Finalize Response:", response.status_code)
print(response.data)
