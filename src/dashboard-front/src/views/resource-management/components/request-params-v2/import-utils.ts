/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) Tencent. All rights reserved.
 * Licensed under the MIT License (the "License"); you may not use this file except
 * in compliance with the License. You may obtain a copy of the License at
 * http://opensource.org/licenses/MIT
 */

import toJsonSchema from 'to-json-schema';
import { openApiSchemaToState, schemaToFieldRow } from './utils';
import {
  type IJsonSchemaObject,
  type IOpenApiOperationSchema,
  type IRequestBodyState,
  PARAMETER_LOCATIONS,
  type ParameterLocation,
} from './types';

type ImportErrorCode = 'operation' | 'parameters' | 'location' | 'schema' | 'scalar'
  | 'reference' | 'body' | 'metadata';

export class RequestParamsImportError extends Error {
  constructor(public code: ImportErrorCode, public path: string) {
    super(code);
  }
}

const isRecord = (value: unknown): value is Record<string, unknown> => {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
};

const fail = (code: ImportErrorCode, path: string): never => {
  throw new RequestParamsImportError(code, path);
};

const validateMetadata = (value: Record<string, unknown>, path: string) => {
  if (('description' in value && typeof value.description !== 'string')
    || ('required' in value && typeof value.required !== 'boolean')) {
    fail('metadata', path);
  }
};

/** 只接受表格能往返编辑的 Schema，避免宽松的详情转换静默丢弃导入结构。 */
const validateSchema = (value: unknown, path: string, scalar = false) => {
  if (!isRecord(value)) {
    return fail('schema', path);
  }
  if (['$ref', '$dynamicRef', 'allOf', 'anyOf', 'oneOf', 'not'].some(key => key in value)) {
    fail('reference', path);
  }
  const type = value.type ?? (isRecord(value.properties) ? 'object' : value.items ? 'array' : undefined);
  if (typeof type !== 'string' || !['string', 'number', 'integer', 'boolean', 'object', 'array'].includes(type)) {
    fail('schema', path);
  }
  if (scalar && (type === 'object' || type === 'array')) {
    fail('scalar', path);
  }
  if ('description' in value && typeof value.description !== 'string') {
    fail('schema', `${path}.description`);
  }
  if ('properties' in value && (type !== 'object' || !isRecord(value.properties))) {
    fail('schema', `${path}.properties`);
  }
  if ('items' in value && type !== 'array') {
    fail('schema', `${path}.items`);
  }
  if ('required' in value && (type !== 'object' || !Array.isArray(value.required)
    || value.required.some(name => typeof name !== 'string' || !isRecord(value.properties)
      || !Object.hasOwn(value.properties, name)))) {
    fail('schema', `${path}.required`);
  }
  if (type === 'object') {
    const names = new Set<string>();
    Object.entries(value.properties ?? {}).forEach(([name, schema]) => {
      if (!name.trim() || names.has(name.trim())) {
        fail('schema', `${path}.properties`);
      }
      names.add(name.trim());
      validateSchema(schema, `${path}.properties[${JSON.stringify(name)}]`);
    });
  }
  if (type === 'array') {
    validateSchema(value.items, `${path}.items`);
  }
  if ('additionalProperties' in value && typeof value.additionalProperties !== 'boolean') {
    validateSchema(value.additionalProperties, `${path}.additionalProperties`);
  }
};

/** 导入单个 Operation 的请求定义，不推测其他包装或普通业务 JSON。 */
export const openApiJsonToState = (input: unknown) => {
  if (!isRecord(input)
    || ['openapi', 'swagger', 'paths', 'openapi_schema', 'request_body'].some(key => key in input)
    || (!('parameters' in input) && !('requestBody' in input))) {
    return fail('operation', '$');
  }
  if ('parameters' in input && !Array.isArray(input.parameters)) {
    fail('parameters', '$.parameters');
  }
  const parameters = Array.isArray(input.parameters) ? input.parameters : [];
  const names = new Set<string>();
  parameters.forEach((parameter, index) => {
    const path = `$.parameters[${index}]`;
    if (!isRecord(parameter)) {
      return fail('parameters', path);
    }
    if ('$ref' in parameter) {
      fail('reference', path);
    }
    if (!PARAMETER_LOCATIONS.includes(parameter.in as ParameterLocation)) {
      fail('location', path);
    }
    if (typeof parameter.name !== 'string' || !parameter.name.trim()) {
      return fail('parameters', path);
    }
    const key = `${parameter.in}:${parameter.name.trim()}`;
    if (names.has(key)) {
      fail('parameters', path);
    }
    names.add(key);
    validateMetadata(parameter, path);
    validateSchema(parameter.schema, `${path}.schema`, true);
    if ('content' in parameter) {
      fail('schema', `${path}.content`);
    }
  });
  if ('requestBody' in input) {
    const body = input.requestBody;
    if (!isRecord(body)) {
      return fail('body', '$.requestBody');
    }
    if ('$ref' in body) {
      fail('reference', '$.requestBody');
    }
    validateMetadata(body, '$.requestBody');
    if (!isRecord(body.content) || Object.keys(body.content).length !== 1
      || !isRecord(body.content['application/json'])) {
      return fail('body', '$.requestBody.content');
    }
    validateSchema(body.content['application/json'].schema, '$.requestBody.content.application/json.schema');
  }
  return openApiSchemaToState(input as IOpenApiOperationSchema);
};

/** 普通 JSON 始终作为示例；无法推断的节点明确列出，供用户在表格中调整。 */
export const jsonExampleToBody = (input: unknown): {
  body: IRequestBodyState
  uncertainPaths: string[]
} => {
  const uncertainPaths: string[] = [];
  // 数组逐层合并全部样本的字段，避免推断库在对象形状不同时丢弃 properties。
  const infer = (samples: unknown[], path: string): IJsonSchemaObject => {
    const values = samples.filter(value => value !== null);
    const types = new Set(values.map(value => Array.isArray(value) ? 'array' : typeof value));
    const nullable = values.length < samples.length ? { nullable: true } : {};
    if (!values.length || types.size !== 1) {
      uncertainPaths.push(path);
      return { type: 'string',
        ...nullable };
    }
    if (types.has('object')) {
      const objects = values as Record<string, unknown>[];
      const names = new Set(objects.flatMap(value => Object.keys(value)));
      return {
        type: 'object',
        ...nullable,
        properties: Object.fromEntries([...names].map((name) => {
          const children = objects.filter(value => Object.hasOwn(value, name)).map(value => value[name]);
          return [name, infer(children, `${path}[${JSON.stringify(name)}]`)];
        })),
      };
    }
    if (types.has('array')) {
      return {
        type: 'array',
        ...nullable,
        items: infer(values.flat(), `${path}[]`),
      };
    }
    // 数字样本中存在小数时使用 number，否则保留 integer。
    const sample = types.has('number') ? values.find(value => !Number.isInteger(value)) ?? values[0] : values[0];
    return {
      ...toJsonSchema(sample, { required: false,
        strings: { detectFormat: false } }) as IJsonSchemaObject,
      ...nullable,
    };
  };
  const schema = infer([input], '$');
  validateSchema(schema, '$');
  return {
    body: {
      mediaType: 'application/json',
      required: false,
      root: schemaToFieldRow(schema),
    },
    uncertainPaths,
  };
};
