/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) Tencent. All rights reserved.
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
import type {
  IDocsGatewaysResourcesDocReadResponse,
  IDocsOpenAPISchema,
  IDocsResourceDocPlugin,
  IDocsSchemaObject,
} from '@/services/types/responses/docs.ts';

export const PLUGIN_ACCESS_TOKEN_SOURCE = 'bk-access-token-source';
export const PLUGIN_USERNAME_REQUIRED = 'bk-username-required';

export const HEADER_AUTHORIZATION = 'Authorization';
export const HEADER_API_KEY = 'X-API-KEY';
export const HEADER_BKAPI_AUTHORIZATION = 'X-Bkapi-Authorization';
export const HEADER_BK_USERNAME = 'X-Bk-Username';
export const HEADER_BK_TENANT_ID = 'X-Bk-Tenant-Id';

const STRIP_ALWAYS_HEADINGS = [
  'api地址',
  'api 地址',
  'api path',
  '公共请求参数',
  'public request parameters',
];

const STRIP_PARAM_HEADINGS = [
  '输入参数',
  '请求参数',
  'request parameters',
  'input parameters',
  '响应参数',
  '响应参数说明',
  'response parameters',
  'response parameter description',
];

type StructuredDoc = Pick<IDocsGatewaysResourcesDocReadResponse,
  'plugins' | 'openapi_schema' | 'source' | 'render_mode'>;

export function isStructuredDoc(doc?: StructuredDoc | null): boolean {
  if (!doc) {
    return false;
  }
  return doc.plugins !== undefined
    || doc.openapi_schema !== undefined
    || doc.source !== undefined
    || doc.render_mode !== undefined;
}

export function getPlugin(
  plugins: IDocsResourceDocPlugin[] | undefined,
  type: string,
): IDocsResourceDocPlugin | undefined {
  return plugins?.find(plugin => plugin.type === type);
}

export function getAccessTokenSource(plugins?: IDocsResourceDocPlugin[]): 'bearer' | 'api_key' | null {
  const plugin = getPlugin(plugins, PLUGIN_ACCESS_TOKEN_SOURCE);
  if (!plugin) {
    return null;
  }
  return plugin.config?.source === 'api_key' ? 'api_key' : 'bearer';
}

export function isUsernameHeaderRequired(plugins?: IDocsResourceDocPlugin[]): boolean {
  return Boolean(getPlugin(plugins, PLUGIN_USERNAME_REQUIRED));
}

export function needsAuthSection({
  plugins,
  verifiedAppRequired = false,
  verifiedUserRequired = false,
  isTenantMode = false,
}: {
  plugins?: IDocsResourceDocPlugin[]
  verifiedAppRequired?: boolean
  verifiedUserRequired?: boolean
  isTenantMode?: boolean
}): boolean {
  return verifiedAppRequired
    || verifiedUserRequired
    || isTenantMode
    || isUsernameHeaderRequired(plugins)
    || Boolean(getAccessTokenSource(plugins));
}

export function hasSchemaParams(schema?: IDocsOpenAPISchema): boolean {
  if (!schema || schema.none_schema) {
    return false;
  }
  const hasParameters = Boolean(schema.parameters?.length);
  const hasBody = Boolean(getContentSchema(schema.requestBody?.content));
  const hasResponses = Object.values(schema.responses || {}).some((response) => {
    return Boolean(response.description || getContentSchema(response.content));
  });
  return hasParameters || hasBody || hasResponses;
}

export function getContentSchema(
  content?: Record<string, { schema?: IDocsSchemaObject }>,
): IDocsSchemaObject | undefined {
  const jsonSchema = content?.['application/json']?.schema;
  if (jsonSchema) {
    return jsonSchema;
  }
  return Object.values(content || {}).find(item => item.schema)?.schema;
}

export function shouldRenderSchemaParams(doc: StructuredDoc): boolean {
  const mode = doc.render_mode || 'auto';
  if (mode === 'markdown_first') {
    return false;
  }
  return hasSchemaParams(doc.openapi_schema);
}

export function extractPathParams(path = ''): string[] {
  return Array.from(path.matchAll(/\{([^{}]+)\}/g)).map(match => match[1]);
}

export function buildCurlCommand(options: {
  method?: string
  resourceUrl: string
  plugins?: IDocsResourceDocPlugin[]
  verifiedAppRequired?: boolean
  verifiedUserRequired?: boolean
  isTenantMode?: boolean
  loginTicketKey?: string
}): string {
  const method = (options.method || 'GET').toUpperCase();
  const methodFlag = method === 'GET' ? '' : `-X ${method} `;
  const headers: string[] = [];
  const source = getAccessTokenSource(options.plugins);

  if (source === 'bearer') {
    headers.push(`-H '${HEADER_AUTHORIZATION}: Bearer {access_token}'`);
  }
  else if (source === 'api_key') {
    headers.push(`-H '${HEADER_API_KEY}: {access_token}'`);
  }
  else if (options.verifiedAppRequired || options.verifiedUserRequired) {
    const payload: Record<string, string> = {};
    if (options.verifiedAppRequired) {
      payload.bk_app_code = 'x';
      payload.bk_app_secret = 'y';
    }
    if (options.verifiedUserRequired) {
      payload[options.loginTicketKey || 'bk_token'] = 'z';
    }
    headers.push(`-H '${HEADER_BKAPI_AUTHORIZATION}: ${JSON.stringify(payload)}'`);
  }
  if (isUsernameHeaderRequired(options.plugins)) {
    headers.push(`-H '${HEADER_BK_USERNAME}: {username}'`);
  }
  if (options.isTenantMode) {
    headers.push(`-H '${HEADER_BK_TENANT_ID}: {tenant_id}'`);
  }

  return `curl ${methodFlag}${headers.join(' ')} "${options.resourceUrl}"`.replace(/\s+/g, ' ').trim();
}

export function buildResourceUrl(
  template: string,
  gatewayName: string,
  stageName: string,
  resourcePath: string,
): string {
  const path = resourcePath.startsWith('/') ? resourcePath.slice(1) : resourcePath;
  return template
    .replace('{api_name}', gatewayName)
    .replace('{stage_name}', stageName)
    .replace('{resource_path}', path);
}

function normalizeHeading(heading: string): string {
  return heading.replace(/[#\s]/g, '').toLowerCase();
}

function shouldStripHeading(heading: string, stripParams: boolean): boolean {
  const normalized = normalizeHeading(heading);
  if (STRIP_ALWAYS_HEADINGS.some(item => normalizeHeading(item) === normalized)) {
    return true;
  }
  if (!stripParams) {
    return false;
  }
  return STRIP_PARAM_HEADINGS.some(item => normalizeHeading(item) === normalized);
}

export function stripOverlappingMarkdown(content: string, stripParams: boolean): string {
  if (!content?.trim()) {
    return '';
  }
  const lines = content.replace(/\r\n/g, '\n').split('\n');
  const kept: string[] = [];
  let skippedHeadingLevel: number | null = null;

  for (const line of lines) {
    const headingMatch = /^(#{1,6})\s+(.+?)\s*$/.exec(line);
    if (headingMatch) {
      const headingLevel = headingMatch[1].length;
      if (skippedHeadingLevel !== null && headingLevel > skippedHeadingLevel) {
        continue;
      }
      skippedHeadingLevel = shouldStripHeading(headingMatch[2], stripParams) ? headingLevel : null;
      if (skippedHeadingLevel !== null) {
        continue;
      }
    }
    if (skippedHeadingLevel === null) {
      kept.push(line);
    }
  }

  return kept.join('\n').replace(/\n{3,}/g, '\n\n').trim();
}

function hasHeaderParam(schema: IDocsOpenAPISchema, name: string): boolean {
  return Boolean(schema.parameters?.some(item => item.in === 'header' && item.name.toLowerCase() === name.toLowerCase()));
}

function hasPathParam(schema: IDocsOpenAPISchema, name: string): boolean {
  return Boolean(schema.parameters?.some(item => item.in === 'path' && item.name === name));
}

export function mergeGatewayConfigIntoSchema(
  schema: IDocsOpenAPISchema | undefined,
  options: {
    path?: string
    plugins?: IDocsResourceDocPlugin[]
  },
): IDocsOpenAPISchema {
  const merged: IDocsOpenAPISchema = {
    ...(schema || {}),
    parameters: [...(schema?.parameters || [])],
    requestBody: schema?.requestBody ? { ...schema.requestBody } : undefined,
    responses: schema?.responses ? { ...schema.responses } : undefined,
  };

  const prependHeader = (name: string, description: string) => {
    if (hasHeaderParam(merged, name)) {
      return;
    }
    merged.parameters = [
      {
        name,
        in: 'header',
        required: true,
        description,
        schema: { type: 'string' },
      },
      ...(merged.parameters || []),
    ];
  };

  const source = getAccessTokenSource(options.plugins);
  if (source === 'bearer') {
    prependHeader(HEADER_AUTHORIZATION, 'Bearer {access_token}');
  }
  else if (source === 'api_key') {
    prependHeader(HEADER_API_KEY, '{access_token}');
  }
  if (isUsernameHeaderRequired(options.plugins)) {
    prependHeader(HEADER_BK_USERNAME, t('调用方用户名'));
  }

  extractPathParams(options.path).forEach((name) => {
    if (hasPathParam(merged, name)) {
      return;
    }
    merged.parameters = [
      ...(merged.parameters || []),
      {
        name,
        in: 'path',
        required: true,
        description: name,
        schema: { type: 'string' },
      },
    ];
  });

  return merged;
}
