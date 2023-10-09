<script setup lang="ts">
const columns = [
  {
    label: '网关名',
    type: 'index',
  },
  {
    label: '创建着',
    field: 'ip',
  },
  {
    label: '环境列表',
    field: 'source',
  },
  {
    label: '资源数量',
    field: 'create_time',
  },
  {
    label: '操作',
    field: 'status',
  },
];
const tableData =  [
  {
    ip: '192.168.0.1',
    source: 'QQ',
    status: '创建中',
    create_time: '2018-05-25 15:02:24',
    selected: false,
  },
  {
    ip: '192.168.0.2',
    source: '微信',
    status: '正常',
    create_time: '2018-05-25 15:02:24',
    selected: false,
  },
  {
    ip: '192.168.0.3',
    source: 'QQ',
    status: '创建中',
    create_time: '2018-05-25 15:02:24',
    selected: false,
  },
  {
    ip: '192.168.0.3',
    source: 'QQ',
    status: '创建中',
    create_time: '2018-05-25 15:02:24',
    selected: true,
  },
  {
    ip: '192.168.0.3',
    source: 'QQ',
    status: '创建中',
    create_time: '2018-05-25 15:02:24',
    selected: false,
  },
];
</script>

<template>
  <bk-table
    row-hover="auto"
    :columns="columns"
    :data="tableData"
    show-overflow-tooltip
  />
</template>

<style lang="scss" scoped>

</style>
