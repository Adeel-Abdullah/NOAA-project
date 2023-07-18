from flask import Flask
from flask_caching import Cache
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate


config = {
    "DEBUG": True,          # some Flask specific configs
    "CACHE_TYPE": "SimpleCache",  # Flask-Caching related configs
    "CACHE_DEFAULT_TIMEOUT": 300,
    "SQLALCHEMY_DATABASE_URI":'sqlite:///db.sqlite3'
}

app = Flask(__name__)
app.config.from_mapping(config)
cache = Cache(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

with app.app_context():
    db.create_all()