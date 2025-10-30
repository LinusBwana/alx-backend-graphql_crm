from datetime import datetime
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport


def log_crm_heartbeat():
    """Logs a heartbeat message and checks GraphQL endpoint responsiveness."""
    log_file = "/tmp/crm_heartbeat_log.txt"

    # Define the GraphQL transport
    transport = RequestsHTTPTransport(
        url="http://localhost:8000/graphql/",  # Adjust if your GraphQL endpoint is different
        verify=False,
        retries=3,
    )

    # Create the GraphQL client
    client = Client(transport=transport, fetch_schema_from_transport=True)

    # Define a simple query (the hello field)
    query = gql("""
    query {
        hello
    }
    """)

    try:
        # Execute the query
        result = client.execute(query)
        message = f"{datetime.now().strftime('%d/%m/%Y-%H:%M:%S')} - Heartbeat success: {result.get('hello')}\n"
    except Exception as e:
        # Log error if the GraphQL request fails
        message = f"{datetime.now().strftime('%d/%m/%Y-%H:%M:%S')} - Heartbeat failed: {e}\n"

    # Append the message to the log file
    with open(log_file, "a") as f:
        f.write(message)


def update_low_stock():
    """Executes a GraphQL mutation to update low-stock products and logs results."""
    log_file = "/tmp/low_stock_updates_log.txt"

    # Define the GraphQL transport
    transport = RequestsHTTPTransport(
        url="http://localhost:8000/graphql/",  # Adjust if needed
        verify=False,
        retries=3,
    )

    # Create the GraphQL client
    client = Client(transport=transport, fetch_schema_from_transport=True)

    # Define the mutation
    mutation = gql("""
    mutation {
        updateLowStockProducts {
            success
            message
            updatedProducts {
                id
                name
                stock
            }
        }
    }
    """)

    try:
        # Execute the mutation
        result = client.execute(mutation)
        response = result.get("updateLowStockProducts", {})
        message = response.get("message", "No message")
        products = response.get("updatedProducts", [])

        # Format log entry
        log_entry = f"{datetime.now().strftime('%d/%m/%Y-%H:%M:%S')} - {message}\n"
        for p in products:
            log_entry += f"   → {p['name']} restocked to {p['stock']}\n"

    except Exception as e:
        # Handle GraphQL or connection errors
        log_entry = f"{datetime.now().strftime('%d/%m/%Y-%H:%M:%S')} - Low stock update failed: {e}\n"

    # Append to the log file
    with open(log_file, "a") as f:
        f.write(log_entry)
