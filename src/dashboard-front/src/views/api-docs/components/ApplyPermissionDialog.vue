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
  <BkDialog
    v-model:is-show="isShow"
    :title="t('申请权限')"
    :quick-close="false"
    width="480"
    @closed="handleClose"
  >
    <BkForm
      ref="formRef"
      :model="formData"
      :rules="rules"
      form-type="vertical"
    >
      <BkFormItem
        :label="t('选择应用')"
        property="application"
        class="relative"
        required
      >
        <BkSelect
          v-model="formData.application"
          :placeholder="t('请选择要申请权限的应用')"
          filterable
        >
          <BkOption
            v-for="app in applicableApps"
            :key="app.bk_app_code"
            :label="`${app.name} (${app.bk_app_code})`"
            :value="app.bk_app_code"
          />
        </BkSelect>
        <div
          class="new-application flex items-center cursor-pointer"
          @click="handleCreateNewApp"
        >
          <AgIcon
            name="add-small"
            size="22"
            color="#3A84FF"
          />
          <span class="color-#3A84FF ml--2px">{{ t('新建应用') }}</span>
        </div>
      </BkFormItem>
    </BkForm>
    <template #footer>
      <BkButton
        theme="primary"
        class="mr-8px"
        :loading="submitting"
        @click="handleConfirm"
      >
        {{ t('确定') }}
      </BkButton>
      <BkButton @click="handleClose">
        {{ t('取消') }}
      </BkButton>
    </template>
  </BkDialog>
</template>

<script lang="tsx" setup>
import { type Form, InfoBox } from 'bkui-vue';
import { applyDocsResourcePermission } from '@/services/source/docs';
import { getApplicableApps } from '@/services/source/mcp-market';
import type { IApplicableAppOutput } from '@/services/types/responses/mcp-marketplace.ts';
import { useEnv } from '@/stores';

interface IProps {
  gatewayName: string
  resourceName: string
}

const isShow = defineModel<boolean>('isShow', { default: false });

const {
  gatewayName,
  resourceName,
} = defineProps<IProps>();

const { t } = useI18n();
const envStore = useEnv();

const formRef = useTemplateRef<InstanceType<typeof Form>>('formRef');
const submitting = ref(false);
const applicableApps = ref<IApplicableAppOutput[]>([]);
const formData = ref({
  application: '',
});
const rules = {
  application: [
    {
      required: true,
      message: t('请选择应用'),
      trigger: 'change',
    },
  ],
};

const selectedAppName = computed(() => {
  return applicableApps.value.find(app => app.bk_app_code === formData.value.application)?.name ?? '';
});

const loadApps = async () => {
  try {
    applicableApps.value = await getApplicableApps() ?? [];
  }
  catch (error) {
    console.error(error);
    applicableApps.value = [];
  }
};

const handleCreateNewApp = () => {
  const url = envStore.env.PAAS_APP_CREATE_LINK;
  if (url) {
    window.open(url, '_blank');
  }
};

const resetForm = () => {
  formData.value.application = '';
  formRef.value?.clearValidate?.();
};

const handleClose = () => {
  resetForm();
  isShow.value = false;
};

const handleConfirm = async () => {
  try {
    await formRef.value?.validate();
  }
  catch {
    return;
  }

  submitting.value = true;
  try {
    const res = await applyDocsResourcePermission(gatewayName, {
      bk_app_code: formData.value.application,
      reason: '',
      resource_name: resourceName,
    });
    const name = selectedAppName.value;
    const ticketUrl = res?.itsm_ticket_url ?? '';
    handleClose();
    InfoBox({
      type: 'success',
      title: t('权限申请已提交'),
      confirmText: t('完成'),
      content: () => (
        <div>
          <div class="py-12px px-16px text-align-left bg-#f5f7fa mb-16px">
            {t('申请成功后，{name} 应用将拥有资源 {resource} 的访问权限。权限审批通过后即可正常使用。', {
              name,
              resource: resourceName,
            })}
          </div>
          {
            ticketUrl && (
              <div
                class="color-#3A84FF font-size-14px cursor-pointer"
                onClick={() => window.open(ticketUrl, '_blank')}
              >
                {t('查看审批进度')}
              </div>
            )
          }
        </div>
      ),
    });
  }
  catch (error) {
    console.error(error);
  }
  finally {
    submitting.value = false;
  }
};

watch(isShow, (visible) => {
  if (visible) {
    loadApps();
  }
});
</script>

<style scoped lang="scss">
.new-application {
  cursor: pointer;
  position: absolute;
  top: -32px;
  right: 0;
}
</style>
