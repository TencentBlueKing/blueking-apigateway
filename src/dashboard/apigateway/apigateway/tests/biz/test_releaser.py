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
import json

import pytest
from ddf import G

from apigateway.biz.releaser import (
    BaseGatewayReleaser,
    MicroGatewayReleaseHistory,
    MicroGatewayReleaser,
    ReleaseError,
    Releaser,
    ReleaseValidationError,
)
from apigateway.core.constants import ReleaseStatusEnum
from apigateway.core.models import Release, ReleaseHistory, ResourceVersion, Stage

pytestmark = pytest.mark.django_db(transaction=True)


def get_release_data(gateway):
    stage = G(Stage, gateway=gateway)
    resource_version = G(
        ResourceVersion,
        gateway=gateway,
        name=f"{gateway.id}-{stage.id}",
        _data=json.dumps([{"id": 1, "name": "demo", "method": "GET", "path": "/"}]),
    )

    return {
        "stage_id": stage.id,
        "resource_version_id": resource_version.id,
        "comment": "",
    }


class TestBaseGatewayReleaser:
    def test_from_data(self, fake_gateway, fake_stage, fake_resource_version):
        releaser = BaseGatewayReleaser.from_data(
            fake_gateway,
            fake_stage.id,
            fake_resource_version.id,
            "",
            access_token="access_token",
        )
        assert isinstance(releaser, BaseGatewayReleaser)

        # 资源版本 不存在
        with pytest.raises(ResourceVersion.DoesNotExist):
            BaseGatewayReleaser.from_data(fake_gateway, fake_stage.id, 0, "", access_token="access_token")

    def test_release(self, mocker, fake_gateway):
        release_data = get_release_data(fake_gateway)
        releaser = BaseGatewayReleaser.from_data(
            fake_gateway,
            release_data["stage_id"],
            release_data["resource_version_id"],
            release_data.get("comment", ""),
            access_token="access_token",
        )

        # 校验失败
        mocker.patch.object(releaser, "_validate", side_effect=ReleaseValidationError)
        with pytest.raises(ReleaseError):
            releaser.release()
        ReleaseHistory.objects.filter(gateway=fake_gateway, status=ReleaseStatusEnum.FAILURE.value).exists()

        # 校验成功
        mocker.patch.object(releaser, "_validate", return_value=None)
        mock_release = mocker.patch.object(releaser, "_do_release")
        # mock_post_release = mocker.patch.object(releaser, "_post_release")

        releaser.release()
        resource_version_ids = list(
            Release.objects.filter(stage_id=release_data["stage_id"])
            .distinct()
            .values_list("resource_version_id", flat=True)
        )
        assert len(resource_version_ids) == 1
        assert resource_version_ids[0] == release_data["resource_version_id"]
        # assert ReleaseHistory.objects.filter(gateway=fake_gateway, status=ReleaseStatusEnum.SUCCESS.value).exists()
        assert Stage.objects.filter(id=release_data["stage_id"], status=1).count() == 1

        mock_release.assert_called()
        # mock_post_release.assert_called()

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
            "apigateway.biz.validators.ResourceVersionHandler.get_used_stage_vars",
            return_value=mock_used_stage_vars,
        )

        fake_stage.vars = vars
        fake_stage.save(update_fields=["_vars"])
        releaser = BaseGatewayReleaser(gateway=fake_gateway, stage=fake_stage, resource_version=fake_resource_version)

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
            "apigateway.biz.releaser.StageProxyHTTPContext.contain_hosts",
            return_value=contain_hosts_ret,
        ):
            releaser = BaseGatewayReleaser(
                gateway=fake_gateway, stage=fake_stage, resource_version=fake_resource_version
            )

            if not succeeded:
                with pytest.raises(ReleaseValidationError):
                    releaser._validate_stage_upstreams(fake_gateway.id, fake_stage, fake_resource_version.id)
            else:
                assert (
                    releaser._validate_stage_upstreams(fake_gateway.id, fake_stage, fake_resource_version.id) is None
                )

    def test_activate_stages(self, fake_gateway, fake_resource_version):
        s1 = G(Stage, gateway=fake_gateway, status=0)

        releaser = BaseGatewayReleaser(gateway=fake_gateway, stage=s1, resource_version=fake_resource_version)
        releaser._post_release()

        assert Stage.objects.filter(id__in=[s1.id], status=1).count() == 1


class TestMicroGatewayReleaser:
    @pytest.fixture(autouse=True)
    def setup_fixtures(self, fake_gateway):
        self.gateway = fake_gateway
        release_data = get_release_data(self.gateway)
        # self.releaser = BaseGatewayReleaser.from_data(
        self.releaser = MicroGatewayReleaser.from_data(
            self.gateway,
            release_data["stage_id"],
            release_data["resource_version_id"],
            release_data["comment"],
            access_token="access_token",
        )

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
            "apigateway.biz.releaser.release_gateway_by_helm",
            wraps=celery_mock_task,
        )
        releaser = MicroGatewayReleaser(
            gateway=fake_gateway,
            stage=fake_stage,
            resource_version=fake_resource_version,
            access_token="access_token",
        )

        releaser._do_release(fake_release, fake_release_history)

        mock_release_gateway_by_helm.si.assert_called_once_with(
            access_token="access_token",
            release_id=fake_release.pk,
            micro_gateway_release_history_id=mocker.ANY,
            username=releaser.username,
        )

        assert ReleaseHistory.objects.filter(
            id=fake_release_history.id,
        ).exists()

        qs = MicroGatewayReleaseHistory.objects.filter(
            gateway=fake_gateway,
            stage=fake_stage,
            release_history=fake_release_history,
        )

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
            "apigateway.biz.releaser.release_gateway_by_registry",
            wraps=celery_mock_task,
        )
        releaser = MicroGatewayReleaser(gateway=fake_gateway, stage=fake_stage, resource_version=fake_resource_version)

        releaser._do_release(fake_release, fake_release_history)

        mock_release_gateway_by_registry.si.assert_called_once_with(
            micro_gateway_id=fake_shared_gateway.id,
            release_id=fake_release.id,
            micro_gateway_release_history_id=mocker.ANY,
            publish_id=fake_release_history.id,
        )

        assert ReleaseHistory.objects.filter(
            id=fake_release_history.id,
        ).exists()

        assert MicroGatewayReleaseHistory.objects.filter(
            gateway=fake_gateway,
            stage=fake_stage,
            micro_gateway=fake_shared_gateway,
            release_history=fake_release_history,
        ).exists()


class TestReleaser:
    def test_release(self, mocker, fake_gateway):
        mock_release = mocker.patch("apigateway.biz.releaser.BaseGatewayReleaser.release")
        release_data = get_release_data(fake_gateway)
        Releaser(access_token="access_token").release(
            fake_gateway, release_data["stage_id"], release_data["resource_version_id"], release_data["comment"]
        )
        mock_release.assert_called_once_with()
