from rest_framework import serializers

from apigateway.common.constants import SDKGenerationLanguageEnum


class SDKGenerationLanguageField(serializers.ChoiceField):
    """Accept the legacy ``golang`` spelling while exposing canonical OAS choices."""

    def __init__(self, **kwargs):
        super().__init__(choices=SDKGenerationLanguageEnum.get_choices(), **kwargs)

    def to_internal_value(self, data):
        if data == "golang":
            data = SDKGenerationLanguageEnum.GO.value
        return super().to_internal_value(data)
