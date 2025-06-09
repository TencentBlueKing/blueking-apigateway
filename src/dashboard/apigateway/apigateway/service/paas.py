from django.conf import settings


def gen_programmable_gateway_links(app_code: str) -> dict:
    paas3_url = settings.BK_PAAS3_URL

    base_url = f"{paas3_url}/developer-center/apps/{app_code}"

    return {
        # 开发api
        "develop": [
            {"name": "查看密钥", "link": f"{base_url}/settings/application/info"},
            {"name": "环境变量", "link": f"{base_url}/default/settings/modules/env"},
            {"name": "增强服务", "link": f"{base_url}/default/settings/modules/services"},
            {"name": "云 API 权限申请", "link": f"{base_url}/cloudapi"},
        ],
        # 查询日志
        "logging": [
            {"name": "结构化日志", "link": f"{base_url}/default/logging"},
            {"name": "标准输出日志", "link": f"{base_url}/default/logging?tab=stream"},
            {"name": "访问日志", "link": f"{base_url}/default/logging?tab=access"},
        ],
        # 更多操作
        "more": [
            {"name": "部署管理", "link": f"{base_url}/deployments/prod"},
            {"name": "访问管理", "link": f"{base_url}/app_entry_config?tab=moduleAddress"},
        ],
    }
