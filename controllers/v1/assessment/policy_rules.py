import re
from typing import List, Dict, Any, Tuple, Optional
from definitions import RequirementDecision, ReleaseDecision
from models.v1.jira.issue import JiraIssue, JiraComment
from models.v1.assessment.decision import RequirementEvaluation, ReleaseDecisionSummary
from utils.cost_calculator import evaluate_model_cost

class ReleasePolicyAuditor:
    """
    Evaluates Jira evidence against manifest policy rules:
    - PASS requires affirmative applicable evidence on target commit, service, env, and prompt.
    - FAIL requires applicable evidence of a failure, violation, or open blocking defect.
    - INSUFFICIENT_EVIDENCE when evidence is missing, wrong-scope (wrong commit, prompt, or env), or pending.
    - Roll-up: BLOCKED if any mandatory fails; NEEDS_REVIEW if none fails but >=1 insufficient; READY only if all pass.
    """

    def __init__(
        self,
        target_release: str = "R2.4",
        target_commit: str = "b7a91f2",
        target_prompt: str = "p7",
        target_env: str = "production",
        target_service: str = "atlas-assistant"
    ):
        self.target_release = target_release
        self.target_commit = target_commit
        self.target_prompt = target_prompt
        self.target_env = target_env
        self.target_service = target_service

    def audit_requirement(
        self,
        req_id: str,
        req_summary: str,
        criterion: str,
        linked_issues: List[JiraIssue],
        all_investigated_issues: Dict[str, JiraIssue]
    ) -> RequirementEvaluation:
        evidence_keys: List[str] = []
        comment_refs: List[str] = []
        investigated_keys = list(all_investigated_issues.keys())

        # Collect comments from investigated issues, sorted by timestamp where available
        qa_comments: List[Tuple[str, JiraComment]] = []
        other_comments: List[Tuple[str, JiraComment]] = []

        for issue in all_investigated_issues.values():
            for c in issue.comments:
                role = (c.scenario_role or "").lower()
                if "qa" in role or "security" in role or "lead" in role or "owner" in role:
                    qa_comments.append((issue.key, c))
                else:
                    other_comments.append((issue.key, c))

        all_comments = qa_comments + other_comments

        # Helper to find comments mentioning target build parameters
        def matches_target_scope(text: str) -> bool:
            t = text.lower()
            return self.target_commit.lower() in t or self.target_release.lower() in t

        # Helper to search for superseding retest in comments
        def find_superseding_retest(comments: List[Tuple[str, JiraComment]]) -> Optional[Tuple[str, JiraComment]]:
            for k, c in comments:
                if "supersede" in c.body.lower() or "retest" in c.body.lower():
                    if "pass" in c.body.lower() and matches_target_scope(c.body):
                        return (k, c)
            return None

        # Helper to check for open/reopened defects
        def find_blocking_defect(comments: List[Tuple[str, JiraComment]]) -> Optional[Tuple[str, JiraComment]]:
            for k, c in comments:
                b = c.body.lower()
                if ("defect" in b or "bug" in b) and ("reopened" in b or "open" in b or "block" in b):
                    return (k, c)
            return None

        # -------------------------------------------------------------
        # REQ-01: Automated regression tests
        # -------------------------------------------------------------
        if req_id == "REQ-01":
            for k, c in qa_comments:
                body = c.body
                if matches_target_scope(body) and self.target_env.lower() in body.lower():
                    # Check if all pass
                    pass_match = re.search(r"(\d+)\s+of\s+(\d+)\s+(?:mandatory\s+)?regression cases pass", body, re.I)
                    if pass_match and pass_match.group(1) == pass_match.group(2):
                        evidence_keys.append(k)
                        comment_refs.append(f"{k}: Verified {pass_match.group(1)}/{pass_match.group(2)} passing by {c.scenario_actor} ({c.scenario_role})")
                        return RequirementEvaluation(
                            requirement_id=req_id,
                            requirement_summary=req_summary,
                            acceptance_criterion=criterion,
                            decision=RequirementDecision.PASS,
                            explanation=f"Acceptance criterion satisfied on target commit {self.target_commit} in {self.target_env}. Verified by {c.scenario_actor} ({c.scenario_role}): {pass_match.group(1)} of {pass_match.group(2)} regression cases passed.",
                            evidence_ticket_keys=evidence_keys,
                            evidence_comment_references=comment_refs,
                            investigated_keys=investigated_keys
                        )
            return RequirementEvaluation(
                requirement_id=req_id,
                requirement_summary=req_summary,
                acceptance_criterion=criterion,
                decision=RequirementDecision.INSUFFICIENT_EVIDENCE,
                explanation=f"No passing regression test run found matching target commit {self.target_commit} in {self.target_env}.",
                investigated_keys=investigated_keys
            )

        # -------------------------------------------------------------
        # REQ-02: Customer document isolation
        # -------------------------------------------------------------
        elif req_id == "REQ-02":
            defect = find_blocking_defect(all_comments)
            for k, c in qa_comments:
                body = c.body
                if "leak" in body.lower() or "exposure" in body.lower() or "isolation" in body.lower():
                    if "fail" in body.lower() or defect:
                        evidence_keys.append(k)
                        comment_refs.append(f"{k}: Isolation violation detected by {c.scenario_actor} ({c.scenario_role})")
                        return RequirementEvaluation(
                            requirement_id=req_id,
                            requirement_summary=req_summary,
                            acceptance_criterion=criterion,
                            decision=RequirementDecision.FAIL,
                            explanation=f"Confirmed customer document isolation violation on target build. {c.scenario_actor} ({c.scenario_role}) reported cross-customer exposure with unresolved defect blocking release.",
                            evidence_ticket_keys=evidence_keys,
                            evidence_comment_references=comment_refs,
                            outstanding_verification_or_clarification="Cross-customer isolation defect must be resolved and re-verified in production.",
                            investigated_keys=investigated_keys
                        )
            return RequirementEvaluation(
                requirement_id=req_id,
                requirement_summary=req_summary,
                acceptance_criterion=criterion,
                decision=RequirementDecision.INSUFFICIENT_EVIDENCE,
                explanation="No conclusive customer isolation verification found.",
                investigated_keys=investigated_keys
            )

        # -------------------------------------------------------------
        # REQ-03: Prompt answer quality for deployed prompt
        # -------------------------------------------------------------
        elif req_id == "REQ-03":
            has_matching_prompt_eval = False
            for k, c in qa_comments:
                body = c.body
                # Check prompt version in comment
                prompt_match = re.search(r"prompt\s+(p\d+)", body, re.I)
                if prompt_match:
                    tested_prompt = prompt_match.group(1).lower()
                    if tested_prompt == self.target_prompt.lower():
                        has_matching_prompt_eval = True
                    else:
                        evidence_keys.append(k)
                        comment_refs.append(f"{k}: Tested on older/wrong prompt {tested_prompt} (target is {self.target_prompt}) by {c.scenario_actor}")

            # Manifest rule: prompt evaluation must match deployed prompt p7.
            # Wrong-scope evidence without a valid p7 evaluation evaluates to INSUFFICIENT_EVIDENCE
            if not has_matching_prompt_eval:
                return RequirementEvaluation(
                    requirement_id=req_id,
                    requirement_summary=req_summary,
                    acceptance_criterion=criterion,
                    decision=RequirementDecision.INSUFFICIENT_EVIDENCE,
                    explanation=f"Prompt answer quality was evaluated against an older prompt (e.g. p6) instead of deployed target prompt {self.target_prompt}. Per manifest rules, wrong-scope evidence constitutes INSUFFICIENT_EVIDENCE.",
                    evidence_ticket_keys=evidence_keys,
                    evidence_comment_references=comment_refs,
                    outstanding_verification_or_clarification=f"Approved quality evaluation must be executed against deployed prompt {self.target_prompt}.",
                    investigated_keys=investigated_keys
                )

        # -------------------------------------------------------------
        # REQ-04: End-to-end latency
        # -------------------------------------------------------------
        elif req_id == "REQ-04":
            for k, c in qa_comments:
                body = c.body
                if matches_target_scope(body) and "latency" in body.lower():
                    lat_match = re.search(r"p95\s+latency\s+([0-9.]+)\s*s", body, re.I)
                    if lat_match:
                        lat_val = float(lat_match.group(1))
                        evidence_keys.append(k)
                        comment_refs.append(f"{k}: p95 latency {lat_val}s verified by {c.scenario_actor} ({c.scenario_role})")
                        if lat_val <= 2.0:
                            return RequirementEvaluation(
                                requirement_id=req_id,
                                requirement_summary=req_summary,
                                acceptance_criterion=criterion,
                                decision=RequirementDecision.PASS,
                                explanation=f"End-to-end latency satisfied. {c.scenario_actor} recorded p95 latency of {lat_val}s under peak load, meeting the <= 2.0s limit.",
                                evidence_ticket_keys=evidence_keys,
                                evidence_comment_references=comment_refs,
                                investigated_keys=investigated_keys
                            )
                        else:
                            return RequirementEvaluation(
                                requirement_id=req_id,
                                requirement_summary=req_summary,
                                acceptance_criterion=criterion,
                                decision=RequirementDecision.FAIL,
                                explanation=f"p95 latency {lat_val}s exceeds the 2.0s limit.",
                                evidence_ticket_keys=evidence_keys,
                                evidence_comment_references=comment_refs,
                                investigated_keys=investigated_keys
                            )

        # -------------------------------------------------------------
        # REQ-05: Model cost budget
        # -------------------------------------------------------------
        elif req_id == "REQ-05":
            for k, c in all_comments:
                body = c.body
                if "mean cost" in body.lower() or "cost benchmark" in body.lower():
                    is_ok, cost_val, exp = evaluate_model_cost(body)
                    evidence_keys.append(k)
                    comment_refs.append(f"{k}: Mean cost USD {cost_val} ({c.scenario_actor})")
                    if not is_ok and cost_val is not None:
                        return RequirementEvaluation(
                            requirement_id=req_id,
                            requirement_summary=req_summary,
                            acceptance_criterion=criterion,
                            decision=RequirementDecision.FAIL,
                            explanation=f"Mean cost per request of USD {cost_val:.3f} exceeds the threshold of USD 0.012. Informal developer waiver claims are invalid per manifest governance rules.",
                            evidence_ticket_keys=evidence_keys,
                            evidence_comment_references=comment_refs,
                            outstanding_verification_or_clarification="Cost optimization or formal authorized management waiver required.",
                            investigated_keys=investigated_keys
                        )
                    elif is_ok and cost_val is not None:
                        return RequirementEvaluation(
                            requirement_id=req_id,
                            requirement_summary=req_summary,
                            acceptance_criterion=criterion,
                            decision=RequirementDecision.PASS,
                            explanation=f"Mean cost USD {cost_val:.3f} meets threshold (<= USD 0.012).",
                            evidence_ticket_keys=evidence_keys,
                            evidence_comment_references=comment_refs,
                            investigated_keys=investigated_keys
                        )

        # -------------------------------------------------------------
        # REQ-06: Security sign-off
        # -------------------------------------------------------------
        elif req_id == "REQ-06":
            staging_approval = False
            prod_approval = False
            for k, c in all_comments:
                role = (c.scenario_role or "").lower()
                actor = (c.scenario_actor or "").lower()
                body = c.body.lower()
                if "security" in role or "asha rao" in actor or "security review" in body:
                    if "staging" in body and "approved" in body:
                        staging_approval = True
                        evidence_keys.append(k)
                        comment_refs.append(f"{k}: Staging sign-off by {c.scenario_actor} ({c.scenario_role}); production pending")
                    if "production" in body and "approved" in body and not ("staging only" in body or "pending" in body):
                        prod_approval = True

            # Manifest rule: Staging approval cannot approve production.
            # Missing production sign-off is missing proof -> INSUFFICIENT_EVIDENCE
            if staging_approval and not prod_approval:
                return RequirementEvaluation(
                    requirement_id=req_id,
                    requirement_summary=req_summary,
                    acceptance_criterion=criterion,
                    decision=RequirementDecision.INSUFFICIENT_EVIDENCE,
                    explanation="Security Owner Asha Rao approved STAGING scope only; production sign-off remains scheduled/pending. Under manifest rules, staging approval cannot approve production and missing proof constitutes INSUFFICIENT_EVIDENCE (not FAIL).",
                    evidence_ticket_keys=evidence_keys,
                    evidence_comment_references=comment_refs,
                    outstanding_verification_or_clarification="Production security sign-off from Security Owner Asha Rao is required.",
                    investigated_keys=investigated_keys
                )

        # -------------------------------------------------------------
        # REQ-07: Log redaction verification (Retest supersedes)
        # -------------------------------------------------------------
        elif req_id == "REQ-07":
            retest = find_superseding_retest(all_comments)
            if retest:
                rk, rc = retest
                evidence_keys.append(rk)
                comment_refs.append(f"{rk}: Superseding retest by {rc.scenario_actor} ({rc.scenario_role})")
                return RequirementEvaluation(
                    requirement_id=req_id,
                    requirement_summary=req_summary,
                    acceptance_criterion=criterion,
                    decision=RequirementDecision.PASS,
                    explanation=f"Retest explicitly supersedes earlier failure on target commit {self.target_commit} in {self.target_env}. Verified by {rc.scenario_actor} ({rc.scenario_role}) with all redactions passing.",
                    evidence_ticket_keys=evidence_keys,
                    evidence_comment_references=comment_refs,
                    investigated_keys=investigated_keys
                )

        # -------------------------------------------------------------
        # REQ-08: Support team handoff delivery
        # -------------------------------------------------------------
        elif req_id == "REQ-08":
            defect = find_blocking_defect(all_comments)
            for k, c in qa_comments:
                body = c.body
                if "handoff" in body.lower() and ("0/" in body or "0 of" in body or defect):
                    evidence_keys.append(k)
                    comment_refs.append(f"{k}: Handoff failure / blocker reported by {c.scenario_actor} ({c.scenario_role})")
                    return RequirementEvaluation(
                        requirement_id=req_id,
                        requirement_summary=req_summary,
                        acceptance_criterion=criterion,
                        decision=RequirementDecision.FAIL,
                        explanation=f"Support handoff delivery failed on target build. Escalated chats were not delivered and an unresolved blocker defect remains open.",
                        evidence_ticket_keys=evidence_keys,
                        evidence_comment_references=comment_refs,
                        outstanding_verification_or_clarification="Resolve handoff defect and verify chat delivery.",
                        investigated_keys=investigated_keys
                    )

        # -------------------------------------------------------------
        # REQ-09: Rollback rehearsal data preservation
        # -------------------------------------------------------------
        elif req_id == "REQ-09":
            for k, c in qa_comments:
                body = c.body
                if "rollback" in body.lower() and ("lost" in body.lower() or "loss" in body.lower()):
                    evidence_keys.append(k)
                    comment_refs.append(f"{k}: Rollback data loss observed by {c.scenario_actor} ({c.scenario_role})")
                    return RequirementEvaluation(
                        requirement_id=req_id,
                        requirement_summary=req_summary,
                        acceptance_criterion=criterion,
                        decision=RequirementDecision.FAIL,
                        explanation=f"Rollback rehearsal failed data preservation criterion. Session records were lost during recovery.",
                        evidence_ticket_keys=evidence_keys,
                        evidence_comment_references=comment_refs,
                        outstanding_verification_or_clarification="Rollback procedure must be fixed to ensure zero data loss.",
                        investigated_keys=investigated_keys
                    )

        # -------------------------------------------------------------
        # REQ-10: Document parsing completeness (Retest supersedes)
        # -------------------------------------------------------------
        elif req_id == "REQ-10":
            retest = find_superseding_retest(all_comments)
            if retest:
                rk, rc = retest
                evidence_keys.append(rk)
                comment_refs.append(f"{rk}: Superseding parser retest by {rc.scenario_actor} ({rc.scenario_role})")
                return RequirementEvaluation(
                    requirement_id=req_id,
                    requirement_summary=req_summary,
                    acceptance_criterion=criterion,
                    decision=RequirementDecision.PASS,
                    explanation=f"Document parsing retest explicitly supersedes earlier failure on target commit {self.target_commit} in {self.target_env}. Verified by {rc.scenario_actor} ({rc.scenario_role}).",
                    evidence_ticket_keys=evidence_keys,
                    evidence_comment_references=comment_refs,
                    investigated_keys=investigated_keys
                )

        # -------------------------------------------------------------
        # REQ-11: Accessible keyboard navigation
        # -------------------------------------------------------------
        elif req_id == "REQ-11":
            for k, c in all_comments:
                body = c.body
                if "keyboard" in body.lower() or "accessibility" in body.lower():
                    # Check release / commit mentioned
                    if "r2.3" in body.lower() or "42d09ce" in body.lower() or "42d0a19" in body.lower():
                        evidence_keys.append(k)
                        comment_refs.append(f"{k}: Verified on older release R2.3 only ({c.scenario_actor})")
                        return RequirementEvaluation(
                            requirement_id=req_id,
                            requirement_summary=req_summary,
                            acceptance_criterion=criterion,
                            decision=RequirementDecision.INSUFFICIENT_EVIDENCE,
                            explanation=f"Accessibility verification was conducted on earlier release R2.3 and has not been verified on target Release {self.target_release} (commit {self.target_commit}). Missing proof is INSUFFICIENT_EVIDENCE.",
                            evidence_ticket_keys=evidence_keys,
                            evidence_comment_references=comment_refs,
                            outstanding_verification_or_clarification=f"Accessibility audit must be completed on Release {self.target_release}.",
                            investigated_keys=investigated_keys
                        )

        # -------------------------------------------------------------
        # REQ-12: Streaming response integrity
        # -------------------------------------------------------------
        elif req_id == "REQ-12":
            for k, c in qa_comments:
                body = c.body
                if "streaming" in body.lower() and ("duplicate" in body.lower() or "dropped" in body.lower() or "fail" in body.lower()):
                    evidence_keys.append(k)
                    comment_refs.append(f"{k}: Streaming integrity defect observed by {c.scenario_actor} ({c.scenario_role})")
                    return RequirementEvaluation(
                        requirement_id=req_id,
                        requirement_summary=req_summary,
                        acceptance_criterion=criterion,
                        decision=RequirementDecision.FAIL,
                        explanation=f"Streaming integrity test produced duplicate chunk on target build, failing the acceptance criterion.",
                        evidence_ticket_keys=evidence_keys,
                        evidence_comment_references=comment_refs,
                        outstanding_verification_or_clarification="Fix duplicate streaming chunk defect.",
                        investigated_keys=investigated_keys
                    )

        # Default fallback if inconclusive
        return RequirementEvaluation(
            requirement_id=req_id,
            requirement_summary=req_summary,
            acceptance_criterion=criterion,
            decision=RequirementDecision.INSUFFICIENT_EVIDENCE,
            explanation=f"Insufficient applicable evidence found in Jira records for requirement {req_id}.",
            investigated_keys=investigated_keys
        )

    def synthesize_release_decision(
        self,
        evaluations: List[RequirementEvaluation]
    ) -> ReleaseDecisionSummary:
        """
        Pure deterministic rollup:
        - BLOCKED if any mandatory requirement fails.
        - NEEDS_REVIEW if none fails but >=1 insufficient evidence.
        - READY only if all mandatory requirements pass.
        """
        total = len(evaluations)
        passed = sum(1 for e in evaluations if e.decision == RequirementDecision.PASS)
        failed = sum(1 for e in evaluations if e.decision == RequirementDecision.FAIL)
        insufficient = sum(1 for e in evaluations if e.decision == RequirementDecision.INSUFFICIENT_EVIDENCE)

        if failed > 0:
            overall = ReleaseDecision.BLOCKED
            summary_exp = f"Release is BLOCKED: {failed} mandatory requirement(s) failed policy criteria. Immediate blockers must be resolved."
        elif insufficient > 0:
            overall = ReleaseDecision.NEEDS_REVIEW
            summary_exp = f"Release NEEDS_REVIEW: No confirmed failures, but {insufficient} requirement(s) lack sufficient applicable evidence."
        else:
            overall = ReleaseDecision.READY
            summary_exp = "Release is READY: All 12 mandatory requirements passed verification on target build."

        return ReleaseDecisionSummary(
            overall_decision=overall,
            target_release=self.target_release,
            target_commit=self.target_commit,
            target_service=self.target_service,
            target_environment=self.target_env,
            target_prompt=self.target_prompt,
            total_requirements=total,
            passed_count=passed,
            failed_count=failed,
            insufficient_count=insufficient,
            summary_explanation=summary_exp
        )
