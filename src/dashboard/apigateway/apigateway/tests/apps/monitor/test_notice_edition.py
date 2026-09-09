"""EE alerts must not include TE-only IM delivery."""

import pytest

from apigateway.apps.monitor import tasks
from apigateway.apps.monitor.constants import NoticeWayEnum


@pytest.mark.parametrize("edition", ["ee", "te"])
@pytest.mark.parametrize(
    "task, alerter",
    [
        ("monitor_resource_backend", "ResourceBackendAlerter"),
        ("monitor_app_request", "AppRequestAlerter"),
        ("monitor_nginx_error", "NginxErrorAlerter"),
    ],
)
def test_supported_notification_channels(settings, mocker, edition, task, alerter):
    settings.EDITION = edition
    mocker.patch.object(tasks, "MonitorEvent")
    mocker.patch.object(tasks, "AlertFlow")
    mocker.patch.object(tasks, "get_es_index", return_value="test")
    send = mocker.patch.object(tasks, alerter)
    getattr(tasks, task)({})
    expected = [NoticeWayEnum.WECHAT.value]
    if edition == "te":
        expected.insert(0, NoticeWayEnum.IM.value)
    send.assert_called_once_with(notice_ways=expected)
