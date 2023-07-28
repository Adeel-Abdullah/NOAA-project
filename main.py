from app import app, db, celery_app
from models import *
from views import *
from celery.schedules import crontab
from test import updateDB


celery_app.conf.beat_schedule = {
    'add-every-4-hours': {
        'task': 'updateDB',
        'schedule':crontab(hour='*/4'),
    }
}
celery_app.conf.timezone = 'Asia/Karachi'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

# celery -A main.celery_app worker --pool=solo -l INFO