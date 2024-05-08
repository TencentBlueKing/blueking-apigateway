# -*- coding: utf-8 -*-
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


class DBRouter:
    """
    A router to control all database operations on models in the auth application.
    """

    APP_LABEL_TO_DB = {
        "bkcore": "bkcore",
        "apigateway": "legacy",
    }

    def db_for_read(self, model, **hints):
        """
        Attempts to read auth models go to auth_db.
        """
        return self.APP_LABEL_TO_DB.get(model._meta.app_label, "default")

    def db_for_write(self, model, **hints):
        """
        Attempts to write auth models go to auth_db.
        """
        return self.APP_LABEL_TO_DB.get(model._meta.app_label, "default")

    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations if a model in the auth app is involved.
        """
        return self.APP_LABEL_TO_DB.get(obj1._meta.app_label) == self.APP_LABEL_TO_DB.get(obj2._meta.app_label)

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Make sure the auth app only appears in the 'auth_db'
        database.
        """
        return self.APP_LABEL_TO_DB.get(app_label, "default") == db
