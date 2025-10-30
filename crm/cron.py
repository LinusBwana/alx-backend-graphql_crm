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
