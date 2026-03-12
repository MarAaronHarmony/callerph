"""Tests for system prompt loader."""

import pytest

from app.voice.prompts import load_prompt


def test_load_valid_prompt():
    content = load_prompt("pagepro.md")
    assert "PagePro" in content
    assert "₱15,000" in content
    assert "₱25,000" in content


def test_load_nonexistent_prompt():
    with pytest.raises(FileNotFoundError):
        load_prompt("nonexistent.md")


def test_prompt_contains_lead_capture():
    content = load_prompt("pagepro.md")
    assert "Lead Capture" in content or "lead capture" in content.lower()


def test_prompt_contains_language_instructions():
    content = load_prompt("pagepro.md")
    assert "Tagalog" in content or "Taglish" in content
