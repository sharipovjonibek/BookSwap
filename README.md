
# BookX v4 — Hardened DRF backend

## Run
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # add GOOGLE_API_KEY if available
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver

### Automatic superuser on Railway

Set the following environment variables in Railway (or copy them into your `.env` locally) and the `ensure_superuser` management command will provision the account on every deploy:

```
DJANGO_SUPERUSER_USERNAME=<your-admin-username>
DJANGO_SUPERUSER_EMAIL=<your-admin-email>
DJANGO_SUPERUSER_PASSWORD=<your-strong-password>
```

If you leave the password empty, a secure password is generated and printed to the deployment logs.

Docs: http://127.0.0.1:8000/api/docs/
Health: http://127.0.0.1:8000/api/health/

## AI endpoint doesn’t 500
- Safe try/except in AI client
- If key missing or model fails → returns `_warning` and empty suggestions

## Redirect after AI
1) Call AI: `GET /api/ai/books/advice/?prompt=...` or `POST` JSON `{ "prompt":"..." }`
2) Read `filter_query.titles[]` & `authors[]`
3) Redirect frontend to: `/api/books/?titles=<t1>&titles=<t2>&authors=<a1>`

## Filters on main list
- `?q=` full text
- `?titles=` repeat or comma-separated
- `?authors=` repeat or comma-separated
