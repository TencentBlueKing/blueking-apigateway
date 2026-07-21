from collections.abc import Mapping

from rest_framework import serializers

from apigateway.core.ai_backend import get_ai_backend_provider_config
from apigateway.core.constants import AIBackendProviderEnum


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
    endpoint = serializers.URLField(required=False)
    model_endpoint = serializers.URLField(required=False, allow_null=True)
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
