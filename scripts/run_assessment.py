#!/usr/bin/env python
import os
import sys
import argparse

# Add workspace root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from definitions import (
    DEFAULT_DATASET_LABEL, DEFAULT_TARGET_RELEASE, DEFAULT_TARGET_COMMIT,
    DEFAULT_TARGET_PROMPT, DEFAULT_TARGET_SERVICE, DEFAULT_TARGET_ENV,
    ARTIFACTS_DIR
)
from models.v1.assessment.report import AssessmentRunRequest
from controllers.v1.assessment.orchestrator import orchestrator
from controllers.v1.report.generator import ReportGenerator
from utils.context import settings

def main():
    parser = argparse.ArgumentParser(description="Run Jira Release Readiness Assessment Agent")
    parser.add_argument("--release", default=DEFAULT_TARGET_RELEASE, help="Target Release (default: R2.4)")
    parser.add_argument("--project", default=settings.jira_project_key or "KAN", help="Jira Project Key (default: KAN)")
    parser.add_argument("--cloud", action="store_true", help="Run against live Jira Cloud instance")
    parser.add_argument("--mock", action="store_true", help="Force in-memory mock Jira provider")
    parser.add_argument("--output-dir", default=ARTIFACTS_DIR, help="Output directory for artifacts")
    args = parser.parse_args()

    # Determine execution mode
    if args.cloud:
        force_mock = False
    elif args.mock:
        force_mock = True
    else:
        force_mock = settings.use_mock_jira or not bool(settings.jira_base_url and settings.jira_api_token)

    mode_str = "High-Performance Mock Jira Provider" if force_mock else f"Live Jira Cloud ({settings.jira_base_url})"

    print("=================================================================")
    print("      YELLOW NETWORK - JIRA RELEASE READINESS EVIDENCE AGENT     ")
    print("=================================================================")
    print(f"Target Release:     {args.release}")
    print(f"Project Key:        {args.project}")
    print(f"Dataset Scope:      {DEFAULT_DATASET_LABEL}")
    print(f"Execution Mode:     {mode_str}")
    print(f"Active LLM Model:   {settings.llm_model}")
    print("Starting autonomous evidence investigation across Jira issues...\n")

    request = AssessmentRunRequest(
        project_key=args.project,
        dataset_label=DEFAULT_DATASET_LABEL,
        target_release=args.release,
        force_mock=force_mock
    )

    report, trace = orchestrator.run_assessment(request)

    print("\n------------------- ASSESSMENT SCORECARD -------------------")
    s = report.summary
    print(f"Overall Release Decision: {s.overall_decision}")
    print(f"Total Requirements:       {s.total_requirements}")
    print(f"Passed:                   {s.passed_count}")
    print(f"Failed:                   {s.failed_count}")
    print(f"Needs Review/Insufficient: {s.insufficient_count}")
    print(f"\nExecutive Summary:\n{s.summary_explanation}\n")

    print("------------------- DETAILED FINDINGS ----------------------")
    for req in report.requirements:
        symbol = "[PASS]" if req.decision == "PASS" else ("[FAIL]" if req.decision == "FAIL" else "[INSUF]")
        print(f"{symbol:7} {req.requirement_id}: {req.requirement_summary}")
        print(f"        Verdict: {req.decision}")
        print(f"        Finding: {req.explanation[:110]}...")
        if req.evidence_ticket_keys:
            print(f"        Evidence: {', '.join(req.evidence_ticket_keys)}")

    print("\n------------------ INVESTIGATION TELEMETRY -----------------")
    print(f"Total Tool Invocations:   {trace.total_tool_calls}")
    print(f"Total Execution Time:     {trace.total_execution_time_seconds:.3f}s")
    print(f"Total Tokens Analyzed:    {trace.token_usage.get('total_tokens', 0)}")
    print(f"Total Model Cost (USD):   ${trace.cost_usd:.5f}")

    deliverables = ReportGenerator.save_deliverables(report, trace, args.output_dir)
    print("\n------------------- GENERATED ARTIFACTS --------------------")
    print(f"Markdown Report: {deliverables['markdown_report']}")
    print(f"JSON Report:     {deliverables['json_report']}")
    print(f"Trace Log:       {deliverables['trace']}")
    print("=================================================================\n")

if __name__ == "__main__":
    main()
