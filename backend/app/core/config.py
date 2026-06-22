"""Central typed settings, loaded from env / .env via pydantic-settings."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"), env_file_encoding="utf-8", extra="ignore"
    )

    # core
    app_name: str = "JobHunter AI"
    environment: str = "development"
    debug: bool = True
    api_base_url: str = "http://localhost:8000"

    # security
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    encryption_key: str = ""  # Fernet key; if empty one is derived from jwt_secret

    # db / cache / queue
    database_url: str = "sqlite+pysqlite:///./jobhunter.db"
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # vector / embeddings
    chroma_dir: str = "./storage/chroma"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # llm
    llm_provider: str = "anthropic"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-opus-4-8"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-pro"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"

    # matching / limits
    match_threshold: int = 75
    max_applications_per_day: int = 50

    # storage
    storage_dir: str = "./storage"

    # email
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""

    # scrapers (enable only allowed sources)
    enable_remoteok: bool = True
    enable_weworkremotely: bool = True
    enable_ycombinator: bool = True
    # company ATS boards (public APIs, automation-friendly) — set the *_list vars below
    enable_greenhouse: bool = False
    enable_lever: bool = False
    enable_ashby: bool = False
    greenhouse_boards: str = ""   # comma list of board tokens, e.g. "gitlab,figma"
    lever_companies: str = ""     # comma list of lever slugs, e.g. "netflix,plaid"
    ashby_orgs: str = ""          # comma list of ashby slugs, e.g. "ramp,linear"
    enable_linkedin: bool = False
    enable_indeed: bool = False
    enable_naukri: bool = False
    enable_glassdoor: bool = False
    enable_wellfound: bool = False
    enable_foundit: bool = False

    # apply safety: real network submissions only happen when this is True.
    # Left False so nothing is submitted by accident; flip on once you've reviewed output.
    enable_real_apply: bool = False

    # browser robot: run headless (True, for servers) or visible (False, for local testing).
    playwright_headless: bool = True
    # If >0 AND running headed, pause on a CAPTCHA so YOU can solve it in the open window;
    # the bot waits up to this many seconds, then continues. This is a human-in-the-loop
    # assist (you solve the check), NOT an automated CAPTCHA bypass.
    captcha_manual_wait_seconds: int = 0

    # on-demand "Apply" button: run in-process (False) or via Celery/Redis (True).
    enable_celery: bool = False

    # notifications (needs_review / CAPTCHA alerts). All optional → falls back to log.
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    notify_email: str = ""

    cors_origins: list[str] = Field(default_factory=lambda: ["*"])

    @staticmethod
    def _csv(value: str) -> list[str]:
        return [v.strip() for v in (value or "").split(",") if v.strip()]

    def greenhouse_boards_list(self) -> list[str]:
        return self._csv(self.greenhouse_boards)

    def lever_companies_list(self) -> list[str]:
        return self._csv(self.lever_companies)

    def ashby_orgs_list(self) -> list[str]:
        return self._csv(self.ashby_orgs)

    @property
    def storage_path(self) -> Path:
        p = Path(self.storage_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p

    def enabled_scrapers(self) -> list[str]:
        flags = {
            "remoteok": self.enable_remoteok,
            "weworkremotely": self.enable_weworkremotely,
            "ycombinator": self.enable_ycombinator,
            "greenhouse": self.enable_greenhouse,
            "lever": self.enable_lever,
            "ashby": self.enable_ashby,
            "linkedin": self.enable_linkedin,
            "indeed": self.enable_indeed,
            "naukri": self.enable_naukri,
            "glassdoor": self.enable_glassdoor,
            "wellfound": self.enable_wellfound,
            "foundit": self.enable_foundit,
        }
        return [name for name, on in flags.items() if on]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
