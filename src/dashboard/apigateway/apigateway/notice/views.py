from bk_notice_sdk import config
from bk_notice_sdk.utils import api_call, return_json_response


@return_json_response
def get_current_information(request):
    """获得当前平台的通知公告信息"""
    default_language = config.DEFAULT_LANGUAGE
    language = request.COOKIES.get(config.LANGUAGE_COOKIE_NAME, default_language)

    tenant_id = "default"
    if config.ENABLE_MULTI_TENANT_MODE:
        tenant_id = getattr(request.user, "tenant_id", "") or config.BK_APP_TENANT_ID

    res = api_call(
        api_method="announcement_get_current_announcements",
        tenant_id=tenant_id,
        success_message="平台获取通知公告信息成功",
        error_message="获取通知公告异常",
        params={"platform": config.PLATFORM, "language": language},
    )

    data_list = res.get("data")
    if data_list is None:
        return res

    for data in data_list:
        data.pop("content_list", [])

    res["data"] = data_list
    return res
