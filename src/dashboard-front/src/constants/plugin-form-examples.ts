// 插件表单填写示例
import { t } from '@/locales';

export const PLUGIN_FORM_EXAMPLE_MAP: { [pluginCode: string]: string } = {
  'proxy-cache': t('插件示例.proxy-cache'),
  'bk-user-restriction': t('插件示例.bk-user-restriction'),
  'bk-request-body-limit': t('插件示例.bk-request-body-limit'),
  'bk-access-token-source': t('插件示例.bk-access-token-source'),
  'ai-proxy': t('插件示例.ai-proxy'),
  'ai-rate-limiting': t('插件示例.ai-rate-limiting'),
  'redirect': t('插件示例.redirect'),
  'bk-mock': t('插件示例.bk-mock'),
  'response-rewrite': t('插件示例.response-rewrite'),
  'fault-injection': t('插件示例.fault-injection'),
  'request-validation': t('插件示例.request-validation'),
  'api-breaker': t('插件示例.api-breaker'),
  'bk-cors': t('插件示例.bk-cors'),
  'bk-ip-restriction': t('插件示例.bk-ip-restriction'),
  'bk-header-rewrite': t('插件示例.bk-header-rewrite'),
  'bk-rate-limit': t('插件示例.bk-rate-limit'),
  'bk-status-rewrite': '',
  'bk-legacy-invalid-params': '',
  'bk-username-required': '',
};

export default PLUGIN_FORM_EXAMPLE_MAP;
