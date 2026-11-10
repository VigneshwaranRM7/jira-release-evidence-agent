import json
import time
import re
from typing import Dict, Any, List, Optional
from controllers.v1.jira.base_client import BaseJiraClient
from models.v1.jira.dataset import DatasetPayload, DatasetRecord
from utils.text_parser import parse_scenario_comment

class JiraBulkImporter:
    """
    Two-pass repeatable bulk importer that imports dataset records into Jira,
    preserving source identifiers, scenario actors, roles, timestamps, and issue relationships.
    Idempotent: checks for existing issues to avoid duplicate creation.
    """

    def __init__(self, jira_client: Optional[BaseJiraClient] = None, client: Optional[BaseJiraClient] = None):
        self.client = jira_client or client
        if not self.client:
            raise ValueError("Jira client must be provided to JiraBulkImporter")
        self.source_map: Dict[str, str] = {}

    def import_from_json(self, file_path: str, project_key: str = "KAN", batch_delay: float = 0.0) -> Dict[str, Any]:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        payload = DatasetPayload(**data)
        return self.import_dataset(payload, batch_delay=batch_delay)

    def import_dataset(self, payload: DatasetPayload, batch_delay: float = 0.0) -> Dict[str, Any]:
        dataset_label = payload.dataset_label
        records = payload.records
        total = len(records)
        created_count = 0
        comments_count = 0
        links_count = 0

        print(f"Starting bulk import of {total} records with label '{dataset_label}'...")

        # Pre-check for existing issues in Jira to ensure repeatability/idempotency
        try:
            jql = f'labels = "{dataset_label}"'
            existing = self.client.search_issues(jql, max_results=100)
            for iss in existing.issues:
                # Summary format: "[source_id] ..."
                m = re.match(r"^\[([A-Za-z0-9_-]+)\]", iss.summary)
                if m:
                    src_id = m.group(1)
                    self.source_map[src_id] = iss.key
            if self.source_map:
                print(f"Discovered {len(self.source_map)} already imported records in Jira.")
        except Exception as e:
            print(f"Notice: pre-check for existing issues encountered: {e}")

        # PASS 1: Create all issues and record source_id -> jira_key mapping
        for idx, rec in enumerate(records, 1):
            source_id = rec.source_id
            if source_id in self.source_map:
                continue

            labels = [dataset_label, f"kind-{rec.kind}"]
            if rec.release:
                labels.append(f"rel-{rec.release}")

            description_text = f"Source ID: {source_id}\n\n{rec.description}"
            fields = {
                "source_id": source_id,
                "summary": f"[{source_id}] {rec.summary}",
                "description": description_text,
                "kind": rec.kind,
                "release": rec.release,
                "status": rec.recorded_status,
                "labels": labels
            }
            assigned_key = self.client.create_issue(fields)
            if assigned_key:
                self.source_map[source_id] = assigned_key
                created_count += 1
                if created_count % 20 == 0:
                    print(f"  Created {created_count}/{total} issues (latest: {assigned_key})...")
            
            if batch_delay > 0:
                time.sleep(batch_delay)

        print(f"Pass 1 complete: {len(self.source_map)} issues ready in mapping ({created_count} newly created).")

        # PASS 2: Add comments and issue links
        for idx, rec in enumerate(records, 1):
            source_id = rec.source_id
            jira_key = self.source_map.get(source_id, source_id)

            # Add comments preserving scenario metadata
            for comment_text in rec.comments:
                cid = self.client.add_comment(jira_key, comment_text)
                if cid:
                    comments_count += 1

            # Create links
            for target_source_id in rec.links:
                target_key = self.source_map.get(target_source_id, target_source_id)
                success = self.client.create_issue_link(jira_key, target_key, link_type="Relates")
                if success:
                    links_count += 1

            if batch_delay > 0:
                time.sleep(batch_delay)

        print(f"Pass 2 complete: {comments_count} comments added, {links_count} links established.")

        return {
            "status": "success",
            "dataset_label": dataset_label,
            "total_records": total,
            "issues_created": created_count,
            "comments_created": comments_count,
            "links_created": links_count,
            "source_id_mapping": self.source_map
        }
