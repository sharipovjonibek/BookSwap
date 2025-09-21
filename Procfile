web: python manage.py migrate \
     && python manage.py collectstatic --noinput \
     && python manage.py createsuperuser --noinput || true \
     && python manage.py runserveer
