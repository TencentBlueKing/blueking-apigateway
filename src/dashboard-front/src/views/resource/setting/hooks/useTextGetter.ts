import { useI18n } from 'vue-i18n';

export default function useTextGetter() {
  const { t } = useI18n();
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
