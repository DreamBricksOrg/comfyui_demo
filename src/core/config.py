from pydantic import Field
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    BASE_URL: str = Field(..., env="BASE_URL")
    STATIC_DIR: str = Field(..., env="STATIC_DIR")
    IMAGE_TEMP_FOLDER: str = Field(default="static/outputs", env="IMAGE_TEMP_FOLDER")
    TIMER_TERMS: str = Field(20, env="TIMER_TERMS")
    COMFYUI_API_SERVER1: str = Field(default=None, env="COMFYUI_API_SERVER1")
    COMFYUI_API_SERVER2: str = Field(default=None, env="COMFYUI_API_SERVER2")
    COMFYUI_API_SERVER3: str = Field(default=None, env="COMFYUI_API_SERVER3")
    COMFYUI_API_SERVER4: str = Field(default=None, env="COMFYUI_API_SERVER4")
    WORKFLOW_PATH: str = Field(default="workflows/comfyui_basic_input_model_v0.json", env="WORKFLOW_PATH")
    WORKFLOW_NODE_ID_KSAMPLER: str = Field(default="3", env="WORKFLOW_NODE_ID_KSAMPLER")
    WORKFLOW_NODE_ID_IMAGE_LOAD: str = Field(default="15", env="WORKFLOW_NODE_ID_IMAGE_LOAD")
    WORKFLOW_NODE_ID_TEXT_INPUT: str = Field(default="18", env="WORKFLOW_NODE_ID_TEXT_INPUT")
    CONFIG_INDEX: str = Field(default=6, env="CONFIG_INDEX")
    DEFAULT_PROCESSING_TIME: int = Field(8000, env="DEFAULT_PROCESSING_TIME")
    LOG_API: Optional[str] = Field(default=None, env="LOG_API")
    LOG_PROJECT_ID: Optional[str] = Field(default=None, env="LOG_PROJECT_ID")
    REDIS_URL: str = Field(..., env="REDIS_URL")
    SENTRY_DSN: Optional[str] = Field(default=None, env="SENTRY_DSN")
    SMS_API_URL: Optional[str] = Field(default=None, env='SMS_API_URL')
    SMS_API_KEY: Optional[str] = Field(default=None, env='SMS_API_KEY')
    AWS_REGION: str = Field(..., env="AWS_REGION")
    S3_BUCKET: str = Field(..., env="S3_BUCKET")


    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()