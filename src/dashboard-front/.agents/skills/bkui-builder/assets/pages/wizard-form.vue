<template>
  <div class="wizard-container">
    <div class="wizard-steps-header mb30">
      <bk-steps :cur-step="currentStep" :steps="stepList" />
    </div>

    <div class="wizard-content card-style">
      <!-- 步骤 1: 基本信息 -->
      <bk-form v-if="currentStep === 1" form-type="vertical">
        <bk-form-item label="任务名称" required>
          <bk-input v-model="form.name" placeholder="输入任务名称" />
        </bk-form-item>
        <bk-form-item label="任务类型">
          <bk-radio-group v-model="form.type">
            <bk-radio label="sync">同步任务</bk-radio>
            <bk-radio label="async">异步任务</bk-radio>
          </bk-radio-group>
        </bk-form-item>
      </bk-form>

      <!-- 步骤 2: 参数配置 -->
      <div v-else-if="currentStep === 2">
        <bk-alert theme="warning" title="请仔细检查参数，错误的参数可能导致执行失败。" class="mb20" />
        <bk-form form-type="vertical">
          <bk-form-item label="并发数">
            <bk-slider v-model="form.concurrency" :max-value="100" />
          </bk-form-item>
          <bk-form-item label="通知邮箱">
            <bk-tag-input v-model="form.emails" placeholder="输入邮箱并回车" />
          </bk-form-item>
        </bk-form>
      </div>

      <!-- 步骤 3: 确认提交 -->
      <div v-else-if="currentStep === 3" class="confirm-view">
        <bk-exception type="empty" scene="part" title="配置确认">
          <div class="summary">
            <p>名称: {{ form.name }}</p>
            <p>并发: {{ form.concurrency }}</p>
          </div>
        </bk-exception>
      </div>
    </div>

    <div class="wizard-footer mt20">
      <bk-button v-if="currentStep > 1" @click="currentStep--">上一步</bk-button>
      <bk-button v-if="currentStep < 3" theme="primary" class="ml10" @click="currentStep++">下一步</bk-button>
      <bk-button v-else theme="success" class="ml10" @click="handleFinish">立即提交</bk-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue';
import { Message } from 'bkui-vue';

const currentStep = ref(1);
const stepList = [
  { title: '基本信息' },
  { title: '参数配置' },
  { title: '确认提交' }
];

const form = reactive({
  name: '',
  type: 'sync',
  concurrency: 20,
  emails: []
});

const handleFinish = () => {
  Message({ theme: 'success', message: '任务已提交' });
};
</script>

<style scoped>
.wizard-container { max-width: 900px; margin: 0 auto; padding: 40px 0; }
.card-style { background: #fff; padding: 30px; border-radius: 2px; box-shadow: 0 2px 4px 0 rgba(0,0,0,0.1); }
.summary { text-align: left; background: #f5f7fa; padding: 15px; display: inline-block; width: 300px; }
.mb30 { margin-bottom: 30px; }
.mb20 { margin-bottom: 20px; }
.mt20 { margin-top: 20px; }
.ml10 { margin-left: 10px; }
</style>
