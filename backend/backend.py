import os
import tempfile
import uuid
from pathlib import Path

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

from hr_workflow import analyze_pdf_paths

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["POST"],
    allow_headers=["*"],
)


@app.post("/analyze")
async def analyze(files: list[UploadFile] = File(...)):
    tmp_paths = []
    try:
        # Save each uploaded PDF to a temp file
        for upload in files:
            content = await upload.read()
            tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
            tmp.write(content)
            tmp.close()
            tmp_paths.append(tmp.name)

        candidates = analyze_pdf_paths(tmp_paths)

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
            })

        return {"candidates": result}

    finally:
        for path in tmp_paths:
            try:
                os.unlink(path)
            except OSError:
                pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend:app", host="0.0.0.0", port=8000, reload=True)
