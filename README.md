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

## Első indításkor** (létrehozza a konténert és a perzisztens volume-ot):
```bash
docker run -d --name chroma -p 8000:8000 -v chroma-data:/chroma/chroma chromadb/chroma:1.0.0
```

## Minden további indításkor** (meglévő konténer újraindítása, adatok megmaradnak):
```bash
docker start chroma
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

### 7. hét

Az előző megoldásomat átalakítottam agent alapú megoldásra a megbeszéltek szerint.

Minden egyes feladathoz egy külön agentet hoztam létre, amik az adott elemek szűrésével foglakozik a bemenetként kapott PDF-ből.

Ezek az agentek rendre 
- Neveket illetve ehhez tartozó információk szűrésével foglakozó agent
- Olyan szakmáknak a szűrésével foglakozó agent, amik nemre utalhatnak
- Névmások szűrésével fogakozó agent
- Családhoz, illetve a családban betöltött szerepből származó informácókat szűrő agent
- Egy ember elétében bekövetkezett események amik a nemre utalhatnak, ilyen például a terhesség stb.

Kijavítottam a PDF generálást, mivel a a módszer, hogy egyből a szövegbe beleírom nem működött, mivel vagy üresen hagyta a kicseréledő szavak helyét, vagy pedig többszörösen írta át, így a következő meggoldásra jutottam. Az eredeti önéletrajzból kinyert szöveget anonimizálás után egy teljesen új PDF-be mentem el, amit a 0-ról építek fel átadva neki az anonimizáló szöveget. Itt a jövőben érdemes lesz javítani a kinézeten, de a szöveg midnen eleme helyesen, az anonimizált verzióval szerepel.

Frissítettem a gráfot is ami mentén végrehajtódik a folyamat, így minden agent egy gráf csomópontba került, illetve egy a gráf utolsó pontja állítja elő az új PDF-et az anonimizált szövegből.

Jelenleg a folyamatot console-ban lehet követni, illetve tesztelni, valamint a kész PDF is bekerül futás után a teszt_cvs mappába.

Mivel sokszor keveset tudtam tezstelni, mivel gyorsan elértem a napi limitemet a választott nagy nyelvi modellnél, így áttértem lokálisan futtatott LLM-re. Először Ollama segítségével próbáltam futtatni de, mindig Internal Server EDrrort kaptam, és mivel sok ideig nem tudtam megoldani, végül a Docker-ben történő futtatás mellett döntöttem.

Jelenleg a agentek is már a lokális LLM-et hívják, ami a Gemma4:e4b változata.

Illetve megismerkedtem a Google Stitch UI designer használatával, ami segítségével a jövőben könnyebben tudom fejleszteni a UI elemeket az alkalmazásban.

### 8. hét

Az előző héten tesztelt anonimizálást átemeltem a tényleges környezetben, és mostmár ott is elérhető. Annyi módosítssal, hogy nem PDF-ben menti el az anonimizált önéletrajzor, hanem HTML formában, ami meg tud lehet tekinte a jelentkezőnél a UI-on.

Itt is módosítottam, hogy a lokálisan futtatott LLM-et használja a feladat megvalósításához.

Került bejelentkezés illetve regisztráció az appba, ahol Jelentkező és HR szerepkörök közül lehet választani.

HR szerepkör esetén van lehetőség álláshírdetésket létrehozni, ahol azt is ki lehet választani, hogy az anonimizáló agentek közül melyiket szeretné használni. Ezekre a álláshírdésekre jelentkezett embereknek a átszűrt önéletrajzát meg tudja tekinteni.

Jelentkező szerepkör esetén a létrehozott álláshiyrdetéseket látja a felhasználó, ahol le tudja adni a jelentkezését egy önéletrajz feltöltésével.


## 9. hét
Frissítettem az indítási útmutatót, hogy a ChromaDB Docker konténer névvel és perzisztens volume-mal induljon el, így az adatok újraindítás után is megmaradnak.

Eddigi felvedezett UI hibákat javítottam. (pl.: Toggle button kikapcsolat állapotban is látszik már)

Implementáltam egy rangsorolási funkciót, amely az álláshirdetés részletes oldalán érhető el. A „Rangsorolás" gombra kattintva a rendszer először a ChromaDB vektoros adatbázisból lekéri azokat a jelölteket, akiknek az önéletrajza el van tárolva, majd egy LLM segítségével rangsorolja őket az adott pozíció leírása alapján. Minden jelölt mellé rövid, 1-2 mondatos magyar indoklás is generálódik, hogy miért került arra a helyre.

A rangsorolás eredménye egymás alatti, teljes szélességű kártyákon jelenik meg. Minden kártya tartalmazza a jelölt sorszámát (az első helyen lévő kiemelve), nevét, helyszínét, az LLM által generált indoklást, valamint a skill-jeit.

Korábban az önéletrajzok véletlenszerű UUID-vel kerültek be a ChromaDB-be, ami miatt a rangsorolás során nem lehetett visszakötni az eredményeket az egyes jelöltekhez. Megoldottam, hogy minden új jelentkezésnél a CV szövege a Supabase-ben kiosztott application_id-vel tárolódik el a ChromaDB-ben, egy új /store-cv backend endpoint segítségével.

Lehetőséget van mostmár az álláshirdetések törlésére a HR dashboardon.

## 10. hét

Kibővítettem a rangsorolás funkcióját: az LLM mostantól először kinyeri az álláshirdetés leírásából az 5 legfontosabb követelményt, majd minden jelöltnél megjelöli, hogy teljesíti-e ezeket (true/false). Az eredmény a rangsorolási kártyákon checkbox-lista formájában jelenik meg. Zöld pipa ha a jelölt megfelel az adott kritériumnak, áthúzott szöveg ha nem. Emellett egy 1-2 mondatos indoklás is generálódik, amely konkrétan megnevezi, mit teljesít és mit nem az adott jelölt.

Létrehoztam egy tesztkörnyezetet az anonimizáció automatikus ellenőrzéséhez. A tesztek a `tests/test_anonymization.py` fájlban találhatók, és 4 csoportba vannak szervezve:
- **Egyenkénti filterek BE** (5 teszt): minden anonimizáló agent külön-külön kerül tesztelésre
- **Egyenkénti filterek KI** (5 teszt): minden agent ki van kapcsolva, a többi fut – az adott tartalom megmarad
- **Mind kikapcsolva** (1 teszt): ha minden filter ki van kapcsolva, a szöveg változatlan marad
- **Kombinációk** (5 teszt): több filter egyidejű kombinációi

A tesztek futtatásához egy `run_tests.sh` scriptet készítettem a projekt gyökerébe.

**Az összes teszt futtatása:**
```bash
./run_tests.sh
```

**Egy konkrét teszt futtatása:**
```bash
./run_tests.sh test_names_only
```

**Az elérhető tesztek listázása:**
```bash
./run_tests.sh --list
```

A tesztek futtatásához szükséges, hogy a lokális LLM szolgáltatás (`http://localhost:12434`) elérhető legyen. Ha nem elérhető, a tesztek automatikusan átlépésre kerülnek egy figyelmeztető üzenettel.

A tesztelés során kiderült, hogy az anonimizáló agentek promptjai túl általánosak voltak, és egymás területére léptek (pl. a névmás-agent a munkakörmegnevezéseket is semlegesítette, a családi állapot agent a névmásokat [PERSONAL DATA]-ra cserélte). Ezeket a promptokat pontosítottam, hogy minden agent kizárólag a saját feladatával foglalkozzon.

