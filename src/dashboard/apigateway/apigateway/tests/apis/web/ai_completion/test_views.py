#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) Tencent. All rights reserved.
# Licensed under the MIT License (the "License"); you may not use this file except
# in compliance with the License. You may obtain a copy of the License at
#
#     http://opensource.org/licenses/MIT
#
# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the License for the specific language governing permissions and
# limitations under the License.
#
# We undertake not to change the open source license (MIT license) applicable
# to the current version of the project delivered to anyone in the future.
#
import pytest
from django.contrib.auth import get_user_model
from django_dynamic_fixture import G

from apigateway.apps.rbac.models import GatewayMember
from apigateway.apps.support.models import ResourceDoc
from apigateway.apps.support.task import batch_translate_docs
from apigateway.core.models import Gateway

pytestmark = pytest.mark.django_db


@pytest.fixture
def documents(fake_gateway):
    local_doc = G(ResourceDoc, gateway=fake_gateway, resource_id=1, language="zh", content="local source")
    foreign_doc = G(ResourceDoc, gateway=G(Gateway), resource_id=1, language="zh", content="foreign source")
    return local_doc, foreign_doc


@pytest.fixture
def gateway_admin(fake_gateway):
    member = GatewayMember.objects.filter(gateway=fake_gateway).get()
    return get_user_model()(username=member.username, is_superuser=False)


@pytest.mark.parametrize("selection", ["foreign", "mixed", "mixed_reverse", "missing"])
def test_reject_invalid_ids_without_enqueue_or_translation(
    request_view, fake_gateway, gateway_admin, documents, mocker, selection
):
    local_doc, foreign_doc = documents
    ids = {
        "foreign": [foreign_doc.id],
        "mixed": [local_doc.id, foreign_doc.id],
        "mixed_reverse": [foreign_doc.id, local_doc.id],
        "missing": [local_doc.id, max(local_doc.id, foreign_doc.id) + 1],
    }[selection]
    enqueue = mocker.patch("apigateway.apis.web.ai_completion.views.delay_on_commit")
    ai = mocker.patch("apigateway.apps.support.task.AIHandler.analyze_content")
    response = request_view(
        method="POST",
        view_name="ai_completion.batch_translate",
        path_params={"gateway_id": fake_gateway.id},
        user=gateway_admin,
        data={"doc_ids": ids},
    )
    assert response.status_code == 400, response.json()
    enqueue.assert_not_called()
    ai.assert_not_called()
    assert ResourceDoc.objects.count() == 2
    foreign_doc.refresh_from_db()
    assert foreign_doc.content == "foreign source"


@pytest.mark.parametrize("selection", ["explicit", "duplicate", "omitted", "empty"])
def test_enqueue_only_request_gateway_documents(
    request_view, fake_gateway, gateway_admin, documents, mocker, selection
):
    local_doc, _ = documents
    ids = [local_doc.id, local_doc.id] if selection == "duplicate" else [local_doc.id]
    data = {"target_language": "en"}
    if selection != "omitted":
        data["doc_ids"] = [] if selection == "empty" else ids
    enqueue = mocker.patch("apigateway.apis.web.ai_completion.views.delay_on_commit")
    response = request_view(
        method="POST",
        view_name="ai_completion.batch_translate",
        path_params={"gateway_id": fake_gateway.id},
        user=gateway_admin,
        data=data,
    )
    assert response.status_code == 200, response.json()
    assert response.json()["data"]["doc_count"] == len(ids)
    enqueue.assert_called_once_with(
        batch_translate_docs, doc_ids=ids, target_language="en", gateway_id=fake_gateway.id
    )


def test_empty_gateway_does_not_enqueue(request_view, fake_gateway, gateway_admin, mocker):
    enqueue = mocker.patch("apigateway.apis.web.ai_completion.views.delay_on_commit")
    response = request_view(
        method="POST",
        view_name="ai_completion.batch_translate",
        path_params={"gateway_id": fake_gateway.id},
        user=gateway_admin,
        data={},
    )
    assert response.status_code == 400
    enqueue.assert_not_called()


def test_enqueue_failure_reports_error(request_view, fake_gateway, gateway_admin, documents, mocker):
    local_doc, _ = documents
    mocker.patch("apigateway.apis.web.ai_completion.views.delay_on_commit", side_effect=RuntimeError("broker failed"))
    response = request_view(
        method="POST",
        view_name="ai_completion.batch_translate",
        path_params={"gateway_id": fake_gateway.id},
        user=gateway_admin,
        data={"doc_ids": [local_doc.id]},
    )
    assert response.status_code == 500
    assert ResourceDoc.objects.count() == 2
