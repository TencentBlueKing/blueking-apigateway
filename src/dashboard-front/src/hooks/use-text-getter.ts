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

/**
 * 自定义钩子函数，用于获取文本信息
 */
export function useTextGetter() {
  const { t } = useI18n();

  /**
   * 获取认证配置的文本描述
   * @param {string | object | null | undefined} authConfig - 认证配置
   * @returns {string} - 认证配置的文本描述
   */
  const getAuthConfigText = (authConfig: string | object | null | undefined) => {
    if (!authConfig) return '--';
    let auth;

    try {
      if (typeof authConfig === 'string') {
        auth = JSON.parse(authConfig);
      }
      else {
        auth = authConfig;
      }
      const tmpArr: string[] = [];

      if (auth?.app_verified_required) {
        tmpArr.push(`${t('蓝鲸应用认证')}`);
      }
      if (auth?.auth_verified_required) {
        tmpArr.push(`${t('用户认证')}`);
      }
      return tmpArr.join(', ') || '--';
    }
    catch {
      return '--';
    }
  };

  /**
   * 获取权限要求的文本描述
   * @param {string | object | null | undefined} authConfig - 认证配置
   * @returns {string} - 权限要求的文本描述
   */
  const getPermRequiredText = (authConfig: string | object | null | undefined) => {
    if (!authConfig) return '--';
    let auth;

    try {
      if (typeof authConfig === 'string') {
        auth = JSON.parse(authConfig);
      }
      else {
        auth = authConfig;
      }
      if (auth?.resource_perm_required) {
        return `${t('是')}`;
      }
      return `${t('否')}`;
    }
    catch {
      return '--';
    }
  };

  /**
   * 获取公开设置的文本描述
   * @param {boolean | null | undefined} is_public - 是否公开
   * @returns {string} - 公开设置的文本描述
   */
  const getPublicSettingText = (is_public: boolean | null | undefined) => {
    let result;

    if (is_public) {
      result = t('是');
    }
    else if (is_public === false) {
      result = t('否');
    }
    else {
      result = t('是');
    }

    return result;
  };

  /**
   * 获取是否允许申请权限的文本描述
   * @param {boolean | null | undefined} allow_apply_permission - 是否允许申请权限
   * @returns {string} - 是否允许申请权限的文本描述
   */
  const getAllowApplyPermissionText = (allow_apply_permission: boolean | null | undefined) => {
    let result;

    if (allow_apply_permission) {
      result = t('是');
    }
    else if (allow_apply_permission === false) {
      result = t('否');
    }
    else {
      result = t('是');
    }

    return result;
  };

  return {
    getAuthConfigText,
    getPermRequiredText,
    getPublicSettingText,
    getAllowApplyPermissionText,
  };
};
