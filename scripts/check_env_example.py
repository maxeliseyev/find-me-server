#!/usr/bin/env python
"""Проверяет, что каждая переменная, читаемая настройками, есть в `.env.example`.

Забытая переменная не роняет CI и не роняет dev-машину автора — она роняет
следующего человека, который клонирует репозиторий. Ловим здесь.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SETTINGS = ROOT / "config" / "settings"
ENV_EXAMPLE = ROOT / ".env.example"

# env("NAME"), env.bool("NAME", ...), env.list("NAME"), env.int("NAME"), env.db("NAME", ...)
PATTERN = re.compile(r"\benv(?:\.\w+)?\(\s*[\"']([A-Z][A-Z0-9_]*)[\"']")

# Задаются оркестратором (compose, CI, PaaS), в примере окружения не нужны.
IGNORED = {"DJANGO_SETTINGS_MODULE"}


def main() -> int:
    if not ENV_EXAMPLE.exists():
        print("✗ .env.example не найден")
        return 1

    documented = {
        line.split("=", 1)[0].strip().lstrip("# ").strip()
        for line in ENV_EXAMPLE.read_text(encoding="utf-8").splitlines()
        if "=" in line
    }

    used: set[str] = set()
    for path in SETTINGS.glob("*.py"):
        used |= set(PATTERN.findall(path.read_text(encoding="utf-8")))

    missing = sorted(used - documented - IGNORED)
    if missing:
        print("✗ Настройки читаются из окружения, но не описаны в .env.example:")
        for name in missing:
            print(f"    {name}")
        return 1

    print(f"✓ .env.example покрывает все {len(used)} переменных настроек")
    return 0


if __name__ == "__main__":
    sys.exit(main())
