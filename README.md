# Futtatás

### Előfeltételek
- Python 3.12
- Node.js 18+
- Docker

### 1. Környezeti változók beállítása

`backend/.env`:
```
GEMINI_API_KEY=...
CHROMA_COHERE_API_KEY=...
```

`frontend/.env.local`:
```
BACKEND_URL=http://localhost:8001
```

### 2. Python virtuális környezet és függőségek

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install chromadb cohere fastapi uvicorn python-multipart langchain-community langchain-google-genai langgraph pypdf pillow python-dotenv
```

### 3. ChromaDB indítása (Docker)

```bash
docker run -p 8000:8000 chromadb/chroma:1.0.0
```

### 4. Python backend indítása

A projekt gyökeréből (`LLM---HR-Assistant`):
```bash
uvicorn backend.backend:app --port 8001 --reload
```

### 5. Next.js frontend indítása

```bash
cd frontend
npm install
npm run dev
```

Az alkalmazás ezután elérhető: `http://localhost:3000`


# Haladások

### 1. hét
A megbeszéltek szerint, a következőkkel haladtam a héten:

Létrehoztam egy Github repot, amiben a félév során minden munkám ide fog kerülni. Ezen belül létrehoztam 2 ágat, a main illetve a develop branch-et. A main ág lesz fogja tartalmazni a "release"-eket. A develop branch-ből ágaznak el a feature branch-ek, amiket majd ide merge-elek vissza, amint elkészül az adott feature.

Regisztráltam a Google Gemini API-ra, és legenráltam egy api kulcsot.

Írtam egy Python szrkiptet, amivel API segítségével kommunkál, nem pedig egy chat felületen. Ehhez használtam a legenerált API kulcsot, amit kiszerveztem egy .env fájlba.

Megismerkedtem a Promptolás alapjaival a promptingguide.ai oldalról.

Megismerkedtem a temperature és a top_p fogalmakkal, amiket változtatgattam és figyeltem a kapott válaszok között lévő különbséget. Ezen kívül sok más lehetésges beállítást is láttam és kirpóbáltam. Ehhez a Google AI Studio Playground felületet használtam. 

Megismerkedtem hogy egy prompt hogyan épül fel, és az oldalon lévő példákon keresztül ezt magam is kirpóbáltam.

Végül megisemrkedtem pár prompt teknikával, mint a Zero-shot prompting, Few-shot prompting, CoT (Chain-of-Thought), Self-Consistency

### 2. hét

Megismerkedtem az Agentek alapjaival, illetve alapvető működésükkel.

Megismerkedem a LangChain használatával, valamint kicsit belenéztem a LangGraph és a LangChain különbségébe is.

Kerestem egy példa önéletrajzot, amiből kinyertem az adatokat a pypdf könyvtár segítségével.

Létrehoztam egy Agent-tet a LangChain segítségével, ami rendelkezik 2 tool-lal, az egyikkel a skilleket a másikkal a személyes adatokat lehet kinyerni a neki átadott önéletrajz szövegből. 

Végül egyesítettem a két dolgot, így kinyertem az adatokat a példa önéletrajzból, majd átadtam az agent-nek, hogy szedje ki belőle az adatokat (skill-lek, személyes adatok), és ezt visszaadta JSON formátumba.


### 3. hét

Átírtam a Langchain workflow-t, mivel úgy itéltem meg hogy erre egy külön agentet létrehozni felesleges egyenlőre, így egy Langchain-ben használatos chain-t csináltam, ami egymás után meghívja a megfelelő dolgokat.

Módosítottam a PDF feldolgozón, mivel az eredetiben sok karakter után rakott egy felesleges szóközt, ami a későbbi vektor adatbázisnál problémát jelentett.

Készítettem egy nagyon minimális UI-t, ahol a felhasználónak lehetősége van feltölteni önéletrajzokat, amit utána a backend feldolgoz (kiszedi a személyes infókat és a skill-eket), majd pedig létrehoz jelentkezőkből kártáykat az adataikkal és a skill-jeikkel. Ehhez az eddig megírt PDF feldolgozó workflow-t használtam.

Megismerkedtem az embedding fogalmával, valamint a RAG fogalmával is.

Kipróbáltam a ChromaDB vektor adatbázist, amit lokálisan dockerben futtattam, feltöltöttem pár önéletrajzot és különböző query-k segítségével teszteltem mire milyen választ ad vissza. (Itt probléma lehet ha több nyelvű önéletrajzok lesznek tárolva)

### 4. hét

Átszerveztem a projekt struktúráját: létrehoztam egy külön backend mappát, ahova kiszerveztem az összes szerveroldali fájlt (ChromaDB kliens, workflow, segédfüggvények).

Megismerkedtem a LangGraph-fal. Átírtam az eredeti Langchain workflow-t LangGraph graph-ra, amelynek 4 csúcsa van:
- pdf_to_text: PDF fájlokból szöveget nyer ki
- text_to_vectordb: a szövegeket eltárolja a ChromaDB-ben
- analyze_cv: az LLM segítségével strukturált JSON-t állít elő minden önéletrajzból (név, email, telefon, helyszín, skill-ek, nyelvek)
- print_candidates: a kinyert adatokat kiírja a konzolra

Módosítottam a Python backendet (backend.py), amely egy /analyze végponton fogadja a feltöltött PDF fájlokat, majd meghívja a LangGraph workflow-t, és a feldolgozott jelöltek adatait JSON-ban adja vissza.

Kibővítettem a ChromaDB klienst két függvénnyel: az egyik dokumentumokat ad hozzá a gyűjteményhez, a másik szöveges query alapján visszakeresi a leghasonlóbb bejegyzéseket. Hozzáadtam egy duplikátumszűrőt is, hogy ugyanaz az önéletrajz ne kerüljön be kétszer az adatbázisba.

Létrehoztam egy /query végpontot a backenden, ami a ChromaDB-t kérdezi le a felhasználó által begépelt kérdés alapján. (ez még nem teljesen adja vissza a jó eredményt)

A Next.js frontendhez API route-okat írtam (/api/analyze, /api/query), amelyek továbbítják a kéréseket a Python backendnek.

Összekapcsoltam a frontend chat dobozát a backenddel: a felhasználó kérdést tud feltenni a feltöltött jelöltekről, a rendszer a ChromaDB-ből visszakeresi a legrelevásabb önéletrajz-részleteket, és azokat kártyákon jeleníti meg az UI-ban.

Frissítettem az UI dizájnját, hogy intuitívabb és egyertelműbb legyen a helyes használat.

Készítettem egy futtatási útmutatót.

### 5. hét

A héten az anonimizálással tervezésével foglalkoztam. Átgondoltam, hogy milyen workflow legyen és arra jutottam, hogy egy Agent formájában fog megvalósulni. Ez az Agent megkapja a egyes önéletrajzokat, és ezen kívül minden anonimizációhoz szükséges tool-t. Feldogozza az önéletrajz szövegét, megfelelő tool-ok segítségével pedig anonimizálja azt. 

Összeírtam magamnak, hogy az anonimizáláskor, milyen szövegekre/dolgokra kell majd figyelni amikor a jövő héten implementálom ezt az Agent-et.

### 6. hét

Telepítettem a PyMuPDF szerkesztőt, amit használtam az anonimizáció megvalósításához.

Tesztkörnyezetben létrehoztam egy egyszerű PDF-et (example5.pdf), ami kifejezetten a tartalmaz a jelentkező nemére vonatkozó információkat, és erre létrehoztam egy anonimizáló gráfot Langrapf segítségével. 

Az elején még agent formájában próbáltam megvalósítani, de mivel nem volt konzisztens minden adat kiszűrése, így a gráf mellett döntöttem.

A gráf tartalmaz 4 csúcsot, amik közül mindegyik más rész anonimizációjáért fele. Az elsőés a második a nemre vonatkozó konkrét szavakat szűrik ki, míg a hamradik csúcs azokat a szakmákat alakítja át áltaálnossá, amik tartlamaznak a nemre utaló jeleket mint például a pincérnő. Végül az utolsó csúcs alkalmazza ezeket a változtatásokat a pdf-re, ami keretein belül beírja a módosításkat az eredeti PDF másolatába, figyelve a szöveg formátumára.

Jelenleg csak angol szövegekkel működik.

