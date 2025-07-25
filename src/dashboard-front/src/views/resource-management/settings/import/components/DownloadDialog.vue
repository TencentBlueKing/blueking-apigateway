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
  <!-- 下载 dialog -->
  <BkDialog
    :is-show="isShow"
    width="600"
    :title="config.title"
    theme="primary"
    quick-close
    :is-loading="config.loading"
    @confirm="handleConfirm"
    @closed="isShow = false"
  >
    <BkForm
      label-position="left"
      label-width="100"
    >
      <BkFormItem :label="t('下载内容')">
        <BkRadioGroup v-model="config.docType">
          <BkRadio label="resource">
            {{ t('资源配置') }}
          </BkRadio>
          <BkRadio label="docs">
            {{ t('资源文档') }}
          </BkRadio>
        </BkRadioGroup>
      </BkFormItem>
      <BkFormItem
        v-if="config.docType === 'resource'"
        :label="t('下载格式')"
      >
        <BkRadioGroup v-model="params.file_type">
          <BkRadio label="yaml">
            {{ t('YAML格式') }}
          </BkRadio>
          <BkRadio label="json">
            {{ t('JSON格式') }}
          </BkRadio>
        </BkRadioGroup>
      </BkFormItem>
      <BkFormItem
        v-else
        :label="t('下载格式')"
      >
        <BkRadioGroup v-model="params.file_type">
          <BkRadio label="zip">
            Zip
          </BkRadio>
          <BkRadio label="tgz">
            Tgz
          </BkRadio>
        </BkRadioGroup>
      </BkFormItem>
    </BkForm>
  </BkDialog>
</template>

<script setup lang="ts">
import { type IDialog } from '@/types/common';
import { Message } from 'bkui-vue';
import { exportDocs } from '@/services/source/gateway';
import { exportResources } from '@/services/source/resource';
import { useRouteParams } from '@vueuse/router';

const isShow = defineModel<boolean>({
  required: true,
  default: false,
});

const { t } = useI18n();
const gatewayId = useRouteParams('id', 0, { transform: Number });

interface IExportDialog extends Partial<IDialog> { docType: string }

// 下载参数
const params = reactive({
  export_type: 'all',
  file_type: 'yaml',
});

// 下载dialog
const config: IExportDialog = reactive({
  title: t('请选择下载的格式'),
  loading: false,
  docType: 'resource',
});

// 下载
const handleConfirm = async () => {
  const fetchMethod = config.docType === 'resource' ? exportResources : exportDocs;
  try {
    const res = await fetchMethod(gatewayId.value, params);
    if (res.success) {
      Message({
        message: t('下载成功'),
        theme: 'success',
        width: 'auto',
      });
    }
    isShow.value = false;
  }
  catch (err: unknown) {
    const error = err as { message: string };
    Message({
      message: error?.message ?? t('下载出错，请重试'),
      theme: 'error',
      width: 'auto',
    });
  }
};
</script>
