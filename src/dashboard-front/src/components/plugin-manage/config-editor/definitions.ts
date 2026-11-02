import type { Component } from 'vue';
import ProxyCacheForm from '@/components/plugin-form/proxy-cache/Index.vue';
import BkUserRestriction from '@/components/plugin-form/bk-user-restriction/Index.vue';
import BkRequestBodyLimit from '@/components/plugin-form/bk-request-body-limit/Index.vue';
import BkAccessTokenSource from '@/components/plugin-form/bk-access-token-source/Index.vue';
import Redirect from '@/components/plugin-form/redirect/Index.vue';
import BkMock from '@/components/plugin-form/bk-mock/Index.vue';
import ResponseRewrite from '@/components/plugin-form/response-rewrite/Index.vue';
import FaultInjection from '@/components/plugin-form/fault-injection/Index.vue';
import RequestValidation from '@/components/plugin-form/request-validation/Index.vue';
import ApiBreaker from '@/components/plugin-form/api-breaker/Index.vue';
import BkTrafficLabel from '@/components/plugin-form/bk-traffic-label/Index.vue';
import UriBlocker from '@/components/plugin-form/uri-blocker/Index.vue';
import BkQueryStringRewrite from '@/components/plugin-form/bk-query-string-rewrite/Index.vue';
import BkCors from '@/components/plugin-form/bk-cors/Index.vue';
import BkIpRestriction from '@/components/plugin-form/bk-ip-restriction/Index.vue';
import BkHeaderRewrite from '@/components/plugin-form/bk-header-rewrite/Index.vue';
import BkRateLimit from '@/components/plugin-form/bk-rate-limit/Index.vue';
import BkResourceUserRateLimit from '@/components/plugin-form/bk-resource-user-rate-limit/Index.vue';
import WhitelistTable from './components/WhitelistTable.vue';
import schemaCn from '@/json/schemaPluginFormCn.json';
import schemaEn from '@/json/schemaPluginFormEn.json';
import { PLUGIN_FORM_EXAMPLE_CN, PLUGIN_FORM_EXAMPLE_EN } from '@/constants/plugin-form-examples';
import type { IPluginDefinition, IPluginFormConfig } from './types';

const custom = (component: Component): IPluginDefinition => ({
  editor: {
    kind: 'custom',
    component,
  },
});

const schema = (
  component: Component,
  cn: IPluginFormConfig,
  en: IPluginFormConfig,
  notice?: string,
): IPluginDefinition => ({
  editor: {
    kind: 'schema',
    component,
    getFormConfig: locale => locale === 'en' ? en : cn,
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
  'bk-cors': schema(
    BkCors,
    schemaCn['bk-cors'].config,
    schemaEn['bk-cors'].config,
    'allow_origins 与 allow_origins_by_regex 不能同时为空',
  ),
  'bk-ip-restriction': schema(BkIpRestriction, schemaCn['bk-ip-restriction'].config, schemaEn['bk-ip-restriction'].config),
  'bk-header-rewrite': schema(BkHeaderRewrite, schemaCn['bk-header-rewrite'].config, schemaEn['bk-header-rewrite'].config),
  'bk-rate-limit': schema(BkRateLimit, schemaCn['bk-rate-limit'].config, schemaEn['bk-rate-limit'].config),
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
