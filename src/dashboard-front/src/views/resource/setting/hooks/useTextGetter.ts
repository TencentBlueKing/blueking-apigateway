import { useI18n } from 'vue-i18n';

/**
 * 自定义钩子函数，用于获取文本信息
 */
export default function useTextGetter() {
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
      } else {
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
    } catch {
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
      } else {
        auth = authConfig;
      }
      if (auth?.resource_perm_required) {
        return `${t('是')}`;
      }
      return `${t('否')}`;
    } catch {
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
    } else if (is_public === false) {
      result = t('否');
    } else {
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
    } else if (allow_apply_permission === false) {
      result = t('否');
    } else {
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
