
<template>
  <bk-form
    ref="formRef"
    :model="formData"
    :rules="rules"
    class="resource-baseinfo"
    @validate="setInvalidPropId"
  >
    <bk-form-item
      :label="t('名称')"
      property="name"
      required>
      <bk-input
        v-model="formData.name"
        :placeholder="t('由字母、数字、下划线（_）组成，首字符必须是字母，长度小于256个字符')"
        class="name"
        id="base-info-name"
        clearable
      />
      <div class="common-form-tips">
        {{ t("资源名称在网关下唯一，将在SDK中用作操作名称，若修改，请联系 SDK 用户做相应调整") }}
      </div>
    </bk-form-item>
    <bk-form-item :label="t('描述')">
      <bk-input
        v-model="formData.description"
        :placeholder="t('请输入描述')"
        clearable
        class="desc"
      />
    </bk-form-item>
    <bk-form-item :label="t('标签')" class="label-label">
      <SelectCheckBox
        :labels-data="labelsData"
        :width="700"
        :is-add="true"
        v-model="formData.label_ids"
        @update-success="init"
        @label-add-success="init"></SelectCheckBox>
    </bk-form-item>
    <bk-form-item :label="t('认证方式')">
      <bk-checkbox
        v-model="formData.auth_config.app_verified_required"
        :disabled="!common.curApigwData.allow_update_gateway_auth">
        <span class="bottom-line" v-bk-tooltips="{ content: t('请求方需提供蓝鲸应用身份信息') }">{{ t('蓝鲸应用认证') }}</span>
      </bk-checkbox>
      <bk-checkbox class="ml40" v-model="formData.auth_config.auth_verified_required">
        <span class="bottom-line" v-bk-tooltips="{ content: t('请求方需提供蓝鲸用户身份信息') }">{{ t('用户认证') }}</span>
      </bk-checkbox>
    </bk-form-item>
    <bk-form-item
      :label="t('检验应用权限')"
      :description="t('蓝鲸应用需申请资源访问权限')"
      v-if="formData.auth_config.app_verified_required"
    >
      <bk-switcher
        v-model="formData.auth_config.resource_perm_required"
        :disabled="!common.curApigwData.allow_update_gateway_auth"
        theme="primary"
        size="small"
      />
    </bk-form-item>
    <bk-form-item
      :label="t('是否公开')"
      :description="t('公开，则用户可查看资源文档、申请资源权限；不公开，则资源对用户隐藏')"
      property="is_public"
    >
      <div class="flex-row align-items-center public-switch">
        <bk-switcher
          v-model="formData.is_public"
          theme="primary"
          size="small"
        />
        <bk-checkbox
          v-if="formData.is_public" class="ml40"
          v-model="formData.allow_apply_permission">
          <span
            class="bottom-line"
            v-bk-tooltips="{ content: t('允许，则任何蓝鲸应用可在蓝鲸开发者中心申请资源的访问权限；否则，只能通过网关管理员主动授权为某应用添加权限') }">
            {{ t('允许申请权限') }}
          </span>
        </bk-checkbox>
      </div>
    </bk-form-item>
    <!-- <BkSchemaForm
      class="mt20"
      v-model="schemaFormData"
      :schema="formConfig.schema"
      ref="bkForm"
      :label-width="180">
    </BkSchemaForm> -->
  </bk-form>
</template>
<script setup lang="ts">
import { ref, watch } from 'vue';
import SelectCheckBox from './select-check-box.vue';
import { useI18n } from 'vue-i18n';
import { getGatewayLabels } from '@/http';
import { useCommon } from '@/store';

const props = defineProps({
  detail: {
    type: Object,
    default: {},
  },
  isClone: {
    type: Boolean,
    default: false,
  },
});

const formRef = ref(null);
const { t } = useI18n();
const common = useCommon();
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
  () => props.detail,
  (val: any) => {
    if (Object.keys(val).length) {
      const { name, description, auth_config, is_public, allow_apply_permission, labels } = val;
      const label_ids = labels.map((e: { id: number, name: string }) => e.id);
      formData.value = {
        name: props.isClone ? `${name}_clone` : name,
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
  const res = await getGatewayLabels(common.apigwId);
  labelsData.value = res;
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
