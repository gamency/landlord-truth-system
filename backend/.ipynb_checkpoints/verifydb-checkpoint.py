import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# 加载环境变量（从 .env 读取数据库连接）
load_dotenv()
DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/landlord_truth")

# 创建连接
engine = create_engine(DB_URL)

def print_table(title, query):
    print(f"\n================ {title} ================")
    with engine.connect() as conn:
        result = conn.execute(text(query))
        rows = result.mappings().all()
        if not rows:
            print("(表为空，没有数据)")
            return
        for row in rows:
            print(dict(row))

# 查询刚刚生成的租约、账单和事件
print_table("最新租约 (Tenancy)", "SELECT tenancy_id, tenant_name, tenant_phone, monthly_rent, status FROM tenancy ORDER BY created_at DESC LIMIT 1;")
print_table("最新账单草稿 (BillDraft)", "SELECT bill_draft_id, theoretical_amount, actual_amount, status FROM bill_draft ORDER BY created_at DESC LIMIT 1;")
print_table("事件发件箱 (OutboxEvent)", "SELECT event_type, payload, status FROM outbox_event ORDER BY created_at DESC LIMIT 1;")