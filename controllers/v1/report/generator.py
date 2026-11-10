import os
import json
from typing import Dict, Any
from models.v1.assessment.report import ReleaseReadinessReport
from models.v1.telemetry.trace import InvestigationTrace
from definitions import ARTIFACTS_DIR

class ReportGenerator:
    """
    Renders structured assessment results into standard assessment deliverables:
    - artifacts/release_readiness_report.md
    - artifacts/release_readiness_report.json
    - artifacts/investigation_trace.json
    """

    @staticmethod
    def generate_markdown_report(report: ReleaseReadinessReport) -> str:
        s = report.summary
        md = []
        md.append("# Release Readiness Assessment Report")
        md.append(f"**Assessment ID:** `{report.assessment_id}`  ")
        md.append(f"**Generated At:** `{report.generated_at}`  ")
        md.append(f"**Dataset Label:** `{report.dataset_label}`\n")
        md.append("---")
        
        # Decision Banner
        if s.overall_decision == "BLOCKED":
            decision_badge = "🔴 **BLOCKED**"
        elif s.overall_decision == "NEEDS_REVIEW":
            decision_badge = "🟡 **NEEDS_REVIEW**"
        else:
            decision_badge = "🟢 **READY**"

        md.append("## Executive Decision")
        md.append(f"### Overall Release Decision: {decision_badge}\n")
        md.append(f"> **Summary:** {s.summary_explanation}\n")

        # Target Scope Details
        md.append("## Target Scope")
        md.append("| Property | Target Value |")
        md.append("| :--- | :--- |")
        md.append(f"| **Target Release** | `{s.target_release}` |")
        md.append(f"| **Target Commit** | `{s.target_commit}` |")
        md.append(f"| **Target Service** | `{s.target_service}` |")
        md.append(f"| **Target Environment** | `{s.target_environment}` |")
        md.append(f"| **Target Prompt** | `{s.target_prompt}` |\n")

        # Scorecard Summary Table
        md.append("## Decision Scorecard")
        md.append("| Total Requirements | Passed | Failed | Needs Review / Insufficient |")
        md.append("| :---: | :---: | :---: | :---: |")
        md.append(f"| {s.total_requirements} | {s.passed_count} | {s.failed_count} | {s.insufficient_count} |\n")

        # Detailed Requirement Analysis
        md.append("## Detailed Requirement Findings")
        for req in report.requirements:
            status_icon = "✅" if req.decision == "PASS" else ("❌" if req.decision == "FAIL" else "⚠️")
            md.append(f"### {status_icon} [{req.requirement_id}] {req.requirement_summary}")
            md.append(f"- **Decision:** `{req.decision}`")
            md.append(f"- **Acceptance Criteria:** {req.acceptance_criterion}")
            md.append(f"- **Finding & Explanation:** {req.explanation}")
            
            if req.evidence_ticket_keys:
                md.append(f"- **Evidence Tickets:** {', '.join(f'`{k}`' for k in req.evidence_ticket_keys)}")
            else:
                md.append("- **Evidence Tickets:** None verified")

            if req.evidence_comment_references:
                md.append("- **Citations / Key Records:**")
                for cite in req.evidence_comment_references:
                    md.append(f"  - {cite}")

            if req.outstanding_verification_or_clarification:
                md.append(f"- **Action / Outstanding:** {req.outstanding_verification_or_clarification}")
            
            md.append("")

        # Blockers section
        failed_reqs = [r for r in report.requirements if r.decision == "FAIL"]
        if failed_reqs:
            md.append("## Critical Release Blockers")
            for fr in failed_reqs:
                md.append(f"- **{fr.requirement_id} ({fr.requirement_summary}):** {fr.outstanding_verification_or_clarification or fr.explanation}")
            md.append("")

        md.append("---")
        md.append("*Report generated autonomously by Yellow Network Jira Release Evidence Agent.*")
        return "\n".join(md)

    @staticmethod
    def save_deliverables(
        report: ReleaseReadinessReport,
        trace: InvestigationTrace,
        output_dir: str = ARTIFACTS_DIR
    ) -> Dict[str, str]:
        os.makedirs(output_dir, exist_ok=True)
        md_path = os.path.join(output_dir, "release_readiness_report.md")
        json_path = os.path.join(output_dir, "release_readiness_report.json")
        trace_path = os.path.join(output_dir, "investigation_trace.json")

        # 1. Write Markdown report
        md_content = ReportGenerator.generate_markdown_report(report)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        # 2. Write JSON report
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report.model_dump(), f, indent=2)

        # 3. Write Trace
        with open(trace_path, "w", encoding="utf-8") as f:
            json.dump(trace.model_dump(), f, indent=2)

        return {
            "markdown_report": md_path,
            "json_report": json_path,
            "trace": trace_path
        }

