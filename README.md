# Haladások

### Első hét
A megbeszéltek szerint, a következőkkel haladtam a héten:

Létrehoztam egy Github repot, amiben a félév során minden munkám ide fog kerülni. Ezen belül létrehoztam 2 ágat, a main illetve a develop branch-et. A main ág lesz fogja tartalmazni a "release"-eket. A develop branch-ből ágaznak el a feature branch-ek, amiket majd ide merge-elek vissza, amint elkészül az adott feature.


Regisztráltam a Google Gemini API-ra, és legenráltam egy api kulcsot.

Írtam egy Python szrkiptet, amivel API segítségével kommunkál, nem pedig egy chat felületen. Ehhez használtam a legenerált API kulcsot, amit kiszerveztem egy .env fájlba.

Megismerkedtem a Promptolás alapjaival a promptingguide.ai oldalról.

Megismerkedtem a temperature és a top_p fogalmakkal, amiket változtatgattam és figyeltem a kapott válaszok között lévő különbséget. Ezen kívül sok más lehetésges beállítást is láttam és kirpóbáltam. Ehhez a Google AI Studio Playground felületet használtam. 

Megismerkedtem hogy egy prompt hogyan épül fel, és az oldalon lévő példákon keresztül ezt magam is kirpóbáltam.

Végül megisemrkedtem pár prompt teknikával, mint a Zero-shot prompting, Few-shot prompting, CoT (Chain-of-Thought), Self-Consistency

### Második hét

Megismerkedtem az Agentek alapjaival, illetve alapvető működésükkel.

Megismerkedem a LangChain használatával, valamint kicsit belenéztem a LangGraph és a LangChain különbségébe is.

Kerestem egy példa önéletrajzot, amiből kinyertem az adatokat a pypdf könyvtár segítségével.

Létrehoztam egy Agent-tet a LangChain segítségével, ami rendelkezik 2 tool-lal, az egyikkel a skilleket a másikkal a személyes adatokat lehet kinyerni a neki átadott önéletrajz szövegből. 

Végül egyesítettem a két dolgot, így kinyertem az adatokat a példa önéletrajzból, majd átadtam az agent-nek, hogy szedje ki belőle az adatokat (skill-lek, személyes adatok), és ezt visszaadta JSON formátumba.


