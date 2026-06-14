import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test.client import RequestFactory
from django.core.files.uploadedfile import SimpleUploadedFile
from groups.models import Group, GroupMembership
from importer.views import upload_csv, finalize_import
from django.contrib.auth.models import User
from datetime import date

Group.objects.all().delete()
User.objects.all().delete()

# Aisha creates the group today
u1, _ = User.objects.get_or_create(username='Aisha')
group, _ = Group.objects.get_or_create(name='Test Group', created_by=u1)
GroupMembership.objects.create(group=group, user=u1, joined_at=date(2026, 6, 15), is_active=True)

# Add Sam today
u2, _ = User.objects.get_or_create(username='Sam')
GroupMembership.objects.create(group=group, user=u2, joined_at=date(2026, 6, 15), is_active=True)

csv_content = """date,description,paid_by,amount,currency,split_type,split_with,split_details,notes
10-04-2026,Housewarming drinks,Sam,3100,INR,equal,Aisha;Sam,,
15-02-2026,Past Expense,Aisha,100,INR,equal,Aisha;NewGuy,,
"""

file = SimpleUploadedFile('test.csv', csv_content.encode('utf-8'), content_type='text/csv')

factory = RequestFactory()
request = factory.post(f'/api/import/{group.id}/upload/', {'file': file})
request.user = u1

response = upload_csv(request, group.id)
data = response.data
report_id = data['report_id']
print("UPLOAD ROW DECISIONS:", [(r['row_number'], r['is_valid'], [a['anomaly_type'] for a in r['anomalies']]) for r in data['rows']])

row_decisions = {r['row_number']: 'import' for r in data['rows']}

request = factory.post(f'/api/import/{group.id}/reports/{report_id}/finalize/', {'row_decisions': row_decisions}, content_type='application/json')
request.user = u1
request.data = {'row_decisions': row_decisions}

response = finalize_import(request, group.id, report_id)
print("FINALIZE:", response.data)

for m in group.memberships.all():
    print(f"Member: {m.user.username}, Joined: {m.joined_at}")
