# -*- coding: utf-8 -*-
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
from builtins import str
from importlib import import_module

from django.http import HttpResponse

from common.base_utils import html_escape, smart_upper_v2
from components.esb_conf import CUSTOM_APIS_REL_PATH, _rel_path
from esb.component.base import ComponentsManager
from esb.utils import fpath_to_module


def check_custom_codename(request):
    """check custom component codename"""
    component_codename = html_escape(request.GET.get("codename") or "")
    component_manager = ComponentsManager()

    file_import_error = {}
    # custom component config
    comp_config = {
        "path": _rel_path(CUSTOM_APIS_REL_PATH),
        "name_prefix": "generic.",
    }

    # register path
    for current_folder, folders, files in os.walk(comp_config["path"]):
        for filename in files:
            if filename.endswith(".py") and component_manager.should_register(current_folder, filename):
                fpath = os.path.join(current_folder, filename)
                try:
                    module = import_module(fpath_to_module(fpath))
                    component_manager.register_by_module(module, config=comp_config)
                except Exception as ex:
                    file_import_error[fpath] = "Exception: %s" % str(ex)

    error_msg = []
    # check component whether exist
    if component_codename:
        try:
            prefix, sys_name, component_name = component_codename.split(".")
        except Exception:
            return HttpResponse("codename does not math the rule generic.xxx.xxx, please check")
        if component_codename in component_manager.get_registed_components():
            return HttpResponse(
                "component exists, if the visit prompts the error "
                'message "Not found, component class not found", please restart the esb service'
            )
        else:
            error_msg.append("component does not exist, please check the following steps:")
            error_msg.append(
                '1. component path is "%s", please check whether the component file exists' % comp_config["path"]
            )
            error_msg.append('2. component class name should be "%s", please check' % smart_upper_v2(component_name))
            error_msg.append(
                '3. uppercase of compoennt attribute sys_name should be "%s", please check' % sys_name.upper()
            )

    if file_import_error:
        error_msg.append("\n")
        error_msg.append("There are some components loaded exception, please repair:")
        error_msg.extend(
            ["\n".join(item) for item in sorted(iter(list(file_import_error.items())), key=lambda x: x[0])]
        )
    return HttpResponse(content="\n".join(error_msg) or "OK", content_type="text/plain")
