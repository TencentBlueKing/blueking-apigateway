<template>
  <!--  插件配置展示态组件  -->
  <!--  IP访问限制控制插件  -->
  <bk-table
    :data="tableData"
    :columns="tableCols"
    v-bind="$attrs"
  />
</template>

<script setup lang="ts">
import {
  computed,
  ref,
  toRefs,
} from 'vue';
import {
  IBaseTableRow,
  IColumn,
  IPlugin,
} from '@/views/components/plugin-manage/types';
import { useI18n } from 'vue-i18n';

interface IIpRestrictionConfig {
  whitelist?: string
  blacklist?: string
}

interface IIpRestrictionTableRow extends IBaseTableRow {
  type: string
  ip: string
}

interface IProps {
  plugin: IPlugin<IIpRestrictionConfig>
  firstColWidth: string
}

const { t } = useI18n();

const ipTypeTextMap: Record<string, string> = {
  whitelist: t('白名单'),
  blacklist: t('黑名单'),
};

const props = defineProps<IProps>();

const {
  plugin,
  firstColWidth,
} = toRefs(props);

// ip访问限制插件表格列
const tableCols = ref<IColumn[]>([
  {
    label: t('类型'),
    align: 'right',
    field: 'type',
    width: firstColWidth.value,
    index: 0,
  },
  {
    label: 'IP',
    field: 'ip',
  },
]);

// ip访问限制插件表格数据
const tableData = computed(() => {
  const data: IIpRestrictionTableRow[] = [];
  const { config }  = plugin.value;
  Object.entries(config).forEach(([type, ip]) => {
    data.push({
      ip,
      type: ipTypeTextMap[type],
    });
  });
  return data;
});

</script>
