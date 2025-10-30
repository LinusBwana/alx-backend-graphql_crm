# Celery Task for Generating CRM Reports

## Objective
This task configures a **Celery** job (with **Celery Beat**) that runs weekly to generate a CRM summary report using the GraphQL schema.  
The report logs:
- Total number of customers  
- Total number of orders  
- Total revenue (sum of all order totals)

All reports are written to `/tmp/crm_report_log.txt`.

---

## Setup Instructions

### Install Dependencies
Ensure the following packages are added to your `requirements.txt`:

```
celery
django-celery-beat
redis
requests
gql
```

Then install them:

```bash
pip install -r requirements.txt
```

---

### Add to `INSTALLED_APPS`
In `crm/settings.py`, add:

```python
INSTALLED_APPS = [
    ...,
    'django_celery_beat',
]
```

---

### Configure Celery
Create a new file **`crm/celery.py`**:

```python
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm.settings')

app = Celery('crm')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
```

Update **`crm/__init__.py`**:

```python
from .celery import app as celery_app

__all__ = ('celery_app',)
```

---

### Configure Celery and Redis in Settings
Add this to **`crm/settings.py`**:

```python
from celery.schedules import crontab

CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

CELERY_BEAT_SCHEDULE = {
    'generate-crm-report': {
        'task': 'crm.tasks.generate_crm_report',
        'schedule': crontab(day_of_week='mon', hour=6, minute=0),
    },
}
```

---

### Create Celery Task
In **`crm/tasks.py`**:

```python
import requests
from celery import shared_task
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
from datetime import datetime


@shared_task
def generate_crm_report():
    '''Generates a weekly CRM report and logs it.'''
    log_file = "/tmp/crm_report_log.txt"

    transport = RequestsHTTPTransport(
        url="http://localhost:8000/graphql/",
        verify=False,
        retries=3,
    )
    client = Client(transport=transport, fetch_schema_from_transport=True)

    query = gql("""
    query {
        allCustomers {
            id
        }
        allOrders {
            id
            totalAmount
        }
    }
    """)

    try:
        result = client.execute(query)
        customers = result.get("allCustomers", [])
        orders = result.get("allOrders", [])
        total_customers = len(customers)
        total_orders = len(orders)
        total_revenue = sum(float(o.get("totalAmount", 0)) for o in orders)

        report_line = (
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - "
            f"Report: {total_customers} customers, {total_orders} orders, {total_revenue} revenue\n"
        )
    except Exception as e:
        report_line = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Report generation failed: {e}\n"

    with open(log_file, "a") as f:
        f.write(report_line)
```

---

### Start Redis Server
Make sure Redis is running locally.

- **Windows (using WSL or Docker):**
  ```bash
  redis-server
  ```
- **Ubuntu / macOS:**
  ```bash
  sudo service redis-server start
  ```

---

### Run Migrations
```bash
python manage.py migrate
```

---

### Start Celery and Celery Beat
Run the following commands in separate terminals:

```bash
celery -A crm worker -l info
```

```bash
celery -A crm beat -l info
```

---

### Verify Output
After the scheduled time (Monday 6:00 AM), check the log file:

```bash
cat /tmp/crm_report_log.txt
```

Expected format:
```
2025-10-30 06:00:00 - Report: 10 customers, 45 orders, 12500.0 revenue
```

---

## Summary
| Component | Purpose |
|------------|----------|
| **Celery** | Executes asynchronous and scheduled tasks |
| **Celery Beat** | Manages periodic task scheduling |
| **Redis** | Acts as broker and backend for Celery |
| **generate_crm_report** | Queries GraphQL API and logs CRM report |
| **/tmp/crm_report_log.txt** | Stores weekly report logs |

---
