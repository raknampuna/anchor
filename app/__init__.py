"""Anchor task planning application."""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Core components that don't depend on Flask
from .schema import MessageType
from .llm import LLMService
from .storage import RedisStorage

# Only initialize Flask app when running as web service
def create_app(test_config=None):
    """Create Flask app for web service"""
    from flask import Flask
    
    # Create Flask app
    app = Flask(__name__)
    
    # Configure app with environment variables
    # In test environments, we can override these with test_config
    if test_config is None:
        app.config.from_mapping(
            SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),
            TWILIO_ACCOUNT_SID=os.environ.get('TWILIO_ACCOUNT_SID'),
            TWILIO_AUTH_TOKEN=os.environ.get('TWILIO_AUTH_TOKEN'),
            TWILIO_PHONE_NUMBER=os.environ.get('TWILIO_PHONE_NUMBER'),
        )
    else:
        app.config.update(test_config)

    # Register blueprints
    # This step is crucial - without it, Flask won't know about our routes
    # The blueprint contains all our SMS-related routes (like /webhook)
    from .routes import bp
    app.register_blueprint(bp)

    # Health check endpoint
    # Simple endpoint that returns 'OK' if the server is running
    # Useful for:
    # 1. Verifying the Flask app is running correctly
    # 2. Confirming route registration is working
    # 3. Basic monitoring and health checks
    @app.route('/health')
    def health_check():
        return 'OK', 200
        
    return app