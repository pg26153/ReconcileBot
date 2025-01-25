import requests
import pymysql
import base64
import json

# GitHub API details
GITHUB_TOKEN = "YOUR_GITHUB_TOKEN"  # GitHub Personal Access Token
GITHUB_OWNER = "YOUR_GITHUB_USERNAME"      # GitHub Username
GITHUB_REPO = "YOUR_GITHUB_REPO"           # GitHub Repository Name
GITHUB_API_URL = "https://api.github.com"
HEADERS = {"Authorization": f"Bearer {GITHUB_TOKEN}"}

# Jira API details
JIRA_URL = "https://your-domain.atlassian.net"  # Replace with your Jira URL
JIRA_USER = "your-email@example.com"            # Your Jira username (email)
JIRA_API_TOKEN = "YOUR_JIRA_API_TOKEN"          # Your Jira API token
JIRA_HEADERS = {
    "Authorization": f"Basic {base64.b64encode(f'{JIRA_USER}:{JIRA_API_TOKEN}'.encode()).decode()}",
    "Content-Type": "application/json"
}

# Database connection details
DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = 'YOUR_DATABASE_PASSWORD'
DB_NAME = 'sakila'

# Function to fetch SQL script from GitHub
def get_sql_from_github(file_path="tes_folder/scripts/reconciliation.sql"):
    search_url = f"{GITHUB_API_URL}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{file_path}"
    response = requests.get(search_url, headers=HEADERS)

    if response.status_code == 200:
        file_data = response.json()

        if 'content' in file_data and file_data['encoding'] == 'base64':
            decoded_content = base64.b64decode(file_data['content']).decode('utf-8')
            print("SQL file fetched successfully.")
            return decoded_content
        else:
            print("No base64 encoded content found.")
            return None
    else:
        print(f"Error fetching file: {response.status_code} - {response.text}")
        return None

# Function to execute the SQL script
def execute_reconciliation_sql(sql_content):
    if sql_content:
        try:
            # Split the SQL content into individual queries by semicolon
            sql_queries = [query.strip() for query in sql_content.split(';') if query.strip()]
            
            connection = pymysql.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME
            )
            
            with connection.cursor() as cursor:
                for sql_query in sql_queries:
                    cursor.execute(sql_query)  # Execute each SQL query individually
                connection.commit()  # Commit the transaction
                print("SQL queries executed successfully.")
        except pymysql.MySQLError as e:
            print(f"Error executing SQL query: {e}")
        finally:
            connection.close()
            return sql_queries
    else:
        print("No SQL query to execute. Exiting.")

# Function to fetch the most recent unresolved failure from the reconciliation_failures table
def fetch_failure_details():
    connection = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, failure_message, failure_details, cycle_date
                FROM reconciliation_failures
                WHERE status = 'Unresolved'
                AND cycle_date = CURRENT_DATE;
            """)
            result = cursor.fetchall()
            
            if result:
                return result
            else:
                print("No unresolved failures found in the database.")
                return None
    finally:
        connection.close()

# Function to partition SQL content and find the block for a specific failure message
def extract_sql_block_by_failure_message(sql_queries, failure_message):
    # Search for the failure_message in each SQL query block
    for sql_query in sql_queries:
        if failure_message in sql_query:
            return sql_query

    # Return None if no matching block is found
    return None

# Function to create a Jira ticket
def create_jira_ticket(id, failure_message, failure_details, cycle_date, sql_query):
    url = f"{JIRA_URL}/rest/api/3/issue"
    payload = {
        "fields": {
            "project": {
                "key": "YOUR_PROJECT_KEY"  # Replace with your Jira project key
            },
            "summary": f"{cycle_date} - {failure_message}",
            "description": f"Failure Details: {failure_details}\n\n{failure_message}",
            "issuetype": {
                "name": "Bug"  # Or "Task" or any other issue type you use in Jira
            }
        }
    }

    # Send POST request to create the Jira issue
    response = requests.post(url, headers=JIRA_HEADERS, data=json.dumps(payload))

    if response.status_code == 201:
        print(f"Jira ticket created successfully: {response.json()['key']}")
        
        # Update failure ticket details in the database
        ticket_key = response.json()['key']
        update_failure_ticket_details(id, ticket_key)

        # Add a comment to the Jira ticket
        add_comment_to_jira_ticket(ticket_key, sql_query)
        
    else:
        print(f"Error creating Jira ticket: {response.status_code} - {response.text}")

# Function to update failure ticket details in the database
def update_failure_ticket_details(id, ticket_key):
    connection = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE reconciliation_failures
                SET ticket=%s
                WHERE status = 'Unresolved'
                AND cycle_date = CURRENT_DATE
                AND id=%s;
            """, (ticket_key, id))  # Use parameterized queries to avoid SQL injection
            connection.commit()  # Make sure changes are saved
    finally:
        connection.close()

# Function to add a comment to the Jira ticket
def add_comment_to_jira_ticket(ticket_key, sql_query):
    url = f"{JIRA_URL}/rest/api/3/issue/{ticket_key}/comment"
    comment_payload = {
        "body": f"SQL Query for Failure Resolution:\n{sql_query}"
    }

    # Send POST request to add a comment
    response = requests.post(url, headers=JIRA_HEADERS, data=json.dumps(comment_payload))

    if response.status_code == 201:
        print(f"Comment added to Jira ticket {ticket_key} successfully.")
    else:
        print(f"Error adding comment to Jira ticket: {response.status_code} - {response.text}")


# Main function to handle failure resolution
def handle_failure_resolution():
    
    # Step 1: Fetch the SQL content from GitHub or another source, which will be used for failure resolution
    sql_content = get_sql_from_github()

    # Step 2: Execute the reconciliation SQL based on the fetched content
    sql_queries = execute_reconciliation_sql(sql_content)

    # Step 3: Fetch the most recent unresolved failure records from the database
    result = fetch_failure_details()

    if result:
        # Step 4: Process each failure record
        for id, failure_message, failure_details, cycle_date in result:

            # Check if failure message and failure details are available for the record
            if failure_message and failure_details:
                
                # Step 5: Extract the corresponding SQL block from the SQL content based on failure message
                sql_query = extract_sql_block_by_failure_message(sql_queries, failure_message)
                
                if sql_query:
                    # Step 6: Create a Jira ticket for the failure
                    create_jira_ticket(id, failure_message, failure_details, cycle_date, sql_query)
                else:
                    # Log if no SQL block is found for the given failure message
                    print(f"No SQL block found for failure message: {failure_message}")
            else:
                # Log if there are no unresolved failure details
                print("No unresolved failure details available. Exiting.")
    else:
        # Log if no unresolved failures are found in the database
        print("No unresolved failures found in the database.")

if __name__ == "__main__":
    # Handle failure resolution by searching for failure messages and creating Jira tickets (or any other action)
    handle_failure_resolution()
