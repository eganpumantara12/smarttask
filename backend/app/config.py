"""Konfigurasi aplikasi. Semua nilai sensitif dibaca dari environment variable (NFR-05)."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./smarttask.db"
    secret_key: str = "ganti-saya-di-produksi"
    access_token_minutes: int = 60 * 8
    cors_origins: str = "http://localhost:5173"
    # Akun admin awal (dibuat otomatis jika belum ada)
    admin_email: str = ""
    admin_password: str = ""
    admin_name: str = "Administrator"
    due_soon_hours: int = 48
    log_level: str = "INFO"


settings = Settings()
