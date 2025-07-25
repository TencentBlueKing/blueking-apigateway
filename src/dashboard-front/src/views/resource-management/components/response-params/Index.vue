/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2025 Tencent. All rights reserved.
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
  <div class="response-params-table-wrapper">
    <template
      v-for="response in responseList"
      :key="response.id"
    >
      <ResponseParamsTable
        ref="responseParamsTableRefs"
        :readonly="readonly"
        :response="response"
        @delete="() => handleDelete(response)"
        @change-code="(code) => response.code = code"
      />
    </template>
    <div v-if="!readonly">
      <BkButton
        text
        theme="primary"
        @click="addResponse"
      >
        <AgIcon name="add-small" />
        {{ t('新增状态码') }}
      </BkButton>
    </div>
  </div>
</template>

<script lang="ts" setup>
import ResponseParamsTable from './ResponseParamsTable.vue';
import { type JSONSchema7 } from 'json-schema';
import { uniqueId } from 'lodash-es';

interface IProp {
  detail?: {
    schema?: ISchema
    openapi_schema?: ISchema
  }
  readonly?: boolean
}

interface ISchema {
  responses?: {
    [key: string]: {
      description: string
      content?: { 'application/json': { schema: JSONSchema7 } }
    }
  }
}

interface IResponse {
  id: string
  code: string
  body: {
    description: string
    content?: { 'application/json': { schema: JSONSchema7 } }
  }
}

const {
  detail,
  readonly = false,
} = defineProps<IProp>();

const { t } = useI18n();

const responseParamsTableRefs = ref<InstanceType<typeof ResponseParamsTable>[]>([]);
const responseList = ref<IResponse[]>([]);

watch(() => detail, () => {
  const resourceSchema = detail?.schema || detail.openapi_schema;
  if (resourceSchema?.responses && Object.keys(resourceSchema.responses).length) {
    responseList.value = Object.entries(resourceSchema.responses).map(([code, body]) => ({
      id: uniqueId(),
      code,
      body,
    }));
  }
  else {
    responseList.value = [];
  }
}, { immediate: true });

const addResponse = () => {
  responseList.value.push({
    id: uniqueId(),
    code: '200',
    body: {
      type: 'object',
      description: '',
      content: {
        'application/json': {
          schema: {
            type: 'object',
            properties: {
              example: {
                type: 'string',
                description: '',
                schema: {
                  type: 'string',
                  description: '',
                },
              },
            },
          },
        },
      },
    },
  });
};

const handleDelete = (response: IResponse) => {
  responseList.value = responseList.value.filter(item => item.id !== response.id);
};

defineExpose({
  getValue: () => {
    const result: any = {};
    responseParamsTableRefs.value.forEach((item) => {
      const { code, body } = item.getValue();
      result[code] = body;
    });
    return result;
  },
});

</script>

<style lang="scss" scoped>
.response-params-table-wrapper {
  padding-bottom: 22px;
}
</style>
