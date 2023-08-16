from django.utils.translation import gettext as _
from rest_framework import serializers

from apigateway.common.mixins.contexts import GetGatewayFromContextMixin
from apigateway.core.constants import APP_CODE_PATTERN


class MaxCountPerGatewayValidator(GetGatewayFromContextMixin):
    requires_context = True

    def __init__(self, model, max_count_callback, message):
        self.model = model
        self.max_count_callback = max_count_callback
        self.message = message

    def _get_exist_count(self, gateway):
        return self.model.objects.filter(api_id=gateway.id).count()

    def __call__(self, attrs, serializer):
        gateway = self._get_gateway(serializer)
        instance = getattr(serializer, "instance", None)

        if instance:
            # 更新时，不校验
            return

        if self._get_exist_count(gateway) >= self.max_count_callback(gateway):
            message = self.message.format(max_count=self.max_count_callback(gateway))
            raise serializers.ValidationError(message)


class ResourceIDValidator(GetGatewayFromContextMixin):
    requires_context = True

    def __call__(self, value, serializer_field):
        if not value:
            return

        gateway = self._get_gateway(serializer_field)
        resource_ids = value
        if isinstance(value, int):
            resource_ids = [value]

        assert isinstance(resource_ids, list)

        from apigateway.core.models import Resource

        count = Resource.objects.filter(api_id=gateway.id, id__in=resource_ids).count()
        if count != len(set(resource_ids)):
            raise serializers.ValidationError(_("网关【id={api_id}】下指定的部分资源ID不存在。").format(api_id=gateway.id))


class BKAppCodeListValidator:
    def __call__(self, value):
        if not value:
            return

        assert isinstance(value, list)

        invalid_app_codes = [app_code for app_code in value if not APP_CODE_PATTERN.match(app_code)]
        if invalid_app_codes:
            raise serializers.ValidationError(
                _("蓝鲸应用【{app_codes}】不匹配要求的模式。").format(app_codes=", ".join(sorted(invalid_app_codes)))
            )


class BKAppCodeValidator:
    def __call__(self, value):
        if not value:
            return

        assert isinstance(value, str)

        if not APP_CODE_PATTERN.match(value):
            raise serializers.ValidationError(_("蓝鲸应用【{value}】不匹配要求的模式。").format(value=value))
