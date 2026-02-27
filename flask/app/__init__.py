from flask import Flask
from .config import Config
from .extensions import db, migrate, jwt, cors,bcrypt, mail
from flask_cors import CORS


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    bcrypt.init_app(app)
    cors.init_app(app)
    mail.init_app(app)
    cors.init_app(
        app,
        resources={r"/auth/*": {"origins": "http://localhost:3000"}},
        supports_credentials=True
    )

    from .auth.routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix="/auth")

    return app
