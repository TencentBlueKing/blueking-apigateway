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
  <BkSideslider
    v-model:is-show="isShow"
    width="1200"
  >
    <template #header>
      <div>
        <span>{{ titleConfig.title }}</span>
        -
        <span>{{ getOpObjectTypeText(data?.op_object_type) }}（{{ data?.op_object || '--' }}）</span>
        <BkTag theme="info">
          {{ getOpTypeText(data?.op_type) || '--' }}
        </BkTag>
      </div>
    </template>
    <template #default>
      <div
        v-if="!isContentEqual"
        class="content-wrapper"
      >
        <div class="diff-titles">
          <div><span class="diff-title before">{{ titleConfig.before }}</span></div>
          <div>
            <span class="diff-title after">{{ titleConfig.after }}</span>
          </div>
        </div>
        <div class="diff-wrapper">
          <BkCodeDiff
            :key="dateKey"
            :diff-context="20"
            :hljs="highlightjs"
            :new-content="newContent"
            :old-content="oldContent"
            diff-format="side-by-side"
            language="json"
          />
        </div>
      </div>
      <div
        v-else
        class="diff-wrapper"
      >
        <BkException
          :description="t('没有差异')"
          class="exception-wrap"
          scene="part"
          type="empty"
        />
      </div>
    </template>
    <template
      v-if="showFooter"
      #footer
    >
      <div class="footer-actions">
        <BkButton
          theme="primary"
          @click="handleConfirmClick"
        >
          {{ t('确定') }}
        </BkButton>
        <BkButton @click="handleCancelClick">
          {{ t('取消') }}
        </BkButton>
      </div>
    </template>
  </BkSideslider>
</template>

<script lang="ts" setup>
import i18n from '@/locales';
import { isEqual } from 'lodash-es';
import highlightjs from 'highlight.js';
import { useJsonTransformer } from '@/hooks/use-json-transformer';
import type { IAuditEventLogOutput } from '@/services/types/responses/gateways.ts';
import { useAccessLog } from '@/stores';

const isShow = defineModel<boolean>({
  required: true,
  default: false,
});

const {
  data,
  showFooter = false,
  titleConfig = {
    title: i18n.global.t('操作详情'),
    before: i18n.global.t('操作前'),
    after: i18n.global.t('操作后'),
  },
} = defineProps<IProps>();

const emit = defineEmits<{
  confirm: [void]
  cancel: [void]
}>();

interface IProps {
  data: IAuditEventLogOutput
  showFooter?: boolean
  titleConfig?: Record<string, any>
}

const { t } = useI18n();

const accessLogStore = useAccessLog();

const { formatJSON } = useJsonTransformer();

const dateKey = ref<number>(+new Date());

const newContent = computed(() => {
  dateKey.value = +new Date();
  return formatJSON({ source: data?.data_after });
});

const oldContent = computed(() => {
  dateKey.value = +new Date();
  return formatJSON({ source: data?.data_before });
});

const isContentEqual = computed(() => {
  return isEqual(oldContent.value, newContent.value);
});

const handleConfirmClick = () => {
  emit('confirm');
};

const handleCancelClick = () => {
  isShow.value = false;
  emit('cancel');
};

const getOpObjectTypeText = (type: string) => {
  const name = accessLogStore.auditOptions.OPObjectType.find(
    (item: Record<string, string>) => item.value === type,
  )?.name;
  return name ?? '--';
};

const getOpTypeText = (type: string) => {
  const name = accessLogStore.auditOptions.OPType.find((item: Record<string, string>) => item.value === type)?.name;
  return name ?? '--';
};

</script>

<style lang="scss" scoped>

.content-wrapper {
  padding: 24px 24px 0;

  .diff-titles {
    font-size: 14px;
    position: relative;
    display: flex;
    align-items: center;
    height: 40px;
    margin-bottom: 8px;
    background: #dcdee5;
    gap: 522px;

    &::after {
      position: absolute;
      top: 8px;
      left: 50%;
      margin-left: -1px;
      width: 1px;
      height: 24px;
      content: "";
      background: #FFFFFF;
    }

    .diff-title {
      color: #313238;
      font-weight: bold;
      font-size: 14px;
      margin-left: 12px;
    }
  }
}

.footer-actions {
  display: flex;
  gap: 12px;
}

.diff-wrapper {
  height: calc(100vh - 172px);
  overflow-y: auto;
  :deep(.d2h-file-wrapper) {
    border-radius: 0px;
  }
  .exception-wrap {
    margin-top: 200px;
  }
}

</style>
