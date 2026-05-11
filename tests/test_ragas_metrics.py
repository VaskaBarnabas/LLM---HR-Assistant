"""
RAGAS metrika tesztek — Faithfulness és Relevancy mérése.

- Faithfulness: A rangsorolási indoklás tényleg az önéletrajzból ered-e,
  vagy az LLM "hallucinál"?
- Relevancy (ContextRelevance): A visszakeresett CV-szöveg mekkora hányada
  releváns a munkaköri leíráshoz képest?

Futtatás:
    ./run_tests.sh --ragas
    ./run_tests.sh --ragas test_faithfulness_grounded

Előfeltétel: a helyi LLM elérhetőnek kell lennie (http://localhost:12434).
"""

import asyncio
import urllib.request
import urllib.error
from pathlib import Path

import pytest
from dotenv import load_dotenv
from openai import AsyncOpenAI
from ragas.llms import llm_factory
from ragas.metrics.collections import Faithfulness, ContextRelevance

load_dotenv(Path(__file__).parent.parent / "backend" / ".env")


# ─── Konfiguráció ─────────────────────────────────────────────────────────────

_LLM_BASE_URL = "http://localhost:12434/v1"
_LLM_MODEL = "docker.io/ai/gemma4:E4B"


@pytest.fixture(scope="module", autouse=True)
def require_llm():
    try:
        urllib.request.urlopen(f"{_LLM_BASE_URL}/models", timeout=5)
    except (urllib.error.URLError, OSError):
        pytest.skip("LLM nem elérhető a http://localhost:12434 címen — indítsd el előbb")


@pytest.fixture(scope="module")
def ragas_llm():
    client = AsyncOpenAI(base_url=_LLM_BASE_URL, api_key="docker")
    return llm_factory(_LLM_MODEL, provider="openai", client=client)


# ─── Tesztadatok ──────────────────────────────────────────────────────────────

_JOB_DESCRIPTION = """
Senior Python fejlesztő
Elvárások: 5+ év Python tapasztalat, FastAPI vagy Django, PostgreSQL,
REST API tervezés, Docker, CI/CD pipeline-ok ismerete.
"""

_CV_RELEVANT = """
Kovács János — Senior szoftverfejlesztő
5+ éves Python fejlesztési tapasztalat.
FastAPI keretrendszerrel RESTful API-kat fejlesztett fintech platformokhoz.
Erős PostgreSQL ismeretek: lekérdezés-optimalizálás és sématervezés.
Dockert és Kubernetes-t használt éles környezetben.
GitHub Actions segítségével CI/CD pipeline-okat üzemeltetett.
"""

_CV_IRRELEVANT = """
Kiss Béla — Séf / Cukrász
15 éves tapasztalat a gasztronómia területén.
Michelin-csillagos étteremben dolgozott sous-chef pozícióban.
Specialitása a francia és olasz konyha, cukrászdák süteménysorozatainak fejlesztése.
Felelős az alapanyag-rendelésért és a napi ételek minőség-ellenőrzéséért.
"""

# Indoklás, amely kizárólag a CV tényleges tartalmából táplálkozik
_GROUNDED_EXPLANATION = (
    "A jelölt 5+ éves Python tapasztalattal rendelkezik, FastAPI-t alkalmazott "
    "REST API fejlesztéshez, PostgreSQL adatbázist kezelt, Docker és Kubernetes "
    "környezetben dolgozott, és CI/CD pipeline-okat állított fel GitHub Actions-szel."
)

# Indoklás, amely a CV-ben nem szereplő kitalált tényeket tartalmaz
_HALLUCINATED_EXPLANATION = (
    "A jelölt kiemelkedő gépi tanulási tapasztalattal rendelkezik, vezető AI kutató "
    "volt az MIT-en, tíz sikeres startupot alapított Silicon Valley-ben, és Nobel-díjas "
    "kutatócsoport tagja volt. Doktori fokozatát a Stanford Egyetemen szerezte."
)


# ─── Faithfulness tesztek ─────────────────────────────────────────────────────

def test_faithfulness_grounded(ragas_llm):
    """CV-ből merített indoklás faithfulness pontszáma >= 0.5 legyen."""
    scorer = Faithfulness(llm=ragas_llm)
    result = asyncio.run(scorer.ascore(
        user_input=_JOB_DESCRIPTION,
        response=_GROUNDED_EXPLANATION,
        retrieved_contexts=[_CV_RELEVANT],
    ))
    score = result.value
    print(f"\n[Faithfulness — grounded] score: {score:.3f}")
    assert score is not None, "A Faithfulness pontszám None nem lehet"
    assert 0.0 <= score <= 1.0, f"Pontszám [0,1] tartományon kívül: {score}"
    assert score >= 0.5, (
        f"CV-alapú indoklásnak >= 0.5 kellene, kapott érték: {score:.3f}. "
        "Az indoklás valódi CV-tényeket idéz, mégis alacsony pontszámot kapott."
    )


def test_faithfulness_hallucinated(ragas_llm):
    """Kitalált tényeket tartalmazó indoklás faithfulness pontszáma <= 0.5 legyen."""
    scorer = Faithfulness(llm=ragas_llm)
    result = asyncio.run(scorer.ascore(
        user_input=_JOB_DESCRIPTION,
        response=_HALLUCINATED_EXPLANATION,
        retrieved_contexts=[_CV_RELEVANT],
    ))
    score = result.value
    print(f"\n[Faithfulness — hallucinated] score: {score:.3f}")
    assert score is not None, "A Faithfulness pontszám None nem lehet"
    assert 0.0 <= score <= 1.0, f"Pontszám [0,1] tartományon kívül: {score}"
    assert score <= 0.5, (
        f"Hallucinált indoklásnak <= 0.5 kellene, kapott érték: {score:.3f}. "
        "Az indoklás a CV-ben nem szereplő tényeket tartalmaz."
    )


# ─── Relevancy tesztek (ContextRelevance) ────────────────────────────────────
#
# Az AnswerRelevancy metrika professzionális CV-knél nem differenciál jól,
# mert minden önéletrajzból hasonló általános kérdéseket generál.
# A ContextRelevance méri közvetlenül, hogy a visszakeresett szöveg
# (CV) mekkora hányada releváns a kérdéshez (állásleírás) — ez pontosan
# az a mérés, amit a RAG retrieval minőségéhez keresünk.

def test_relevancy_matching_cv(ragas_llm):
    """A munkaköri leírással egyező CV context relevance pontszáma >= 0.5 legyen."""
    scorer = ContextRelevance(llm=ragas_llm)
    result = asyncio.run(scorer.ascore(
        user_input=_JOB_DESCRIPTION,
        retrieved_contexts=[_CV_RELEVANT],
    ))
    score = result.value
    print(f"\n[ContextRelevance — matching CV] score: {score:.3f}")
    assert score is not None, "A Relevancy pontszám None nem lehet"
    assert 0.0 <= score <= 1.0, f"Pontszám [0,1] tartományon kívül: {score}"
    assert score >= 0.5, (
        f"Illeszkedő CV-nek >= 0.5 kellene, kapott érték: {score:.3f}. "
        "A Python fejlesztő CV mondatainak többségének relevánsnak kell lennie a pozícióhoz."
    )


def test_relevancy_mismatched_cv(ragas_llm):
    """Nem illeszkedő CV context relevance pontszáma <= 0.3 legyen."""
    scorer = ContextRelevance(llm=ragas_llm)
    result = asyncio.run(scorer.ascore(
        user_input=_JOB_DESCRIPTION,
        retrieved_contexts=[_CV_IRRELEVANT],
    ))
    score = result.value
    print(f"\n[ContextRelevance — mismatched CV] score: {score:.3f}")
    assert score is not None, "A Relevancy pontszám None nem lehet"
    assert 0.0 <= score <= 1.0, f"Pontszám [0,1] tartományon kívül: {score}"
    assert score <= 0.3, (
        f"Nem illeszkedő CV-nek <= 0.3 kellene, kapott érték: {score:.3f}. "
        "A séf CV mondatai nem relevánsak egy Python fejlesztői pozícióhoz."
    )
