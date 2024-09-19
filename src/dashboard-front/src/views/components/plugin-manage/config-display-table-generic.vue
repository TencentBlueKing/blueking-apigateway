<template>
  <!--  插件配置展示态组件  -->
  <!--  通用的展示表格  -->
  <bk-table
    :data="tableData"
    :columns="tableCols"
    :thead="{ isShow: false }"
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

interface IGenericConfig {
  [key: string]: unknown
}

interface IProps {
  plugin: IPlugin<IGenericConfig>
}

const { t } = useI18n();

// 键名对应文本
const rowKeyTextMap: Record<string, string> = {
  // 熔断插件
  break_response_body: t('熔断响应体'),
  break_response_code: t('熔断响应状态码'),
  break_response_headers: t('熔断响应头'),
  healthy: t('健康状态'),
  max_breaker_sec: t('最大熔断时间'),
  unhealthy: t('不健康状态'),
  http_statuses: t('状态码'),
  successes: t('健康次数'),
  failures: t('不健康次数'),
  // mocking 插件
  response_status: t('响应状态码'),
  response_example: t('响应体'),
  response_headers: t('响应头'),
};

const props = defineProps<IProps>();

const { plugin } = toRefs(props);

// 通用表格列
const tableCols = ref<IColumn[]>([
  {
    label: t('键'),
    align: 'right',
    field: 'key',
    width: '200',
    index: 0,
    rowspan: ({ row }) => row.rowSpan,
  },
  {
    label: t('值'),
    field: 'value',
  },
]);

// 通用表格数据
const tableData = computed(() => {
  const data: IBaseTableRow[] = [];
  const { config } = plugin.value;
  Object.entries(config).forEach(([key, value]) => {
    key = rowKeyTextMap[key] || key;
    if (!Array.isArray(value)) {
      data.push({
        key,
        value,
        rowSpan: 1,
      });
    } else {
      value.forEach((subValue, index) => {
        data.push({
          key,
          value: subValue,
          rowSpan: index === 0 ? value.length : 0,
        });
      });
    }
  });
  return data;
});

</script>
