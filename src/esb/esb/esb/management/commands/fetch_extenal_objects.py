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
from tempfile import TemporaryDirectory
from zipfile import ZipFile

import requests
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "-u",
            "--url",
            nargs="*",
            required=True,
            help="package url",
        )
        parser.add_argument(
            "-p",
            "--path",
            required=True,
            help="restore root dir",
        )
        parser.add_argument(
            "-t",
            "--timeout",
            default=10,
            help="download timeout",
        )
        parser.add_argument(
            "-c",
            "--chunk-size",
            default=4096,
            help="download chunk size",
        )
        parser.add_argument("-P", "--pwd", default=None, help="")

    def extract(self, filename, path, pwd, **kwargs):
        if pwd is not None:
            pwd = pwd.encode("utf-8")

        zip_file = ZipFile(filename)
        zip_file.extractall(path, pwd=pwd)

    def download(self, url, filename, timeout, chunk_size, **kwargs):
        with requests.get(url, timeout=timeout) as response:
            response.raise_for_status()

            with open(filename, "wb") as fp:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    fp.write(chunk)

    def restore(self, url, path, pwd, **kwargs):
        with TemporaryDirectory() as root_dir:
            filename = os.path.join(root_dir, "x")

            self.download(url, filename, **kwargs)
            self.extract(filename, path, pwd, **kwargs)

    def handle(self, url, path, pwd, *args, **kwargs):
        if not os.path.exists(path):
            os.makedirs(path)

        for i in url:
            self.restore(i, path, pwd, **kwargs)
