<template>
  <div class="dashboard-wrapper">
    <bk-container :col="4" :margin="20">
      <bk-row>
        <bk-col v-for="stats in statsList" :key="stats.id">
          <bk-card :title="stats.label" class="stats-card">
            <div class="stats-value">{{ stats.value }}</div>
            <div class="stats-footer">
              较昨日 <span :class="stats.trend">{{ stats.percent }}% ↑</span>
            </div>
          </bk-card>
        </bk-col>
      </bk-row>
    </bk-container>

    <div class="main-content mt20">
      <bk-row :gutter="20">
        <bk-col :span="16">
          <bk-card title="访问趋势">
            <div class="chart-placeholder">
              <bk-loading :loading="loading" title="数据加载中...">
                <div style="height: 300px; display: flex; align-items: center; justify-content: center;">
                  图表渲染区域
                </div>
              </bk-loading>
            </div>
          </bk-card>
        </bk-col>
        <bk-col :span="8">
          <bk-card title="最近操作">
            <bk-timeline :list="timelineList" />
          </bk-card>
        </bk-col>
      </bk-row>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';

const loading = ref(true);

const statsList = ref([
  { id: 1, label: '总活跃用户', value: '12,480', percent: '12', trend: 'up' },
  { id: 2, label: '今日请求量', value: '84,200', percent: '5', trend: 'up' },
  { id: 3, label: '告警事件', value: '3', percent: '2', trend: 'down' },
  { id: 4, label: '资源占用率', value: '65%', percent: '1', trend: 'up' }
]);

const timelineList = ref([
  { tag: '2024-03-20', content: '系统内核升级完成' },
  { tag: '2024-03-19', content: '新增 5 台集群节点' }
]);

onMounted(() => {
  setTimeout(() => (loading.value = false), 1000);
});
</script>

<style scoped>
.dashboard-wrapper { padding: 20px; background: #f5f7fa; }
.stats-card { text-align: center; }
.stats-value { font-size: 28px; font-weight: bold; padding: 10px 0; color: #313238; }
.stats-footer { font-size: 12px; color: #979ba5; }
.up { color: #2dcb56; }
.down { color: #ea3636; }
.mt20 { margin-top: 20px; }
</style>
