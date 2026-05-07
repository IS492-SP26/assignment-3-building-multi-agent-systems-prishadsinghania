"""
Input Guardrail
Checks user inputs for safety violations.
"""

from typing import Dict, Any, List


class InputGuardrail:
    """
    Guardrail for checking input safety.

    TODO: YOUR CODE HERE
    - Integrate with Guardrails AI or NeMo Guardrails
    - Define validation rules
    - Implement custom validators
    - Handle different types of violations
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize input guardrail.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.min_query_length = int(config.get("min_query_length", 5))
        self.max_query_length = int(config.get("max_query_length", 2000))
        self.allowed_topic_keywords = [
            keyword.lower()
            for keyword in config.get(
                "allowed_topic_keywords",
                [
                    "hci",
                    "human computer interaction",
                    "ux",
                    "ui",
                    "usability",
                    "accessibility",
                    "interaction design",
                    "user research",
                    "ai",
                    "education",
                    "ar",
                    "vr",
                    "interface",
                ],
            )
        ]
        self.toxic_keywords = [
            keyword.lower()
            for keyword in config.get(
                "toxic_keywords",
                ["kill", "bomb", "weapon", "self-harm", "hate speech", "terror"],
            )
        ]

    def validate(self, query: str) -> Dict[str, Any]:
        """
        Validate input query.

        Args:
            query: User input to validate

        Returns:
            Validation result

        TODO: YOUR CODE HERE
        - Implement validation logic
        - Check for toxic language
        - Check for prompt injection attempts
        - Check query length and format
        - Check for off-topic queries
        """
        violations = []
        normalized = (query or "").strip()

        if len(normalized) < self.min_query_length:
            violations.append({
                "validator": "length",
                "reason": f"Query too short (minimum {self.min_query_length} characters)",
                "severity": "low"
            })

        if len(normalized) > self.max_query_length:
            violations.append({
                "validator": "length",
                "reason": f"Query too long (maximum {self.max_query_length} characters)",
                "severity": "medium"
            })

        violations.extend(self._check_toxic_language(normalized))
        violations.extend(self._check_prompt_injection(normalized))
        violations.extend(self._check_relevance(normalized))

        high_risk = any(v.get("severity") == "high" for v in violations)
        return {
            "valid": len(violations) == 0,
            "violations": violations,
            "sanitized_input": normalized,
            "action": "refuse" if high_risk else ("warn" if violations else "allow"),
        }

    def _check_toxic_language(self, text: str) -> List[Dict[str, Any]]:
        """
        Check for toxic/harmful language.

        TODO: YOUR CODE HERE
        Suggested implementation:
        - Use a moderation API, Guardrails validator, or keyword/rule-based classifier
        - Return a list of violations with validator name, reason, and severity
        - Mark clearly unsafe requests as high severity
        """
        violations = []
        lower_text = text.lower()
        for keyword in self.toxic_keywords:
            if keyword in lower_text:
                violations.append({
                    "validator": "toxic_language",
                    "reason": f"Contains unsafe keyword: {keyword}",
                    "severity": "high",
                    "category": "harmful_content",
                })
        return violations

    def _check_prompt_injection(self, text: str) -> List[Dict[str, Any]]:
        """
        Check for prompt injection attempts.

        TODO: YOUR CODE HERE
        Suggested implementation:
        - Detect phrases like \"ignore previous instructions\",
        #   attempts to reveal system prompts, or role-confusion attacks
        - Consider whether the result should block the request or sanitize it
        """
        violations = []
        # Check for common prompt injection patterns
        injection_patterns = [
            "ignore previous instructions",
            "disregard",
            "forget everything",
            "system:",
            "sudo",
        ]

        for pattern in injection_patterns:
            if pattern.lower() in text.lower():
                violations.append({
                    "validator": "prompt_injection",
                    "reason": f"Potential prompt injection: {pattern}",
                    "severity": "high"
                })

        return violations

    def _check_relevance(self, query: str) -> List[Dict[str, Any]]:
        """
        Check if query is relevant to the system's purpose.

        TODO: YOUR CODE HERE
        Suggested implementation:
        - Compare the query to the configured topic in config.yaml
        - Use keyword heuristics or an LLM classifier
        - Return low/medium severity violations for off-topic requests
        """
        violations = []
        lower_query = query.lower()
        if self.allowed_topic_keywords and not any(
            keyword in lower_query for keyword in self.allowed_topic_keywords
        ):
            violations.append({
                "validator": "topic_relevance",
                "reason": "Query appears off-topic for configured research domain",
                "severity": "medium",
                "category": "off_topic_queries",
            })
        return violations
