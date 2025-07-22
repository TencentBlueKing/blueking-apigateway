import i18n from '@/locales';
const { t } = i18n.global;

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

export {
  TENANT_MODE_TEXT_MAP,
  APPROVAL_STATUS_MAP,
  APPROVAL_HISTORY_STATUS_MAP,
};
