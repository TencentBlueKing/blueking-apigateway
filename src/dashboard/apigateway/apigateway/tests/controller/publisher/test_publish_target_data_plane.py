from unittest.mock import Mock, patch

from apigateway.apps.data_plane.models import DataPlane
from apigateway.controller.publisher.publish import _trigger_rolling_update, trigger_gateway_publish
from apigateway.core.constants import PublishSourceEnum
from apigateway.core.models import Gateway, Release, ReleaseHistory, ResourceVersion, Stage


class TestTargetDataPlanePublish:
    @patch("apigateway.controller.publisher.publish._trigger_rolling_update")
    @patch("apigateway.controller.publisher.publish.Release.objects.filter")
    def test_trigger_gateway_publish_passes_target_data_plane_ids(self, mock_filter, mock_trigger):
        release = Mock(spec=Release)
        mock_filter.return_value.prefetch_related.return_value.all.return_value = [release]

        trigger_gateway_publish(
            PublishSourceEnum.GATEWAY_ENABLE,
            "tester",
            gateway_id=1,
            target_data_plane_ids=[11, 22],
        )

        mock_trigger.assert_called_once()
        kwargs = mock_trigger.call_args.kwargs
        assert kwargs["target_data_plane_ids"] == {11, 22}

    @patch("apigateway.controller.publisher.publish.GatewayDataPlaneBinding.objects.get_gateway_active_data_planes")
    @patch("apigateway.controller.publisher.publish.delay_on_commit")
    @patch("apigateway.controller.publisher.publish.PublishEventReporter")
    @patch("apigateway.controller.publisher.publish._pre_publish_check_is_gateway_ready_for_releasing")
    @patch("apigateway.controller.publisher.publish._pre_publish_save_release_history")
    def test_trigger_rolling_update_filters_target_data_plane_ids(
        self,
        mock_save_history,
        mock_check,
        mock_reporter,
        mock_delay_on_commit,
        mock_get_data_planes,
    ):
        gateway = Mock(spec=Gateway)
        gateway.pk = 1

        stage = Mock(spec=Stage)
        stage.pk = 1

        resource_version = Mock(spec=ResourceVersion)
        resource_version.pk = 1

        release = Mock(spec=Release)
        release.pk = 1
        release.gateway = gateway
        release.gateway_id = 1
        release.stage = stage
        release.resource_version = resource_version

        release_history = Mock(spec=ReleaseHistory)
        release_history.pk = 123
        mock_save_history.return_value = release_history
        mock_check.return_value = (True, "")

        data_plane_1 = Mock(spec=DataPlane)
        data_plane_1.id = 101
        data_plane_2 = Mock(spec=DataPlane)
        data_plane_2.id = 202
        mock_get_data_planes.return_value = [data_plane_1, data_plane_2]

        _trigger_rolling_update(
            PublishSourceEnum.GATEWAY_ENABLE,
            "tester",
            [release],
            is_sync=False,
            target_data_plane_ids={202},
        )

        mock_delay_on_commit.assert_called_once()
        assert mock_delay_on_commit.call_args.kwargs["data_plane_id"] == 202
