from flask_sqlalchemy import SQLAlchemy
from flask_apscheduler import APScheduler
from flask_apscheduler.scheduler import BackgroundScheduler
from flask_migrate import Migrate
from flask_caching import Cache


scheduler = APScheduler(BackgroundScheduler())
db = SQLAlchemy()
migrate = Migrate()
cache = Cache()