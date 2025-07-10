import i18n from '@/locales';

const { t } = i18n.global;

const TENANT_MODE_TEXT_MAP: Record<string, string> = {
  global: t('全租户'),
  single: t('单租户'),
};

export { TENANT_MODE_TEXT_MAP };
