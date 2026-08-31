import logging
from typing import TYPE_CHECKING

from django.utils.translation import gettext as _
from pydantic import ValidationError as PydanticValidationError
from rest_framework import serializers

from .adapter import AIBackendWebConfigAdapter, AIBackendWebConfigNotRepresentable
from .serializers import AIBackendWebOutputSLZ

if TYPE_CHECKING:
    from apigateway.core.models import BackendConfig

logger = logging.getLogger(__name__)


def serialize_ai_backend_config_for_web(
    backend_config: BackendConfig,
    *,
    error_field: str = "config",
) -> dict:
    try:
        config = AIBackendWebConfigAdapter.to_web(backend_config.config)
    except PydanticValidationError, AIBackendWebConfigNotRepresentable:
        logger.exception(
            "failed to convert AI backend config for Web: backend_config_id=%s",
            backend_config.id,
        )
        raise serializers.ValidationError({error_field: _("已有模型服务配置无法通过 Web 接口编辑。")}) from None

    return AIBackendWebOutputSLZ(config).data
