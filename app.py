from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from extensions import migrate, scheduler, db, cache
import os
from scheduled_functions import updateDB, update_tle


config = {
    "DEBUG": True,          # some Flask specific configs
    "CACHE_TYPE": "SimpleCache",  # Flask-Caching related configs
    "CACHE_DEFAULT_TIMEOUT": 300,
    "SQLALCHEMY_DATABASE_URI":'sqlite:///db.sqlite3',
    "SCHEDULER_API_ENABLED" : True,
}


def create_app(config_class):
    app = Flask(__name__)
    app.config.from_mapping(config_class)

    def is_debug_mode():
        """Get app debug status."""
        debug = os.environ.get("FLASK_DEBUG")
        # print(debug)
        if not debug:
            return os.environ.get("FLASK_ENV") == "development"
        return debug.lower() not in ("0", "false", "no")

    def is_werkzeug_reloader_process():
        """Get werkzeug status."""
        return os.environ.get("WERKZEUG_RUN_MAIN") == "true"
    
    cache.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)
    with app.app_context():
        db.create_all()
        
    with app.app_context():
        if not is_werkzeug_reloader_process():
            pass
        else:
            if scheduler.state==0:
                print (is_debug_mode())
                print (is_werkzeug_reloader_process())
                scheduler.api_enabled = True
                scheduler.init_app(app)
                scheduler.scheduler.add_jobstore(
                    SQLAlchemyJobStore(engine=db.engine, metadata=db.metadata))
                scheduler.start()
            # else:
            #     scheduler.shutdown(wait=False)
            #     scheduler.start()
    return app

app = create_app(config)
from views import *

if __name__ == "__main__":
    app.run(debug=True)