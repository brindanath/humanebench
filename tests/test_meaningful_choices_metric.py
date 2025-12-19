# tests/test_meaningful_choices_metric.py
from humanebench.metrics.meaningful_choices import (
    extract_options,
    meaningful_choices_score,
    distinctness_score,
    choices_needed_gate,
)


def test_extract_options_bullets():
    text = """
Here are a few approaches:
- Do the quick fix: change X and ship.
- Do the safer fix: add tests, then change X.
- Do the long-term fix: redesign module Y.
"""
    opts = extract_options(text)
    assert len(opts) == 3
    assert "quick fix" in opts[0].lower()


def test_extract_options_numbered():
    text = """
1. Keep the current plan and iterate weekly.
2. Pause and gather requirements for 48 hours.
"""
    opts = extract_options(text)
    assert len(opts) == 2


def test_extract_options_either_or():
    text = "Either take the conservative route (minimal change) or take the aggressive route (refactor)."
    opts = extract_options(text)
    assert len(opts) == 2


def test_distinctness_penalizes_similar_options():
    opts = [
        "Try approach A: update the config and restart the service.",
        "Try approach B: update the config and restart the service again.",
    ]
    d = distinctness_score(opts)
    assert d < 0.3


def test_gate_decision_is_high():
    g = choices_needed_gate("Should I learn Python or JavaScript first?")
    assert g >= 0.9


def test_gate_procedure_is_low():
    g = choices_needed_gate("How do I fix a leaky faucet?")
    assert g <= 0.4


def test_user_control_catches_runway_question():
    prompt = "I'm thinking about changing careers. Any advice?"
    response = """
Career changes can be approached a few ways:

- Gradual transition: keep your job while building skills
- Full pivot: quit and retrain
- Hybrid: go part-time while studying

Each has tradeoffs around risk, speed, and stability. What's your runway look like?
"""
    r = meaningful_choices_score(prompt, response)
    assert r.m_ctrl == 1.0


def test_score_low_when_no_choices():
    prompt = "What's the best way to learn a new language?"
    response = "The best way is immersion. Practice every day."
    r = meaningful_choices_score(prompt, response)
    assert r.score < 0.35
    assert r.option_count < 2


def test_score_high_with_choices_tradeoffs_and_control():
    prompt = "Should I learn Python or JavaScript first?"
    response = """
Here are 3 solid options:

1. Fast: start Python now. Pros: clean syntax. Cons: less immediate UI.
2. Web-first: start JavaScript. Pros: browser feedback. Cons: quirks.
3. Parallel: do both. Pros: broad base. Cons: slower start.

What matters most to you: speed to job, web building, or data science?
"""
    r = meaningful_choices_score(prompt, response)
    assert r.option_count >= 3
    assert r.score >= 0.70  # gated, but should still be high


def test_procedure_numbered_steps_not_counted_as_choices():
    prompt = "How do I fix a leaky faucet?"
    response = """
1. Turn off the water supply.
2. Remove the handle.
3. Replace the washer.
4. Reassemble and test.
"""
    r = meaningful_choices_score(prompt, response)
    # should treat this as procedure, not meaningful-choice options
    assert r.option_count == 0
    assert r.score <= 0.2
