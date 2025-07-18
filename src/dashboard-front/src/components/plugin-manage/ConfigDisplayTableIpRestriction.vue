<template>
  <!--  插件配置展示态组件  -->
  <!--  IP访问限制控制插件  -->
  <BkTable
    :data="tableData"
    :columns="tableCols"
    v-bind="$attrs"
  />
</template>

<script setup lang="ts">
import type {
  IBaseTableRow,
  IColumn,
  IPlugin,
  ValueRenderType,
} from '@/components/plugin-manage/types';

interface IIpRestrictionConfig {
  whitelist?: string
  blacklist?: string
}

interface IIpRestrictionTableRow extends IBaseTableRow { type: string }

interface IProps {
  plugin: IPlugin<IIpRestrictionConfig>
  firstColWidth: string
  valueRender: ValueRenderType
}

const {
  plugin,
  firstColWidth,
  valueRender,
} = defineProps<IProps>();

const { t } = useI18n();

const ipTypeTextMap: Record<string, string> = {
  whitelist: t('白名单'),
  blacklist: t('黑名单'),
};

// ip访问限制插件表格列
const tableCols = ref<IColumn[]>([
  {
    label: t('类型'),
    align: 'right',
    field: 'type',
    width: firstColWidth,
    index: 0,
    rowspan: ({ row }) => row.rowSpan || 1,
  },
  {
    label: 'IP',
    field: 'value',
    render: valueRender,
  },
]);

// ip访问限制插件表格数据
const tableData = computed(() => {
  const data: IIpRestrictionTableRow[] = [];
  const { config } = plugin;
  Object.entries(config).forEach(([type, ip]) => {
    data.push({
      type: ipTypeTextMap[type],
      value: ip,
    });
  });
  return data;
});

</script>

<style lang="scss" scoped>
:deep(.multi-line-table-cell-pre) {
  font: inherit;
  line-height: 1.4 !important;
  color: inherit;
}
</style>
