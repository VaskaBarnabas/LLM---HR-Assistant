#### Rövid Leírás

A project egy olyan fejlett dokumentumfeldolgozó és döntéstámogató rendszer megtervezése és implementálása, amely képes önéletrajzok automatikus anonimizálására és strukturált elemzésére, ezáltal támogatva a modern, előítélet-mentes (blind recruitment) toborzási folyamatokat.

#### Kontextus

A HR szakemberekre háruló adminisztrációs teher miatt a beérkező önéletrajzok előszűrése gyakran felületes. Ezt súlyosbítja az emberi döntéshozatalban akaratlanul is jelenlévő tudattalan torzítás (unconscious bias), amely hátrányosan érinthet bizonyos demográfiai csoportokat. A jelenlegi kulcsszó-alapú szűrőszoftverek merevek, és gyakran értékes jelölteket szűrnek ki pusztán formai okokból.

#### A feladat részletes kifejtése

A fejlesztés több, egymásra épülő modulból áll:

1. Dokumentumfeldolgozó pipeline: Különböző formátumú (PDF, DOCX) önéletrajzok szöveges tartalmának kinyerése OCR és szövegbányászati eszközökkel.
2. Anonimizáló Ágens: Egy LLM-alapú komponens implementálása, amely felismeri és maszkolja a személyes azonosításra alkalmas adatokat (PII), mint például nevek, fotók, lakcímek, vagy nemre utaló nyelvi fordulatok, miközben a szakmai tartalmat érintetlenül hagyja.
3. Strukturálás és Rangsorolás: A megtisztított adatokból JSON formátumú egységes profilok generálása, majd ezek összevetése a pozícióleírással RAG (Retrieval-Augmented Generation) technológia segítségével.
4. Szintetikus Tesztkörnyezet (Kutatási modul): Egy generátor modul készítése, amely képes százas nagyságrendben fiktív önéletrajzokat gyártani kontrollált változókkal (pl. ugyanaz a szakmai tapasztalat, de eltérő nem vagy származás), hogy ezzel mérhetővé váljon az alapmodell esetleges torzítása.
5. Végeredmény: Egy webes felülettel rendelkező kliens-szerver alkalmazás, amelyre a felhasználó feltöltheti a CV-ket, és válaszul egy anonimizált, rangsorolt listát kap indoklással ellátva. A rendszer backendje Python alapú AI szolgáltatásokkal kommunikál, az adatokat (pl. vektorok) adatbázisban tárolja.

#### Használt technológiák:

- **Backend:** Node.js a szerver logikához.
- **Frontend:** React a kezelőfelülethez.
- **LLM/AI:** Python, LangChain, OpenAI API vagy HuggingFace modellek.
