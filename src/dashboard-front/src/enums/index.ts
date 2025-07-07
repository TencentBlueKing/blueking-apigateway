import i18n from '@/language/i18n';

const { t } = i18n.global;

const TENANT_MODE_TEXT_MAP: Record<string, string> = {
  global: t('全租户'),
  single: t('单租户'),
};

export {
  TENANT_MODE_TEXT_MAP,
};
