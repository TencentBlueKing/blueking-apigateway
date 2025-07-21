<template>
  <!--  插件配置展示态组件  -->
  <!--  频率控制插件  -->
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
} from '@/components/plugin-manage/types';

interface IRateLimitConfig {
  rates: {
    [key: string]: {
      period: number
      tokens: number
    }[]
  }
}

interface IRateLimitTableRow extends IBaseTableRow {
  type: string
  tokens: number
  period: string
  appId?: string
}

interface IProps {
  plugin: IPlugin<IRateLimitConfig>
  firstColWidth: string
}

const {
  plugin,
  firstColWidth,
} = defineProps<IProps>();

const { t } = useI18n();

const periodTextMap: Record<number, string> = {
  1: t('秒'),
  60: t('分'),
  3600: t('时'),
  86400: t('天'),
};

// 频率控制插件表格列
const tableCols = ref<IColumn[]>([
  {
    label: t('类别'),
    align: 'right',
    field: 'type',
    width: firstColWidth,
    index: 0,
    rowspan: ({ row }) => row.rowSpan || 1,
  },
  {
    label: t('次数'),
    field: 'tokens',
  },
  {
    label: t('时间范围'),
    field: 'period',
  },
  {
    label: t('蓝鲸应用ID'),
    field: 'appId',
  },
]);

// 频率控制插件表格数据
const tableData = computed(() => {
  const defaultData: IRateLimitTableRow[] = [];
  const specialData: IRateLimitTableRow[] = [];
  const { rates } = plugin.config;
  Object.entries(rates).forEach(([appId, rateConfig]) => {
    const { tokens, period } = rateConfig[0];
    if (appId === '__default') {
      defaultData.push({
        tokens,
        type: t('默认频率限制'),
        period: periodTextMap[period],
        appId: '--',
      });
    }
    else {
      specialData.push({
        appId,
        tokens,
        type: t('特殊频率限制'),
        period: periodTextMap[period],
      });
    }
  });
  if (specialData.length > 0) {
    specialData[0].rowSpan = specialData.length;
  }
  return [...defaultData, ...specialData];
});

</script>
