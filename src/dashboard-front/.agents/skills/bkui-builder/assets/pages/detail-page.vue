<template>
  <div class="detail-page">
    <!-- 状态概览栏 -->
    <bk-card class="mb20" :border="false">
      <div class="status-header">
        <div class="status-left">
          <h2 class="title">单据详情: #REQ-20231201</h2>
          <bk-tag theme="success">执行成功</bk-tag>
        </div>
        <div class="status-steps">
          <bk-steps :cur-step="3" :steps="steps" />
        </div>
      </div>
    </bk-card>

    <!-- 分组详情 -->
    <bk-collapse v-model="activePanels" class="info-collapse">
      <bk-collapse-panel name="basic">
        基本信息
        <template #content>
          <bk-container :col="2" :margin="0">
            <bk-row class="mb10">
              <bk-col :span="1"><span class="label">申请人：</span>admin</bk-col>
              <bk-col :span="1"><span class="label">申请时间：</span>2023-12-01 10:00:00</bk-col>
            </bk-row>
            <bk-row>
              <bk-col :span="1"><span class="label">所属业务：</span>王者荣耀</bk-col>
              <bk-col :span="1"><span class="label">备注：</span>无</bk-col>
            </bk-row>
          </bk-container>
        </template>
      </bk-collapse-panel>

      <bk-collapse-panel name="log">
        执行记录
        <template #content>
          <bk-timeline :list="timelineList" />
        </template>
      </bk-collapse-panel>
    </bk-collapse>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

const activePanels = ref(['basic', 'log']);

const steps = [
  { title: '提交申请' },
  { title: '审批通过' },
  { title: '执行完成' },
];

const timelineList = [
  { tag: '2023-12-01 10:05', content: '审批通过', type: 'success' },
  { tag: '2023-12-01 10:00', content: '用户提交申请', type: 'primary' },
];
</script>

<style scoped>
.detail-page {
  padding: 20px;
}

.status-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
}

.title {
  display: inline-block;
  margin-right: 10px;
  font-size: 18px;
  color: #313238;
}

.status-steps {
  width: 400px;
}

.label {
  color: #979ba5;
  display: inline-block;
  width: 80px;
  text-align: right;
}

.mb20 { margin-bottom: 20px; }
.mb10 { margin-bottom: 10px; }
</style>
