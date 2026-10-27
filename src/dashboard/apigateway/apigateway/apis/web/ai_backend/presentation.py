import logging
from typing import TYPE_CHECKING

from django.utils.translation import gettext as _
from drf_spectacular.utils import OpenApiParameter
from pydantic import ValidationError as PydanticValidationError
from rest_framework import serializers

from .adapter import AIBackendWebConfigAdapter, AIBackendWebConfigNotRepresentable
from .serializers import AIBackendWebOutputSLZ, AIBackendWebPoolOutputSLZ

if TYPE_CHECKING:
    from apigateway.core.models import BackendConfig

logger = logging.getLogger(__name__)

AI_BACKEND_CONFIG_FORMAT_PARAMETER = OpenApiParameter(
    "config_format",
    str,
    enum=["legacy", "instances"],
    default="legacy",
    description="模型服务配置输出格式：legacy 为兼容单实例格式，instances 返回包含实例 name 的数组。",
)


class AIBackendConfigFormatSLZ(serializers.Serializer):
    config_format = serializers.ChoiceField(choices=["legacy", "instances"], default="legacy")


def get_ai_backend_config_format_context(request) -> dict:
    serializer = AIBackendConfigFormatSLZ(data=request.query_params)
    serializer.is_valid(raise_exception=True)
    return dict(serializer.validated_data)


def serialize_ai_backend_config_for_web(
    backend_config: BackendConfig,
    *,
    error_field: str = "config",
    config_format: str = "legacy",
) -> dict:
    try:
        config = AIBackendWebConfigAdapter.to_web(backend_config.config, config_format=config_format)
    except PydanticValidationError, AIBackendWebConfigNotRepresentable:
        logger.exception(
            "failed to convert AI backend config for Web: backend_config_id=%s",
            backend_config.id,
        )
        message = _("已有模型服务配置无法通过 Web 接口编辑。")
        if config_format == "legacy" and len(backend_config.config.get("instances", [])) > 1:
            message += _("请使用 config_format=instances 查询完整配置。")
        raise serializers.ValidationError({error_field: message}) from None

    output_class = AIBackendWebPoolOutputSLZ if config_format == "instances" else AIBackendWebOutputSLZ
    return output_class(config).data
