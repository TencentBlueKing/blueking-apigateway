<template>
  <bk-dialog
    :is-loading="exportDialogConfig.loading"
    :is-show="exportDialogConfig.isShow"
    :title="exportDialogConfig.title"
    quick-close
    theme="primary"
    class="export-resource-dialog"
    :width="exportDialogConfig?.width ?? 600"
    @closed="handleClose"
    @confirm="handleExportDownload"
  >
    <div class="resource-number" v-if="!exportDialogConfig.hiddenResourceTip">
      {{
        ["all"].includes(exportParams.export_type)
          ? $t("已选择全部资源")
          : $t("已选择{num}个资源", { num: checkedList.length })
      }}
    </div>
    <!-- 这里提供自定义内容扩展 -->
    <template v-if="slots?.default">
      <slot></slot>
    </template>
    <template v-else>
      <bk-form>
        <bk-form-item
          :label="$t('导出内容')"
          v-if="!exportDialogConfig.hiddenExportContent"
        >
          <bk-radio-group v-model="exportDialogConfig.exportFileDocType">
            <bk-radio label="resource">{{ $t("资源配置") }}</bk-radio>
            <bk-radio label="docs">{{ $t("资源文档") }}</bk-radio>
          </bk-radio-group>
        </bk-form-item>

        <bk-form-item
          v-if="['resource'].includes(exportDialogConfig.exportFileDocType)"
          :label="getResourceTypeLabel"
        >
          <bk-radio-group v-model="exportParams.file_type">
            <bk-radio v-for="item in fileTypeList" :key="item.label" :label="item.label">
              {{ $t(item.text) }}
            </bk-radio>
          </bk-radio-group>
        </bk-form-item>
      </bk-form>
    </template>
  </bk-dialog>
</template>

<script setup lang="tsx">
import i18n from '@/language/i18n';
import { computed, PropType, useSlots } from 'vue';
import { IExportDialog, IExportParams, ReturnRecordType } from '@/types';

type IExportParamsFields = IExportParams & { width?: number; id?: number };

const props = defineProps({
  dialogConfig: {
    type: Object as PropType<IExportDialog>,
    default: () => {},
  },
  dialogParams: {
    type: Object as PropType<IExportParamsFields>,
    default: () => {},
  },
  selections: {
    type: Array as PropType<unknown[]>,
    default: () => [],
  },
});
const emit = defineEmits(['update:dialogConfig', 'update:dialogParams', 'confirm']);

const slots = useSlots();

const exportDialogConfig = computed({
  get: () => props.dialogConfig,
  set: (val) => {
    emit('update:dialogConfig', val);
  },
});

const checkedList = computed(() => props.selections);

const exportParams = computed({
  get: () => props.dialogParams,
  set: (val) => {
    emit('update:dialogParams', val);
  },
});

const getResourceTypeLabel = computed(() => {
  if (!exportDialogConfig.value.hiddenExportTypeLabel) {
    return i18n.global.t('导出格式');
  }
  return '';
});

const fileTypeList = computed(() => {
  const typeMap: ReturnRecordType<string, { label: string; text: string }[]> = {
    resource: () => {
      return [
        { label: 'yaml', text: 'YAML格式' },
        { label: 'json', text: 'JSON格式' },
      ];
    },
    other: () => {
      return [
        { label: 'zip', text: 'Zip' },
        { label: 'tgz', text: 'Tgz' },
      ];
    },
  };
  return typeMap[exportDialogConfig.value.exportFileDocType]?.() ?? typeMap['other']();
});

const handleClose = () => {
  exportDialogConfig.value.isShow = false;
  if (exportParams.value.id) {
    exportParams.value.id = 0;
  }
};

const handleExportDownload = () => {
  emit('confirm');
};
</script>

<style lang="scss" scoped>
.export-resource-dialog {
  .resource-number {
    color: #c4c6cc;
  }
}
</style>
