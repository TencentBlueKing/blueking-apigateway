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
  <BkForm
    ref="formRef"
    :model="formData"
    :rules="rules"
    class="resource-baseinfo"
    @validate="setInvalidPropId"
  >
    <BkFormItem
      :label="t('名称')"
      property="name"
      required
    >
      <BkInput
        id="base-info-name"
        v-model="formData.name"
        :placeholder="t('由字母、数字、下划线（_）组成，首字符必须是字母，长度小于256个字符')"
        class="name"
        clearable
      />
      <div class="text-12px! color-#979ba5!">
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
        @update-success="init"
        @label-add-success="handleLabelAddSuccess"
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
    <BkFormItem :label="t('认证方式')">
      <BkCheckbox
        v-model="formData.auth_config.app_verified_required"
        :disabled="!gatewayStore.currentGateway?.allow_update_gateway_auth"
      >
        <span
          v-bk-tooltips="{ content: t('请求方需提供蓝鲸应用身份信息') }"
          class="bottom-line"
        >{{ t('蓝鲸应用认证') }}</span>
      </BkCheckbox>
      <BkCheckbox
        v-model="formData.auth_config.auth_verified_required"
        class="ml-40px!"
      >
        <span
          v-bk-tooltips="{ content: t('请求方需提供蓝鲸用户身份信息') }"
          class="bottom-line"
        >{{ t('用户认证') }}</span>
      </BkCheckbox>
    </BkFormItem>
    <BkFormItem
      v-if="formData.auth_config.app_verified_required"
      :label="t('检验应用权限')"
      :description="t('蓝鲸应用需申请资源访问权限')"
    >
      <BkSwitcher
        v-model="formData.auth_config.resource_perm_required"
        :disabled="!gatewayStore.currentGateway?.allow_update_gateway_auth"
        theme="primary"
        size="small"
      />
    </BkFormItem>
    <BkFormItem
      :label="t('是否公开')"
      :description="t('公开，则用户可查看资源文档、申请资源权限；不公开，则资源对用户隐藏')"
      property="is_public"
    >
      <div class="flex items-center public-switch">
        <BkSwitcher
          v-model="formData.is_public"
          theme="primary"
          size="small"
        />
        <BkCheckbox
          v-if="formData.is_public && formData.auth_config.resource_perm_required"
          v-model="formData.allow_apply_permission"
          class="ml-40px!"
        >
          <span
            v-bk-tooltips="{ content: t('允许，则任何蓝鲸应用可在蓝鲸开发者中心申请资源的访问权限；否则，只能通过网关管理员主动授权为某应用添加权限') }"
            class="bottom-line"
          >
            {{ t('允许申请权限') }}
          </span>
        </BkCheckbox>
      </div>
    </BkFormItem>
  </BkForm>
</template>

<script setup lang="ts">
import SelectCheckBox from '../settings/components/SelectCheckBox.vue';
import { getGatewayLabels } from '@/services/source/gateway.ts';
import { useRouteParams } from '@vueuse/router';
import { useGateway } from '@/stores';

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

const formRef = ref(null);
const formData = ref({
  name: '',
  description: '',
  label_ids: [],
  auth_config: {
    auth_verified_required: true,
    app_verified_required: true,
    resource_perm_required: true,
  },
  is_public: true,
  allow_apply_permission: true,
});

const labelsData = ref<{
  id: number
  name: string
}[]>([]);

const rules = {
  name: [
    {
      required: true,
      message: t('请填写名称'),
      trigger: 'blur',
    },
    {
      validator: (value: string) => {
        const reg = /^[a-zA-Z][a-zA-Z0-9_]{0,255}$|^$/;
        return reg.test(value);
      },
      message: '由字母、数字、下划线（_）组成，首字符必须是字母，长度小于256个字符',
      trigger: 'blur',
    },
  ],
};

const resourcePermRequiredBackup = ref(false);

// 错误表单项的 #id
const invalidFormElementIds = ref<string[]>([]);

watch(
  () => detail,
  (val: any) => {
    if (Object.keys(val).length) {
      const { name, description, auth_config, is_public, allow_apply_permission, labels } = val;
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
          label_ids = labelsData.value.filter(label => labels.includes(label.name)).map(label => label.id);
        }
      }
      formData.value = {
        name: isClone ? `${name}_clone` : name,
        description,
        auth_config: { ...auth_config },
        is_public,
        allow_apply_permission,
        label_ids,
      };
      resourcePermRequiredBackup.value = !!auth_config?.resource_perm_required;
    }
  },
  { immediate: true },
);

watch(
  () => [formData.value.is_public, formData.value.auth_config.resource_perm_required],
  ([v1, v2]) => {
    if (!v1 || !v2) {
      formData.value.allow_apply_permission = false;
    }
  },
);

watch(
  () => formData.value.auth_config.app_verified_required,
  (val: boolean) => {
    formData.value.auth_config.resource_perm_required = val ? resourcePermRequiredBackup.value : false;
  },
);

const init = async () => {
  labelsData.value = await getGatewayLabels(gatewayId.value);
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
  await formRef.value?.validate();
};

init();

defineExpose({
  formData,
  invalidFormElementIds,
  validate,
});
</script>

<style lang="scss" scoped>
.resource-baseinfo {

  .desc,
  .name {
    max-width: 700px;
  }

  .public-switch {
    height: 32px;
  }

  .label-label {

    :deep(.bk-form-label) {
      margin-top: 4px;
    }
  }
}

.bottom-line {
  cursor: pointer;
  border-bottom: 1px dashed #979ba5;
}
</style>
