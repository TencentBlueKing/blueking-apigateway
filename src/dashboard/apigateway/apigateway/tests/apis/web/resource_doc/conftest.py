import pytest
from ddf import G

from apigateway.apps.support.models import ResourceDoc


@pytest.fixture
def fake_resource_doc(faker, fake_resource):
    return G(
        ResourceDoc,
        api=fake_resource.api,
        resource_id=fake_resource.id,
        language=faker.random_element(
            ["en", "zh"],
        ),
    )
