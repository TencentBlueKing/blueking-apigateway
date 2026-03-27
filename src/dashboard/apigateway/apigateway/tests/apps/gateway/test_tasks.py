#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
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
from datetime import timedelta
from unittest.mock import patch

import pytest
from ddf import G
from django.utils import timezone

from apigateway.apps.gateway.tasks import InactiveGatewayNotifier, notify_inactive_gateway_maintainers
from apigateway.apps.metrics.models import StatisticsGatewayRequestByDay
from apigateway.biz.gateway.gateway import OPERATION_STATUS_DELTA_DAYS
from apigateway.core.constants import GatewayStatusEnum, StageStatusEnum
from apigateway.core.models import Gateway, Release, ResourceVersion, Stage


@pytest.fixture
def _make_released_gateway(faker):
    """Create a gateway with an active released stage."""

    def factory(
        maintainers="admin",
        created_time_delta_days=200,
        stage_name="prod",
        gateway_status=GatewayStatusEnum.ACTIVE.value,
        stage_status=StageStatusEnum.ACTIVE.value,
    ):
        gateway = G(
            Gateway,
            name=faker.pystr(),
            _maintainers=maintainers,
            status=gateway_status,
            is_public=True,
            created_by="creator",
            tenant_mode="single",
            tenant_id="default",
        )
        # push created_time back
        Gateway.objects.filter(id=gateway.id).update(
            created_time=timezone.now() - timedelta(days=created_time_delta_days)
        )
        gateway.refresh_from_db()

        stage = G(Stage, gateway=gateway, status=stage_status, name=stage_name)
        rv = G(ResourceVersion, gateway=gateway, version="1.0.0", _data="[]")
        G(Release, gateway=gateway, stage=stage, resource_version=rv)
        return gateway

    return factory


class TestNotifyInactiveGatewayMaintainersTask:
    @patch("apigateway.apps.gateway.tasks.InactiveGatewayNotifier.notify")
    def test_feature_flag_disabled(self, mock_notify, settings):
        settings.ENABLE_GATEWAY_OPERATION_STATUS = False
        settings.ENABLE_MULTI_TENANT_MODE = False
        notify_inactive_gateway_maintainers()
        mock_notify.assert_not_called()

    @patch("apigateway.apps.gateway.tasks.InactiveGatewayNotifier.notify")
    def test_feature_flag_enabled(self, mock_notify, settings):
        settings.ENABLE_GATEWAY_OPERATION_STATUS = True
        settings.ENABLE_MULTI_TENANT_MODE = False
        notify_inactive_gateway_maintainers()
        mock_notify.assert_called_once()

    @patch("apigateway.apps.gateway.tasks.InactiveGatewayNotifier.notify")
    def test_multi_tenant_mode_enabled(self, mock_notify, settings):
        settings.ENABLE_GATEWAY_OPERATION_STATUS = True
        settings.ENABLE_MULTI_TENANT_MODE = True
        notify_inactive_gateway_maintainers()
        mock_notify.assert_not_called()


class TestInactiveGatewayNotifierGetInactiveGateways:
    def test_no_releases(self):
        notifier = InactiveGatewayNotifier()
        result = notifier._get_inactive_gateways()
        assert result == []

    def test_excludes_inactive_gateway(self, _make_released_gateway):
        _make_released_gateway(gateway_status=GatewayStatusEnum.INACTIVE.value)
        notifier = InactiveGatewayNotifier()
        result = notifier._get_inactive_gateways()
        assert len(result) == 0

    def test_excludes_inactive_stage(self, _make_released_gateway):
        _make_released_gateway(stage_status=StageStatusEnum.INACTIVE.value)
        notifier = InactiveGatewayNotifier()
        result = notifier._get_inactive_gateways()
        assert len(result) == 0

    def test_excludes_recently_created_gateway(self, _make_released_gateway):
        # created 179 days ago, within 180-day window -> excluded
        _make_released_gateway(created_time_delta_days=OPERATION_STATUS_DELTA_DAYS - 1)
        notifier = InactiveGatewayNotifier()
        result = notifier._get_inactive_gateways()
        assert len(result) == 0

    def test_includes_gateway_created_beyond_delta_days(self, _make_released_gateway):
        # created 181 days ago, outside 180-day window -> included
        gateway = _make_released_gateway(created_time_delta_days=OPERATION_STATUS_DELTA_DAYS + 1)
        notifier = InactiveGatewayNotifier()
        result = notifier._get_inactive_gateways()
        assert gateway.id in [gw.id for gw in result]

    def test_excludes_gateway_with_traffic(self, _make_released_gateway):
        gateway = _make_released_gateway()
        now = timezone.now()
        G(
            StatisticsGatewayRequestByDay,
            gateway_id=gateway.id,
            stage_name="prod",
            resource_id=0,
            total_count=100,
            start_time=now - timedelta(days=10),
            end_time=now - timedelta(days=9),
        )
        notifier = InactiveGatewayNotifier()
        result = notifier._get_inactive_gateways()
        assert gateway.id not in [gw.id for gw in result]

    def test_returns_inactive_gateway(self, _make_released_gateway):
        gateway = _make_released_gateway()
        notifier = InactiveGatewayNotifier()
        result = notifier._get_inactive_gateways()
        assert gateway.id in [gw.id for gw in result]


class TestInactiveGatewayNotifierGroupByUser:
    def test_single_maintainer(self, faker):
        gw1 = G(Gateway, name=faker.pystr(), _maintainers="user1", status=1, tenant_mode="single", tenant_id="default")
        gw2 = G(Gateway, name=faker.pystr(), _maintainers="user1", status=1, tenant_mode="single", tenant_id="default")

        result = InactiveGatewayNotifier._group_by_user([gw1, gw2])
        assert result["user1"] == {gw1.id, gw2.id}

    def test_multiple_maintainers(self, faker):
        gw = G(
            Gateway,
            name=faker.pystr(),
            _maintainers="user1;user2",
            status=1,
            tenant_mode="single",
            tenant_id="default",
        )

        result = InactiveGatewayNotifier._group_by_user([gw])
        assert gw.id in result["user1"]
        assert gw.id in result["user2"]


class TestInactiveGatewayNotifierDedupeByGatewaySet:
    def test_same_gateway_set_merged(self):
        user_to_gateways = {
            "user1": {1, 2},
            "user2": {1, 2},
            "user3": {3},
        }
        result = InactiveGatewayNotifier._dedupe_by_gateway_set(user_to_gateways)
        assert frozenset({1, 2}) in result
        assert sorted(result[frozenset({1, 2})]) == ["user1", "user2"]
        assert result[frozenset({3})] == ["user3"]


class TestInactiveGatewayNotifierSendMails:
    @patch("apigateway.apps.gateway.tasks.cmsi_component")
    def test_gray_user_list_filters(self, mock_cmsi, settings, faker):
        settings.INACTIVE_GATEWAY_NOTIFY_GRAY_USER_LIST = ["user1"]
        settings.DASHBOARD_FE_URL = "https://example.com"
        mock_cmsi.send_mail.return_value = (True, "")

        gw = G(
            Gateway,
            name=faker.pystr(),
            _maintainers="user1;user2",
            status=1,
            created_by="creator",
            tenant_mode="single",
            tenant_id="default",
        )

        mail_groups = {frozenset({gw.id}): ["user1", "user2"]}
        gateway_data_map = {
            gw.id: {
                "name": gw.name,
                "created_by": "creator",
                "stage_names": "prod",
                "resource_count": 5,
                "request_count": 0,
            }
        }

        notifier = InactiveGatewayNotifier()
        notifier._send_mails(mail_groups, gateway_data_map, [gw])

        mock_cmsi.send_mail.assert_called_once()
        call_args = mock_cmsi.send_mail.call_args
        assert call_args[0][1]["receiver__username"] == "user1"

    @patch("apigateway.apps.gateway.tasks.cmsi_component")
    def test_empty_gray_list_sends_to_all(self, mock_cmsi, settings, faker):
        settings.INACTIVE_GATEWAY_NOTIFY_GRAY_USER_LIST = []
        settings.DASHBOARD_FE_URL = "https://example.com"
        mock_cmsi.send_mail.return_value = (True, "")

        gw = G(
            Gateway,
            name=faker.pystr(),
            _maintainers="user1;user2",
            status=1,
            created_by="creator",
            tenant_mode="single",
            tenant_id="default",
        )

        mail_groups = {frozenset({gw.id}): ["user1", "user2"]}
        gateway_data_map = {
            gw.id: {
                "name": gw.name,
                "created_by": "creator",
                "stage_names": "prod",
                "resource_count": 5,
                "request_count": 0,
            }
        }

        notifier = InactiveGatewayNotifier()
        notifier._send_mails(mail_groups, gateway_data_map, [gw])

        mock_cmsi.send_mail.assert_called_once()
        call_args = mock_cmsi.send_mail.call_args
        assert call_args[0][1]["receiver__username"] == "user1;user2"

    @patch("apigateway.apps.gateway.tasks.cmsi_component")
    def test_gray_list_skips_all_users(self, mock_cmsi, settings, faker):
        settings.INACTIVE_GATEWAY_NOTIFY_GRAY_USER_LIST = ["allowed_user"]
        settings.DASHBOARD_FE_URL = "https://example.com"

        gw = G(
            Gateway,
            name=faker.pystr(),
            _maintainers="user1;user2",
            status=1,
            created_by="creator",
            tenant_mode="single",
            tenant_id="default",
        )

        mail_groups = {frozenset({gw.id}): ["user1", "user2"]}
        gateway_data_map = {
            gw.id: {
                "name": gw.name,
                "created_by": "creator",
                "stage_names": "prod",
                "resource_count": 5,
                "request_count": 0,
            }
        }

        notifier = InactiveGatewayNotifier()
        notifier._send_mails(mail_groups, gateway_data_map, [gw])

        mock_cmsi.send_mail.assert_not_called()

    @patch("apigateway.apps.gateway.tasks.logger")
    @patch("apigateway.apps.gateway.tasks.cmsi_component")
    def test_send_mail_failure_logs_error(self, mock_cmsi, mock_logger, settings, faker):
        settings.INACTIVE_GATEWAY_NOTIFY_GRAY_USER_LIST = []
        settings.DASHBOARD_FE_URL = "https://example.com"
        mock_cmsi.send_mail.return_value = (False, "send failed")

        gw = G(
            Gateway,
            name=faker.pystr(),
            _maintainers="user1",
            status=1,
            created_by="creator",
            tenant_mode="single",
            tenant_id="default",
        )

        mail_groups = {frozenset({gw.id}): ["user1"]}
        gateway_data_map = {
            gw.id: {
                "name": gw.name,
                "created_by": "creator",
                "stage_names": "prod",
                "resource_count": 5,
                "request_count": 0,
            }
        }

        notifier = InactiveGatewayNotifier()
        notifier._send_mails(mail_groups, gateway_data_map, [gw])

        mock_logger.error.assert_called_once_with(
            "send inactive gateway notification failed, users=%s, gateway_count=%d, error_msg=%s",
            ["user1"],
            1,
            "send failed",
        )


class TestInactiveGatewayNotifierNotify:
    @patch("apigateway.apps.gateway.tasks.cmsi_component")
    def test_end_to_end_no_inactive(self, mock_cmsi):
        notifier = InactiveGatewayNotifier()
        notifier.notify()
        mock_cmsi.send_mail.assert_not_called()

    @patch("apigateway.apps.gateway.tasks.cmsi_component")
    def test_end_to_end_with_inactive(self, mock_cmsi, settings, _make_released_gateway):
        settings.INACTIVE_GATEWAY_NOTIFY_GRAY_USER_LIST = []
        settings.DASHBOARD_FE_URL = "https://example.com"
        mock_cmsi.send_mail.return_value = (True, "")

        _make_released_gateway(maintainers="user_a;user_b")

        notifier = InactiveGatewayNotifier()
        notifier.notify()

        mock_cmsi.send_mail.assert_called_once()
        call_args = mock_cmsi.send_mail.call_args
        params = call_args[0][1]
        assert "user_a" in params["receiver__username"]
        assert "user_b" in params["receiver__username"]
        assert params["title"] == "【蓝鲸API网关】你维护的网关存在不活跃网关，请及时处理"
