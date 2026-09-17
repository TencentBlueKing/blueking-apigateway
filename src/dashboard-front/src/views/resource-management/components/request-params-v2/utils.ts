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

import { cloneDeep, uniqueId } from 'lodash-es';
import toJsonSchema from 'to-json-schema';

import {
  type BodyParameterType,
  type IFlatRequestFieldRow,
  type IJsonSchemaObject,
  type IOpenApiOperationSchema,
  type IOpenApiParameter,
  type IOpenApiRequestBody,
  type IRequestBodyState,
  type IRequestFieldRow,
  type IRequestParameterRow,
  type IRequestParamsState,
  type IRequestParamsValue,
  type JsonSchema,
  PARAMETER_LOCATIONS,
  type ParameterLocation,
  type ScalarParameterType,
} from './types';

const STRUCTURAL_SCHEMA_KEYS = [
  'description',
  'items',
  'properties',
  'required',
  'type',
];

const SCHEMA_HINT_KEYS = [
  '$ref',
  'allOf',
  'anyOf',
  'enum',
  'format',
  'items',
  'oneOf',
  'properties',
  'type',
];

const JSON_SCHEMA_TYPE_NAMES = [
  'array',
  'boolean',
  'integer',
  'null',
  'number',
  'object',
  'string',
];

/** 判断输入是否为非数组的普通对象。 */
const isRecord = (value: unknown): value is Record<string, unknown> => {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
};

/** 将普通对象收窄为组件可处理的 JSON Schema 对象。 */
const isJsonSchemaObject = (value: unknown): value is IJsonSchemaObject => {
  return isRecord(value);
};

/** 判断输入是否为请求参数支持的 header、query 或 path 位置。 */
const isParameterLocation = (value: unknown): value is ParameterLocation => {
  return PARAMETER_LOCATIONS.includes(value as ParameterLocation);
};

/** 根据示例值推断非 Body 参数支持的基础类型。 */
const inferScalarType = (value: unknown): ScalarParameterType => {
  if (typeof value === 'boolean') {
    return 'boolean';
  }

  if (typeof value === 'number') {
    return 'number';
  }

  return 'string';
};

/** 解析 Schema 类型，并将 integer 统一映射为编辑器使用的 number。 */
const getSchemaType = (schema: IJsonSchemaObject): BodyParameterType => {
  const rawType = Array.isArray(schema.type)
    ? schema.type.find(type => type !== 'null')
    : schema.type;

  if (rawType === 'integer' || rawType === 'number') {
    return 'number';
  }

  if ([
    'array',
    'boolean',
    'object',
    'string',
  ].includes(String(rawType))) {
    return rawType as BodyParameterType;
  }

  if (isRecord(schema.properties)) {
    return 'object';
  }

  if (schema.items) {
    return 'array';
  }

  return 'string';
};

/** 提取非结构性的 Schema 配置，供字段设置浮窗继续编辑。 */
const getSchemaOptions = (schema: IJsonSchemaObject) => {
  const options = cloneDeep(schema);
  STRUCTURAL_SCHEMA_KEYS.forEach((key) => {
    delete options[key];
  });
  return options;
};

/** 将未知输入规范化为可安全修改的 Schema 副本。 */
const normalizeSchema = (schema: unknown): IJsonSchemaObject => {
  if (isJsonSchemaObject(schema)) {
    return cloneDeep(schema);
  }

  return {};
};

/** 将 Schema 限制为基础类型，并移除 header、query、path 不支持的嵌套结构。 */
const normalizeScalarSchema = (schema: IJsonSchemaObject) => {
  const type = getSchemaType(schema);
  const scalarType: ScalarParameterType = [
    'string',
    'number',
    'boolean',
  ].includes(type)
    ? type as ScalarParameterType
    : 'string';
  const normalizedSchema = cloneDeep(schema);

  delete normalizedSchema.items;
  delete normalizedSchema.properties;
  delete normalizedSchema.required;
  normalizedSchema.type = scalarType;

  return normalizedSchema;
};

/** 创建一个带唯一标识的 Body 字段行。 */
export const createRequestField = (
  type: BodyParameterType = 'string',
  name = '',
): IRequestFieldRow => {
  return {
    description: '',
    id: uniqueId('request-field-'),
    name,
    options: {},
    required: false,
    type,
  };
};

/** 创建指定参数位置的空参数行，path 参数默认必填。 */
export const createRequestParameter = (
  location: ParameterLocation,
): IRequestParameterRow => {
  return {
    description: '',
    id: uniqueId('request-parameter-'),
    in: location,
    name: '',
    options: {},
    required: location === 'path',
    type: 'string',
  };
};

/** 创建使用 application/json 的空请求体状态。 */
export const createRequestBody = (): IRequestBodyState => {
  return {
    mediaType: 'application/json',
    required: false,
    root: createRequestField('object'),
  };
};

/** 创建不包含任何参数与请求体的初始编辑状态。 */
export const createEmptyRequestParamsState = (): IRequestParamsState => {
  return {
    parameters: {
      header: [],
      path: [],
      query: [],
    },
  };
};

/** 递归地将 JSON Schema 转换为 Body 参数树。 */
export const schemaToFieldRow = (
  schemaValue: JsonSchema | undefined,
  name = '',
  required = false,
): IRequestFieldRow => {
  const schema = typeof schemaValue === 'boolean'
    ? {}
    : normalizeSchema(schemaValue);
  const type = getSchemaType(schema);
  const row: IRequestFieldRow = {
    description: typeof schema.description === 'string' ? schema.description : '',
    id: uniqueId('request-field-'),
    name,
    options: getSchemaOptions(schema),
    required,
    type,
  };

  if (type === 'object') {
    const properties = isRecord(schema.properties) ? schema.properties : {};
    const requiredNames = new Set(Array.isArray(schema.required) ? schema.required : []);
    row.children = Object.entries(properties).map(([propertyName, propertySchema]) => {
      return schemaToFieldRow(
        propertySchema as JsonSchema,
        propertyName,
        requiredNames.has(propertyName),
      );
    });
  }
  else if (type === 'array') {
    const itemSchema = Array.isArray(schema.items)
      ? schema.items[0]
      : schema.items;
    row.children = itemSchema === undefined
      ? []
      : [schemaToFieldRow(itemSchema, '', false)];
  }

  return row;
};

/** 递归地将 Body 参数树还原为 JSON Schema。 */
export const fieldRowToSchema = (row: IRequestFieldRow): IJsonSchemaObject => {
  const schema = cloneDeep(row.options);
  schema.type = row.type;

  if (row.description) {
    schema.description = row.description;
  }
  else {
    delete schema.description;
  }

  if (row.type === 'object') {
    const properties = Object.fromEntries(
      (row.children ?? [])
        .filter(child => child.name)
        .map(child => [child.name, fieldRowToSchema(child)]),
    );
    const required = (row.children ?? [])
      .filter(child => child.name && child.required)
      .map(child => child.name);
    schema.properties = properties;

    if (required.length) {
      schema.required = required;
    }
    else {
      delete schema.required;
    }

    delete schema.items;
  }
  else if (row.type === 'array') {
    schema.items = row.children?.[0]
      ? fieldRowToSchema(row.children[0])
      : { type: 'string' };
    delete schema.properties;
    delete schema.required;
  }
  else {
    delete schema.items;
    delete schema.properties;
    delete schema.required;
  }

  return schema;
};

/** 将单个 OpenAPI 参数转换为表格行，不支持的位置会被忽略。 */
const parameterToRow = (parameter: IOpenApiParameter): IRequestParameterRow | undefined => {
  if (!isParameterLocation(parameter.in)) {
    return undefined;
  }

  const legacySchema = {
    default: parameter.default,
    enum: parameter.enum,
    type: parameter.type,
  };
  const schema = normalizeScalarSchema(normalizeSchema(parameter.schema ?? legacySchema));
  const type = getSchemaType(schema) as ScalarParameterType;

  return {
    description: parameter.description
      ?? (typeof schema.description === 'string' ? schema.description : ''),
    id: uniqueId('request-parameter-'),
    in: parameter.in,
    name: parameter.name ?? '',
    options: getSchemaOptions(schema),
    required: parameter.in === 'path' ? true : Boolean(parameter.required),
    type,
  };
};

/** 从 OpenAPI requestBody 中提取可编辑的 application/json 请求体状态。 */
const getRequestBodyState = (
  requestBody: IOpenApiRequestBody | undefined,
): IRequestBodyState | undefined => {
  if (!requestBody || !isRecord(requestBody.content)) {
    return undefined;
  }

  const sourceMediaType = requestBody.content['application/json']
    ? 'application/json'
    : Object.keys(requestBody.content)[0];
  const schema = requestBody.content[sourceMediaType]?.schema;

  if (!sourceMediaType || schema === undefined) {
    return undefined;
  }

  const root = schemaToFieldRow(schema);

  if (requestBody.description) {
    root.description = requestBody.description;
  }

  return {
    mediaType: 'application/json',
    required: Boolean(requestBody.required),
    root,
  };
};

/** 将 OpenAPI Operation 转换为请求参数编辑器的内部状态。 */
export const openApiSchemaToState = (
  operation: IOpenApiOperationSchema | undefined,
): IRequestParamsState => {
  const state = createEmptyRequestParamsState();

  if (!operation) {
    return state;
  }

  const parameters = Array.isArray(operation.parameters) ? operation.parameters : [];
  const legacyBodyParameter = parameters.find(parameter => parameter.in === 'body');
  parameters.forEach((parameter) => {
    const row = parameterToRow(parameter);

    if (row) {
      state.parameters[row.in].push(row);
    }
  });

  state.body = getRequestBodyState(operation.requestBody);

  if (!state.body && legacyBodyParameter?.schema) {
    state.body = {
      mediaType: 'application/json',
      required: Boolean(legacyBodyParameter.required),
      root: schemaToFieldRow(legacyBodyParameter.schema),
    };
    state.body.root.description = legacyBodyParameter.description ?? state.body.root.description;
  }

  return state;
};

/** 将基础参数表格行序列化为 OpenAPI Parameter。 */
const parameterRowToOpenApi = (row: IRequestParameterRow): IOpenApiParameter => {
  const schema = cloneDeep(row.options);
  schema.type = row.type;

  return {
    description: row.description,
    in: row.in,
    name: row.name,
    ...(row.required || row.in === 'path' ? { required: true } : {}),
    schema,
  };
};

/** 将请求参数编辑状态转换为组件对外输出的 OpenAPI 数据。 */
export const requestParamsStateToValue = (state: IRequestParamsState): IRequestParamsValue => {
  const parameters = PARAMETER_LOCATIONS.flatMap((location) => {
    return state.parameters[location].map(parameterRowToOpenApi);
  });
  const requestBody: IOpenApiRequestBody | null = state.body
    ? {
      content: {
        'application/json': {
          schema: fieldRowToSchema(state.body.root),
        },
      },
      description: state.body.root.description,
      required: state.body.required,
    }
    : null;

  return {
    parameters,
    requestBody,
  };
};

/** 将普通 JSON 示例转换为 Schema，转换失败时回退为基础类型。 */
const sampleToSchema = (value: unknown): IJsonSchemaObject => {
  try {
    return normalizeSchema(toJsonSchema(value));
  }
  catch {
    return {
      type: inferScalarType(value),
    };
  }
};

/** 判断对象是否包含足以识别为 JSON Schema 的关键字。 */
const isSchemaLike = (value: unknown): value is IJsonSchemaObject => {
  if (!isRecord(value)) {
    return false;
  }

  if ('type' in value) {
    const types = Array.isArray(value.type) ? value.type : [value.type];
    const hasValidType = types.length > 0 && types.every((type) => {
      return JSON_SCHEMA_TYPE_NAMES.includes(String(type));
    });

    if (hasValidType) {
      return true;
    }
  }

  return SCHEMA_HINT_KEYS
    .filter(key => key !== 'type')
    .some(key => key in value);
};

/** 将分组 JSON 中的单个参数转换为 OpenAPI Parameter。 */
const groupedParameterToOpenApi = (
  name: string,
  value: unknown,
  location: ParameterLocation,
): IOpenApiParameter => {
  if (isRecord(value)) {
    const description = typeof value.description === 'string' ? value.description : '';
    const required = location === 'path' || Boolean(value.required);

    if (isRecord(value.schema)) {
      return {
        description,
        in: location,
        name,
        required,
        schema: normalizeScalarSchema(value.schema),
      };
    }

    if (isSchemaLike(value)) {
      const schema = cloneDeep(value);
      [
        'description',
        'in',
        'name',
        'required',
        'value',
      ].forEach((key) => {
        delete schema[key];
      });

      if (schema.default === undefined && 'value' in value) {
        schema.default = value.value;
      }

      return {
        description,
        in: location,
        name,
        required,
        schema: normalizeScalarSchema(schema),
      };
    }

    if ('value' in value) {
      const sampleValue = value.value;

      return {
        description,
        in: location,
        name,
        required,
        schema: {
          ...(sampleValue === undefined ? {} : { default: sampleValue }),
          type: inferScalarType(sampleValue),
        },
      };
    }
  }

  const scalarValue = isRecord(value) || Array.isArray(value)
    ? JSON.stringify(value)
    : value;
  const type = inferScalarType(scalarValue);

  return {
    in: location,
    name,
    required: location === 'path',
    schema: {
      ...(scalarValue === undefined ? {} : { default: scalarValue }),
      type,
    },
  };
};

/** 兼容数组和键值对象两种分组参数写法，并统一输出参数列表。 */
const parseGroupedParameters = (
  value: unknown,
  location: ParameterLocation,
): IOpenApiParameter[] => {
  if (Array.isArray(value)) {
    return value
      .filter(isRecord)
      .map((item) => {
        return groupedParameterToOpenApi(
          typeof item.name === 'string' ? item.name : '',
          item,
          location,
        );
      });
  }

  if (!isRecord(value)) {
    return [];
  }

  return Object.entries(value).map(([name, item]) => {
    return groupedParameterToOpenApi(name, item, location);
  });
};

/** 将分组 JSON 的 body 内容转换为 OpenAPI requestBody。 */
const groupedBodyToRequestBody = (value: unknown): IOpenApiRequestBody | undefined => {
  if (isRecord(value) && isRecord(value.content)) {
    return value as unknown as IOpenApiRequestBody;
  }

  if (value === undefined) {
    return undefined;
  }

  if (
    isRecord(value)
    && (typeof value.schema === 'boolean' || isRecord(value.schema))
  ) {
    return {
      content: {
        'application/json': { schema: value.schema as JsonSchema },
      },
      description: typeof value.description === 'string' ? value.description : '',
      required: Boolean(value.required),
    };
  }

  return {
    content: {
      'application/json': { schema: sampleToSchema(value) },
    },
    required: false,
  };
};

/** 判断输入是否具备 OpenAPI Operation 的请求参数结构。 */
const isOpenApiOperation = (value: Record<string, unknown>) => {
  return Array.isArray(value.parameters)
    || isRecord(value.parameters)
    || isRecord(value.requestBody);
};

/** 判断输入是否为按 header、query、path、body 分组的请求 JSON。 */
const isGroupedRequest = (value: Record<string, unknown>) => {
  const locations = PARAMETER_LOCATIONS.filter(location => location in value);

  if (!locations.length) {
    return false;
  }

  const hasValidLocationValues = locations.every((location) => {
    return isRecord(value[location]) || Array.isArray(value[location]);
  });
  const onlyContainsRequestGroups = Object.keys(value).every((key) => {
    return key === 'body' || PARAMETER_LOCATIONS.includes(key as ParameterLocation);
  });

  return hasValidLocationValues
    && (locations.length > 1 || onlyContainsRequestGroups);
};

/**
 * 将编辑器或导入文件中的 JSON 转换为请求参数状态。
 * 兼容包装后的 OpenAPI、分组参数以及作为 Body 示例的普通 JSON。
 */
export const requestJsonToState = (input: unknown): IRequestParamsState => {
  if (!isRecord(input)) {
    const state = createEmptyRequestParamsState();
    state.body = {
      mediaType: 'application/json',
      required: false,
      root: schemaToFieldRow(sampleToSchema(input)),
    };
    return state;
  }

  if (isRecord(input.openapi_schema)) {
    return requestJsonToState(input.openapi_schema);
  }

  if (isRecord(input.schema) && isOpenApiOperation(input.schema)) {
    return requestJsonToState(input.schema);
  }

  if (isOpenApiOperation(input)) {
    const operation = cloneDeep(input) as IOpenApiOperationSchema;
    const parameterGroups = input.parameters;

    if (isRecord(parameterGroups)) {
      operation.parameters = PARAMETER_LOCATIONS.flatMap((location) => {
        return parseGroupedParameters(parameterGroups[location], location);
      });
      operation.requestBody = operation.requestBody
        ?? groupedBodyToRequestBody(parameterGroups.body);
    }

    return openApiSchemaToState(operation);
  }

  if (isGroupedRequest(input)) {
    const operation: IOpenApiOperationSchema = {
      parameters: PARAMETER_LOCATIONS.flatMap((location) => {
        return parseGroupedParameters(input[location], location);
      }),
      requestBody: groupedBodyToRequestBody(input.body),
    };
    return openApiSchemaToState(operation);
  }

  const state = createEmptyRequestParamsState();
  state.body = {
    mediaType: 'application/json',
    required: false,
    root: schemaToFieldRow(sampleToSchema(input)),
  };
  return state;
};

/** 生成 JSON 编辑器需要展示的 OpenAPI 请求参数结构。 */
export const requestParamsStateToEditorJson = (state: IRequestParamsState) => {
  const value = requestParamsStateToValue(state);

  return {
    parameters: value.parameters,
    ...(value.requestBody ? { requestBody: value.requestBody } : {}),
  };
};

/** 按深度优先顺序展开 Body 参数树，并保留层级、父节点和 Schema 路径。 */
export const flattenRequestFields = (root: IRequestFieldRow): IFlatRequestFieldRow[] => {
  const result: IFlatRequestFieldRow[] = [];

  /** 递归遍历字段树并记录表格渲染所需的上下文。 */
  const visit = (
    row: IRequestFieldRow,
    depth: number,
    parent?: IRequestFieldRow,
    path = '#',
  ) => {
    result.push({
      depth,
      isArrayItem: parent?.type === 'array',
      isRoot: !parent,
      parent,
      path,
      row,
    });
    row.children?.forEach((child) => {
      const childPath = row.type === 'array'
        ? `${path}/items`
        : `${path}/properties/${child.name}`;
      visit(child, depth + 1, row, childPath);
    });
  };

  visit(root, 0);
  return result;
};

/** 切换字段类型，并清理新类型不兼容的子节点和 Schema 配置。 */
export const resetFieldForType = (
  row: IRequestFieldRow,
  type: BodyParameterType,
) => {
  const previousType = row.type;
  row.type = type;

  if (type === 'object') {
    row.children = previousType === 'object' ? row.children ?? [] : [];
  }
  else if (type === 'array') {
    row.children = previousType === 'array' ? row.children?.slice(0, 1) ?? [] : [];
  }
  else {
    delete row.children;
  }

  const nextOptions = cloneDeep(row.options);
  const incompatibleKeys: Record<BodyParameterType, string[]> = {
    array: [
      'format',
      'maxLength',
      'maximum',
      'minLength',
      'minimum',
      'multipleOf',
      'pattern',
    ],
    boolean: [
      'format',
      'maxItems',
      'maxLength',
      'maxProperties',
      'maximum',
      'minItems',
      'minLength',
      'minProperties',
      'minimum',
      'multipleOf',
      'pattern',
      'uniqueItems',
    ],
    number: [
      'format',
      'maxItems',
      'maxLength',
      'maxProperties',
      'minItems',
      'minLength',
      'minProperties',
      'pattern',
      'uniqueItems',
    ],
    object: [
      'format',
      'maxItems',
      'maxLength',
      'maximum',
      'minItems',
      'minLength',
      'minimum',
      'multipleOf',
      'pattern',
      'uniqueItems',
    ],
    string: [
      'maxItems',
      'maxProperties',
      'maximum',
      'minItems',
      'minProperties',
      'minimum',
      'multipleOf',
      'uniqueItems',
    ],
  };
  incompatibleKeys[type].forEach((key) => {
    delete nextOptions[key];
  });
  delete nextOptions.default;
  delete nextOptions.enum;
  delete nextOptions.examples;
  row.options = nextOptions;
};

/** 深拷贝请求参数状态，避免导入结果与原始对象共享引用。 */
export const cloneRequestParamsState = (state: IRequestParamsState) => {
  return cloneDeep(state);
};
