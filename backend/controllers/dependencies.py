"""HTTP dependency injection; controllers do not construct providers or services."""

from typing import Annotated

from fastapi import Depends, Request

from core.config import Settings
from services.analysis_service import AnalysisService


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_analysis_service(request: Request) -> AnalysisService:
    return request.app.state.analysis_service


SettingsDependency = Annotated[Settings, Depends(get_settings)]
AnalysisServiceDependency = Annotated[AnalysisService, Depends(get_analysis_service)]
