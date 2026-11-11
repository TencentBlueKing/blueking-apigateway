import type { Component } from 'vue';
import ProxyCacheForm from '@/components/plugin/plugin-form/proxy-cache/Index.vue';
import BkUserRestriction from '@/components/plugin/plugin-form/bk-user-restriction/Index.vue';
import BkRequestBodyLimit from '@/components/plugin/plugin-form/bk-request-body-limit/Index.vue';
import BkAccessTokenSource from '@/components/plugin/plugin-form/bk-access-token-source/Index.vue';
import Redirect from '@/components/plugin/plugin-form/redirect/Index.vue';
import BkMock from '@/components/plugin/plugin-form/bk-mock/Index.vue';
import ResponseRewrite from '@/components/plugin/plugin-form/response-rewrite/Index.vue';
import FaultInjection from '@/components/plugin/plugin-form/fault-injection/Index.vue';
import RequestValidation from '@/components/plugin/plugin-form/request-validation/Index.vue';
import ApiBreaker from '@/components/plugin/plugin-form/api-breaker/Index.vue';
import BkTrafficLabel from '@/components/plugin/plugin-form/bk-traffic-label/Index.vue';
import UriBlocker from '@/components/plugin/plugin-form/uri-blocker/Index.vue';
import BkQueryStringRewrite from '@/components/plugin/plugin-form/bk-query-string-rewrite/Index.vue';
import BkCors from '@/components/plugin/plugin-form/bk-cors/Index.vue';
import BkIpRestriction from '@/components/plugin/plugin-form/bk-ip-restriction/Index.vue';
import BkHeaderRewrite from '@/components/plugin/plugin-form/bk-header-rewrite/Index.vue';
import BkRateLimit from '@/components/plugin/plugin-form/bk-rate-limit/Index.vue';
import BkResourceUserRateLimit from '@/components/plugin/plugin-form/bk-resource-user-rate-limit/Index.vue';
import WhitelistTable from './components/WhitelistTable.vue';
import { PLUGIN_FORM_EXAMPLE_CN, PLUGIN_FORM_EXAMPLE_EN } from '@/constants/plugin-form-examples';
import type { IPluginDefinition } from './types';

const custom = (component: Component, notice?: string): IPluginDefinition => ({
  editor: {
    kind: 'custom',
    component,
  },
  notice,
});

// 每个插件只注册一次，渲染和提交共用 editor.kind 决定接入方式。
// 新增插件时，无需在表单宿主中添加针对插件 code 的分支。
export const pluginDefinitions = {
  'proxy-cache': custom(ProxyCacheForm),
  'bk-user-restriction': custom(BkUserRestriction),
  'bk-request-body-limit': custom(BkRequestBodyLimit),
  'bk-access-token-source': custom(BkAccessTokenSource),
  'redirect': custom(Redirect),
  'bk-mock': custom(BkMock),
  'response-rewrite': custom(ResponseRewrite),
  'fault-injection': custom(FaultInjection),
  'request-validation': custom(RequestValidation),
  'api-breaker': custom(ApiBreaker),
  'bk-traffic-label': custom(BkTrafficLabel),
  'uri-blocker': custom(UriBlocker),
  'bk-query-string-rewrite': custom(BkQueryStringRewrite),
  'bk-cors': custom(BkCors, 'allow_origins 与 allow_origins_by_regex 不能同时为空'),
  'bk-ip-restriction': custom(BkIpRestriction),
  'bk-header-rewrite': custom(BkHeaderRewrite),
  'bk-rate-limit': custom(BkRateLimit),
  'bk-resource-user-rate-limit': custom(BkResourceUserRateLimit),
  'bk-verified-user-exempted-apps': {
    editor: {
      kind: 'whitelist',
      component: WhitelistTable,
    },
  },
  'bk-status-rewrite': { editor: { kind: 'none' } },
  'bk-username-required': { editor: { kind: 'none' } },
  'bk-legacy-invalid-params': { editor: { kind: 'none' } },
  'bk-oauth2-verify': { editor: { kind: 'none' } },
  'bk-oauth2-protected-resource': { editor: { kind: 'none' } },
  'bk-oauth2-audience-validate': { editor: { kind: 'none' } },
} satisfies Record<string, IPluginDefinition>;

export const getPluginDefinition = (code: string): IPluginDefinition | undefined =>
  Object.hasOwn(pluginDefinitions, code) ? (pluginDefinitions as Record<string, IPluginDefinition>)[code] : undefined;

export const getPluginExample = (code: string, locale: string): string => {
  const examples = locale === 'en' ? PLUGIN_FORM_EXAMPLE_EN : PLUGIN_FORM_EXAMPLE_CN;
  return examples[code] ?? '';
};
