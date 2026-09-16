/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2026 Tencent. All rights reserved.
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
    @closed="handleCloseApplyPermissionDialog"
  >
    <BkForm
      ref="formRef"
      :model="permissionFormData"
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
          v-model="permissionFormData.application"
          clearable
          filterable
          :placeholder="t('请选择要申请权限的应用')"
        >
          <BkOption
            v-for="app of applicableApps"
            :id="app.bk_app_code"
            :key="app.bk_app_code"
            :name="`${app.name} (${app.bk_app_code})`"
          />
        </BkSelect>
        <div
          class="new-application flex align-items-center cursor-pointer"
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
        :loading="isSubmitting"
        :disabled="!permissionFormData.application"
        @click="handleApplyConfirm"
      >
        {{ t('确定') }}
      </BkButton>
      <BkButton @click="handleCloseApplyPermissionDialog">
        {{ t('取消') }}
      </BkButton>
    </template>
  </BkDialog>
</template>

<script lang="tsx" setup>
import {
  Form,
  InfoBox,
} from 'bkui-vue';
import {
  getApplicableApps,
  marketplacePermissionApply,
} from '@/services/source/mcp-market.ts';
import type {
  IApplicableAppOutput,
  IMarketplacePermissionApplyOutput,
} from '@/services/types/responses/mcp-marketplace.ts';
import { useEnv } from '@/stores';
import AgIcon from '@/components/ag-icon/Index.vue';

interface IProps {
  mcpId: number
  mcpName?: string
}

const isShow = defineModel<boolean>('isShow', { default: false });

const {
  mcpId,
  mcpName = '',
} = defineProps<IProps>();

const { t } = useI18n();
const envStore = useEnv();

const formRef = ref<InstanceType<typeof Form>>();
const applicableApps = ref<IApplicableAppOutput[]>([]);
const itsmTicketUrl = ref('');
const isSubmitting = ref(false);
const permissionFormData = ref<{
  application: string
}>({
  application: '',
});

const rules = {
  application: [
    {
      required: true,
      message: t('请选择应用'),
    },
  ],
};

const selectedAppName = computed(() => {
  const app = applicableApps.value.find(item => item.bk_app_code === permissionFormData.value.application);
  return app?.name ?? '';
});

const getApplicableAppList = async () => {
  try {
    const res = await getApplicableApps();
    applicableApps.value = res ?? [];
  }
  catch {
    applicableApps.value = [];
  }
};

const handleCreateNewApp = () => {
  const url = envStore.env.PAAS_APP_CREATE_LINK;
  if (url) {
    window.open(url, '_blank');
  }
};

const handleApplyConfirm = async () => {
  try {
    await formRef.value?.validate();
    const name = selectedAppName.value;
    isSubmitting.value = true;

    const res = await marketplacePermissionApply(mcpId, {
      reason: t('申请权限'),
      bk_app_code: permissionFormData.value.application,
    });
    const [applyResult] = res as unknown as IMarketplacePermissionApplyOutput[];

    itsmTicketUrl.value = applyResult?.itsm_ticket_url ?? '';
    isShow.value = false;

    InfoBox({
      type: 'success',
      title: t('权限申请已提交'),
      confirmText: t('完成'),
      content: () => (
        <div class="permission-apply-result">
          <div class="py-12px px-16px text-align-left bg-#f5f7fa mb-16px">
            {t('申请成功后，{name} 应用将拥有 {mcp} MCP 所有工具的权限。权限审批通过后即可正常使用。',
              {
                name,
                mcp: mcpName,
              },
            )}
          </div>
          {
            itsmTicketUrl.value && (
              <div
                class="color-#3a84ff font-size-14px cursor-pointer"
                onClick={() => window.open(itsmTicketUrl.value, '_blank')}
              >
                {t('查看审批进度')}
                <AgIcon name="jump" color="#3A84FF" size="16" class="ml-6px" />
              </div>
            )
          }
        </div>
      ),
    });
  }
  catch (e) {
    console.error(e);
  }
  finally {
    isSubmitting.value = false;
  }
};

const handleCloseApplyPermissionDialog = () => {
  isShow.value = false;
  permissionFormData.value.application = '';
  formRef.value?.clearValidate();
};

watch(
  () => isShow.value,
  (val: boolean) => {
    if (val) {
      getApplicableAppList();
    }
  },
);
</script>

<style lang="scss" scoped>
.new-application {
  position: absolute;
  top: -32px;
  right: 0;
  cursor: pointer;
}
</style>
