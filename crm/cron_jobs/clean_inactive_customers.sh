#!/bin/bash

# Absolute path to your Django project root
PROJECT_DIR="/home/alx-backend-graphql_crm"

# source "$PROJECT_DIR/venv/bin/activate"

# Get the count of deleted customers and log it
deleted_count=$(python3 "$PROJECT_DIR/manage.py" shell -c "
from django.utils import timezone
from datetime import timedelta
from crm.models import Customer
one_year_ago = timezone.now() - timedelta(days=365)
deleted, _ = Customer.objects.filter(orders__order_date__lt=one_year_ago).delete()
print(deleted)
")

# Log the result with a timestamp
timestamp=$(date '+%Y-%m-%d %H:%M:%S')
echo \"[$timestamp] Deleted customers: $deleted_count\" >> /tmp/customer_cleanup_log.txt
