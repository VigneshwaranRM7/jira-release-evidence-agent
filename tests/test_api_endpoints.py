import pytest

@pytest.mark.asyncio
async def test_health_check(async_client):
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data
    assert "timestamp" in data

@pytest.mark.asyncio
async def test_jira_import_endpoint(async_client):
    response = await async_client.post("/api/v1/jira/import", json={"project_key": "REL", "force_mock": True})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["imported_issues"] == 400
    assert data["imported_comments"] == 2059
    assert data["created_links"] == 76

@pytest.mark.asyncio
async def test_assessment_run_and_reporting_lifecycle(async_client):
    # 1. Run Assessment
    run_response = await async_client.post(
        "/api/v1/assessment/run",
        json={"target_release": "R2.4", "force_mock": True}
    )
    assert run_response.status_code == 200
    report_data = run_response.json()
    
    assessment_id = report_data["assessment_id"]
    assert assessment_id.startswith("assess-")
    assert report_data["summary"]["overall_decision"] == "BLOCKED"
    assert len(report_data["requirements"]) == 12

    # 2. Check Status
    status_response = await async_client.get(f"/api/v1/assessment/{assessment_id}/status")
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "COMPLETED"

    # 3. Fetch Report (JSON)
    json_report_resp = await async_client.get(f"/api/v1/assessment/{assessment_id}/report?format=json")
    assert json_report_resp.status_code == 200
    assert json_report_resp.json()["assessment_id"] == assessment_id

    # 4. Fetch Report (Markdown)
    md_report_resp = await async_client.get(f"/api/v1/assessment/{assessment_id}/report?format=markdown")
    assert md_report_resp.status_code == 200
    assert "Release Readiness Assessment Report" in md_report_resp.text
    assert "Overall Release Decision: 🔴 **BLOCKED**" in md_report_resp.text

    # 5. Fetch Trace
    trace_resp = await async_client.get(f"/api/v1/assessment/{assessment_id}/trace")
    assert trace_resp.status_code == 200
    trace_data = trace_resp.json()
    assert trace_data["assessment_id"] == assessment_id
    assert trace_data["total_tool_calls"] > 0
    assert len(trace_data["tool_invocations"]) > 0

    # 6. Test 'latest' shortcut
    latest_report = await async_client.get("/api/v1/assessment/latest/report")
    assert latest_report.status_code == 200
    assert latest_report.json()["assessment_id"] == assessment_id
