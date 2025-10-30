#!/usr/bin/env python3
import datetime
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

# GraphQL endpoint
GRAPHQL_URL = "http://localhost:8000/graphql"

def get_recent_orders():
    """Fetch pending orders created within the last 7 days."""
    transport = RequestsHTTPTransport(url=GRAPHQL_URL, verify=False)
    client = Client(transport=transport, fetch_schema_from_transport=True)

    # Date 7 days ago
    seven_days_ago = (datetime.datetime.now() - datetime.timedelta(days=7)).date().isoformat()

    # GraphQL query
    query = gql("""
        query GetRecentOrders($startDate: Date!) {
            orders(filter: { order_date_Gte: $startDate, status: "PENDING" }) {
                id
                customer {
                    email
                }
                order_date
            }
        }
    """)

    variables = {"startDate": seven_days_ago}
    result = client.execute(query, variable_values=variables)
    return result.get("orders", [])

def log_reminders(orders):
    """Log each order reminder with timestamp."""
    log_path = "/tmp/order_reminders_log.txt"
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(log_path, "a") as log_file:
        for order in orders:
            log_entry = f"[{now}] Order ID: {order['id']}, Email: {order['customer']['email']}\n"
            log_file.write(log_entry)

def main():
    orders = get_recent_orders()
    if orders:
        log_reminders(orders)
    print("Order reminders processed!")

if __name__ == "__main__":
    main()
