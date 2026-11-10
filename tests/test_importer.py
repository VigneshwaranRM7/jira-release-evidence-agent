import os
import pytest
from controllers.v1.jira.mock_client import MockJiraClient
from controllers.v1.jira.bulk_importer import JiraBulkImporter

def test_mock_jira_client_load(dataset_path):
    client = MockJiraClient(dataset_path)
    # The client indexes by both generated REL key and source_id
    assert len(client.issues) >= 400
    assert len(client.source_id_to_key) == 400

    # Verify sample record
    rec_1001 = client.get_issue("REC-1001")
    assert rec_1001 is not None
    assert rec_1001.source_id == "REC-1001"
    assert rec_1001.kind == "evidence"
    assert len(rec_1001.comments) > 0

    # Verify comment scenario parsing
    first_comment = rec_1001.comments[0]
    assert first_comment.scenario_actor is not None
    assert first_comment.scenario_role is not None

def test_bulk_importer_execution(dataset_path):
    empty_client = MockJiraClient()
    # Reset internal issues
    empty_client.issues = {}
    empty_client.source_id_to_key = {}
    
    importer = JiraBulkImporter(client=empty_client)
    stats = importer.import_from_json(dataset_path, project_key="REL")

    assert stats["status"] == "success"
    assert stats["issues_created"] == 400
    assert stats["comments_created"] == 2059
    assert stats["links_created"] == 76
    assert len(importer.source_map) == 400

def test_link_resolution_in_importer(mock_client):
    # Verify link traversal between known related records
    # REC-4076 links to REC-9635
    rec_4076 = mock_client.get_issue("REC-4076")
    assert rec_4076 is not None
    assert len(rec_4076.links) > 0
    linked_target = rec_4076.links[0]
    target_issue = mock_client.get_issue(linked_target)
    assert target_issue is not None
    assert target_issue.source_id == "REC-9635"

