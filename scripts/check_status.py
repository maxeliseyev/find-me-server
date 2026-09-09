#!/usr/bin/env python
"""Сверяет `docs/status.md` с реальной веткой.

Курсор смены — самый быстро протухающий файл в репозитории: агент дописывает
код и забывает переписать статус, следующая сессия стартует с чужой ветки.
Проверка дешёвая, поэтому механическая, а не «не забудь».

Использование:
    python scripts/check_status.py                 # сверить с текущей веткой
    python scripts/check_status.py --branch <name> # сверить с веткой PR (CI)
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

STATUS = Path(__file__).resolve().parent.parent / "docs" / "status.md"
REQUIRED = ("Branch:", "## Now", "## Next", "## Resume")


def current_branch() -> str:
    return subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--branch", default=None)
    args = parser.parse_args()

    if not STATUS.exists():
        print(f"✗ {STATUS} не найден. Шаблон — docs/handoff.md.")
        return 1

    text = STATUS.read_text(encoding="utf-8")

    missing = [field for field in REQUIRED if field not in text]
    if missing:
        print(f"✗ В status.md нет обязательных полей: {', '.join(missing)}")
        return 1

    match = re.search(r"^Branch:\s*(.+)$", text, re.MULTILINE)
    declared = match.group(1).strip().strip("`") if match else ""

    branch = args.branch or current_branch()
    if branch == "main":
        # На main статус описывает уже слитую работу — сверять не с чем.
        return 0

    if declared != branch:
        print(f"✗ status.md: Branch = «{declared}», а работа идёт в «{branch}».")
        print("  Перепишите docs/status.md (шаблон — docs/handoff.md).")
        return 1

    print(f"✓ status.md соответствует ветке {branch}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
