from django.conf import settings


def get_max_resource_count(gateway_name: str) -> int:
    return settings.API_GATEWAY_RESOURCE_LIMITS["max_resource_count_per_gateway_whitelist"].get(
        gateway_name, settings.API_GATEWAY_RESOURCE_LIMITS["max_resource_count_per_gateway"]
    )
