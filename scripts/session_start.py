#!/usr/bin/env python
"""Ритуал старта сессии одной командой (`make session-start`).

Протокол — `docs/handoff.md`: пока это не прочитано, фичу не писать.
Скрипт не заменяет чтение, он собирает всё в один вывод, чтобы шаг нельзя
было пропустить «потому что долго».
"""

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATUS = ROOT / "docs" / "status.md"


def run(cmd: list[str]) -> str:
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
    return (result.stdout or result.stderr).rstrip()


def section(title: str, body: str) -> None:
    print(f"\n\033[1m{title}\033[0m\n{body or '(пусто)'}")


def main() -> int:
    section("Ветка и состояние", run(["git", "status", "-sb"]))
    section("Последние коммиты", run(["git", "log", "-5", "--oneline"]))

    if shutil.which("gh"):
        section("Открытые PR", run(["gh", "pr", "list", "--limit", "10"]))
    else:
        section("Открытые PR", "gh не установлен — проверьте вручную")

    if STATUS.exists():
        section("docs/status.md", STATUS.read_text(encoding="utf-8").strip())
    else:
        section("docs/status.md", "✗ файла нет. Шаблон — docs/handoff.md")
        return 1

    check = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_status.py")],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    section("Сверка статуса с git", (check.stdout or check.stderr).strip())

    print(
        "\n\033[1mДальше\033[0m\n"
        "  1. Прочитать session note, если статус на неё ссылается\n"
        "  2. Нужный раздел спеки — не всю спеку\n"
        "  3. Ветка от актуального main: git checkout -b feat/<тема>\n"
    )
    return check.returncode


if __name__ == "__main__":
    sys.exit(main())
