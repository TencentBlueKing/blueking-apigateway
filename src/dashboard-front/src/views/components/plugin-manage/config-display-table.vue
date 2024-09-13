<template>
  <!--  插件配置展示态组件  -->
  <component
    :is="tableComponent"
    :plugin="plugin"
    :cell-style="getFirstColCellStyle"
    :border="['outer', 'col']"
  />
</template>

<script setup lang="ts">
import {
  computed,
  toRefs,
} from 'vue';
import type { Component } from 'vue';
import ConfigDisplayTableHeaderRewrite from '@/views/components/plugin-manage/config-display-table-header-rewrite.vue';
import ConfigDisplayTableRateLimit from '@/views/components/plugin-manage/config-display-table-rate-limit.vue';
import ConfigDisplayTableIpRestriction from '@/views/components/plugin-manage/config-display-table-ip-restriction.vue';
import ConfigDisplayTableGeneric from '@/views/components/plugin-manage/config-display-table-generic.vue';
import {
  IColumn,
  IPlugin,
} from '@/views/components/plugin-manage/types';

interface IProps {
  plugin: IPlugin<unknown>
}

// Header转换插件、频率控制插件、IP访问限制插件配置展示表格
const tableComponentMap: { [key: string]: Component } = {
  'bk-header-rewrite': ConfigDisplayTableHeaderRewrite,
  'bk-rate-limit': ConfigDisplayTableRateLimit,
  'bk-ip-restriction': ConfigDisplayTableIpRestriction,
};

const props = withDefaults(defineProps<IProps>(), {
  plugin: () => ({
    code: '',
    config_id: 0,
    name: '',
    config: {},
  }),
});

const { plugin } = toRefs(props);

// 根据 code 或 type 动态获取表格组件
const tableComponent = computed(() => {
  return tableComponentMap[plugin.value.code || plugin.value.type] || ConfigDisplayTableGeneric;
});

// 给表格最左列一个背景色
const getFirstColCellStyle = (col: IColumn) => {
  return col.index === 0 ? { backgroundColor: '#fafbfd' } : {};
};

</script>
