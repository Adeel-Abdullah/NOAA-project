from flask import Flask
from flask_caching import Cache
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from celery import Celery, Task


config = {
    "DEBUG": True,          # some Flask specific configs
    "CACHE_TYPE": "SimpleCache",  # Flask-Caching related configs
    "CACHE_DEFAULT_TIMEOUT": 300,
    "SQLALCHEMY_DATABASE_URI":'sqlite:///db.sqlite3',
    "CELERY": dict(
        broker_url="sqla+sqlite:///db.sqlite3",
        result_backend="db+sqlite:///db.sqlite3",
        task_ignore_result=True,
    ),
}


def celery_init_app(app: Flask) -> Celery:
    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app


app = Flask(__name__)
app.config.from_mapping(config)
celery_app = Celery(app.name)
celery_app.config_from_object(app.config["CELERY"])
# celery_app = celery_init_app(app)
cache = Cache(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)


with app.app_context():
    db.create_all()