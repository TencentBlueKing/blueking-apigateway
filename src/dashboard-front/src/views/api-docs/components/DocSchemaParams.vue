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

<template>
  <div class="ag-markdown-view">
    <table v-if="mode === 'request'">
      <thead>
        <tr>
          <th>{{ t('参数名') }}</th>
          <th>{{ t('位置') }}</th>
          <th>{{ t('类型') }}</th>
          <th>{{ t('必填') }}</th>
          <th>{{ t('备注') }}</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="row in requestRows"
          :key="`${row.in}-${row.name}`"
        >
          <td>{{ row.name }}</td>
          <td>{{ row.in }}</td>
          <td>{{ row.type }}</td>
          <td>{{ row.required ? t('是') : t('否') }}</td>
          <td>{{ row.description || '--' }}</td>
        </tr>
      </tbody>
    </table>
    <template v-else>
      <section
        v-for="group in responseGroups"
        :key="group.code"
        class="mb-16px"
      >
        <p class="mb-8px">
          <strong>{{ group.code }}</strong>
          <span
            v-if="group.description"
            class="ml-8px color-#63656e"
          >{{ group.description }}</span>
        </p>
        <table v-if="group.rows.length">
          <thead>
            <tr>
              <th>{{ t('参数名') }}</th>
              <th>{{ t('类型') }}</th>
              <th>{{ t('备注') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="row in group.rows"
              :key="row.name"
            >
              <td>{{ row.name }}</td>
              <td>{{ row.type }}</td>
              <td>{{ row.description || '--' }}</td>
            </tr>
          </tbody>
        </table>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import type { IDocsOpenAPISchema, IDocsSchemaObject } from '@/services/types/responses/docs.ts';
import { getContentSchema } from '../utils/compose-doc';

interface IParamRow {
  name: string
  in: string
  type: string
  required: boolean
  description: string
}

interface IResponseGroup {
  code: string
  description: string
  rows: IParamRow[]
}

interface IProps {
  schema?: IDocsOpenAPISchema
  mode?: 'request' | 'response'
}

const {
  schema = {},
  mode = 'request',
} = defineProps<IProps>();

const { t } = useI18n();

const locationLabel: Record<string, string> = {
  header: 'Header',
  query: 'Query',
  path: 'Path',
  cookie: 'Cookie',
  body: 'Body',
};

const schemaType = (value?: IDocsSchemaObject): string => {
  if (!value) {
    return 'string';
  }
  if (Array.isArray(value.type)) {
    return value.type.join(' | ');
  }
  if (value.type === 'array') {
    return `array<${schemaType(value.items || {})}>`;
  }
  if (value.type === 'integer') {
    return 'number';
  }
  return value.type || 'object';
};

const flattenProperties = (
  value: IDocsSchemaObject | undefined,
  prefix = '',
  location = 'body',
): IParamRow[] => {
  if (!value) {
    return [];
  }
  const requiredList = new Set(value.required || []);
  const properties = value.properties || {};
  const rows: IParamRow[] = [];
  Object.keys(properties).forEach((key) => {
    const property = properties[key] || {};
    const name = prefix ? `${prefix}.${key}` : key;
    rows.push({
      name,
      in: locationLabel[location] || location,
      type: schemaType(property),
      required: requiredList.has(key),
      description: property.description || '',
    });
    if (property.type === 'object' || property.properties) {
      rows.push(...flattenProperties(property, name, location));
    }
    else if (property.type === 'array' && property.items?.type === 'object') {
      rows.push(...flattenProperties(property.items, `${name}[]`, location));
    }
  });
  return rows;
};

const requestRows = computed<IParamRow[]>(() => {
  const rows: IParamRow[] = (schema?.parameters || []).map(parameter => ({
    name: parameter.name,
    in: locationLabel[parameter.in] || parameter.in,
    type: schemaType(parameter.schema),
    required: Boolean(parameter.required),
    description: parameter.description || '',
  }));
  const bodySchema = getContentSchema(schema?.requestBody?.content);
  if (bodySchema) {
    rows.push({
      name: t('根节点'),
      in: locationLabel.body,
      type: schemaType(bodySchema),
      required: Boolean(schema?.requestBody?.required),
      description: schema?.requestBody?.description || '',
    });
    rows.push(...flattenProperties(bodySchema));
  }
  return rows;
});

const responseGroups = computed<IResponseGroup[]>(() => {
  return Object.entries(schema?.responses || {}).map(([code, response]) => {
    const bodySchema = getContentSchema(response.content);
    const rows: IParamRow[] = [];
    if (bodySchema) {
      rows.push({
        name: t('根节点'),
        in: locationLabel.body,
        type: schemaType(bodySchema),
        required: false,
        description: response.description || '',
      });
      rows.push(...flattenProperties(bodySchema));
    }
    return {
      code,
      description: response.description || '',
      rows,
    };
  });
});
</script>
