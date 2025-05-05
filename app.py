import os
import logging

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix


# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///multiagent.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize the app with the extension
db.init_app(app)

with app.app_context():
    # Import models to ensure tables are created
    import models  # noqa: F401
    
    # Explicitly create tables in the correct order
    from models import Agent, Project, Ticket, Conversation, Message, Comment, Customer, Subscription
    
    # Create tables with proper dependency order
    db.create_all()
    logger.info("Database tables created successfully")

# Import and register routes
from routes.main_routes import main_bp
from routes.api_routes import api_bp
from routes.auth_routes import auth_bp
from routes.payment_routes import payment_bp

app.register_blueprint(main_bp)
app.register_blueprint(api_bp, url_prefix='/api')
app.register_blueprint(auth_bp)
app.register_blueprint(payment_bp, url_prefix='/payment')

logger.info("Application initialized successfully")
