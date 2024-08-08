<template>
  <!-- 下载 dialog -->
  <bk-dialog
    :is-show="isShow"
    width="600"
    :title="config.title"
    theme="primary"
    quick-close
    :is-loading="config.loading"
    @confirm="handleConfirm"
    @closed="isShow = false"
  >
    <bk-form label-position="left" label-width="100">
      <bk-form-item :label="t('下载内容')">
        <bk-radio-group v-model="config.docType">
          <bk-radio label="resource">{{ t('资源配置') }}</bk-radio>
          <bk-radio label="docs">{{ t('资源文档') }}</bk-radio>
        </bk-radio-group>
      </bk-form-item>
      <bk-form-item :label="t('下载格式')" v-if="config.docType === 'resource'">
        <bk-radio-group v-model="params.file_type">
          <bk-radio label="yaml"> {{ $t('YAML格式') }}</bk-radio>
          <bk-radio label="json"> {{ $t('JSON格式') }}</bk-radio>
        </bk-radio-group>
      </bk-form-item>
      <bk-form-item :label="t('下载格式')" v-else>
        <bk-radio-group v-model="params.file_type">
          <bk-radio label="zip"> {{ $t('Zip') }}</bk-radio>
          <bk-radio label="tgz"> {{ $t('Tgz') }}</bk-radio>
        </bk-radio-group>
      </bk-form-item>
    </bk-form>
  </bk-dialog>
</template>

<script setup lang="ts">
import { IDialog } from '@/types';
import { reactive, defineModel } from 'vue';
import { Message } from 'bkui-vue';
import { useI18n } from 'vue-i18n';
import {
  exportResources,
  exportDocs,
} from '@/http';
import { useCommon } from '@/store';

const common = useCommon();
const { t } = useI18n();
const { apigwId } = common; // 网关id

interface IexportDialog extends Partial<IDialog> {
  docType: string
}

const isShow = defineModel<boolean>({
  required: true,
  default: false,
});

// 下载参数
const params = reactive({
  export_type: 'all',
  file_type: 'yaml',
});

// 下载dialog
const config: IexportDialog = reactive({
  title: t('请选择下载的格式'),
  loading: false,
  docType: 'resource',
});

// 下载
const handleConfirm = async () => {
  const fetchMethod = config.docType === 'resource' ? exportResources : exportDocs;
  try {
    const res = await fetchMethod(apigwId, params);
    if (res.success) {
      Message({
        message: t('下载成功'),
        theme: 'success',
        width: 'auto',
      });
    }
    isShow.value = false;
  } catch (err: unknown) {
    const error = err as { message: string };
    Message({
      message: error?.message ?? '下载出错，请重试',
      theme: 'error',
      width: 'auto',
    });
  }
};
</script>

<style scoped lang="scss">

</style>
