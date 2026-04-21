"""
LLM Tool Use Demo
=================
Python skript, který volá Claude API (Anthropic), umožňuje LLM používat
definované nástroje (tools) a vrací finální odpověď uživateli.

Ukázka tzv. "agentic loop": LLM může volat nástroje opakovaně,
dokud nemá dost informací pro finální odpověď.

Autor: <tvé jméno>
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from typing import Any

import anthropic
from dotenv import load_dotenv
from simpleeval import simple_eval

# ---------- Načtení prostředí ----------
load_dotenv()

API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not API_KEY:
    sys.exit(
        "❌ Chybí ANTHROPIC_API_KEY. Vytvoř soubor .env podle .env.example "
        "a vlož do něj svůj klíč z https://console.anthropic.com/"
    )

MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")
MAX_ITERATIONS = 10  # pojistka proti nekonečné smyčce

client = anthropic.Anthropic(api_key=API_KEY)


# ---------- Definice nástrojů (funkce) ----------
def calculator(expression: str) -> str:
    """Bezpečně vyhodnotí matematický výraz."""
    try:
        result = simple_eval(expression)
        return f"Výsledek: {result}"
    except Exception as exc:  # noqa: BLE001
        return f"Chyba při vyhodnocení výrazu '{expression}': {exc}"


def get_current_time(timezone: str = "Europe/Prague") -> str:
    """Vrátí aktuální čas (lokální čas serveru)."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"Aktuální čas ({timezone}): {now}"


def get_weather(city: str) -> str:
    """Mock funkce vracející počasí (v reálném použití by volala API)."""
    fake_data = {
        "praha": {"temp": 12, "condition": "oblačno"},
        "brno": {"temp": 14, "condition": "slunečno"},
        "ostrava": {"temp": 10, "condition": "déšť"},
        "plzeň": {"temp": 13, "condition": "polojasno"},
    }
    data = fake_data.get(city.lower())
    if not data:
        return f"Pro město '{city}' nemám data (dostupná: Praha, Brno, Ostrava, Plzeň)."
    return f"Počasí v {city}: {data['temp']} °C, {data['condition']}."


# Registr nástrojů: název -> Python funkce
TOOL_REGISTRY: dict[str, Any] = {
    "calculator": calculator,
    "get_current_time": get_current_time,
    "get_weather": get_weather,
}

# Schéma nástrojů pro Claude API
TOOLS_SCHEMA = [
    {
        "name": "calculator",
        "description": (
            "Vyhodnotí matematický výraz a vrátí výsledek. "
            "Podporuje +, -, *, /, **, (), a základní funkce."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Matematický výraz, např. '(12 + 7) * 3'.",
                }
            },
            "required": ["expression"],
        },
    },
    {
        "name": "get_current_time",
        "description": "Vrátí aktuální datum a čas.",
        "input_schema": {
            "type": "object",
            "properties": {
                "timezone": {
                    "type": "string",
                    "description": "Časová zóna, např. 'Europe/Prague'.",
                }
            },
            "required": [],
        },
    },
    {
        "name": "get_weather",
        "description": "Vrátí aktuální počasí pro zadané město (mock data).",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "Název města, např. 'Praha'.",
                }
            },
            "required": ["city"],
        },
    },
]


# ---------- Agentic loop ----------
def run_conversation(user_message: str, verbose: bool = True) -> str:
    """
    Spustí konverzaci s LLM a v případě potřeby opakovaně volá nástroje,
    dokud model nevrátí finální textovou odpověď.
    """
    messages: list[dict[str, Any]] = [
        {"role": "user", "content": user_message}
    ]

    if verbose:
        print(f"\n👤 Uživatel: {user_message}\n")

    for iteration in range(1, MAX_ITERATIONS + 1):
        if verbose:
            print(f"--- Iterace {iteration} ---")

        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            tools=TOOLS_SCHEMA,
            messages=messages,
        )

        # Uložíme celou odpověď asistenta do historie
        messages.append({"role": "assistant", "content": response.content})

        # Pokud model skončil bez volání nástroje, máme finální odpověď
        if response.stop_reason != "tool_use":
            final_text = "\n".join(
                block.text for block in response.content if block.type == "text"
            )
            if verbose:
                print(f"\n🤖 Claude: {final_text}\n")
            return final_text

        # Jinak zpracujeme všechny požadavky na volání nástrojů
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                tool_name = block.name
                tool_input = block.input

                if verbose:
                    print(f"🔧 Volám nástroj: {tool_name}({json.dumps(tool_input, ensure_ascii=False)})")

                func = TOOL_REGISTRY.get(tool_name)
                if func is None:
                    result = f"Chyba: nástroj '{tool_name}' neexistuje."
                else:
                    try:
                        result = func(**tool_input)
                    except Exception as exc:  # noqa: BLE001
                        result = f"Chyba při volání '{tool_name}': {exc}"

                if verbose:
                    print(f"   ↳ Výsledek: {result}")

                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    }
                )

        # Výsledky vložíme jako user message a pokračujeme v loopu
        messages.append({"role": "user", "content": tool_results})

    raise RuntimeError(
        f"Překročen limit {MAX_ITERATIONS} iterací – model pravděpodobně "
        f"uvízl ve smyčce volání nástrojů."
    )


# ---------- CLI rozhraní ----------
def main() -> None:
    print("🤖 LLM Tool Use Demo — Claude + Python")
    print(f"   Model: {MODEL}")
    print(f"   Dostupné nástroje: {', '.join(TOOL_REGISTRY.keys())}")
    print("   Ukončení: Ctrl+C nebo napiš 'exit'\n")

    # Pokud uživatel zadal dotaz jako argument, spustíme ho jednorázově
    if len(sys.argv) > 1:
        run_conversation(" ".join(sys.argv[1:]))
        return

    # Jinak interaktivní smyčka
    try:
        while True:
            user_input = input("👤 Tvůj dotaz: ").strip()
            if not user_input:
                continue
            if user_input.lower() in {"exit", "quit", "konec"}:
                print("👋 Nashle!")
                break
            run_conversation(user_input)
    except (KeyboardInterrupt, EOFError):
        print("\n👋 Nashle!")


if __name__ == "__main__":
    main()
