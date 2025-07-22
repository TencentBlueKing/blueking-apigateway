<template>
  <BkDialog
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
    <div
      v-if="!exportDialogConfig.hiddenResourceTip"
      class="resource-number"
    >
      {{
        ["all"].includes(exportParams.export_type)
          ? t("已选择全部资源")
          : t("已选择{num}个资源", { num: checkedList.length })
      }}
    </div>
    <!-- 这里提供自定义内容扩展 -->
    <template v-if="slots?.default">
      <slot />
    </template>
    <template v-else>
      <BkForm>
        <BkFormItem
          v-if="!exportDialogConfig.hiddenExportContent"
          :label="t('导出内容')"
        >
          <BkRadioGroup v-model="exportDialogConfig.exportFileDocType">
            <BkRadio label="resource">
              {{ t("资源配置") }}
            </BkRadio>
            <BkRadio label="docs">
              {{ t("资源文档") }}
            </BkRadio>
          </BkRadioGroup>
        </BkFormItem>

        <BkFormItem
          v-if="['resource'].includes(exportDialogConfig.exportFileDocType)"
          :label="getResourceTypeLabel"
        >
          <BkRadioGroup v-model="exportParams.file_type">
            <BkRadio
              v-for="item in fileTypeList"
              :key="item.label"
              :label="item.label"
            >
              {{ t(item.text) }}
            </BkRadio>
          </BkRadioGroup>
        </BkFormItem>
      </BkForm>
    </template>
  </BkDialog>
</template>

<script setup lang="tsx">
import {
  type IExportDialog,
  type IExportParams,
  type ReturnRecordType,
} from '@/types/common';

type IExportParamsFields = IExportParams & {
  width?: number
  id?: number
};

interface IProps {
  dialogConfig?: IExportDialog
  dialogParams?: IExportParamsFields
  selections?: any[]
}

const {
  dialogConfig = {},
  dialogParams = {},
  selections = [],
} = defineProps<IProps>();

const emit = defineEmits<{
  'update:dialogConfig': [val: IExportDialog]
  'update:dialogParams': [val: IExportParamsFields]
  'confirm': [void]
}>();

const { t } = useI18n();
const slots = useSlots();

const exportDialogConfig = computed<IExportDialog>({
  get: () => dialogConfig,
  set: (val) => {
    emit('update:dialogConfig', val);
  },
});

const checkedList = computed(() => selections);

const exportParams = computed({
  get: () => dialogParams,
  set: (val) => {
    emit('update:dialogParams', val);
  },
});

const getResourceTypeLabel = computed(() => {
  if (!exportDialogConfig.value.hiddenExportTypeLabel) {
    return t('导出格式');
  }
  return '';
});

const fileTypeList = computed(() => {
  const typeMap: ReturnRecordType<string, {
    label: string
    text: string
  }[]> = {
    resource: () => {
      return [
        {
          label: 'yaml',
          text: 'YAML格式',
        },
        {
          label: 'json',
          text: 'JSON格式',
        },
      ];
    },
    other: () => {
      return [
        {
          label: 'zip',
          text: 'Zip',
        },
        {
          label: 'tgz',
          text: 'Tgz',
        },
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
