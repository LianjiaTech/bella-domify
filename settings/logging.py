from pydantic.v1 import BaseSettings
import os

env = os.getenv("ENVTYPE", "test")
if env == "test":
    base_path = os.path.dirname(os.path.dirname((os.path.abspath(__file__))))
else:
    base_path = "/data0/www/applogs"


class Settings(BaseSettings):
    LOG_LEVEL: str = "INFO"
    LOG_PATH: str = base_path + "/app-{time:YYYY-MM-DD}.log"
    FIX_LOG_PATH: str = base_path + "/app.log"
    LOG_RETENTION: str = "14 days"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


log_settings = Settings()
