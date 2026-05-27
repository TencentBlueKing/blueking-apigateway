from typing import Dict

from apigateway.core.models import Backend


def get_backend_id_to_instance(gateway_id: int) -> Dict[int, Backend]:
    return {backend.id: backend for backend in Backend.objects.filter(gateway_id=gateway_id)}
