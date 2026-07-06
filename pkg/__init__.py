from flask import Flask
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from pkg.config import LiveConfig

from pkg.models import db

csrf = CSRFProtect()

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_pyfile("config.py")
    app.config.from_object(LiveConfig)

    db.init_app(app)
    migrate = Migrate(app, db)
    csrf.init_app(app)

    return app

app = create_app()

from pkg import auth_route, facility_route, worker_route, admin_route, forms
