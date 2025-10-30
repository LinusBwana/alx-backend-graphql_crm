import requests
from celery import shared_task
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
from datetime import datetime

@shared_task
def generate_crm_report():
    """Generates a weekly CRM report and logs it."""
    log_file = "/tmp/crm_report_log.txt"

    # Setup GraphQL transport
    transport = RequestsHTTPTransport(
        url="http://localhost:8000/graphql/",
        verify=False,
        retries=3,
    )
    client = Client(transport=transport, fetch_schema_from_transport=True)

    # GraphQL query to get total customers, orders, and revenue
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
