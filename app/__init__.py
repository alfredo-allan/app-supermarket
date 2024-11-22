from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate


# Instância de SQLAlchemy fora da função
db = SQLAlchemy()
migrate = Migrate()


def create_app():
    app = Flask(__name__)

    # Configurações do banco de dados
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///supermarket.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Inicializar extensões
    db.init_app(app)
    migrate.init_app(app, db)

    # Registrar blueprints
    from .routes import main

    app.register_blueprint(main)

    return app
