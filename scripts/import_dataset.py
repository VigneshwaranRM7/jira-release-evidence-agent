#!/usr/bin/env python
import os
import sys
import argparse

# Add workspace root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from definitions import DATA_DIR
from controllers.v1.jira.bulk_importer import JiraBulkImporter
from controllers.v1.jira.mock_client import MockJiraClient
from controllers.v1.jira.cloud_client import JiraCloudClient
from utils.context import settings

def main():
    parser = argparse.ArgumentParser(description="Repeatable Jira Bulk Importer for Dataset")
    parser.add_argument("--file", default=os.path.join(DATA_DIR, "dataset.json"), help="Path to dataset.json")
    parser.add_argument("--project", default="REL", help="Jira Project Key")
    parser.add_argument("--mock", action="store_true", help="Force in-memory mock client even if cloud credentials exist")
    args = parser.parse_args()

    print(f"=== Jira Dataset Bulk Importer ===")
    print(f"Dataset File: {args.file}")
    print(f"Project Key:  {args.project}")

    if not os.path.exists(args.file):
        print(f"Error: Dataset file not found at {args.file}")
        sys.exit(1)

    if not args.mock and settings.JIRA_BASE_URL and settings.JIRA_API_TOKEN:
        print(f"Connecting to Jira Cloud at: {settings.JIRA_BASE_URL} ({settings.JIRA_USER_EMAIL})")
        client = JiraCloudClient(
            base_url=settings.JIRA_BASE_URL,
            user_email=settings.JIRA_USER_EMAIL,
            api_token=settings.JIRA_API_TOKEN
        )
    else:
        print("Using High-Performance In-Memory Mock Jira Client")
        client = MockJiraClient()

    importer = JiraBulkImporter(client=client)
    stats = importer.import_from_json(args.file, project_key=args.project)

    print("\n--- Import Summary ---")
    print(f"Issues Created:   {stats.get('issues_created', 0)}")
    print(f"Comments Created: {stats.get('comments_created', 0)}")
    print(f"Links Created:    {stats.get('links_created', 0)}")
    print("Bulk import completed successfully.")

if __name__ == "__main__":
    main()

