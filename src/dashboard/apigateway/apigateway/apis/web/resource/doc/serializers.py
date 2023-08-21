from django.utils.translation import gettext as _
from rest_framework import serializers

from apigateway.apps.support.constants import DocLanguageEnum
from apigateway.apps.support.models import ResourceDoc


class DocInputSLZ(serializers.ModelSerializer):
    language = serializers.ChoiceField(choices=DocLanguageEnum.get_choices())

    class Meta:
        model = ResourceDoc
        fields = ["language", "content"]

    def validate_language(self, value):
        gateway_id = self.context["gateway_id"]
        resource_id = self.context["resource_id"]
        queryset = ResourceDoc.objects.filter(api_id=gateway_id, resource_id=resource_id, language=value)
        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError(_("该资源语言 {value} 的文档已存在。").format(value=value))

        return value


class DocOutputSLZ(serializers.ModelSerializer):
    class Meta:
        model = ResourceDoc
        fields = [
            "id",
            "language",
            "content",
        ]
        read_only_fields = fields
