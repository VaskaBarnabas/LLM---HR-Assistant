import os
import json
import tempfile
import uuid
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from backend.workflow import chain, anonymized_text_to_html
from backend.chromaClient import query as chroma_query, store_cv_with_id, rank_by_job

_rank_llm = ChatOpenAI(
    model="docker.io/ai/gemma4:E4B",
    base_url="http://localhost:12434/v1",
    api_key="docker",
    temperature=0,
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["POST"],
    allow_headers=["*"],
)


@app.post("/analyze")
async def analyze(files: list[UploadFile] = File(...), filters: str = Form("{}")):
    tmp_paths = []
    try:
        # Save each uploaded PDF to a temp file
        for upload in files:
            content = await upload.read()
            tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
            tmp.write(content)
            tmp.close()
            tmp_paths.append(tmp.name)

        try:
            filters_dict = json.loads(filters)
        except Exception:
            filters_dict = {}

        result_state = chain.invoke({"paths": tmp_paths, "filters": filters_dict, "anonymized_texts": [], "texts": [], "candidates": []})
        candidates = result_state["candidates"]

        anonymized_texts = result_state.get("anonymized_texts") or []

        result = []
        for i, c in enumerate(candidates):
            # Normalize skills: try multiple possible key names, flatten if nested
            raw_skills = (
                c.get("skills") or
                c.get("competencies") or
                c.get("technologies") or
                []
            )
            if isinstance(raw_skills, dict):
                # e.g. {"technical": [...], "soft": [...]}
                flat = []
                for v in raw_skills.values():
                    flat.extend(v if isinstance(v, list) else [str(v)])
                raw_skills = flat
            elif isinstance(raw_skills, str):
                raw_skills = [s.strip() for s in raw_skills.split(",") if s.strip()]

            raw_langs = c.get("languages") or []
            if isinstance(raw_langs, str):
                raw_langs = [l.strip() for l in raw_langs.split(",") if l.strip()]

            raw_texts = result_state.get("texts") or []
            result.append({
                "id": str(uuid.uuid4()),
                "name": c.get("name") or "Unknown",
                "email": c.get("email") or "",
                "phone": c.get("phone") or "",
                "location": c.get("location") or "",
                "skills": raw_skills,
                "languages": raw_langs,
                "fileName": files[i].filename if i < len(files) else "",
                "analyzedAt": __import__("datetime").datetime.utcnow().isoformat(),
                "anonymizedHtml": anonymized_text_to_html(anonymized_texts[i]) if i < len(anonymized_texts) else "",
                "cvText": raw_texts[i] if i < len(raw_texts) else "",
            })

        return {"candidates": result}

    finally:
        for path in tmp_paths:
            try:
                os.unlink(path)
            except OSError:
                pass


class QueryRequest(BaseModel):
    query: str
    n_results: int = 3


@app.post("/query")
async def query_cvs(body: QueryRequest):
    results = chroma_query(body.query, body.n_results)
    return {"results": results}


class StoreCVRequest(BaseModel):
    application_id: str
    cv_text: str


@app.post("/store-cv")
async def store_cv(body: StoreCVRequest):
    if body.cv_text:
        store_cv_with_id(body.cv_text, body.application_id)
    return {"ok": True}


class RankCandidate(BaseModel):
    id: str
    name: str
    skills: list[str] = []
    languages: list[str] = []
    location: str = ""


class RankRequest(BaseModel):
    job_title: str
    job_description: str
    candidates: list[RankCandidate]


@app.post("/rank")
async def rank_candidates(body: RankRequest):
    if not body.candidates:
        return {"rankings": []}

    query_text = f"{body.job_title}. {body.job_description}".strip()
    candidate_ids = [c.id for c in body.candidates]
    id_to_candidate = {c.id: c for c in body.candidates}

    # ChromaDB retrieves which candidates have stored CVs for this job
    chroma_results = rank_by_job(query_text, candidate_ids, n_results=min(len(candidate_ids), 10))
    pool = [id_to_candidate[r["id"]] for r in chroma_results if r["id"] in id_to_candidate]

    if not pool:
        return {"rankings": []}

    candidates_text = "\n".join(
        f"ID: {c.id}\n  Név: {c.name}\n  Skills: {', '.join(c.skills[:10]) or 'N/A'}\n  Helyszín: {c.location or 'N/A'}"
        for c in pool
    )

    import re
    prompt = (
        f"Te egy tapasztalt HR szakértő vagy. Rangsorold az alábbi jelölteket a megadott pozícióhoz "
        f"legjobbtól leggyengébbig, és minden jelölthöz írj 1-2 mondatos magyar indoklást.\n\n"
        f"Pozíció: {body.job_title}\n"
        f"Leírás: {body.job_description or 'Nem megadott'}\n\n"
        f"Jelöltek:\n{candidates_text}\n\n"
        f"Válaszolj kizárólag JSON tömbként, a legjobb jelölttől kezdve:\n"
        f'[{{"id": "<jelölt id>", "explanation": "indoklás"}}, ...]\n'
        f"Csak a JSON tömböt add vissza, semmi mást."
    )

    try:
        resp = _rank_llm.invoke([HumanMessage(content=prompt)])
        match = re.search(r'\[.*\]', resp.content, re.DOTALL)
        parsed = json.loads(match.group()) if match else json.loads(resp.content)
    except Exception:
        parsed = []

    seen: set[str] = set()
    rankings = []
    for item in parsed:
        cid = item.get("id", "")
        if cid in id_to_candidate and cid not in seen:
            seen.add(cid)
            c = id_to_candidate[cid]
            rankings.append({
                "id": cid,
                "rank": len(rankings) + 1,
                "name": c.name,
                "skills": c.skills,
                "location": c.location,
                "explanation": item.get("explanation", ""),
            })
        if len(rankings) >= 5:
            break

    return {"rankings": rankings}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend:app", host="0.0.0.0", port=8000, reload=True)
