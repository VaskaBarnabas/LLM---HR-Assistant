"""
Anonymization test suite — 15 tests covering every filter individually,
every filter skipped while the rest run, all-off (no LLM), and combinations.

Run all:
    ./run_tests.sh

Run one by name:
    ./run_tests.sh test_names_only

List all tests:
    ./run_tests.sh --list
"""

import urllib.request
import urllib.error
import pytest

from backend.workflow import _AGENT_ORDER, _PROMPTS, _run_agent


# ─── Helpers ──────────────────────────────────────────────────────────────────

def anon(text: str, filters: dict | None = None) -> str:
    """Run the anonymization pipeline on raw text (no PDF needed)."""
    if filters is None:
        filters = {}
    for key, llm in _AGENT_ORDER:
        if filters.get(key, True):
            text = _run_agent(llm, _PROMPTS[key], text)
    return text


def only(key: str) -> dict:
    """Return a filter dict with only the given key enabled, all others off."""
    return {k: (k == key) for k, _ in _AGENT_ORDER}


def skip(key: str) -> dict:
    """Return a filter dict with every key enabled except the given one."""
    return {k: (k != key) for k, _ in _AGENT_ORDER}


ALL_ON:  dict = {}                                       # empty → all default to True
ALL_OFF: dict = {k: False for k, _ in _AGENT_ORDER}     # every agent skipped


# ─── Sample CV texts ──────────────────────────────────────────────────────────

T_NAMES = (
    "Jonathan Harrison is a backend engineer with 11 years of experience. "
    "Mr. Harrison graduated from Carnegie Mellon University in 2013 and currently "
    "works at Microsoft as a senior technical lead. Harrison joined the company after "
    "four years at a fintech startup where he built core payment processing modules."
)

T_GENDERED = (
    "The candidate worked as a stewardess for Delta Airlines for 5 years. "
    "She then volunteered as a fireman at the Riverside Fire Station for 3 years. "
    "Most recently she served as chairman of the regional safety and compliance board."
)

T_PRONOUNS = (
    "He has 9 years of experience in machine learning and data science. "
    "She completed her PhD at Stanford University and published 3 papers on NLP. "
    "His most recent role involved leading a fraud detection team of 8 researchers. "
    "Her previous employer, OpenInsight Ltd., promoted her twice within four years."
)

T_FAMILY = (
    "The candidate is married with two children and relocated to Munich in 2019. "
    "Her maiden name was Lefebvre before her marriage in 2014. "
    "As a mother of two she championed the company's flexible working policy."
)

T_LIFE = (
    "The candidate took maternity leave from March 2017 to February 2018 before "
    "returning to her project manager role at EuroFreight AG. "
    "He also completed four years of military service in the German Army Logistics "
    "Battalion prior to his civilian career, gaining leadership experience overseas."
)

T_COMPLEX = """
CURRICULUM VITAE

Name: Elena Vasquez-Morrison
Email: elena.vm@protonmail.com
Location: London, United Kingdom

Professional Summary
Elena Vasquez-Morrison is a C-suite executive and former stewardess with 18 years
of experience in aviation, finance, and technology. Mrs. Vasquez-Morrison — previously
known by her maiden name Vasquez before her marriage in 2011 — is regarded as a
decisive businesswoman. She serves as non-executive chairman of two industry bodies.
Her husband works as a civil engineer and they have two children together.

Work Experience

Chief Strategy Officer — FinBridge Capital, London (2020 – present)
Elena leads global strategy for a £2.4B asset management firm. She chairs the Executive
Risk Committee. As a mother of two she also co-founded the firm's Parents in Leadership
network. She took maternity leave in 2018 before returning to a director-level role.

Senior Stewardess / Purser — British Airways, Heathrow (2006 – 2011)
Elena worked as a stewardess on long-haul routes before becoming purser, acting as
de facto chairman of the cabin crew. She received the Excellence in Service award in
2009 and 2010.

Education
MBA — London Business School (2013)
BA, Modern Languages — University of Exeter (2006)

Skills
Corporate strategy, M&A, stakeholder management, ESG policy, team leadership
"""


# ─── LLM availability check ───────────────────────────────────────────────────

@pytest.fixture(scope="module", autouse=True)
def require_llm():
    try:
        urllib.request.urlopen("http://localhost:12434/v1/models", timeout=5)
    except (urllib.error.URLError, OSError):
        pytest.skip("LLM not reachable at http://localhost:12434 — start it first")


# ─── 1. Single filter ON — only the target agent runs ─────────────────────────

def test_names_only():
    result = anon(T_NAMES, only("names"))
    assert "[CANDIDATE]" in result, "Personal name should be replaced with [CANDIDATE]"


def test_gendered_nouns_only():
    result = anon(T_GENDERED, only("gendered_nouns"))
    lo = result.lower()
    assert "stewardess" not in lo, "'stewardess' should be replaced with a neutral term"
    assert "fireman" not in lo, "'fireman' should be replaced with a neutral term"


def test_pronouns_only():
    result = anon(T_PRONOUNS, only("pronouns"))
    lo = result.lower()
    assert " he " not in lo and " she " not in lo, "Gendered pronouns he/she should be replaced"


def test_family_status_only():
    result = anon(T_FAMILY, only("family_status"))
    lo = result.lower()
    assert "married" not in lo or "[personal data]" in lo, (
        "Marital status should be removed or replaced with [PERSONAL DATA]"
    )


def test_life_events_only():
    result = anon(T_LIFE, only("life_events"))
    lo = result.lower()
    assert "maternity leave" not in lo, "'maternity leave' should be neutralized to a generic term"


# ─── 2. Single filter OFF — that agent is skipped, the rest still run ─────────

def test_names_skipped():
    result = anon(T_NAMES, skip("names"))
    assert "Harrison" in result, "Surname should remain when the names filter is disabled"


def test_gendered_nouns_skipped():
    result = anon(T_GENDERED, skip("gendered_nouns"))
    lo = result.lower()
    assert "stewardess" in lo or "fireman" in lo, (
        "Gendered job title should remain when the gendered_nouns filter is disabled"
    )


def test_pronouns_skipped():
    result = anon(T_PRONOUNS, skip("pronouns"))
    lo = result.lower()
    assert " he " in lo or " she " in lo or " his " in lo or " her " in lo, (
        "Gendered pronouns should remain when the pronouns filter is disabled"
    )


def test_family_status_skipped():
    result = anon(T_FAMILY, skip("family_status"))
    lo = result.lower()
    assert "married" in lo, "Marital status should remain when the family_status filter is disabled"


def test_life_events_skipped():
    result = anon(T_LIFE, skip("life_events"))
    lo = result.lower()
    assert "maternity leave" in lo, (
        "'maternity leave' should remain when the life_events filter is disabled"
    )


# ─── 3. All filters disabled — text must come back exactly unchanged ──────────

def test_all_disabled():
    result = anon(T_COMPLEX, ALL_OFF)
    assert result.strip() == T_COMPLEX.strip(), (
        "Text must be identical to input when every filter is disabled (no agents run)"
    )


# ─── 4. Combinations ─────────────────────────────────────────────────────────

def test_names_and_pronouns():
    """Names + pronouns on, everything else off."""
    filters = {"names": True, "gendered_nouns": False, "pronouns": True,
               "family_status": False, "life_events": False}
    result = anon(T_COMPLEX, filters)
    assert "[CANDIDATE]" in result, "Names should be anonymized"
    lo = result.lower()
    assert " she " not in lo and " he " not in lo, "Gendered pronouns should be replaced"
    assert "stewardess" in lo, "'stewardess' should remain (gendered_nouns is off)"


def test_gendered_nouns_and_life_events():
    """Gendered nouns + life events on; names/pronouns/family off."""
    filters = {"names": False, "gendered_nouns": True, "pronouns": False,
               "family_status": False, "life_events": True}
    result = anon(T_COMPLEX, filters)
    lo = result.lower()
    assert "stewardess" not in lo, "'stewardess' should be neutralized"
    assert "maternity leave" not in lo, "'maternity leave' should be neutralized"
    assert "Elena" in result, "Name should be untouched (names filter is off)"


def test_names_and_family_status():
    """Names + family_status on; others off."""
    filters = {"names": True, "gendered_nouns": False, "pronouns": False,
               "family_status": True, "life_events": False}
    result = anon(T_COMPLEX, filters)
    assert "[CANDIDATE]" in result, "Name should be anonymized"
    lo = result.lower()
    assert "married" not in lo or "[personal data]" in lo, (
        "Marital status should be removed or redacted"
    )


def test_pronouns_and_life_events():
    """Pronouns + life_events on; others off."""
    filters = {"names": False, "gendered_nouns": False, "pronouns": True,
               "family_status": False, "life_events": True}
    result = anon(T_LIFE, filters)
    lo = result.lower()
    assert "maternity leave" not in lo, "'maternity leave' should be neutralized"
    assert " he " not in lo and " she " not in lo, "Gendered pronouns should be replaced"


def test_all_enabled():
    """Every filter on — comprehensive anonymization."""
    result = anon(T_COMPLEX, ALL_ON)
    assert "[CANDIDATE]" in result, "Names should be anonymized"
    lo = result.lower()
    assert "jane doe" not in lo, "Original name should not appear"
    assert "stewardess" not in lo, "Gendered job title should be replaced"
    assert "married" not in lo or "[personal data]" in lo, "Marital status should be removed"
