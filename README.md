# 🤖 LLM Tool Use — Python skript pro LLM API

Python skript, který demonstruje **tool use** (volání nástrojů) s LLM přes Anthropic Claude API. Skript pošle uživatelský dotaz modelu, ten si vyžádá volání jedné z definovaných funkcí (kalkulačka, čas, počasí), výsledek se vrátí zpět modelu a ten zformuluje finální odpověď.

Projekt je řešením zadání: *„Napiš Python skript, který zavolá LLM API, použije nástroj (např. výpočetní funkci) a vrátí odpověď zpět LLM.“*

---

## ✨ Co skript umí

- ✅ Volá **Anthropic Claude API** (model `claude-sonnet-4-5`)
- ✅ Implementuje **agentic loop** — LLM může volat více nástrojů za sebou
- ✅ Nabízí **tři nástroje**:
  - `calculator` — bezpečné vyhodnocení matematického výrazu (přes `simpleeval`)
  - `get_current_time` — aktuální datum a čas
  - `get_weather` — počasí pro zadané město (mock)
- ✅ **Interaktivní režim** i jednorázové volání přes CLI argument
- ✅ Podrobný **verbose výstup** — vidíš, které nástroje LLM volá a s jakými parametry
- ✅ Pojistka proti nekonečné smyčce (max. 10 iterací)
- ✅ Graceful handling chyb a chybějícího API klíče

---

## 🚀 Rychlý start

### 1. Naklonuj repo

```bash
git clone https://github.com/<tvuj-username>/llm-tool-use.git
cd llm-tool-use
```

### 2. Vytvoř virtuální prostředí a nainstaluj závislosti

```bash
python -m venv venv
source venv/bin/activate        # Linux / macOS
# venv\Scripts\activate         # Windows

pip install -r requirements.txt
```

### 3. Nastav API klíč

```bash
cp .env.example .env
# Otevři .env a vlož svůj klíč z https://console.anthropic.com/
```

### 4. Spusť

**Interaktivní režim:**
```bash
python main.py
```

**Jednorázový dotaz:**
```bash
python main.py "Kolik je (123 * 45) + odmocnina ze 144?"
```

---

## 💡 Příklady použití

### Matematika (kalkulačka)
```
👤 Tvůj dotaz: Kolik je (15 * 23) + (78 / 2)?
🔧 Volám nástroj: calculator({"expression": "(15 * 23) + (78 / 2)"})
   ↳ Výsledek: Výsledek: 384.0
🤖 Claude: Výsledek je 384.
```

### Kombinace nástrojů
```
👤 Tvůj dotaz: Kolik stupňů je teď v Praze a kolik by to bylo ve Fahrenheitech?
🔧 Volám nástroj: get_weather({"city": "Praha"})
   ↳ Výsledek: Počasí v Praha: 12 °C, oblačno.
🔧 Volám nástroj: calculator({"expression": "12 * 9/5 + 32"})
   ↳ Výsledek: Výsledek: 53.6
🤖 Claude: V Praze je teď 12 °C (oblačno), což odpovídá 53,6 °F.
```

### Aktuální čas
```
👤 Tvůj dotaz: Kolik je hodin?
🔧 Volám nástroj: get_current_time({})
   ↳ Výsledek: Aktuální čas (Europe/Prague): 2026-04-21 22:15:03
🤖 Claude: Je 22:15.
```

---

## 🏗️ Architektura

```
┌──────────┐    dotaz     ┌──────────────┐
│ Uživatel │────────────▶│   main.py    │
└──────────┘              │  (Python)    │
      ▲                   └──────┬───────┘
      │                          │ messages.create()
      │                          ▼
      │                   ┌──────────────┐
      │                   │  Claude API  │
      │                   └──────┬───────┘
      │                          │ stop_reason = "tool_use"
      │                          ▼
      │                   ┌──────────────┐
      │  finální odpověď  │ Tool Registry│
      └───────────────────┤ (kalkulačka, │
                          │  čas, …)     │
                          └──────────────┘
```

**Jádro je smyčka v `run_conversation()`**:
1. Pošli zprávu Claudovi spolu se schématem nástrojů.
2. Pokud má Claude finální odpověď (`stop_reason != "tool_use"`), vrať ji.
3. Pokud chce volat nástroj, vykonej Python funkci a výsledek pošli zpět.
4. Opakuj, dokud Claude nevrátí finální odpověď (max. 10 iterací).

---

## 🔒 Bezpečnost

- API klíč je v `.env`, který je v `.gitignore` — **NIKDY** se necommituje.
- Matematický výraz je vyhodnocen přes knihovnu `simpleeval`, která neumožňuje provádět libovolný Python kód (na rozdíl od `eval()`).
- Pojistka proti nekonečné smyčce nástrojů.

---

## 📁 Struktura projektu

```
llm-tool-use/
├── main.py              # hlavní skript
├── requirements.txt     # závislosti
├── .env.example         # šablona pro API klíč
├── .gitignore
└── README.md
```

---

## 🛠️ Použité technologie

- **Python 3.10+**
- [`anthropic`](https://pypi.org/project/anthropic/) — oficiální SDK pro Claude API
- [`python-dotenv`](https://pypi.org/project/python-dotenv/) — načítání `.env`
- [`simpleeval`](https://pypi.org/project/simpleeval/) — bezpečné vyhodnocování výrazů

---

## 📚 Zdroje

- [Anthropic — Tool use dokumentace](https://docs.claude.com/en/docs/agents-and-tools/tool-use/overview)
- [Anthropic Console (získání API klíče)](https://console.anthropic.com/)

---

## 📝 Licence

MIT
