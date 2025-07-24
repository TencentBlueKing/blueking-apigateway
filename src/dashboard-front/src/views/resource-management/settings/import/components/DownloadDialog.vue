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
