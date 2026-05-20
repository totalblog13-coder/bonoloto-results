# bonoloto-results

Ежедневный экспорт результатов испанской лотереи Bonoloto в статичный JSON
для Android-приложения.

## Что внутри

- `update.py` — тянет последние ~2 месяца с официального API
  `loteriasyapuestas.es` и пишет `results.json` с 20 последними тиражами.
- `.github/workflows/update.yml` — GitHub Actions: cron ежедневно 04:00 UTC,
  коммитит обновлённый `results.json` обратно в репозиторий.
- `results.json` — публикуется через GitHub Pages.

## URL

```
https://totalblog13-coder.github.io/bonoloto-results/results.json
```

## Формат

```json
{
  "updated_at": "2026-05-20T04:00:12Z",
  "game": "bonoloto",
  "draws": [
    {
      "date": "2026-05-19",
      "draw_no": "61",
      "numbers": [3, 12, 18, 25, 34, 47],
      "complementario": 8,
      "reintegro": 4
    }
  ]
}
```

`draws` отсортированы по убыванию даты (свежий первый), максимум 20 элементов.

## Локальный запуск

```bash
pip install -r requirements.txt
python update.py
```
