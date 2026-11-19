from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:168@localhost:5432/landlord_truth"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = "change-me-in-production"
    AI_OCR_PROVIDER: str = "bd"  # local / baidu / tencent / qwen-vl
    AI_LLM_PROVIDER: str = "doubao"   # qwen / openai / deepseek
    AI_LLM_API_KEY: str = "9a428a16-c5cd-407f-861e-82fc0fc0e51b"
    AI_LLM_ENDPOINT: str = "https://ark.cn-beijing.volces.com/api/v3"
    DEFAULT_MODEL_ID: str = "ep-20261013162131-bcqbj"
    
    AI_LLM_BASE_URL: str = "https://ark.cn-beijing.volces.com/api/v3"
    AI_LLM_MODEL: str = "ep-20261013162131-bcqbj"
    
    class Config:
        env_file = ".env"

settings = Settings()