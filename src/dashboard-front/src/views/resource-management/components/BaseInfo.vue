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
  <BkForm
    ref="formRef"
    :model="formData"
    :rules="rules"
    label-width="180"
    class="resource-basic-info"
    @validate="setInvalidPropId"
  >
    <BkFormItem
      v-if="isAIGateway"
      :label="t('资源类型')"
      required
    >
      <BkTag theme="info">
        {{ isModelProxy ? t('模型代理 API') : t('普通 API') }}
      </BkTag>
    </BkFormItem>
    <BkFormItem
      :label="t('名称')"
      property="name"
      required
    >
      <BkInput
        id="base-info-name"
        v-model="formData.name"
        :placeholder="namePlaceholder"
        class="name"
        clearable
      />
      <div
        v-if="!isModelProxy"
        class="text-12px color-#979ba5"
      >
        {{ t("资源名称在网关下唯一，将在SDK中用作操作名称，若修改，请联系 SDK 用户做相应调整") }}
      </div>
    </BkFormItem>
    <BkFormItem :label="t('描述')">
      <BkInput
        v-model="formData.description"
        :placeholder="t('请输入描述')"
        clearable
        class="desc"
      />
    </BkFormItem>
    <BkFormItem
      :label="t('标签')"
      class="label-label"
    >
      <SelectCheckBox
        v-if="isLabelsEditable"
        v-model="formData.label_ids"
        :labels-data="labelsData"
        :width="700"
        is-add
        @updated="init"
        @added="handleLabelAddSuccess"
      />
      <div v-else>
        <div
          v-if="detail?.labels?.length"
          class="mt-8px flex gap-4px"
        >
          <BkTag
            v-for="(label, index) in detail.labels"
            :key="index"
          >
            {{ label }}
          </BkTag>
        </div>
        <span v-else>--</span>
      </div>
    </BkFormItem>
  </BkForm>
</template>

<script setup lang="ts">
import { useRouteParams, useRouteQuery } from '@vueuse/router';
import { useGateway } from '@/stores';
import { getLabelList } from '@/services/source/gateway/label';
import SelectCheckBox from '@/views/resource-management/settings/components/SelectCheckBox.vue';

interface IProps {
  detail?: any
  isClone?: boolean
  // 是否允许编辑标签，用于控制是否只展示静态标签
  isLabelsEditable?: boolean
}

const {
  detail = {},
  isClone = false,
  isLabelsEditable = true,
} = defineProps<IProps>();

const { t } = useI18n();
const gatewayStore = useGateway();
const gatewayId = useRouteParams('id', 0, { transform: Number });
const queryKind = useRouteQuery('kind');

const formRef = useTemplateRef('formRef');
const formData = ref({
  kind: queryKind.value,
  name: '',
  description: '',
  label_ids: [] as number[],
});

const labelsData = ref<{
  id: number
  name: string
}[]>([]);

// 错误表单项的 #id
const invalidFormElementIds = ref<string[]>([]);

const isAIGateway = computed(() => gatewayStore.isAIGateway);
// 是否是模型代理 API
const isModelProxy = computed(() => isAIGateway && queryKind.value === 'ai');

const namePlaceholder = t('由字母、数字、下划线（_）组成，首字符必须是字母，长度小于256个字符');

const rules = {
  name: [
    {
      required: true,
      message: t('请填写名称'),
      trigger: 'blur',
    },
    {
      trigger: 'blur',
      message: namePlaceholder,
      validator: (value: string) => {
        const reg = /^[a-zA-Z][a-zA-Z0-9_]{0,255}$|^$/;
        return reg.test(value);
      },
    },
  ],
};

watch(
  () => detail,
  (val: any) => {
    if (Object.keys(val).length) {
      const { name, description, labels } = val;
      let label_ids: number[] = [];
      if (labels?.length) {
        // labels 由 id 和 name 组成的情况
        if (labels[0].id && labels[0].name) {
          label_ids = labels.map((label: {
            id: number
            name: string
          }) => label.id);
        }
        // labels 由纯数组组成的情况
        else {
          label_ids = labelsData.value.filter((label: {
            id: number
            name: string
          }) => labels.includes(label.name)).map((label: {
            id: number
            name: string
          }) => label.id);
        }
      }
      formData.value = {
        kind: queryKind.value,
        name: isClone ? `${name}_clone` : name,
        description,
        label_ids,
      };
    }
  },
  { immediate: true },
);

const init = async () => {
  labelsData.value = await getLabelList(gatewayId.value);
};

const handleLabelAddSuccess = async (labelId: number) => {
  await init();
  if (!formData.value.label_ids.includes(labelId)) {
    formData.value.label_ids.push(labelId);
  }
};

// 监听表单校验时间，收集 #id
const setInvalidPropId = (property: string, result: boolean) => {
  if (!result) {
    invalidFormElementIds.value.push(`base-info-${property}`);
  }
};

const validate = async () => {
  invalidFormElementIds.value = [];
  await (formRef.value as any)?.validate();
};

init();

defineExpose({
  formData,
  invalidFormElementIds,
  validate,
});
</script>

<style lang="scss" scoped>
.resource-basic-info {

  .desc,
  .name {
    max-width: 700px;
  }

  .label-label {

    :deep(.bk-form-label) {
      margin-top: 4px;
    }
  }
}
</style>
