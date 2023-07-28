# Commands to run the app

*All of the following services need to be run in seperate consoles or the app to run properly*

## Flask
```console
flask -A main.py run --debug
```

## Celery beat scheduler
```console
celery -A main.celery_app beat
```
The celery beat scheduler is currently scheduled to execute tasks every 4 hours

## Celery worker
```console
celery -A main.celery_app worker --pool=solo -l INFO
```
A pool of a single celery worker is spun up to execute the scheduled tasks