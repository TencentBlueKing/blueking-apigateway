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
  <BkDialog
    v-model:is-show="renewalDialogConfig.isShow"
    :title="renewalDialogConfig.title"
    :width="860"
    theme="primary"
    quick-close
  >
    <div>
      <ExpireDaySelector v-model:expire-days="expireDays" />
      <BkForm
        label-position="right"
        label-width="100"
      >
        <BkFormItem :label="t('蓝鲸应用ID')">
          <div>{{ curSelections?.[0].bk_app_code || "--" }}</div>
        </BkFormItem>
        <BkFormItem :label="t('资源名称')">
          <div>{{ curSelections?.[0].resource_name || "--" }}</div>
        </BkFormItem>
        <BkFormItem :label="t('有效期')">
          <div>
            <span
              :style="{ color: permissionStore.getDurationTextColor(curSelections?.[0].expires)}"
            >
              {{ permissionStore.getDurationText(curSelections?.[0].expires) }}</span>
            <span class="m-l-4px m-r-4px">
              <AgIcon
                name="arrows--right--line"
                style="color: #699df4"
              />
            </span>
            <span>
              <span
                v-if="!curSelections?.[0].renewable"
                class="font-bold color-#ea3636"
              >
                {{ t("不可续期") }}
              </span>
              <span
                v-else
                class="ag-normal primary"
              >
                {{ permissionStore.getDurationAfterRenew(curSelections?.[0].expires, expireDays) }}
              </span>
            </span>
          </div>
        </BkFormItem>
      </BkForm>
    </div>
    <template #footer>
      <template v-if="applyCount">
        <BkButton
          theme="primary"
          :disabled="applyCount === 0"
          :loading="renewalDialogConfig.saveLoading"
          @click="handleConfirm"
        >
          {{ t("确定") }}
        </BkButton>
      </template>
      <template v-else>
        <BkPopover
          placement="top"
          :content="t('无可续期的权限')"
        >
          <BkButton
            theme="primary"
            disabled
          >
            {{ t("确定") }}
          </BkButton>
        </BkPopover>
      </template>
      <BkButton
        class="m-l-8px"
        @click="handleApplyDialogClose"
      >
        {{ t("取消") }}
      </BkButton>
    </template>
  </BkDialog>
</template>

<script lang="ts" setup>
import { usePermission } from '@/stores';
import { t } from '@/locales';
import { type IPermission } from '@/types/permission';
import AgIcon from '@/components/ag-icon/Index.vue';
import ExpireDaySelector from '@/views/permission/app/components/ExpireDaySelector.vue';

type IDialogParams = {
  isShow: boolean
  saveLoading: boolean
  title: string
};

interface IProps {
  applyCount?: number
  expireDate: number
  selections: IPermission
  dialogParams?: IDialogParams
}

interface Emits {
  (e: 'update:expireDate', value: number)
  (e: 'update:dialogParams', value: IDialogParams)
  (e: 'confirm'): void
}

const expireDays = defineModel('expireDate', {
  type: Number,
  required: true,
  default: 0,
});
const curSelections = defineModel('selections', {
  type: Array,
  required: true,
  default: [],
});
const {
  applyCount = 0,
  dialogParams = {
    title: '',
    saveLoading: false,
    isShow: false,
  },
} = defineProps<IProps>();
const emits = defineEmits<Emits>();

const permissionStore = usePermission();

const renewalDialogConfig = computed({
  get: () => dialogParams,
  set: (params) => {
    emits('update:dialogParams', params);
  },
});

const handleConfirm = () => {
  emits('confirm');
};

const handleApplyDialogClose = () => {
  expireDays.value = 0;
  renewalDialogConfig.value.isShow = false;
};

</script>

<style lang="scss" scoped>

</style>
