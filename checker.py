"""
DecodeLabs - Cyber Security Industrial Training Kit
Project 1: Password Strength Checker
----------------------------------------------------
Core analysis engine — deliberately kept framework-agnostic so it can be
imported by the Flask web app, a CLI, or unit tests without change.

Key skills demonstrated:
    - String handling
    - Conditional logic
    - Security fundamentals (entropy estimation, constant-time comparison
      against a known-breach list, timing-attack awareness)
"""

from __future__ import annotations

import hmac
import math
import re
from dataclasses import dataclass, field, asdict

MIN_LENGTH = 8
IDEAL_LENGTH = 12

# A compact sample of frequently leaked / breached passwords. A production
# deployment would swap this for a full corpus (e.g. HaveIBeenPwned's
# k-anonymity API or a local rockyou.txt-derived set).
COMMON_PASSWORDS = {
    "123456", "123456789", "qwerty", "password", "12345",
    "12345678", "111111", "1234567", "123123", "abc123",
    "password1", "iloveyou", "1q2w3e4r", "qwertyuiop", "admin",
    "letmein", "welcome", "monkey", "dragon", "football",
}

CHECK_LABELS = {
    "length_8plus": "At least 8 characters",
    "length_12plus": "At least 12 characters (ideal)",
    "has_lowercase": "Contains a lowercase letter",
    "has_uppercase": "Contains an uppercase letter",
    "has_digit": "Contains a digit",
    "has_symbol": "Contains a symbol",
}


@dataclass
class StrengthResult:
    verdict: str = "Idle"           # Idle | Weak | Medium | Strong
    score: int = 0                  # 0-6
    entropy: float = 0.0            # estimated bits
    checks: dict = field(default_factory=dict)
    reasons: list = field(default_factory=list)
    leaked: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


def is_common_password(password: str) -> bool:
    """
    Compare against the known-leaked list using hmac.compare_digest so the
    check runs in constant time regardless of where a mismatch occurs —
    this avoids the timing side-channel the training material calls out
    (see 'Advanced Vulnerability: Timing Attacks').
    """
    candidate = password.lower().encode()
    for leaked in COMMON_PASSWORDS:
        if hmac.compare_digest(candidate, leaked.encode()):
            return True
    return False


def calculate_entropy(password: str) -> float:
    """
    Rough entropy estimate in bits: length * log2(charset size), where the
    charset size grows with the variety of character classes present.
    """
    charset = 0
    if re.search(r"[a-z]", password):
        charset += 26
    if re.search(r"[A-Z]", password):
        charset += 26
    if re.search(r"[0-9]", password):
        charset += 10
    if re.search(r"[^a-zA-Z0-9]", password):
        charset += 32
    if charset == 0 or not password:
        return 0.0
    return round(len(password) * math.log2(charset), 1)


def analyze_password(password: str) -> StrengthResult:
    """
    Evaluate a password and classify it as Weak, Medium, or Strong.
    This is the single source of truth used by both the CLI and the
    Flask API, so results are always consistent across interfaces.
    """
    result = StrengthResult()

    if not password:
        return result

    result.entropy = calculate_entropy(password)

    if is_common_password(password):
        result.verdict = "Weak"
        result.leaked = True
        result.reasons = ["This password appears in known data breach lists."]
        return result

    if len(password) < MIN_LENGTH:
        result.verdict = "Weak"
        result.checks = {"length_8plus": False}
        result.reasons = [f"Too short (< {MIN_LENGTH} characters) — immediate fail risk."]
        return result

    checks = {
        "length_8plus": len(password) >= MIN_LENGTH,
        "length_12plus": len(password) >= IDEAL_LENGTH,
        "has_lowercase": bool(re.search(r"[a-z]", password)),
        "has_uppercase": bool(re.search(r"[A-Z]", password)),
        "has_digit": bool(re.search(r"[0-9]", password)),
        "has_symbol": bool(re.search(r"[^a-zA-Z0-9]", password)),
    }
    result.checks = checks
    result.score = sum(1 for v in checks.values() if v)

    reasons = []
    if not checks["has_uppercase"]:
        reasons.append("Add at least one uppercase letter.")
    if not checks["has_lowercase"]:
        reasons.append("Add at least one lowercase letter.")
    if not checks["has_digit"]:
        reasons.append("Add at least one number.")
    if not checks["has_symbol"]:
        reasons.append("Add at least one symbol (e.g. ! @ # $ %).")
    if not checks["length_12plus"]:
        reasons.append(f"Consider using {IDEAL_LENGTH}+ characters for stronger protection.")

    if result.score <= 3:
        result.verdict = "Weak"
    elif result.score <= 5:
        result.verdict = "Medium"
    else:
        result.verdict = "Strong"

    result.reasons = reasons if reasons else ["Meets all checked criteria."]
    return result
