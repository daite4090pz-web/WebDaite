from flask import Flask
from flask_login import LoginManager
from config import Config

loginManager = LoginManager()
loginManager.login_view = 'main.login'
loginManager.login_message = 'Авторизуйтесь для доступа к разделу'

def create_app(configClass=Config):
    app = Flask(__name__)
    app.config.from_object(configClass)

    loginManager.init_app(app)

    from app.models import Yuzer, dbSession, Category

    @app.teardown_appcontext
    def shutdownSession(exception=None):
        dbSession.remove()

    @loginManager.user_loader
    def loadYuzer(yuzerId):
        sessia = dbSession()
        return sessia.get(Yuzer, int(yuzerId))

    @app.context_processor
    def utilityProcessor():
        def getKategoriiSoStatyami():
            sessia = dbSession()
            return sessia.query(Category).filter(Category.statyi.any()).all()
        return dict(getKategoriiSoStatyami=getKategoriiSoStatyami)

    from app.routes import main
    app.register_blueprint(main)

    return app