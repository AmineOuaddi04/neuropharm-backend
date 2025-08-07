from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_ENV: str = "dev"
    APP_PORT: int = 8080
    FRONTEND_ORIGIN: str = "http://localhost:8030"

    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str
    SUPABASE_DB_URL: str
    SUPABASE_BUCKET_VCF: str
    SUPABASE_BUCKET_REPORTS: str

    OPENAI_API_KEY: str
    OPENAI_MODEL_ANALYSIS: str
    OPENAI_MODEL_CHATBOT: str

    PDF_LOGO_PATH: str

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"  # ← Esto permite que haya variables adicionales en el .env
    )

settings = Settings()
