from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/landlord_truth"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = "change-me-in-production"
    AI_OCR_PROVIDER: str = "local"  # local / baidu / tencent / qwen-vl
    AI_LLM_PROVIDER: str = "qwen"   # qwen / openai / deepseek
    AI_LLM_API_KEY: str = ""
    AI_LLM_ENDPOINT: str = ""
    
    class Config:
        env_file = ".env"

settings = Settings()