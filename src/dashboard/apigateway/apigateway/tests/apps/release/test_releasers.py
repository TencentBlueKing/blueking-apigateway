# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2017 THL A29 Limited, a Tencent company. All rights reserved.
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
from ddf import G
from django.http import Http404

from apigateway.apps.release.releasers import (
    DefaultGatewayReleaser,
    GatewayReleaserFactory,
    MicroGatewayReleaseHistory,
    MicroGatewayReleaser,
    ReleaseBatchManager,
    ReleaseError,
    ReleaseValidationError,
)
from apigateway.core.constants import APIHostingTypeEnum, ReleaseStatusEnum
from apigateway.core.models import Release, ReleaseHistory, ResourceVersion, Stage

pytestmark = pytest.mark.django_db(transaction=True)


def get_release_data(api):
    stage = G(Stage, api=api)
    resource_version = G(ResourceVersion, api=api, name=f"{api.id}-{stage.id}")

    return {
        "stage_ids": [stage.id],
        "resource_version_id": resource_version.id,
        "comment": "",
    }


class TestGatewayReleaserFactory:
    @pytest.mark.parametrize(
        "hosting_type, expected",
        [
            (APIHostingTypeEnum.MICRO.value, MicroGatewayReleaser),
            (APIHostingTypeEnum.DEFAULT.value, DefaultGatewayReleaser),
        ],
    )
    def test_get_releaser(self, fake_gateway, hosting_type, expected):
        fake_gateway.hosting_type = hosting_type

        release_data = get_release_data(fake_gateway)
        result = GatewayReleaserFactory.get_releaser(fake_gateway, release_data, access_token="access_token")
        assert isinstance(result, expected)


class TestDefaultGatewayReleaser:
    def test_from_data(self, fake_gateway, fake_stage, fake_resource_version):
        releaser = DefaultGatewayReleaser.from_data(
            fake_gateway,
            {"stage_ids": [fake_stage.id], "resource_version_id": fake_resource_version.id},
            access_token="access_token",
        )
        assert isinstance(releaser, DefaultGatewayReleaser)

        # 资源版本 不存在
        with pytest.raises(Http404):
            DefaultGatewayReleaser.from_data(
                fake_gateway, {"stage_ids": [fake_stage.id], "resource_version_id": 0}, access_token="access_token"
            )

    def test_release_batch(self, mocker, fake_gateway):
        release_data = get_release_data(fake_gateway)
        releaser = DefaultGatewayReleaser.from_data(fake_gateway, release_data, access_token="access_token")

        # 校验失败
        mocker.patch.object(releaser, "_validate", side_effect=ReleaseValidationError)
        with pytest.raises(ReleaseError):
            releaser.release_batch()
        ReleaseHistory.objects.filter(api=fake_gateway, status=ReleaseStatusEnum.FAILURE.value).exists()

        # 校验成功
        mocker.patch.object(releaser, "_validate", return_value=None)
        mock_release = mocker.patch.object(releaser, "_do_release")
        mock_update_and_clear_released_resources = mocker.patch.object(
            releaser, "_update_and_clear_released_resources"
        )
        mock_update_and_clear_released_resource_docs = mocker.patch.object(
            releaser, "_update_and_clear_released_resource_docs"
        )

        releaser.release_batch()
        resource_version_ids = list(
            Release.objects.filter(stage_id__in=release_data["stage_ids"])
            .distinct()
            .values_list("resource_version_id", flat=True)
        )
        assert len(resource_version_ids) == 1
        assert resource_version_ids[0] == release_data["resource_version_id"]
        assert ReleaseHistory.objects.filter(api=fake_gateway, status=ReleaseStatusEnum.SUCCESS.value).exists()
        assert Stage.objects.filter(id__in=release_data["stage_ids"], status=1).count() == len(
            release_data["stage_ids"]
        )

        mock_release.assert_called()
        mock_update_and_clear_released_resources.assert_called()
        mock_update_and_clear_released_resource_docs.assert_called()

    @pytest.mark.parametrize(
        "vars, mock_used_stage_vars, will_error",
        [
            # ok
            (
                {
                    "prefix": "/o",
                    "domain": "bking.com",
                },
                {
                    "in_path": ["prefix"],
                    "in_host": ["domain"],
                },
                False,
            ),
            # var in path not exist
            (
                {
                    "domain": "bking.com",
                },
                {
                    "in_path": ["prefix"],
                    "in_host": ["domain"],
                },
                True,
            ),
            # var in path invalid
            (
                {
                    "prefix": "/test/?a=b",
                    "domain": "bking.com",
                },
                {
                    "in_path": ["prefix"],
                    "in_host": ["domain"],
                },
                True,
            ),
            # var in hosts not exist
            (
                {
                    "prefix": "/test/",
                },
                {
                    "in_path": ["prefix"],
                    "in_host": ["domain"],
                },
                True,
            ),
            # var in hosts invalid
            (
                {
                    "prefix": "/test/",
                    "domain": "http://bking.com",
                },
                {
                    "in_path": ["prefix"],
                    "in_host": ["domain"],
                },
                True,
            ),
        ],
    )
    def test_validate_stage_vars(
        self, mocker, fake_gateway, fake_stage, fake_resource_version, vars, mock_used_stage_vars, will_error
    ):
        mocker.patch(
            "apigateway.core.managers.ResourceVersionManager.get_used_stage_vars",
            return_value=mock_used_stage_vars,
        )

        fake_stage.vars = vars
        fake_stage.save(update_fields=["_vars"])
        releaser = DefaultGatewayReleaser(
            gateway=fake_gateway, stages=[fake_stage], resource_version=fake_resource_version
        )

        if will_error:
            with pytest.raises(Exception):
                releaser._validate_stage_vars(fake_stage, fake_resource_version.id)
            return

        assert releaser._validate_stage_vars(fake_stage, fake_resource_version.id) is None

    @pytest.mark.parametrize(
        "contain_hosts_ret,succeeded",
        [
            (True, True),
            (False, False),
        ],
    )
    def test_validate_stage_upstreams(
        self,
        contain_hosts_ret,
        succeeded,
        fake_gateway,
        fake_stage,
        fake_resource_version,
        mocker,
    ):
        with mocker.patch(
            "apigateway.apps.release.releasers.StageProxyHTTPContext.contain_hosts",
            return_value=contain_hosts_ret,
        ):
            releaser = DefaultGatewayReleaser(
                gateway=fake_gateway, stages=[fake_stage], resource_version=fake_resource_version
            )

            if not succeeded:
                with pytest.raises(ReleaseValidationError):
                    releaser._validate_stage_upstreams(fake_gateway.id, fake_stage, fake_resource_version.id)
            else:
                assert (
                    releaser._validate_stage_upstreams(fake_gateway.id, fake_stage, fake_resource_version.id) is None
                )

    def test_activate_stages(self, fake_gateway):
        s1 = G(Stage, api=fake_gateway, status=0)
        s2 = G(Stage, api=fake_gateway, status=1)

        releaser = DefaultGatewayReleaser(gateway=fake_gateway, stages=[s1, s2], resource_version=None)
        releaser._activate_stages()

        assert Stage.objects.filter(id__in=[s1.id, s2.id], status=1).count() == 2


class TestMicroGatewayReleaser:
    @pytest.fixture(autouse=True)
    def setup_fixtures(self, fake_gateway):
        self.api = fake_gateway
        self.releaser = MicroGatewayReleaser.from_data(
            self.api, get_release_data(self.api), access_token="access_token"
        )

    def test_save_ok_release_history(self):
        self.releaser._save_ok_release_history()

        assert ReleaseHistory.objects.filter(api=self.api, status=ReleaseStatusEnum.PENDING.value).count() == 1

    def test_do_release_edge_gateway(
        self,
        mocker,
        celery_task_eager_mode,
        fake_gateway,
        fake_stage,
        fake_resource_version,
        fake_shared_gateway,
        fake_edge_gateway,
        fake_release,
        fake_release_history,
        celery_mock_task,
    ):
        mock_release_gateway_by_helm = mocker.patch(
            "apigateway.apps.release.releasers.release_gateway_by_helm",
            wraps=celery_mock_task,
        )
        mock_release_gateway_by_registry = mocker.patch(
            "apigateway.apps.release.releasers.release_gateway_by_registry",
            wraps=celery_mock_task,
        )
        releaser = MicroGatewayReleaser(
            gateway=fake_gateway,
            stages=[fake_stage],
            resource_version=fake_resource_version,
            access_token="access_token",
        )

        releaser._do_release([fake_release], fake_release_history)

        mock_release_gateway_by_helm.si.assert_called_once_with(
            access_token="access_token",
            release_id=fake_release.pk,
            micro_gateway_release_history_id=mocker.ANY,
            username=releaser.username,
        )
        # mock_release_gateway_by_registry.si.assert_called_once_with(
        #     release_id=fake_release.pk,
        #     micro_gateway_release_history_id=mocker.ANY,
        #     micro_gateway_id=fake_shared_gateway.id,
        # )

        assert ReleaseHistory.objects.filter(
            id=fake_release_history.id,
            status=ReleaseStatusEnum.SUCCESS.value,
        ).exists()

        qs = MicroGatewayReleaseHistory.objects.filter(
            api=fake_gateway,
            stage=fake_stage,
            release_history=fake_release_history,
        )

        # assert qs.filter(micro_gateway=fake_shared_gateway).exists()
        assert qs.filter(micro_gateway=fake_edge_gateway).exists()

    def test_do_release_shared_gateway(
        self,
        mocker,
        celery_task_eager_mode,
        fake_gateway,
        fake_stage,
        fake_resource_version,
        fake_shared_gateway,
        fake_release,
        fake_release_history,
        celery_mock_task,
    ):
        mock_release_gateway_by_registry = mocker.patch(
            "apigateway.apps.release.releasers.release_gateway_by_registry",
            wraps=celery_mock_task,
        )
        releaser = MicroGatewayReleaser(
            gateway=fake_gateway, stages=[fake_stage], resource_version=fake_resource_version
        )

        releaser._do_release([fake_release], fake_release_history)

        mock_release_gateway_by_registry.si.assert_called_once_with(
            micro_gateway_id=fake_shared_gateway.id,
            release_id=fake_release.id,
            micro_gateway_release_history_id=mocker.ANY,
        )

        assert ReleaseHistory.objects.filter(
            id=fake_release_history.id,
            status=ReleaseStatusEnum.SUCCESS.value,
        ).exists()

        assert MicroGatewayReleaseHistory.objects.filter(
            api=fake_gateway,
            stage=fake_stage,
            micro_gateway=fake_shared_gateway,
            release_history=fake_release_history,
        ).exists()


class TestReleaseBatchManager:
    def test_release_batch(self, mocker, fake_gateway):
        mock_release_batch = mocker.patch("apigateway.apps.release.releasers.DefaultGatewayReleaser.release_batch")

        ReleaseBatchManager(access_token="access_token").release_batch(fake_gateway, get_release_data(fake_gateway))
        mock_release_batch.assert_called_once_with()
