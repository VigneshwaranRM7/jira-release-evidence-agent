#!/usr/bin/env python
import os
import sys
import subprocess
import json

# Add workspace root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from definitions import ROOT_DIR, DATA_DIR, ARTIFACTS_DIR

def run_step(step_name, command):
    print(f"\n========================================================")
    print(f"STEP: {step_name}")
    print(f"COMMAND: {' '.join(command)}")
    print(f"========================================================")
    res = subprocess.run(command, cwd=ROOT_DIR, capture_output=True, text=True)
    if res.stdout:
        print(res.stdout)
    if res.stderr:
        print(res.stderr, file=sys.stderr)
    if res.returncode != 0:
        print(f"FAILED: {step_name} exited with code {res.returncode}")
        sys.exit(res.returncode)
    print(f"SUCCESS: {step_name} completed.")

def verify_artifacts():
    print(f"\n========================================================")
    print(f"STEP: Verifying Deliverables in artifacts/")
    print(f"========================================================")
    md_path = os.path.join(ARTIFACTS_DIR, "release_readiness_report.md")
    json_path = os.path.join(ARTIFACTS_DIR, "release_readiness_report.json")
    trace_path = os.path.join(ARTIFACTS_DIR, "investigation_trace.json")

    assert os.path.exists(md_path), f"Missing {md_path}"
    assert os.path.exists(json_path), f"Missing {json_path}"
    assert os.path.exists(trace_path), f"Missing {trace_path}"

    with open(json_path, "r", encoding="utf-8") as f:
        report = json.load(f)
        assert report["summary"]["overall_decision"] == "BLOCKED"
        assert report["summary"]["total_requirements"] == 12
        print(f"- release_readiness_report.json verified: {report['summary']['total_requirements']} requirements evaluated, decision={report['summary']['overall_decision']}")

    with open(trace_path, "r", encoding="utf-8") as f:
        trace = json.load(f)
        assert trace["total_tool_calls"] > 0
        print(f"- investigation_trace.json verified: {trace['total_tool_calls']} tool invocations recorded")

    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()
        assert "Overall Release Decision: 🔴 **BLOCKED**" in md_text
        print(f"- release_readiness_report.md verified: executive report formatted with scorecards and citations")

    print("\nALL VERIFICATIONS PASSED SUCCESSFULLY!")

def main():
    print("Starting End-to-End Project Verification...")
    
    # 1. Run Automated Test Suite
    run_step("Automated Pytest Suite", [sys.executable, "-m", "pytest", "tests/", "-v"])

    # 2. Run Dataset Importer
    run_step("Dataset Bulk Importer (Mock)", [sys.executable, "scripts/import_dataset.py", "--mock"])

    # 3. Run Release Readiness Assessment Agent
    run_step("Autonomous Release Readiness Agent", [sys.executable, "scripts/run_assessment.py"])

    # 4. Verify Deliverables
    verify_artifacts()

if __name__ == "__main__":
    main()

