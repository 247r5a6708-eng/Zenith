#!/bin/bash
echo ""
echo "  ⬆  ZENITH — Reach Your Peak"
echo "  ─────────────────────────────"
echo ""
pip install "Django>=3.2" -q
python manage.py migrate
python manage.py create_badges
echo ""
echo "→ Starting at http://127.0.0.1:8000"
echo "  Press Ctrl+C to stop."
echo ""
python manage.py runserver
