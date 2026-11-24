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
from types import SimpleNamespace

import pytest
from django_dynamic_fixture import G

from apigateway.apps.support.models import ResourceDoc
from apigateway.apps.support.task import batch_translate_docs, translate_single_doc
from apigateway.biz.ai import AIContentTypeEnum
from apigateway.core.models import Gateway

pytestmark = pytest.mark.django_db


@pytest.fixture
def documents(fake_gateway):
    local_doc = G(ResourceDoc, gateway=fake_gateway, resource_id=1, language="zh", content="local source")
    foreign_doc = G(ResourceDoc, gateway=G(Gateway), resource_id=1, language="zh", content="foreign source")
    return local_doc, foreign_doc


@pytest.fixture
def ai(mocker):
    return mocker.patch(
        "apigateway.apps.support.task.AIHandler.analyze_content",
        return_value=SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="translated"))]),
    )


@pytest.mark.parametrize("message_format", ["positional", "keyword", "mixed", "explicit_null"])
def test_legacy_batch_messages_fail_without_ai_or_writes(documents, ai, message_format):
    local_doc, foreign_doc = documents
    if message_format == "positional":
        result = batch_translate_docs.run([local_doc.id], "en")
    elif message_format == "keyword":
        result = batch_translate_docs.run(doc_ids=[local_doc.id], target_language="en")
    elif message_format == "mixed":
        result = batch_translate_docs.run([local_doc.id, foreign_doc.id])
    else:
        result = batch_translate_docs.run([local_doc.id], "en", gateway_id=None)
    assert result["success"] is False
    ai.assert_not_called()
    assert ResourceDoc.objects.count() == 2


@pytest.mark.parametrize("selection", ["foreign", "mixed", "mixed_reverse", "missing", "empty"])
def test_scoped_batch_rejects_all_invalid_ids(fake_gateway, documents, ai, selection):
    local_doc, foreign_doc = documents
    ids = {
        "foreign": [foreign_doc.id],
        "mixed": [local_doc.id, foreign_doc.id],
        "mixed_reverse": [foreign_doc.id, local_doc.id],
        "missing": [local_doc.id, max(local_doc.id, foreign_doc.id) + 1],
        "empty": [],
    }[selection]
    result = batch_translate_docs.run(ids, gateway_id=fake_gateway.id)
    assert result["success"] is False
    ai.assert_not_called()
    assert ResourceDoc.objects.count() == 2


@pytest.mark.parametrize("change", ["delete", "move"])
def test_scope_is_rechecked_after_enqueue(fake_gateway, documents, ai, change):
    local_doc, foreign_doc = documents
    ids = [local_doc.id]
    if change == "delete":
        local_doc.delete()
    else:
        ResourceDoc.objects.filter(id=local_doc.id).update(gateway_id=foreign_doc.gateway_id, resource_id=2)
    result = batch_translate_docs.run(ids, gateway_id=fake_gateway.id)
    assert result["success"] is False
    ai.assert_not_called()
    assert not ResourceDoc.objects.filter(language="en").exists()


@pytest.mark.parametrize("target_content", ["missing", "", "   ", None])
def test_translate_local_missing_or_empty_target_only(fake_gateway, documents, ai, target_content):
    local_doc, foreign_doc = documents
    target = None
    if target_content != "missing":
        target = G(
            ResourceDoc, gateway=fake_gateway, resource_id=local_doc.resource_id, language="en", content=target_content
        )
    result = batch_translate_docs.run([local_doc.id, local_doc.id], "en", gateway_id=fake_gateway.id)
    assert result["success"] is True
    assert result["success_count"] == 1
    assert result["error_count"] == 0
    ai.assert_called_once_with(content_type=AIContentTypeEnum.DOC_TRANSLATE, content="local source", language="en")
    translated = ResourceDoc.objects.get(gateway=fake_gateway, resource_id=local_doc.resource_id, language="en")
    assert translated.content == "translated"
    if target is not None:
        assert translated.id == target.id
    assert not ResourceDoc.objects.filter(gateway=foreign_doc.gateway, language="en").exists()
    foreign_doc.refresh_from_db()
    assert foreign_doc.content == "foreign source"


@pytest.mark.parametrize("source_language, target_language", [("zh", "en"), ("en", "zh")])
def test_single_document_legacy_signature_still_translates(documents, ai, source_language, target_language):
    local_doc, _ = documents
    local_doc.language = source_language
    local_doc.save(update_fields=["language"])
    result = translate_single_doc.run(local_doc.id, target_language)
    assert result["success"] is True
    ai.assert_called_once_with(
        content_type=AIContentTypeEnum.DOC_TRANSLATE, content="local source", language=target_language
    )
    assert (
        ResourceDoc.objects.get(
            gateway=local_doc.gateway, resource_id=local_doc.resource_id, language=target_language
        ).content
        == "translated"
    )


def test_single_document_missing_id_fails(ai):
    assert translate_single_doc.run(1)["success"] is False
    ai.assert_not_called()


@pytest.mark.parametrize("reason", ["nonempty_target", "same_language", "empty_source"])
def test_existing_skip_behavior(fake_gateway, documents, ai, reason):
    local_doc, _ = documents
    if reason == "nonempty_target":
        G(ResourceDoc, gateway=fake_gateway, resource_id=local_doc.resource_id, language="en", content="keep this")
    elif reason == "empty_source":
        local_doc.content = "   "
        local_doc.save(update_fields=["content"])
    result = batch_translate_docs.run(
        [local_doc.id], "zh" if reason == "same_language" else "en", gateway_id=fake_gateway.id
    )
    assert result["success"] is True
    assert result["success_count"] == 0
    ai.assert_not_called()
    if reason == "nonempty_target":
        assert ResourceDoc.objects.get(gateway=fake_gateway, language="en").content == "keep this"
    else:
        assert not ResourceDoc.objects.filter(language="en").exists()


def test_ai_failure_does_not_write_translation(fake_gateway, documents, ai):
    local_doc, _ = documents
    ai.side_effect = RuntimeError("AI unavailable")
    result = batch_translate_docs.run([local_doc.id], "en", gateway_id=fake_gateway.id)
    assert result["error_count"] == 1
    assert result["success_count"] == 0
    assert not ResourceDoc.objects.filter(language="en").exists()
    local_doc.refresh_from_db()
    assert local_doc.content == "local source"


def test_repeated_batch_keeps_nonempty_translation(fake_gateway, documents, ai):
    local_doc, _ = documents
    first = batch_translate_docs.run([local_doc.id], "en", gateway_id=fake_gateway.id)
    second = batch_translate_docs.run([local_doc.id], "en", gateway_id=fake_gateway.id)
    assert first["success_count"] == 1
    assert second["success_count"] == 0
    assert ResourceDoc.objects.filter(gateway=fake_gateway, language="en").count() == 1
    ai.assert_called_once()


def test_interleaved_gateway_batches_keep_translations_in_their_gateway(documents, ai):
    local_doc, foreign_doc = documents

    def translate(content_type, content, language):
        if content == "local source":
            foreign_result = batch_translate_docs.run([foreign_doc.id], "en", gateway_id=foreign_doc.gateway_id)
            assert foreign_result["success_count"] == 1
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=f"translated {content}"))])

    ai.side_effect = translate
    local_result = batch_translate_docs.run([local_doc.id], "en", gateway_id=local_doc.gateway_id)
    assert local_result["success_count"] == 1
    assert ai.call_count == 2
    assert ResourceDoc.objects.get(gateway=local_doc.gateway, language="en").content == "translated local source"
    assert ResourceDoc.objects.get(gateway=foreign_doc.gateway, language="en").content == "translated foreign source"
