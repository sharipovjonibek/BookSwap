web: python manage.py migrate \
     && python manage.py collectstatic --noinput \
     && python manage.py createsuperuser --noinput || true \
     && gunicorn bookx.wsgi:application --bind 0.0.0.0:$PORT -- workers 3
