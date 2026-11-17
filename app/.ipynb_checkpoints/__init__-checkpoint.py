from flask import Flask
from app.config import settings
from app.shared.db import db

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = settings.DATABASE_URL
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = settings.SECRET_KEY

    db.init_app(app)

    # 导入所有模型（让SQLAlchemy知道它们的存在）
    from app.modules.property import models as property_models 

    # 开发阶段：自动建表
    with app.app_context():
        db.create_all()

    @app.route('/health')
    def health():
        return {'status': 'ok', 'service': 'landlord-truth'}

    return app