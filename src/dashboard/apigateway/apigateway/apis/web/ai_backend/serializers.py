from collections.abc import Mapping
from urllib.parse import urlsplit

from django.utils.http import MAX_URL_LENGTH
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from apigateway.common.security import is_forbidden_host
from apigateway.core.ai_backend import get_ai_backend_provider_config
from apigateway.core.constants import HOST_WITHOUT_SCHEME_PATTERN, AIBackendProviderEnum


class AIBackendEndpointField(serializers.CharField):
    class Meta:
        swagger_schema_fields = {"format": "uri"}

    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        if len(value) > MAX_URL_LENGTH:
            raise serializers.ValidationError(
                _("URL 长度不能超过 {max_length} 个字符。").format(max_length=MAX_URL_LENGTH), code="invalid"
            )
        if any(char.isspace() or ord(char) < 32 for char in value):
            raise serializers.ValidationError(_("URL 中不能包含空白或控制字符。"), code="invalid")
        try:
            parsed = urlsplit(value)
        except ValueError:
            raise serializers.ValidationError(
                _("主机名或 IP 格式不合法，支持 Service 短名称。"), code="invalid"
            ) from None

        if parsed.scheme not in {"http", "https"}:
            raise serializers.ValidationError(
                _("仅支持 HTTP/HTTPS 协议，请以 http:// 或 https:// 开头。"), code="invalid"
            )
        if not parsed.hostname:
            raise serializers.ValidationError(_("URL 缺少主机名或 IP 地址。"), code="invalid")
        if parsed.username is not None or parsed.password is not None:
            raise serializers.ValidationError(_("URL 中不能包含用户名或密码。"), code="invalid")
        try:
            port = parsed.port
        except ValueError:
            raise serializers.ValidationError(_("端口必须是 1～65535 的整数。"), code="invalid") from None
        if port == 0 or parsed.netloc.endswith(":"):
            raise serializers.ValidationError(_("端口必须是 1～65535 的整数。"), code="invalid")

        # Reuse standard backend host:port rules, including single-label service names.
        if not HOST_WITHOUT_SCHEME_PATTERN.fullmatch(parsed.netloc):
            raise serializers.ValidationError(_("主机名或 IP 格式不合法，支持 Service 短名称。"), code="invalid")
        if is_forbidden_host(parsed.hostname) or is_forbidden_host(parsed.netloc):
            raise serializers.ValidationError(_("该主机或端口不允许使用。"), code="invalid")
        return value


class _StrictSerializer(serializers.Serializer):
    def to_internal_value(self, data):
        if isinstance(data, Mapping):
            unknown = set(data) - set(self.fields)
            if unknown:
                raise serializers.ValidationError(dict.fromkeys(sorted(unknown), "未知字段。"))
        return super().to_internal_value(data)


class AIBackendAuthHeaderSLZ(_StrictSerializer):
    name = serializers.CharField(allow_blank=False, trim_whitespace=False)
    value = serializers.CharField(allow_blank=False, trim_whitespace=False)


class AIBackendWebInputSLZ(_StrictSerializer):
    provider = serializers.ChoiceField(choices=AIBackendProviderEnum.get_choices())
    endpoint = AIBackendEndpointField(required=False)
    model_endpoint = AIBackendEndpointField(required=False, allow_null=True)
    api_key = serializers.CharField(required=False, allow_null=True, allow_blank=False, trim_whitespace=False)
    auth_header = AIBackendAuthHeaderSLZ(required=False, allow_null=True)
    model = serializers.CharField(required=False, allow_null=True, allow_blank=False)
    model_options = serializers.DictField(required=False, default=dict)
    timeout = serializers.IntegerField(required=False, default=300, min_value=1, max_value=300)

    def validate(self, attrs):
        provider_config = get_ai_backend_provider_config(attrs["provider"])
        if "model" in attrs["model_options"]:
            raise serializers.ValidationError({"model_options": {"model": "不能包含 model 字段。"}})

        if provider_config is not None:
            if (endpoint := attrs.get("endpoint")) and endpoint != provider_config.endpoint:
                raise serializers.ValidationError({"endpoint": "内置 Provider 的 Endpoint 不可修改。"})
            if (model_endpoint := attrs.get("model_endpoint")) and model_endpoint != provider_config.model_endpoint:
                raise serializers.ValidationError({"model_endpoint": "内置 Provider 的 Models Endpoint 不可修改。"})
            if not attrs.get("api_key"):
                raise serializers.ValidationError({"api_key": "该字段为必填项。"})
            if attrs.get("auth_header") is not None:
                raise serializers.ValidationError({"auth_header": "内置 Provider 请使用 api_key。"})
        else:
            if not attrs.get("endpoint"):
                raise serializers.ValidationError({"endpoint": "该字段为必填项。"})
            if attrs.get("api_key") is not None:
                raise serializers.ValidationError({"api_key": "自定义 Provider 请使用 auth_header。"})
        return attrs


class AIBackendWebOutputSLZ(serializers.Serializer):
    provider = serializers.ChoiceField(choices=AIBackendProviderEnum.get_choices())
    endpoint = serializers.URLField()
    model_endpoint = serializers.URLField(allow_null=True)
    api_key = serializers.CharField(allow_null=True)
    auth_header = AIBackendAuthHeaderSLZ(allow_null=True)
    model = serializers.CharField(allow_null=True)
    model_options = serializers.DictField()
    timeout = serializers.IntegerField()
