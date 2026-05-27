from typing import List

from apigateway.apps.label.models import APILabel
from apigateway.core.models import Gateway


def save_gateway_labels(gateway: Gateway, names: List[str], username: str = ""):
    exist_names = APILabel.objects.filter(gateway=gateway).values_list("name", flat=True)
    need_create_names = set(names) - set(exist_names)
    if not need_create_names:
        return

    APILabel.objects.bulk_create(
        [APILabel(gateway=gateway, name=name, created_by=username, updated_by=username) for name in need_create_names],
        batch_size=100,
    )
