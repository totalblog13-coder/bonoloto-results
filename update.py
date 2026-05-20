# -*- coding: utf-8 -*-
"""Скачивает последние тиражи Bonoloto и пишет results.json.

Запускается GitHub Actions раз в день. Без локального CSV: каждый раз тянет
два последних месяца с официального JSON API loteriasyapuestas.es, сортирует
по дате, оставляет последние LIMIT тиражей.

Локальный запуск:
    python update.py
"""
import calendar
import io
import json
import re
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path

import requests

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

API_URL = "https://www.loteriasyapuestas.es/servicios/buscadorSorteos"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
OUT_PATH = Path(__file__).parent / "results.json"
LIMIT = 20  # сколько последних тиражей кладём в results.json

COMBO_RE = re.compile(
    r"(\d{1,2}) - (\d{1,2}) - (\d{1,2}) - (\d{1,2}) - (\d{1,2}) - (\d{1,2})"
    r" C\((\d{1,2})\) R\((\d)\)"
)


def fetch_month(session: requests.Session, year: int, month: int) -> list[dict]:
    last_day = calendar.monthrange(year, month)[1]
    params = {
        "game_id": "BONO",
        "celebrados": "true",
        "fechaInicioInclusiva": f"{year:04d}{month:02d}01",
        "fechaFinInclusiva": f"{year:04d}{month:02d}{last_day:02d}",
    }
    for attempt in range(3):
        try:
            r = session.get(API_URL, params=params, timeout=20)
            r.raise_for_status()
            data = r.json()
            break
        except Exception as e:
            if attempt < 2:
                time.sleep(5 * (attempt + 1))
            else:
                print(f"ERR {year}-{month:02d}: {e}", file=sys.stderr)
                return []

    if isinstance(data, str) or not data:
        return []

    draws = []
    for item in data:
        m = COMBO_RE.search(item.get("combinacion", ""))
        if not m:
            continue
        n1, n2, n3, n4, n5, n6, comp, ref = (int(x) for x in m.groups())
        draws.append({
            "date": item["fecha_sorteo"][:10],
            "draw_no": str(item.get("numero", "")),
            "numbers": sorted([n1, n2, n3, n4, n5, n6]),
            "complementario": comp,
            "reintegro": ref,
        })
    return draws


def previous_month(year: int, month: int) -> tuple[int, int]:
    return (year - 1, 12) if month == 1 else (year, month - 1)


def main() -> int:
    today = date.today()
    months = [previous_month(today.year, today.month), (today.year, today.month)]

    session = requests.Session()
    session.headers.update({"User-Agent": UA})

    draws: list[dict] = []
    for y, m in months:
        chunk = fetch_month(session, y, m)
        print(f"{y}-{m:02d}: {len(chunk)} draws")
        draws.extend(chunk)

    # Уникальные по дате (на случай пересечений), сортировка по убыванию даты.
    by_date: dict[str, dict] = {d["date"]: d for d in draws}
    sorted_draws = sorted(by_date.values(), key=lambda d: d["date"], reverse=True)
    latest = sorted_draws[:LIMIT]

    payload = {
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "game": "bonoloto",
        "draws": latest,
    }

    OUT_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"OK: {len(latest)} draws -> {OUT_PATH.name}")
    if latest:
        print(f"Latest: {latest[0]['date']} draw {latest[0]['draw_no']}")
    return 0 if latest else 1


if __name__ == "__main__":
    raise SystemExit(main())
