"""
Output Guardrail
Checks system outputs for safety violations.
"""

from typing import Dict, Any, List
import re


class OutputGuardrail:
    """
    Guardrail for checking output safety.

    TODO: YOUR CODE HERE
    - Integrate with Guardrails AI or NeMo Guardrails
    - Check for harmful content in responses
    - Verify factual consistency
    - Detect potential misinformation
    - Remove PII (personal identifiable information)
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize output guardrail.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.block_on_harmful = config.get("block_on_harmful", True)
        self.block_on_pii = config.get("block_on_pii", False)
        self.enable_bias_check = config.get("enable_bias_check", True)

    def validate(self, response: str, sources: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Validate output response.

        Args:
            response: Generated response to validate
            sources: Optional list of sources used (for fact-checking)

        Returns:
            Validation result

        TODO: YOUR CODE HERE
        - Implement validation logic
        - Check for harmful content
        - Check for PII
        - Verify claims against sources
        - Check for bias
        """
        violations = []

        pii_violations = self._check_pii(response)
        violations.extend(pii_violations)

        harmful_violations = self._check_harmful_content(response)
        violations.extend(harmful_violations)

        if sources:
            consistency_violations = self._check_factual_consistency(response, sources)
            violations.extend(consistency_violations)

        if self.enable_bias_check:
            violations.extend(self._check_bias(response))

        high_risk = any(v.get("severity") == "high" for v in violations)
        return {
            "valid": len(violations) == 0 and not high_risk,
            "violations": violations,
            "sanitized_output": self._sanitize(response, violations) if violations else response,
            "action": "refuse" if high_risk else ("sanitize" if violations else "allow"),
        }

    def _check_pii(self, text: str) -> List[Dict[str, Any]]:
        """
        Check for personally identifiable information.

        TODO: YOUR CODE HERE
        Suggested implementation:
        - Expand regex checks for emails, phone numbers, SSNs, addresses, etc.
        - Use a stronger PII detection library if desired
        - Return violation metadata needed for redaction
        """
        violations = []

        # Simple regex patterns for common PII
        patterns = {
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
        }

        for pii_type, pattern in patterns.items():
            matches = re.findall(pattern, text)
            if matches:
                violations.append({
                    "validator": "pii",
                    "pii_type": pii_type,
                    "reason": f"Contains {pii_type}",
                    "severity": "high",
                    "matches": matches
                })

        return violations

    def _check_harmful_content(self, text: str) -> List[Dict[str, Any]]:
        """
        Check for harmful or inappropriate content.

        TODO: YOUR CODE HERE
        Suggested implementation:
        - Detect unsafe instructions, hateful content, or violent guidance
        - Use a moderation model, guardrail validator, or rule-based policy check
        - Return severity levels so the caller knows whether to refuse or sanitize
        """
        violations = []

        harmful_keywords = ["make a bomb", "bypass security", "violent attack", "kill", "harm yourself"]
        for keyword in harmful_keywords:
            if keyword in text.lower():
                violations.append({
                    "validator": "harmful_content",
                    "reason": f"May contain harmful content: {keyword}",
                    "severity": "high",
                    "category": "harmful_content",
                })

        return violations

    def _check_factual_consistency(
        self,
        response: str,
        sources: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Check if response is consistent with sources.

        TODO: YOUR CODE HERE
        Suggested implementation:
        - Compare claims in the response against the retrieved evidence
        - Verify that citations actually support the statements made
        - Optionally use an LLM-based verifier or a citation-grounding check
        """
        violations = []

        if not sources:
            return violations

        normalized_source_text = " ".join(
            f"{source.get('title', '')} {source.get('snippet', '')}".lower()
            for source in sources
            if isinstance(source, dict)
        )
        citation_mentions = response.count("[Source:")
        if citation_mentions > len(sources):
            violations.append({
                "validator": "factual_consistency",
                "reason": "Response has more citation markers than retrieved sources",
                "severity": "medium",
                "category": "misinformation",
            })
        if "according to" in response.lower() and not normalized_source_text:
            violations.append({
                "validator": "factual_consistency",
                "reason": "Response claims evidence without usable source context",
                "severity": "medium",
                "category": "misinformation",
            })

        return violations

    def _check_bias(self, text: str) -> List[Dict[str, Any]]:
        """
        Check for biased language.

        TODO: YOUR CODE HERE
        Suggested implementation:
        - Look for stereotypes, blanket generalizations, or discriminatory language
        - Decide whether to redact, revise, or refuse the output
        """
        violations = []
        biased_phrases = [
            "all people from",
            "those people are",
            "naturally inferior",
            "genetically better",
        ]
        lower_text = text.lower()
        for phrase in biased_phrases:
            if phrase in lower_text:
                violations.append({
                    "validator": "bias",
                    "reason": f"Potentially biased phrase detected: {phrase}",
                    "severity": "medium",
                    "category": "personal_attacks",
                })
        return violations

    def _sanitize(self, text: str, violations: List[Dict[str, Any]]) -> str:
        """
        Sanitize text by removing/redacting violations.

        TODO: YOUR CODE HERE
        Suggested implementation:
        - Redact matched PII spans
        - Replace unsafe sections with placeholder text
        - Optionally return a refusal message for severe violations
        """
        sanitized = text

        # Redact PII
        for violation in violations:
            if violation.get("validator") == "pii":
                for match in violation.get("matches", []):
                    sanitized = sanitized.replace(match, "[REDACTED]")
            if violation.get("validator") == "harmful_content":
                return "I cannot provide this content due to safety policies."

        return sanitized
