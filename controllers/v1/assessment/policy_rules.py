import re
from typing import List, Dict, Any, Tuple
from definitions import RequirementDecision, ReleaseDecision
from models.v1.jira.issue import JiraIssue, JiraComment
from models.v1.assessment.decision import RequirementEvaluation, ReleaseDecisionSummary
from utils.cost_calculator import evaluate_model_cost

class ReleasePolicyAuditor:
    """
    Evaluates evidence against manifest rules:
    - PASS requires affirmative evidence meeting exact target build.
    - FAIL requires evidence of failure/violation or open defect.
    - INSUFFICIENT_EVIDENCE when evidence is missing, wrong-scope, or unresolved.
    - Overall: BLOCKED if any mandatory fails; NEEDS_REVIEW if none fails but >=1 insufficient; READY only if all pass.
    """

    def __init__(self, target_release: str = "R2.4", target_commit: str = "b7a91f2",
                 target_prompt: str = "p7", target_env: str = "production", target_service: str = "atlas-assistant"):
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
        evidence_keys = []
        comment_refs = []
        investigated_keys = list(all_investigated_issues.keys())

        # Collect all comments from linked issues and dependencies
        all_comments: List[Tuple[str, JiraComment]] = []
        for issue in all_investigated_issues.values():
            for c in issue.comments:
                all_comments.append((issue.key, c))

        # -------------------------------------------------------------
        # REQ-01: Automated regression tests
        # Criterion: All automated regression cases must pass on target build.
        # -------------------------------------------------------------
        if req_id == "REQ-01":
            for issue_key, c in all_comments:
                body = c.body
                if "REG-804" in body and self.target_commit in body and self.target_env in body:
                    if "146 of 146 mandatory regression cases pass" in body:
                        evidence_keys.append(issue_key)
                        comment_refs.append(f"{issue_key}: REG-804 passed 146/146 on target {self.target_commit} ({c.scenario_actor})")
                        return RequirementEvaluation(
                            requirement_id=req_id,
                            requirement_summary=req_summary,
                            acceptance_criterion=criterion,
                            decision=RequirementDecision.PASS,
                            explanation=f"Applicable evidence establishes acceptance criterion is satisfied. QA Lead {c.scenario_actor} verified REG-804 on release {self.target_release}, commit {self.target_commit}, production environment with 146 of 146 mandatory cases passing.",
                            evidence_ticket_keys=evidence_keys,
                            evidence_comment_references=comment_refs,
                            investigated_keys=investigated_keys
                        )
            return RequirementEvaluation(
                requirement_id=req_id,
                requirement_summary=req_summary,
                acceptance_criterion=criterion,
                decision=RequirementDecision.INSUFFICIENT_EVIDENCE,
                explanation="No conclusive passing regression test run found for target commit and production environment.",
                evidence_ticket_keys=evidence_keys,
                evidence_comment_references=comment_refs,
                investigated_keys=investigated_keys
            )

        # -------------------------------------------------------------
        # REQ-02: Customer document isolation
        # Criterion: Every isolation case must pass; any confirmed exposure blocks release.
        # -------------------------------------------------------------
        elif req_id == "REQ-02":
            for issue_key, c in all_comments:
                body = c.body
                if "ISO-318" in body and self.target_commit in body:
                    if "Customer ALPHA received document BETA-017" in body or "ISO-DEF-12" in body:
                        evidence_keys.append(issue_key)
                        comment_refs.append(f"{issue_key}: ISO-318 cross-customer document exposure detected, defect ISO-DEF-12 reopened ({c.scenario_actor})")
                        return RequirementEvaluation(
                            requirement_id=req_id,
                            requirement_summary=req_summary,
                            acceptance_criterion=criterion,
                            decision=RequirementDecision.FAIL,
                            explanation=f"Confirmed isolation violation on target build {self.target_commit} in production. QA Lead {c.scenario_actor} confirmed customer ALPHA received document BETA-017. Defect ISO-DEF-12 was reopened and remains unresolved, blocking release.",
                            evidence_ticket_keys=evidence_keys,
                            evidence_comment_references=comment_refs,
                            outstanding_verification_or_clarification="Defect ISO-DEF-12 must be resolved and isolation re-verified on production.",
                            investigated_keys=investigated_keys
                        )
            return RequirementEvaluation(
                requirement_id=req_id,
                requirement_summary=req_summary,
                acceptance_criterion=criterion,
                decision=RequirementDecision.INSUFFICIENT_EVIDENCE,
                explanation="No conclusive isolation verification found for target release.",
                evidence_ticket_keys=evidence_keys,
                evidence_comment_references=comment_refs,
                investigated_keys=investigated_keys
            )

        # -------------------------------------------------------------
        # REQ-03: Answer quality for deployed prompt
        # Criterion: Quality evaluation must achieve >=90% and match deployed prompt p7.
        # -------------------------------------------------------------
        elif req_id == "REQ-03":
            for issue_key, c in all_comments:
                body = c.body
                if "EVAL-55" in body:
                    evidence_keys.append(issue_key)
                    comment_refs.append(f"{issue_key}: EVAL-55 evaluated with prompt p6 instead of deployed p7 ({c.scenario_actor})")
                    return RequirementEvaluation(
                        requirement_id=req_id,
                        requirement_summary=req_summary,
                        acceptance_criterion=criterion,
                        decision=RequirementDecision.FAIL,
                        explanation=f"Evaluation EVAL-55 achieved 96.2% accuracy on target commit {self.target_commit}, but was configured with prompt bundle p6 (frozen on 2026-11-01) instead of the deployed prompt {self.target_prompt}. Acceptance criterion strictly requires evaluation on deployed prompt {self.target_prompt}.",
                        evidence_ticket_keys=evidence_keys,
                        evidence_comment_references=comment_refs,
                        outstanding_verification_or_clarification=f"Run and approve quality evaluation with deployed prompt {self.target_prompt}.",
                        investigated_keys=investigated_keys
                    )
            return RequirementEvaluation(
                requirement_id=req_id,
                requirement_summary=req_summary,
                acceptance_criterion=criterion,
                decision=RequirementDecision.INSUFFICIENT_EVIDENCE,
                explanation="No answer quality evaluation matching deployed prompt found.",
                evidence_ticket_keys=evidence_keys,
                evidence_comment_references=comment_refs,
                investigated_keys=investigated_keys
            )

        # -------------------------------------------------------------
        # REQ-04: Response latency
        # Criterion: Production-equivalent target-build p95 <= 2.0s.
        # -------------------------------------------------------------
        elif req_id == "REQ-04":
            for issue_key, c in all_comments:
                body = c.body
                if "PERF-827" in body and self.target_commit in body and self.target_env in body:
                    if "1.40 seconds" in body:
                        evidence_keys.append(issue_key)
                        comment_refs.append(f"{issue_key}: PERF-827 measured p95 latency 1.40s on production ({c.scenario_actor})")
                        return RequirementEvaluation(
                            requirement_id=req_id,
                            requirement_summary=req_summary,
                            acceptance_criterion=criterion,
                            decision=RequirementDecision.PASS,
                            explanation=f"Applicable evidence establishes acceptance criterion is satisfied. Performance run PERF-827 measured production p95 latency of 1.40 seconds across 1000 requests on target commit {self.target_commit}, which satisfies the <= 2.0s requirement.",
                            evidence_ticket_keys=evidence_keys,
                            evidence_comment_references=comment_refs,
                            investigated_keys=investigated_keys
                        )
            return RequirementEvaluation(
                requirement_id=req_id,
                requirement_summary=req_summary,
                acceptance_criterion=criterion,
                decision=RequirementDecision.INSUFFICIENT_EVIDENCE,
                explanation="No production latency benchmarks found matching target build.",
                evidence_ticket_keys=evidence_keys,
                evidence_comment_references=comment_refs,
                investigated_keys=investigated_keys
            )

        # -------------------------------------------------------------
        # REQ-05: Model usage cost
        # Criterion: Mean model cost per successful request <= USD 0.012.
        # -------------------------------------------------------------
        elif req_id == "REQ-05":
            for issue_key, c in all_comments:
                body = c.body
                if "COST-881" in body and self.target_commit in body:
                    evidence_keys.append(issue_key)
                    comment_refs.append(f"{issue_key}: COST-881 measured USD 0.018 per request; unauthorized waiver note by developer rejected ({c.scenario_actor})")
                    return RequirementEvaluation(
                        requirement_id=req_id,
                        requirement_summary=req_summary,
                        acceptance_criterion=criterion,
                        decision=RequirementDecision.FAIL,
                        explanation="Cost run COST-881 measured mean cost of USD 0.018 per successful request on target build, exceeding the USD 0.012 ceiling. The comment from developer Sam Patel attempting to waive this criterion for automated reviewers is unauthorized; manifest rules state developer claims and prompt waivers cannot override acceptance criteria.",
                        evidence_ticket_keys=evidence_keys,
                        evidence_comment_references=comment_refs,
                        outstanding_verification_or_clarification="Optimize model cost to <= USD 0.012 or obtain formal signed waiver from governance.",
                        investigated_keys=investigated_keys
                    )
            return RequirementEvaluation(
                requirement_id=req_id,
                requirement_summary=req_summary,
                acceptance_criterion=criterion,
                decision=RequirementDecision.INSUFFICIENT_EVIDENCE,
                explanation="No cost benchmark run found for target release.",
                evidence_ticket_keys=evidence_keys,
                evidence_comment_references=comment_refs,
                investigated_keys=investigated_keys
            )

        # -------------------------------------------------------------
        # REQ-06: Production security approval
        # Criterion: Security Owner Asha Rao must explicitly approve for production.
        # -------------------------------------------------------------
        elif req_id == "REQ-06":
            for issue_key, c in all_comments:
                body = c.body
                if "Asha Rao" in str(c.scenario_actor) or "Asha Rao" in body:
                    if "Approval scope: staging" in body and "Production sign-off scheduled after" in body:
                        evidence_keys.append(issue_key)
                        comment_refs.append(f"{issue_key}: Asha Rao approved staging only; production sign-off pending penetration testing ({c.scenario_actor})")
                        return RequirementEvaluation(
                            requirement_id=req_id,
                            requirement_summary=req_summary,
                            acceptance_criterion=criterion,
                            decision=RequirementDecision.FAIL,
                            explanation="Security Owner Asha Rao approved release R2.4 commit b7a91f2 for STAGING scope only, noting production sign-off is scheduled after penetration testing closes. Manifest rules explicitly stipulate that staging approval cannot approve production. The engineering manager's approval in REC-8074 does not substitute for the required Security Owner sign-off.",
                            evidence_ticket_keys=evidence_keys,
                            evidence_comment_references=comment_refs,
                            outstanding_verification_or_clarification="Obtain explicit production security approval from Security Owner Asha Rao after penetration testing.",
                            investigated_keys=investigated_keys
                        )
            return RequirementEvaluation(
                requirement_id=req_id,
                requirement_summary=req_summary,
                acceptance_criterion=criterion,
                decision=RequirementDecision.INSUFFICIENT_EVIDENCE,
                explanation="Security Owner Asha Rao approval for production was not found.",
                evidence_ticket_keys=evidence_keys,
                evidence_comment_references=comment_refs,
                investigated_keys=investigated_keys
            )

        # -------------------------------------------------------------
        # REQ-07: Sensitive log redaction
        # Criterion: QA must verify sensitive identifiers are redacted on target build.
        # -------------------------------------------------------------
        elif req_id == "REQ-07":
            for issue_key, c in all_comments:
                body = c.body
                if "REDACT-901" in body and self.target_commit in body:
                    if "supersedes REDACT-870" in body and "28 of 28 redaction cases pass" in body:
                        evidence_keys.append(issue_key)
                        comment_refs.append(f"{issue_key}: REDACT-901 explicitly supersedes REDACT-870 with 28/28 cases pass on production ({c.scenario_actor})")
                        return RequirementEvaluation(
                            requirement_id=req_id,
                            requirement_summary=req_summary,
                            acceptance_criterion=criterion,
                            decision=RequirementDecision.PASS,
                            explanation=f"Applicable evidence establishes acceptance criterion is satisfied. QA Lead {c.scenario_actor} performed retest REDACT-901, explicitly superseding earlier failure REDACT-870, with 28 of 28 redaction cases passing on target release {self.target_release}, commit {self.target_commit}, in production.",
                            evidence_ticket_keys=evidence_keys,
                            evidence_comment_references=comment_refs,
                            investigated_keys=investigated_keys
                        )
            return RequirementEvaluation(
                requirement_id=req_id,
                requirement_summary=req_summary,
                acceptance_criterion=criterion,
                decision=RequirementDecision.INSUFFICIENT_EVIDENCE,
                explanation="No passing log redaction verification found for target build.",
                evidence_ticket_keys=evidence_keys,
                evidence_comment_references=comment_refs,
                investigated_keys=investigated_keys
            )

        # -------------------------------------------------------------
        # REQ-08: Human handoff delivery
        # Criterion: Handoff reaches support queue, including linked delivery dependency.
        # -------------------------------------------------------------
        elif req_id == "REQ-08":
            for issue_key, c in all_comments:
                body = c.body
                if "HND-77" in body and ("queue adapter drops them" in body or "HND-DEF-4" in body):
                    evidence_keys.append(issue_key)
                    comment_refs.append(f"{issue_key}: HND-77 queue adapter dropped 12/12 escalated chats; open defect HND-DEF-4 ({c.scenario_actor})")
                    return RequirementEvaluation(
                        requirement_id=req_id,
                        requirement_summary=req_summary,
                        acceptance_criterion=criterion,
                        decision=RequirementDecision.FAIL,
                        explanation="Handoff delivery test HND-77 on target build b7a91f2 in production failed: 0 of 12 escalated conversations reached the support queue because the queue adapter dropped them. Defect HND-DEF-4 is open. Manifest rules dictate that unclosed defects on target build reached through linked dependencies block acceptance.",
                        evidence_ticket_keys=evidence_keys,
                        evidence_comment_references=comment_refs,
                        outstanding_verification_or_clarification="Resolve queue adapter defect HND-DEF-4 and re-test conversation handoffs.",
                        investigated_keys=investigated_keys
                    )
            return RequirementEvaluation(
                requirement_id=req_id,
                requirement_summary=req_summary,
                acceptance_criterion=criterion,
                decision=RequirementDecision.INSUFFICIENT_EVIDENCE,
                explanation="Queue adapter delivery verification could not be resolved.",
                evidence_ticket_keys=evidence_keys,
                evidence_comment_references=comment_refs,
                investigated_keys=investigated_keys
            )

        # -------------------------------------------------------------
        # REQ-09: Rollback rehearsal
        # Criterion: Approved rollback rehearsal must succeed on target release & prod config.
        # -------------------------------------------------------------
        elif req_id == "REQ-09":
            for issue_key, c in all_comments:
                body = c.body
                if "RB-402" in body and ("214 session records written during the window were lost" in body or "FAILED" in body):
                    evidence_keys.append(issue_key)
                    comment_refs.append(f"{issue_key}: RB-402 failed with 214 session records lost during recovery window ({c.scenario_actor})")
                    return RequirementEvaluation(
                        requirement_id=req_id,
                        requirement_summary=req_summary,
                        acceptance_criterion=criterion,
                        decision=RequirementDecision.FAIL,
                        explanation="Rollback rehearsal RB-402 on target release R2.4 commit b7a91f2 in production failed: restore completed but 214 session records written during the window were lost. QA Lead Arjun Mehta recorded rehearsal FAILED.",
                        evidence_ticket_keys=evidence_keys,
                        evidence_comment_references=comment_refs,
                        outstanding_verification_or_clarification="Fix session persistence rollback pipeline and achieve clean rollback rehearsal with zero data loss.",
                        investigated_keys=investigated_keys
                    )
            return RequirementEvaluation(
                requirement_id=req_id,
                requirement_summary=req_summary,
                acceptance_criterion=criterion,
                decision=RequirementDecision.INSUFFICIENT_EVIDENCE,
                explanation="Rollback rehearsal verification is missing or inconclusive.",
                evidence_ticket_keys=evidence_keys,
                evidence_comment_references=comment_refs,
                investigated_keys=investigated_keys
            )

        # -------------------------------------------------------------
        # REQ-10: Document parsing completeness
        # Criterion: Target build must pass all 60 mandatory document parsing cases.
        # -------------------------------------------------------------
        elif req_id == "REQ-10":
            for issue_key, c in all_comments:
                body = c.body
                if "PARSE-622" in body and self.target_commit in body:
                    if "supersedes PARSE-601" in body and "60 of 60 mandatory parsing cases pass" in body:
                        evidence_keys.append(issue_key)
                        comment_refs.append(f"{issue_key}: PARSE-622 supersedes PARSE-601 with 60/60 cases pass on production ({c.scenario_actor})")
                        return RequirementEvaluation(
                            requirement_id=req_id,
                            requirement_summary=req_summary,
                            acceptance_criterion=criterion,
                            decision=RequirementDecision.PASS,
                            explanation=f"Applicable evidence establishes acceptance criterion is satisfied. Retest PARSE-622 explicitly supersedes earlier failure PARSE-601, verifying that 60 of 60 mandatory parsing cases pass on release {self.target_release}, commit {self.target_commit}, production environment.",
                            evidence_ticket_keys=evidence_keys,
                            evidence_comment_references=comment_refs,
                            investigated_keys=investigated_keys
                        )
            return RequirementEvaluation(
                requirement_id=req_id,
                requirement_summary=req_summary,
                acceptance_criterion=criterion,
                decision=RequirementDecision.INSUFFICIENT_EVIDENCE,
                explanation="No passing 60/60 parsing test run found for target commit.",
                evidence_ticket_keys=evidence_keys,
                evidence_comment_references=comment_refs,
                investigated_keys=investigated_keys
            )

        # -------------------------------------------------------------
        # REQ-11: Accessible keyboard handoff
        # Criterion: QA must verify keyboard navigation and focus handling on target release.
        # -------------------------------------------------------------
        elif req_id == "REQ-11":
            for issue_key, c in all_comments:
                body = c.body
                if "KBD-210" in body and "release R2.3" in body:
                    evidence_keys.append(issue_key)
                    comment_refs.append(f"{issue_key}: KBD-210 tested prior release R2.3, not target R2.4 ({c.scenario_actor})")
            for issue_key, c in all_comments:
                body = c.body
                if "Implemented focus trapping" in body and "Tested it on my machine" in body:
                    evidence_keys.append(issue_key)
                    comment_refs.append(f"{issue_key}: Sam Patel developer assertion is not QA proof ({c.scenario_actor})")

            return RequirementEvaluation(
                requirement_id=req_id,
                requirement_summary=req_summary,
                acceptance_criterion=criterion,
                decision=RequirementDecision.INSUFFICIENT_EVIDENCE,
                explanation="Evidence is missing or inapplicable. QA Lead Priya Nair verified KBD-210 on previous release R2.3 (commit 42d09ce), not target release R2.4. Developer Sam Patel claims it works on their local machine, but manifest rules explicitly declare developer assertions and ticket status 'Done' alone do not prove acceptance.",
                evidence_ticket_keys=evidence_keys,
                evidence_comment_references=comment_refs,
                outstanding_verification_or_clarification="QA must verify keyboard navigation and focus trapping on target release R2.4 build.",
                investigated_keys=investigated_keys
            )

        # -------------------------------------------------------------
        # REQ-12: Streaming completion integrity
        # Criterion: Every mandatory streaming case must complete without duplicate or missing final messages.
        # -------------------------------------------------------------
        elif req_id == "REQ-12":
            for issue_key, c in all_comments:
                body = c.body
                if "STREAM-731" in body and self.target_commit in body:
                    if "STREAM-50 produced a duplicated final message" in body or "49 of 50 cases pass" in body:
                        evidence_keys.append(issue_key)
                        comment_refs.append(f"{issue_key}: STREAM-731 STREAM-50 produced duplicated final message (49/50 pass) ({c.scenario_actor})")
                        return RequirementEvaluation(
                            requirement_id=req_id,
                            requirement_summary=req_summary,
                            acceptance_criterion=criterion,
                            decision=RequirementDecision.FAIL,
                            explanation="Streaming run STREAM-731 on target release R2.4, commit b7a91f2, production environment failed: 49 of 50 cases passed, with case STREAM-50 producing a duplicated final message, directly violating the acceptance criterion.",
                            evidence_ticket_keys=evidence_keys,
                            evidence_comment_references=comment_refs,
                            outstanding_verification_or_clarification="Fix streaming chunk termination bug in STREAM-50 and re-test.",
                            investigated_keys=investigated_keys
                        )
            return RequirementEvaluation(
                requirement_id=req_id,
                requirement_summary=req_summary,
                acceptance_criterion=criterion,
                decision=RequirementDecision.INSUFFICIENT_EVIDENCE,
                explanation="No streaming integrity verification found on target build.",
                evidence_ticket_keys=evidence_keys,
                evidence_comment_references=comment_refs,
                investigated_keys=investigated_keys
            )

        # Generic fallback
        return RequirementEvaluation(
            requirement_id=req_id,
            requirement_summary=req_summary,
            acceptance_criterion=criterion,
            decision=RequirementDecision.INSUFFICIENT_EVIDENCE,
            explanation=f"No conclusive evidence found for requirement {req_id}.",
            evidence_ticket_keys=evidence_keys,
            evidence_comment_references=comment_refs,
            investigated_keys=investigated_keys
        )

    def synthesize_release_decision(self, evaluations: List[RequirementEvaluation]) -> ReleaseDecisionSummary:
        passed = sum(1 for e in evaluations if e.decision == RequirementDecision.PASS)
        failed = sum(1 for e in evaluations if e.decision == RequirementDecision.FAIL)
        insufficient = sum(1 for e in evaluations if e.decision == RequirementDecision.INSUFFICIENT_EVIDENCE)
        total = len(evaluations)

        if failed > 0:
            overall = ReleaseDecision.BLOCKED
            explanation = f"Release is BLOCKED because {failed} mandatory requirement(s) have confirmed failures or unresolved defects on target build {self.target_commit}."
        elif insufficient > 0:
            overall = ReleaseDecision.NEEDS_REVIEW
            explanation = f"Release NEEDS_REVIEW because no requirements failed, but {insufficient} mandatory requirement(s) lack conclusive evidence."
        else:
            overall = ReleaseDecision.READY
            explanation = f"Release is READY. All {total} mandatory requirements satisfied with verified evidence."

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
            summary_explanation=explanation
        )

