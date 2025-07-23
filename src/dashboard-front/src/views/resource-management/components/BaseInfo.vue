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
        v-model="formData.label_ids"
        :labels-data="labelsData"
        :width="700"
        is-add
        @update-success="init"
        @label-add-success="init"
      />
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
          v-if="formData.is_public"
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
}

const {
  detail = {},
  isClone = false,
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

const labelsData = ref([]);

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
      const label_ids = labels.map((e: {
        id: number
        name: string
      }) => e.id);
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
  () => formData.value.is_public,
  (val: boolean) => {
    // 必须要公开 才能允许申请权限
    formData.value.allow_apply_permission = val;
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
