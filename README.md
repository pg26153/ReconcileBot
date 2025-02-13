# ReconcileBot

### Presentation : https://github.com/pg26153/ReconcileBot/blob/main/Presentation.pptx

## Overview

**ReconcileBot** is an automated tool designed to handle reconciliation failures, execute SQL scripts, and generate Jira tickets for unresolved failures. The bot fetches reconciliation SQL queries from a GitHub repository, executes them on a MySQL database, identifies unresolved failures, and creates Jira tickets to track and resolve these issues. It also updates the database with the Jira ticket information and associates the SQL queries with the corresponding Jira tickets.

## Features

- Fetch reconciliation SQL scripts from a GitHub repository.
- Execute SQL queries on a MySQL database.
- Identify unresolved reconciliation failures from the database.
- Automatically create Jira tickets for each unresolved failure.
- Attach the relevant SQL query to the Jira ticket as a comment.
- Update the database with Jira ticket keys for tracking the status of failures.
- Includes checks to prevent the creation of duplicate Jira tickets for the same failure.

## Prerequisites

Before you begin, ensure you have the following:

1. **Python 3.x**
2. **GitHub Personal Access Token**
3. **Jira API Token**
4. **MySQL Database**

## Installation

1. **Clone the Repository**:

git clone https://github.com/pg26153/reconcilebot.git

2. **Create a Virtual Environment**

```bash
python -m venv venv
```
3. **Activate the Virtual Environment**

Once the virtual environment is created, activate it:

```bash
.\venv\Scripts\activate
```
4. **Install Dependencies**:

Install the required Python libraries listed in the `requirements.txt` file:
```bash
pip install -r requirements.txt
```

5. **Configure the Application**:

Update the configuration variables in the script (`reconcilebot.py`) with your GitHub, Jira, and MySQL tokens.

## Configuration

Before running the script, update the following configuration values:

### GitHub Configuration:
- `GITHUB_TOKEN`: Your GitHub Personal Access Token.
- `GITHUB_OWNER`: Your GitHub username.
- `GITHUB_REPO`: The name of your GitHub repository containing the SQL scripts.

### Jira Configuration:
- `JIRA_URL`: Your Jira instance URL (e.g., `https://your-domain.atlassian.net`).
- `JIRA_USER`: Your Jira username (email address).
- `JIRA_API_TOKEN`: Your Jira API token.
- `JIRA_PROJECT_KEY`: The key of your Jira project.

### MySQL Database Configuration:
- `DB_HOST`: The host address of your MySQL database.
- `DB_USER`: Your MySQL username.
- `DB_PASSWORD`: Your MySQL password.
- `DB_NAME`: The name of the MySQL database (e.g., `sakila`).

6. To run **ReconcileBot**, simply execute the Python script:

```bash
python reconcilebot.py
```

## How It Works

**ReconcileBot** automates the process of resolving reconciliation failures by interacting with GitHub, MySQL, and Jira. Here's a step-by-step breakdown of what happens when you run the bot:

1. **Fetch SQL Script**:
   - The bot connects to a specified GitHub repository and fetches the required SQL script (e.g., `reconciliation.sql`) that contains the necessary reconciliation queries.
   - The SQL script is fetched in base64-encoded format from the GitHub repository, decoded, and stored for execution.

2. **Execute SQL Queries**:
   - The SQL queries retrieved from GitHub are executed sequentially on the connected MySQL database. Each query aims to process and handle reconciliation data or perform necessary actions.
   - If any SQL queries result in failure messages, those are captured for further investigation.

3. **Identify Unresolved Failures**:
   - The bot checks the `reconciliation_failures` table in the connected MySQL database to identify any unresolved reconciliation failures. 
   - The table contains records of failures that still need to be addressed, and the bot looks for entries marked as "unresolved" with the current date.
   - The bot performs checks to ensure no duplicate tickets are created for the same failure by verifying if a similar ticket already exists in Jira.

4. **Create Jira Tickets**:
   - For each unresolved failure found in the database, the bot creates a Jira ticket. The ticket is populated with the failure message, failure details, and cycle date.
   - The Jira ticket is created via the Jira API, using your Jira credentials and project key.

5. **Link SQL Queries**:
   - After the Jira ticket is created, the bot adds the relevant SQL query that caused the failure as a comment on the Jira ticket. This helps the team investigating the issue to quickly review the SQL logic involved in the failure.
   - The SQL query is embedded in the comment for easy access and reference.

6. **Update Database**:
   - Once the Jira ticket is successfully created, the bot updates the `reconciliation_failures` table in the MySQL database by adding the Jira ticket key to the corresponding failure record.
   - This update marks the failure as linked to a Jira ticket, helping to track the resolution status and making it easier for teams to monitor and address the issue in the future.
   - Also if a ticket is resolved, it is then updated in DB.

By automating this workflow, **ReconcileBot** saves time, ensures proper tracking of failure issues, and helps teams manage reconciliation failures more efficiently.

### 🤝 **Contribution**

We welcome contributions from the community! Feel free to fork the repository, submit issues, or create pull requests. When contributing, please ensure:

- **Thorough Testing**: New features should be fully tested before submission.
- **Documentation**: Any code changes should be accompanied by clear documentation.
- **Clear Descriptions**: Provide a detailed explanation of the problem being solved and how your contribution addresses it.

Together, we can make this tool even better! Happy coding! 🚀
