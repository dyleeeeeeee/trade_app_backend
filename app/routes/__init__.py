from quart import Quart
from .auth import auth_bp
from .wallet import wallet_bp
from .trading import trading_bp
from .admin import admin_bp
from .strategies import strategy_bp

def register_routes(app: Quart):
    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(wallet_bp, url_prefix='/api')
    app.register_blueprint(trading_bp, url_prefix='/api')
    app.register_blueprint(admin_bp, url_prefix='/api')
    app.register_blueprint(strategy_bp, url_prefix='/api/strategies')
