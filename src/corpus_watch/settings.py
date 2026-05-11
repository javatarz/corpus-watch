from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    db_path: str = "corpus_watch.db"
    host: str = "0.0.0.0"
    port: int = 8000

    model_config = {"env_prefix": "CORPUS_WATCH_"}


settings = Settings()
