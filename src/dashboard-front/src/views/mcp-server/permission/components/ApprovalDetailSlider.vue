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
  <BkSideslider
    v-model:is-show="approvalSliderConf.isShow"
    quick-close
    :title="approvalSliderConf.title"
    :width="640"
  >
    <template #default>
      <div class="p-24px">
        <div class="approval-detail-slider">
          <div class="item">
            <div class="key">
              {{ t("蓝鲸应用ID：") }}
            </div>
            <div class="value">
              {{ approvalDetail?.bk_app_code }}
            </div>
          </div>
          <template v-if="['mcp'].includes(activeTab)">
            <div class="item">
              <div class="key">
                {{ t('MCPServer 名称：') }}
              </div>
              <div class="value">
                {{ approvalDetail?.mcp_server?.name }}
              </div>
            </div>
            <div class="item">
              <div class="key">
                {{ t('MCPServer 中文名：') }}
              </div>
              <div class="value">
                {{ approvalDetail?.mcp_server?.title }}
              </div>
            </div>
          </template>
          <div class="item">
            <div class="key">
              {{ t("申请人：") }}
            </div>
            <div class="value">
              <template v-if="Boolean(approvalDetail?.applied_by)">
                <span v-if="!featureFlagStore.isEnableDisplayName">{{ approvalDetail?.applied_by }}</span>
                <span v-else><bk-user-display-name :user-id="approvalDetail?.applied_by" /></span>
              </template>
              <template v-else>
                --
              </template>
            </div>
          </div>
          <div class="item">
            <div class="key">
              {{ t("申请时间：") }}
            </div>
            <div class="value">
              {{ approvalDetail?.applied_time || approvalDetail?.created_time }}
            </div>
          </div>
          <div class="item">
            <div class="key">
              {{ t("审批人：") }}
            </div>
            <div class="value">
              <!-- 优先展示 handled_by -->
              <template v-if="approvalDetail?.handled_by">
                <span v-if="!featureFlagStore.isEnableDisplayName">
                  {{ approvalDetail.handled_by }}
                </span>
                <bk-user-display-name
                  v-else
                  :user-id="approvalDetail.handled_by"
                />
              </template>

              <!-- 没有 handled_by 再展示 approvers -->
              <template v-else-if="approvalDetail?.approvers?.length">
                <span v-if="!featureFlagStore.isEnableDisplayName">
                  {{ approvalDetail.approvers.join(', ') }}
                </span>
                <bk-user-display-name
                  v-else
                  :user-id="approvalDetail.approvers.join(',')"
                />
              </template>

              <template v-else>
                --
              </template>
            </div>
          </div>
          <div
            v-if="approvalDetail?.handled_time"
            class="item"
          >
            <div class="key">
              {{ t("审批时间：") }}
            </div>
            <div class="value">
              {{ approvalDetail?.handled_time }}
            </div>
          </div>
          <div class="item">
            <div class="key">
              {{ t("申请理由：") }}
            </div>
            <div class="value">
              {{ approvalDetail?.reason || '--' }}
            </div>
          </div>
          <div class="item">
            <div class="key">
              {{ t("审批状态：") }}
            </div>
            <div class="value">
              {{ renderApplyStatus }}
            </div>
          </div>
        </div>
      </div>
    </template>
  </BkSideslider>
</template>

<script setup lang="tsx">
import { t } from '@/locales';
import { useFeatureFlag } from '@/stores';
import { APPROVAL_HISTORY_STATUS_MAP, APPROVAL_STATUS_MAP } from '@/enums';
import type { IMCPServerAppPermissionApplyListOutput } from '@/services/types/responses/gateways.ts';
import type { IPersonalWorkbenchListResponse } from '@/services/types/responses/personal-workbench.ts';

type IMaybeApproval
  = | Partial<IPersonalWorkbenchListResponse>
    | Partial<IMCPServerAppPermissionApplyListOutput>;

type IApprovalWithOptionalFields = IMaybeApproval & {
  reason?: string
  status?: string
  approvers?: string[]
};

interface IProps {
  approvalDetail: IApprovalWithOptionalFields | null
  activeTab?: string
}

const approvalSliderConf = defineModel('approvalSliderConf', {
  type: Object,
  default: () => {
    return {
      isShow: false,
      title: '',
    };
  },
});

const { approvalDetail, activeTab = 'mcp' } = defineProps<IProps>();

const featureFlagStore = useFeatureFlag();

const renderApplyStatus = computed(() => {
  const statusMap = activeTab.includes('gateway') ? APPROVAL_HISTORY_STATUS_MAP : APPROVAL_STATUS_MAP;
  return statusMap[approvalDetail?.status as keyof typeof statusMap];
});
</script>

<style lang="scss" scoped>
.approval-detail-slider {
  padding: 0 16px;
  background-color: #fafbfd;
  border: 1px solid #f0f1f5;
  border-radius: 2px;

  .item {
    display: flex;
    align-items: center;
    font-size: 14px;
    min-height: 44px;
    border-bottom: 1px dashed #dcdee5;

    .key {
      min-width: 190px;
      flex-shrink: 0;
      color: #63656e;
      text-align: right;
      padding-right: 12px;
    }

    .value {
      color: #313238;
      flex: 1;
      word-break: break-all;
    }

    &:last-child {
      border-bottom: none;
    }
  }
}
</style>
