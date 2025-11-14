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

log_language_prompt_template = {
    "zh-cn": ERROR_LOG_ANALYSIS_ZH_TEMPLATE,
    "zh-hans": ERROR_LOG_ANALYSIS_ZH_TEMPLATE,
    "en": ERROR_LOG_ANALYSIS_EN_TEMPLATE,
    "zh": ERROR_LOG_ANALYSIS_ZH_TEMPLATE,
}

api_log_err_code_file_name = {
    "zh-cn": "api_response_err_code.md",
    "zh-hans": "api_response_err_code.md",
    "en": "api_response_err_code_en.md",
    "zh": "api_response_err_code.md",
}

# 文档翻译提示词模板
DOC_TRANSLATE_ZH_TEMPLATE = """
请将以下API接口文档翻译成{language}(en:英文，zh:中文)，保持markdown格式不变，只翻译文本内容(不要添加任何多余的注释或者说明)：

{doc_content}

翻译要求：
1. 智能识别输入文档的内容语言,如果已经是{language}，无需翻译，保持原样。
2. 如果输入是英文，翻译成中文；如果输入是中文，翻译成英文
3. 保持原有的markdown格式和结构
4. 专业术语翻译要准确
5. 代码示例和参数名保持不变
6. 确保翻译后的文档专业、清晰、易懂
"""

DOC_TRANSLATE_EN_TEMPLATE = """
Please translate the following API documentation to {language}(en:english, zh:chinese), maintaining the markdown format and only translating the text content(Do not add any extra comments or explanations):

{doc_content}

Translation requirements:
1. Intelligently identify the content language of the input document. If it is already in {language}, no translation is needed, keep it as is.
2. If the input is Chinese, translate to English; if the input is English, translate to Chinese
3. Maintain the original markdown format and structure
4. Technical terms should be translated accurately
5. Code examples and parameter names should remain unchanged
6. Ensure the translated documentation is professional, clear, and easy to understand
"""

doc_translate_language_prompt_template = {
    "zh-cn": DOC_TRANSLATE_ZH_TEMPLATE,
    "zh-hans": DOC_TRANSLATE_ZH_TEMPLATE,
    "en": DOC_TRANSLATE_EN_TEMPLATE,
}


class PromptBuilder:
    """AI 提示语句构造器"""

    def __init__(self, content_type: AIContentTypeEnum):
        self.content_type = content_type

    def build(self, log_content: str, language: str) -> str:
        return ai_content_prompt_builders[self.content_type](log_content, language)


def _build_log_analyze_prompt(log_content: str, language: str) -> str:
    """构建日志分析提示语句"""
    file_dir = settings.API_RESPONSE_ERR_CODE_DOC_DIR
    prompt_template = log_language_prompt_template[language]
    api_err_code_doc_name = api_log_err_code_file_name[language]
    log_file_path = os.path.join(file_dir, api_err_code_doc_name)
    return prompt_template.format(content=read_file_content(str(log_file_path)), log=log_content)


def _build_doc_translate_prompt(doc_content: str, language: str) -> str:
    """构建文档翻译提示语句"""
    prompt_template = doc_translate_language_prompt_template[translation.get_language()]
    return prompt_template.format(doc_content=doc_content, language=language)


ai_content_prompt_builders = {
    AIContentTypeEnum.LOG_ANALYSIS: _build_log_analyze_prompt,
    AIContentTypeEnum.DOC_TRANSLATE: _build_doc_translate_prompt,
}
