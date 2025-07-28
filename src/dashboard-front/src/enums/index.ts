/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2025 Tencent. All rights reserved.
 * Licensed under the MIT License (the "License"); you may not use this file except
 * in compliance with the License. You may obtain a copy of the License at
 *
 *     http://opensource.org/licenses/MIT
 *
 * Unless required by applicable law or agreed to in writing, software distributed under
 * the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
 * either express or implied. See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * We undertake not to change the open source license (MIT license) applicable
 * to the current version of the project delivered to anyone in the future.
 */

import { t } from '@/locales';

const TENANT_MODE_TEXT_MAP: Record<string, string> = {
  global: t('全租户'),
  single: t('单租户'),
};

const APPROVAL_STATUS_MAP: Record<string, string> = {
  approved: t('通过'),
  rejected: t('驳回'),
  pending: t('未审批'),
};

const APPROVAL_HISTORY_STATUS_MAP: Record<string, string> = {
  approved: t('全部通过'),
  partial_approved: t('部分通过'),
  rejected: t('全部驳回'),
  pending: t('未审批'),
};

const METHOD_THEMES = {
  POST: 'info',
  GET: 'success',
  DELETE: 'danger',
  PUT: 'warning',
  PATCH: 'info',
  ANY: 'success',
};

const RELEASE_ACTION_TEXT = {
  gateway_enable: t('网关启用'),
  gateway_disable: t('网关停用'),
  version_publish: t('版本发布'),
  plugin_bind: t('插件绑定'),
  plugin_update: t('插件更新'),
  plugin_unbind: t('插件解绑'),
  stage_disable: t('环境下架'),
  stage_delete: t('环境删除'),
  stage_update: t('环境更新'),
  backend_update: t('服务更新'),
};

const RELEASE_STATUS_TEXT = {
  success: t('执行成功'),
  failure: t('执行失败'),
  doing: t('执行中'),
};

const OPERATE_STATUS_MAP: Record<string, string> = {
  success: t('成功'),
  failure: t('失败'),
  pending: t('待同步'),
  releasing: t('同步中'),
};

const PERMISSION_LEVEL_MAP: Record<string, string> = ({
  unlimited: t('无限制'),
  normal: t('普通'),
});

export {
  TENANT_MODE_TEXT_MAP,
  APPROVAL_STATUS_MAP,
  APPROVAL_HISTORY_STATUS_MAP,
  METHOD_THEMES,
  RELEASE_ACTION_TEXT,
  RELEASE_STATUS_TEXT,
  OPERATE_STATUS_MAP,
  PERMISSION_LEVEL_MAP,
};
