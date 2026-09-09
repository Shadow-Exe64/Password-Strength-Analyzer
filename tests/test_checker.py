"""Unit tests for checker.py — the framework-agnostic analysis engine."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from checker import analyze_password, calculate_entropy, is_common_password


def test_empty_password_is_idle():
    result = analyze_password("")
    assert result.verdict == "Idle"
    assert result.score == 0
    assert result.entropy == 0.0


def test_short_password_is_weak():
    # Short but not itself a breached password, so this exercises the
    # length-only rejection branch rather than the breach-list branch.
    result = analyze_password("Zq7$rT")
    assert result.verdict == "Weak"
    assert result.checks == {"length_8plus": False}


def test_short_and_breached_password_flags_breach_first():
    # "abc123" is both short AND in the sample breach list — the breach
    # check should win and report as leaked.
    result = analyze_password("abc123")
    assert result.verdict == "Weak"
    assert result.leaked is True


def test_known_breached_password_is_weak_and_leaked():
    result = analyze_password("password")
    assert result.verdict == "Weak"
    assert result.leaked is True
    assert result.score == 0


def test_breach_check_is_case_insensitive():
    result = analyze_password("PaSsWoRd")
    assert result.leaked is True


def test_medium_password():
    result = analyze_password("Summer2026")
    assert result.verdict == "Medium"
    assert result.leaked is False


def test_strong_password_meets_every_check():
    result = analyze_password("Str0ng!Passw0rd#2026")
    assert result.verdict == "Strong"
    assert result.score == 6
    assert all(result.checks.values())
    assert result.reasons == ["Meets all checked criteria."]


def test_reasons_list_names_missing_criteria():
    result = analyze_password("lowercase1")
    assert any("uppercase" in reason.lower() for reason in result.reasons)
    assert any("symbol" in reason.lower() for reason in result.reasons)


def test_entropy_increases_with_charset_variety():
    lower_only = calculate_entropy("aaaaaaaa")
    mixed = calculate_entropy("aA1!aA1!")
    assert mixed > lower_only


def test_entropy_zero_for_empty_string():
    assert calculate_entropy("") == 0.0


def test_is_common_password_matches_known_entries():
    assert is_common_password("123456") is True
    assert is_common_password("correct-horse-battery-staple") is False
