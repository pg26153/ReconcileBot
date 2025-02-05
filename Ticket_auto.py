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
def get_sql_from_github(file_path="Recon.sql"):
    try:
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
    except requests.exceptions.RequestException as e:
        print(f"Error fetching file from GitHub: {e}")
        return None


# Function to execute the SQL script
def execute_reconciliation_sql(sql_content):
    try:
        if sql_content:
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
            return sql_queries
        else:
            print("No SQL query to execute. Exiting.")
            return None
    except pymysql.MySQLError as e:
        print(f"Error executing SQL query: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error executing SQL queries: {e}")
        return None


# Function to fetch the most recent unresolved failure from the reconciliation_failures table
def fetch_failure_details():
    try:
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )

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
    except pymysql.MySQLError as e:
        print(f"Error fetching failure details from database: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error fetching failure details: {e}")
        return None
    finally:
        if connection:
            connection.close()


# Function to partition SQL content and find the block for a specific failure message
def extract_sql_block_by_failure_message(sql_queries, failure_message):
    try:
        # Search for the failure_message in each SQL query block
        for sql_query in sql_queries:
            if failure_message in sql_query:
                return sql_query
        # Return None if no matching block is found
        return None
    except Exception as e:
        print(f"Error extracting SQL block: {e}")
        return None


def search_existing_jira_ticket(failure_message, cycle_date):
    try:
        summary = f"{cycle_date} - {failure_message}"
        url = f"{JIRA_URL}/rest/api/3/search"

        # Send GET request to search issues
        response = requests.get(url, headers=JIRA_HEADERS)

        if response.status_code == 200:
            issues = response.json().get("issues", [])
            if issues:
                for issue in issues:
                    issue_summary = issue['fields']['summary']
                    if summary == issue_summary:
                        return issue['key']
        else:
            print(f"Error searching for Jira tickets: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error searching Jira tickets: {e}")
        return None


# Function to create a Jira ticket
def create_jira_ticket(id, failure_message, failure_details, cycle_date, sql_query):
    try:
        url = f"{JIRA_URL}/rest/api/3/issue"

        # Check if the ticket already exists
        existing_ticket_key = search_existing_jira_ticket(failure_message, cycle_date)

        # If ticket already exists, skip ticket creation
        if existing_ticket_key:
            print(f"Ticket {existing_ticket_key} already exists. Skipping creation.")

            # Update failure ticket details in the database
            ticket_key = existing_ticket_key
            update_failure_ticket_details(id, ticket_key)
            return

        # Format the description using Atlassian Document Format (ADF)
        description = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Failure Details: {failure_details}\n\nFailure Message: {failure_message}"
                        }
                    ]
                }
            ]
        }

        payload = {
            "fields": {
                "project": {
                    "key": "KAN"  # Your Jira project key
                },
                "summary": f"{cycle_date} - {failure_message}",
                "description": description,
                "issuetype": {
                    "name": "Feature"  # Issue type "Feature"
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
    except requests.exceptions.RequestException as e:
        print(f"Error creating Jira ticket: {e}")
    except Exception as e:
        print(f"Unexpected error creating Jira ticket: {e}")


# Function to update failure ticket details in the database
def update_failure_ticket_details(id, ticket_key):
    try:
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )

        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE reconciliation_failures
                SET ticket=%s
                WHERE status = 'Unresolved'
                AND cycle_date = CURRENT_DATE
                AND id=%s;
            """, (ticket_key, id))  # Use parameterized queries to avoid SQL injection
            connection.commit()  # Make sure changes are saved
    except pymysql.MySQLError as e:
        print(f"Error updating failure ticket details in the database: {e}")
    except Exception as e:
        print(f"Unexpected error updating failure ticket details: {e}")
    finally:
        if connection:
            connection.close()


# Function to add a comment to the Jira ticket
def add_comment_to_jira_ticket(ticket_key, sql_query):
    try:
        url = f"{JIRA_URL}/rest/api/3/issue/{ticket_key}/comment"
        comment_payload = {
            "body": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": "SQL Query check:"
                            }
                        ]
                    },
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": "```"  # Code block start
                            }
                        ]
                    },
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": f"{sql_query}"  # The actual SQL query text
                            }
                        ]
                    },
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": "```"  # Code block end
                            }
                        ]
                    }
                ]
            }
        }

        # Send POST request to add a comment
        response = requests.post(url, headers=JIRA_HEADERS, data=json.dumps(comment_payload))

        if response.status_code == 201:
            print(f"Comment added to Jira ticket {ticket_key} successfully.")
        else:
            print(f"Error adding comment to Jira ticket: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Error adding comment to Jira ticket: {e}")
    except Exception as e:
        print(f"Unexpected error adding comment to Jira ticket: {e}")


# Main function to handle failure resolution
def handle_failure_resolution():
    try:
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
    except Exception as e:
        print(f"Unexpected error in failure resolution process: {e}")


if __name__ == "__main__":
    # Handle failure resolution by searching for failure messages and creating Jira tickets (or any other action)
    handle_failure_resolution()
