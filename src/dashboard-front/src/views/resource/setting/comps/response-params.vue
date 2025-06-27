<template>
  <div class="response-params-table-wrapper">
    <template
      v-for="response in responseList"
      :key="response.id"
    >
      <ResponseParamsTable
        ref="responseParamsTableRefs"
        :response="response"
        @delete="() => handleDelete(response)"
        @change-code="(code) => response.code = code"
      />
    </template>
    <div>
      <bk-button
        text
        theme="primary"
        @click="addResponse"
      >
        <AgIcon name="add-small" />
        {{ t('新增状态码') }}
      </bk-button>
    </div>
  </div>
</template>

<script lang="ts" setup>
import ResponseParamsTable from '@/views/resource/setting/comps/response-params-table.vue';
import { JSONSchema7 } from 'json-schema';
import {
  ref,
  watch,
} from 'vue';
import _ from 'lodash';
import { useI18n } from 'vue-i18n';
import AgIcon from '@/components/ag-icon.vue';

interface IProp {
  detail?: {
    schema: {
      responses?: {
        [key: string]: {
          description: string,
          content?: {
            'application/json': {
              schema: JSONSchema7,
            }
          },
        }
      },
    };
  },
}

interface IResponse {
  id: string,
  code: string,
  body: {
    description: string,
    content?: {
      'application/json': {
        schema: JSONSchema7,
      }
    },
  },
}

const { detail } = defineProps<IProp>();

const { t } = useI18n();

const responseParamsTableRefs = ref<InstanceType<typeof ResponseParamsTable>[]>([]);
const responseList = ref<IResponse[]>([]);

watch(() => detail, () => {
  if (detail?.schema?.responses && Object.keys(detail.schema.responses).length) {
    responseList.value = Object.entries(detail.schema.responses).map(([code, body]) => ({
      id: _.uniqueId(),
      code,
      body,
    }));
  } else {
    responseList.value = [];
  }
});

const addResponse = () => {
  responseList.value.push({
    id: _.uniqueId(),
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
