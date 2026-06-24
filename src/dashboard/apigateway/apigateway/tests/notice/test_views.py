from django.contrib.auth.models import AnonymousUser


class TestGetCurrentInformation:
    def test_uses_app_tenant_for_anonymous_user_in_multi_tenant_mode(self, mocker, request_view):
        api_call = mocker.patch(
            "bk_notice_sdk.views.api_call",
            return_value={
                "result": True,
                "code": 200,
                "message": "ok",
                "data": [{"id": 1, "content_list": [{"content": "detail"}], "title": "announcement"}],
            },
        )
        mocker.patch("apigateway.notice.views.config.ENABLE_MULTI_TENANT_MODE", True)
        mocker.patch("apigateway.notice.views.config.BK_APP_TENANT_ID", "system")
        mocker.patch("apigateway.notice.views.config.PLATFORM", "apigateway")
        mocker.patch("apigateway.notice.views.config.DEFAULT_LANGUAGE", "en")
        mocker.patch("apigateway.notice.views.config.LANGUAGE_COOKIE_NAME", "blueking_language")

        user = AnonymousUser()
        response = request_view(
            method="GET",
            view_name="notice:get_current_information",
            user=user,
        )

        assert response.status_code == 200
        assert user.tenant_id == "system"
        assert response.json()["data"] == [{"id": 1, "title": "announcement"}]
        api_call.assert_called_once_with(
            api_method="announcement_get_current_announcements",
            tenant_id="system",
            success_message="平台获取通知公告信息成功",
            error_message="获取通知公告异常",
            params={"platform": "apigateway", "language": "en"},
        )

    def test_uses_user_tenant_for_authenticated_user(self, mocker, request_view):
        api_call = mocker.patch(
            "bk_notice_sdk.views.api_call",
            return_value={"result": True, "code": 200, "message": "ok", "data": []},
        )
        mocker.patch("apigateway.notice.views.config.ENABLE_MULTI_TENANT_MODE", True)
        mocker.patch("apigateway.notice.views.config.PLATFORM", "apigateway")
        mocker.patch("apigateway.notice.views.config.DEFAULT_LANGUAGE", "en")
        mocker.patch("apigateway.notice.views.config.LANGUAGE_COOKIE_NAME", "blueking_language")

        user = mocker.MagicMock(is_authenticated=True, tenant_id="tenant-a")

        response = request_view(
            method="GET",
            view_name="notice:get_current_information",
            user=user,
        )

        assert response.status_code == 200
        api_call.assert_called_once_with(
            api_method="announcement_get_current_announcements",
            tenant_id="tenant-a",
            success_message="平台获取通知公告信息成功",
            error_message="获取通知公告异常",
            params={"platform": "apigateway", "language": "en"},
        )
