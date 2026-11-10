import json
import time
from typing import Dict, Any, List, Optional
from controllers.v1.jira.base_client import BaseJiraClient
from models.v1.jira.dataset import DatasetPayload, DatasetRecord
from utils.text_parser import parse_scenario_comment

class JiraBulkImporter:
    """
    Two-pass repeatable bulk importer that imports dataset records into Jira,
    preserving source identifiers, scenario actors, roles, timestamps, and issue relationships.
    """

    def __init__(self, jira_client: Optional[BaseJiraClient] = None, client: Optional[BaseJiraClient] = None):
        self.client = jira_client or client
        if not self.client:
            raise ValueError("Jira client must be provided to JiraBulkImporter")
        self.source_map: Dict[str, str] = {}

    def import_from_json(self, file_path: str, project_key: str = "REL", batch_delay: float = 0.0) -> Dict[str, Any]:
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

        # PASS 1: Create all issues and record source_id -> jira_key mapping
        for rec in records:
            source_id = rec.source_id
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
            if batch_delay > 0:
                time.sleep(batch_delay)

        # PASS 2: Add comments and issue links
        for rec in records:
            source_id = rec.source_id
            jira_key = self.source_map.get(source_id, source_id)

            # Add comments preserving scenario metadata
            for comment_text in rec.comments:
                self.client.add_comment(jira_key, comment_text)
                comments_count += 1

            # Create links
            for target_source_id in rec.links:
                target_key = self.source_map.get(target_source_id, target_source_id)
                success = self.client.create_issue_link(jira_key, target_key, link_type="Relates")
                if success:
                    links_count += 1

            if batch_delay > 0:
                time.sleep(batch_delay)

        return {
            "status": "success",
            "dataset_label": dataset_label,
            "total_records": total,
            "issues_created": created_count,
            "comments_created": comments_count,
            "links_created": links_count,
            "source_id_mapping": self.source_map
        }
