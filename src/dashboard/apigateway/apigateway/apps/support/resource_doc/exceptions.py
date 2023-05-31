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
from django.utils.translation import gettext as _
from jinja2.exceptions import TemplateSyntaxError


class NoResourceDocError(Exception):
    """没有资源文档"""


class ResourceDocJinja2TemplateError(Exception):
    """资源文档模板错误"""

    _error_message = _("Jinja2 模板错误")

    def __init__(self, filename: str, raw_err: Exception):
        self.filename = filename
        self.raw_err = raw_err

    def __str__(self) -> str:
        return f'{self._error_message}, File: "{self.filename}", Error: {self.raw_err}'


class ResourceDocJinja2TemplateNotFound(ResourceDocJinja2TemplateError):
    _error_message = _("Jinja2 模板不存在")


class ResourceDocJinja2TemplateSyntaxError(ResourceDocJinja2TemplateError):
    """资源文档模板语法错误"""

    _error_message = _("Jinja2 模板语法错误")

    def __init__(self, base_path: str, filename: str, raw_err: TemplateSyntaxError):
        self.base_path = base_path
        self.filename = filename
        self.raw_err: TemplateSyntaxError = raw_err

    def __str__(self) -> str:
        if not self.raw_err.filename:
            # 实际出错的可能是模板中 include 的其它模板，因此不能使用 err.lineno 获取行号
            return super().__str__()

        return '{message}, File: "{filename}", error file: {err_file}, line: {lineno}, Error: {err}'.format(
            message=self._error_message,
            filename=self.filename,
            err_file=self._get_err_filename(),
            lineno=self.raw_err.lineno,
            err=self.raw_err,
        )

    def _get_err_filename(self) -> str:
        err_filename = self.raw_err.filename
        if err_filename.startswith(self.base_path):
            err_filename = err_filename[len(self.base_path) :].lstrip("/")
        return err_filename
