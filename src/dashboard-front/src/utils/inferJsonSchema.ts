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

/**
 * 根据 JSON 示例推断 JSON Schema，用于替换已停更的 to-json-schema。
 * 类型推断与数组元素合并规则与 to-json-schema 的默认行为保持一致，差异：
 * - 字符串格式只识别参数编辑器支持的格式，ip-address 统一为 ipv4
 * - 数组元素的 Schema 无法合并时不再抛异常，而是退化为只声明元素类型
 * - 合并对象时忽略属性的键顺序，键相同、顺序不同的对象不再退化为 { type: 'object' }
 * - email、uri 正则恢复 jsonschema 原版中 `-` 的转义，to-json-schema 丢失转义后字符类会包含 `.`，
 *   导致邮箱正则在长串点号分段的字符串上指数级回溯
 */
import { isEqual, keys, xor } from 'lodash-es';

export type IInferredSchema = Record<string, any>;

export interface IInferJsonSchemaOptions {
  // 是否根据字符串内容识别 format，默认开启
  detectFormat?: boolean
}

type ValueType = 'integer' | 'number' | 'string' | 'array' | 'object' | 'boolean' | 'null';

// 正则取自 jsonschema（MIT）；按顺序匹配，命中第一个即返回
// 注意字符类中的 `-` 必须转义或放在末尾，否则会构成区间（如 `+-/` 包含 `.`），邮箱正则会出现嵌套量词回溯
const STRING_FORMATS: [string, RegExp][] = [
  ['date-time', /^\d{4}-(?:0[0-9]{1}|1[0-2]{1})-(3[01]|0[1-9]|[12][0-9])[tT ](2[0-4]|[01][0-9]):([0-5][0-9]):(60|[0-5][0-9])(\.\d+)?([zZ]|[+-]([0-5][0-9]):(60|[0-5][0-9]))$/],
  ['date', /^\d{4}-(?:0[0-9]{1}|1[0-2]{1})-(3[01]|0[1-9]|[12][0-9])$/],
  ['time', /^(2[0-4]|[01][0-9]):([0-5][0-9]):(60|[0-5][0-9])$/],
  ['email', /^(?:[\w!#$%&'*+\-/=?^`{|}~]+\.)*[\w!#$%&'*+\-/=?^`{|}~]+@(?:(?:(?:[a-zA-Z0-9](?:[a-zA-Z0-9-](?!\.)){0,61}[a-zA-Z0-9]?\.)+[a-zA-Z0-9](?:[a-zA-Z0-9-](?!$)){0,61}[a-zA-Z0-9]?)|(?:\[(?:(?:[01]?\d{1,2}|2[0-4]\d|25[0-5])\.){3}(?:[01]?\d{1,2}|2[0-4]\d|25[0-5])\]))$/],
  ['ipv4', /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/],
  ['ipv6', /^\s*((([0-9A-Fa-f]{1,4}:){7}([0-9A-Fa-f]{1,4}|:))|(([0-9A-Fa-f]{1,4}:){6}(:[0-9A-Fa-f]{1,4}|((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){5}(((:[0-9A-Fa-f]{1,4}){1,2})|:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){4}(((:[0-9A-Fa-f]{1,4}){1,3})|((:[0-9A-Fa-f]{1,4})?:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){3}(((:[0-9A-Fa-f]{1,4}){1,4})|((:[0-9A-Fa-f]{1,4}){0,2}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){2}(((:[0-9A-Fa-f]{1,4}){1,5})|((:[0-9A-Fa-f]{1,4}){0,3}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){1}(((:[0-9A-Fa-f]{1,4}){1,6})|((:[0-9A-Fa-f]{1,4}){0,4}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(:(((:[0-9A-Fa-f]{1,4}){1,7})|((:[0-9A-Fa-f]{1,4}){0,5}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:)))(%.+)?\s*$/],
  ['uri', /^[a-zA-Z][a-zA-Z0-9+.-]*:[^\s]*$/],
];

const getValueType = (value: unknown): ValueType | undefined => {
  if (typeof value === 'number') {
    if (value % 1 === 0) {
      return 'integer';
    }
    return Number.isFinite(value) ? 'number' : undefined;
  }
  if (typeof value === 'string') {
    return 'string';
  }
  if (Array.isArray(value)) {
    return 'array';
  }
  if (typeof value === 'boolean') {
    return 'boolean';
  }
  if (value === null) {
    return 'null';
  }
  if (value && typeof value === 'object' && !(value instanceof Date)) {
    return 'object';
  }
  return undefined;
};

// 数组元素的公共类型，integer 与 number 混合时视为 number，其余类型不一致时返回 null
const getCommonItemType = (items: unknown[]): ValueType | null => {
  let last: ValueType | undefined;
  for (let i = 0; i < items.length; i++) {
    let current = getValueType(items[i]);
    if (i > 0) {
      if (current === 'integer' && last === 'number') {
        current = 'number';
      }
      else if (current === 'number' && last === 'integer') {
        last = 'number';
      }
      if (last !== current) {
        return null;
      }
    }
    last = current;
  }
  return last ?? null;
};

/**
 * 求能同时校验两个 Schema 的最小公共 Schema，无法合并时返回 null。
 * 仅 integer/number 差异会合并为 number；对象属性不一致时退化为 { type: 'object' }。
 */
const mergeSchemas = (schema1: IInferredSchema | null, schema2: IInferredSchema): IInferredSchema | null => {
  if (!schema1) {
    return null;
  }
  const keys1 = keys(schema1);
  const keys2 = keys(schema2);
  // 按集合比较键，JSON 对象的键顺序没有结构含义
  if (keys1.length !== keys2.length || xor(keys1, keys2).length) {
    if (schema1.type === 'array' && schema2.type === 'array' && isEqual(xor(keys1, keys2), ['items'])) {
      const withoutItems = keys1.length > keys2.length ? schema2 : schema1;
      const withItems = keys1.length > keys2.length ? schema1 : schema2;
      const isSame = keys(withoutItems).every(key => isEqual(withoutItems[key], withItems[key]));
      if (isSame) {
        return withoutItems;
      }
    }
    if (schema1.type !== 'object' || schema2.type !== 'object') {
      return null;
    }
  }

  const merged: IInferredSchema = {};
  for (const key of keys1) {
    if (getValueType(schema1[key]) === 'object') {
      const child = mergeSchemas(schema1[key], schema2[key] ?? {});
      if (!child) {
        if (schema1.type === 'object' || schema2.type === 'object') {
          return { type: 'object' };
        }
        // 数组元素无法合并时可以省略 items
        if (key !== 'items' || schema1.type !== 'array' || schema2.type !== 'array') {
          return null;
        }
      }
      else {
        merged[key] = child;
      }
    }
    else if (key === 'type') {
      if (schema1.type === schema2.type) {
        merged.type = schema1.type;
      }
      else if ([schema1.type, schema2.type].every(type => type === 'integer' || type === 'number')) {
        merged.type = 'number';
      }
      else {
        return null;
      }
    }
    else if (isEqual(schema1[key], schema2[key])) {
      merged[key] = schema1[key];
    }
    else {
      return null;
    }
  }
  return merged;
};

const getSchema = (value: unknown, options: Required<IInferJsonSchemaOptions>): IInferredSchema => {
  const type = getValueType(value);
  if (!type) {
    throw new Error('Type of value couldn\'t be determined');
  }

  if (type === 'object') {
    const schema: IInferredSchema = { type };
    const names = Object.keys(value as object);
    if (names.length) {
      schema.properties = Object.fromEntries(names.map(name => [
        name,
        getSchema((value as Record<string, unknown>)[name], options),
      ]));
    }
    return schema;
  }

  if (type === 'array') {
    const items = value as unknown[];
    const schema: IInferredSchema = { type };
    const commonType = items.length ? getCommonItemType(items) : null;
    if (!commonType) {
      return schema;
    }
    schema.items = { type: commonType };
    if (commonType !== 'integer' && commonType !== 'number') {
      const itemSchemas = items.map(item => getSchema(item, options));
      const initial = itemSchemas.pop()!;
      const merged = itemSchemas.reduce<IInferredSchema | null>((acc, current) => mergeSchemas(acc, current), initial);
      if (merged) {
        schema.items = merged;
      }
    }
    return schema;
  }

  if (type === 'string' && options.detectFormat) {
    const format = STRING_FORMATS.find(([, pattern]) => pattern.test(value as string))?.[0];
    return format
      ? {
        type,
        format,
      }
      : { type };
  }

  return { type };
};

/**
 * 根据 JSON 示例推断 JSON Schema
 * @param value JSON 示例值
 * @param options.detectFormat 是否识别字符串格式，默认 true
 * @throws 值的类型无法识别时（如 undefined、NaN）抛出异常
 */
export const inferJsonSchema = (value: unknown, options: IInferJsonSchemaOptions = {}): IInferredSchema => {
  return getSchema(value, {
    detectFormat: options.detectFormat ?? true,
  });
};
