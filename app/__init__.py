from flask import Flask
from app.config import settings
from app.shared.db import init_db

def create_app():
    app = Flask(__name__)

    # 显式映射配置（Pydantic 的属性名和 Flask 的配置键名不一致）
    app.config['SQLALCHEMY_DATABASE_URI'] = settings.DATABASE_URL
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = settings.SECRET_KEY

    init_db(app)

    @app.route('/health')
    def health():
        return {'status': 'ok', 'service': 'landlord-truth'}

    return app