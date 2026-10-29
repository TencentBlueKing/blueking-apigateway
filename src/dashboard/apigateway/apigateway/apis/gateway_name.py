"""Web 和 Sync 共用的 display_name 校验。"""

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apigateway.core.gateway_name import normalize_display_name
from apigateway.core.models import Gateway


def validate_gateway_display_name(data, instance=None):
    # 更新时省略表示保留；创建时即使省略，也要检查回退后的 name 是否已被占用。
    if instance is not None and "display_name" not in data:
        return
    try:
        value = normalize_display_name(data.get("display_name"), name=instance.name if instance else data["name"])
    except ValidationError as exc:
        raise ValidationError({"display_name": exc}) from exc
    if Gateway.objects.exclude(pk=instance.pk if instance else None).filter(display_name__iexact=value).exists():
        raise ValidationError(
            {"display_name": ValidationError(_("This display name is already in use."), code="unique")}
        )
    if "display_name" in data:
        data["display_name"] = value
