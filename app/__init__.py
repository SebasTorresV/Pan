from flask import Flask
from config import Config
from .db import close_db
from .routes import bp as main_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.secret_key = app.config['SECRET_KEY']  # Necesario para sesiones

    app.register_blueprint(main_bp)
    app.teardown_appcontext(close_db)

    return app
