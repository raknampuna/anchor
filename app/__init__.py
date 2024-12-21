from flask import Flask
from dotenv import load_dotenv
import os

def create_app(test_config=None):
    # Load environment variables
    load_dotenv()
    
    # Create Flask app
    app = Flask(__name__)
    
    # Configure app
    if test_config is None:
        app.config.from_mapping(
            SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),
            TWILIO_ACCOUNT_SID=os.environ.get('TWILIO_ACCOUNT_SID'),
            TWILIO_AUTH_TOKEN=os.environ.get('TWILIO_AUTH_TOKEN'),
            TWILIO_PHONE_NUMBER=os.environ.get('TWILIO_PHONE_NUMBER'),
        )
    else:
        app.config.update(test_config)
    
    # Register routes
    from app import routes
    app.register_blueprint(routes.bp)
    
    return app