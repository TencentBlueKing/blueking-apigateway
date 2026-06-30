from bk_notice_sdk import config
from bk_notice_sdk.views import get_current_information as sdk_get_current_information


def get_current_information(request):
    if config.ENABLE_MULTI_TENANT_MODE and not hasattr(request.user, "tenant_id"):
        request.user.tenant_id = config.BK_APP_TENANT_ID

    return sdk_get_current_information(request)
