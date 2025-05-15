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
import os

from django.conf import settings
from django.utils import translation

from apigateway.utils.file import read_file_content

from .constant import AIContentTypeEnum

# 定义模板
ERROR_LOG_ANALYSIS_ZH_TEMPLATE = """
根据以下错误码文档分析错误日志：
{content}
需要分析的错误日志：
{log}
请按以下格式分析：
1. 原因分析：（根据文档内容说明可能的原因）
2. 处理建议：（根据文档内容给出建议措施）
"""
ERROR_LOG_ANALYSIS_EN_TEMPLATE = """
Analyze the error log based on the following error code documentation:
{content}
Error log to be analyzed:
{log}
Please analyze in the following format:
1. Cause analysis: (Explain possible causes based on the document content)
2. Handling suggestions: (Provide recommended measures based on the document content)
"""

log_language_prompt_template = {"zh-cn": ERROR_LOG_ANALYSIS_ZH_TEMPLATE, "en": ERROR_LOG_ANALYSIS_EN_TEMPLATE}

api_log_err_code_file_name = {
    "zh-cn": "api_response_err_code.md",
    "en": "api_response_err_code_en.md",
}


class PromptBuilder:
    """AI 提示语句构造器"""

    def __init__(self, content_type: AIContentTypeEnum):
        self.content_type = content_type

    def build(self, log_content: str) -> str:
        return ai_content_prompt_builders[self.content_type](log_content)


def _build_log_analyze_prompt(log_content: str) -> str:
    """构建日志分析提示语句"""
    file_dir = settings.API_RESPONSE_ERR_CODE_DOC_DIR
    prompt_template = log_language_prompt_template[translation.get_language()]
    api_err_code_doc_name = api_log_err_code_file_name[translation.get_language()]
    log_file_path = os.path.join(file_dir, api_err_code_doc_name)
    return prompt_template.format(content=read_file_content(str(log_file_path)), log=log_content)


ai_content_prompt_builders = {
    AIContentTypeEnum.LOG_ANALYSIS.value: _build_log_analyze_prompt,
}
