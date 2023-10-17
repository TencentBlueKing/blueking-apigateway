<template>
  <div class="release-sideslider">
    <bk-sideslider
      v-model:isShow="isShow"
      :width="1050"
      title="发布资源至环境"
      quick-close
    >
      <template #default>
        <div class="sideslider-content">
          <div class="top-steps">
            <bk-steps
              :controllable="stepsConfig.controllable"
              :cur-step="stepsConfig.curStep"
              :steps="stepsConfig.objectSteps"
            />
          </div>
          <div class="main">
            <template v-if="stepsConfig.curStep === 1">
              <bk-alert
                theme="info"
                title="当前版本号"
                class="mt15 mb15"
                closable
              />
              <bk-form
                class="example"
                form-type="vertical"
              >
                <bk-form-item label="发布的资源版本">
                  <bk-input
                    placeholder="请输入"
                    clearable
                  />
                  <p slot="tip">
                    新增
                    <span class="add">1</span>
                    个，更新
                    <span class="update">1</span>
                    个， 删除
                    <span class="delete">3</span>
                    个
                  </p>
                </bk-form-item>
                <bk-form-item label="版本日志">
                  <bk-input
                    v-model="versionLog"
                    type="textarea"
                    :rows="4"
                    :maxlength="100"
                  />
                </bk-form-item>
              </bk-form>
            </template>
            <template v-else>
                对比
            </template>
            <div class="operate">
              <bk-button
                v-if="stepsConfig.curStep === 1"
                theme="primary"
                style="width: 100px"
                @click="handleNext"
              >
                下一步
              </bk-button>
              <template v-else-if="stepsConfig.curStep === 2">
                <bk-button
                  theme="primary"
                  style="width: 100px"
                >
                  确认发布
                </bk-button>
                <bk-button
                  class="ml10"
                  style="width: 100px"
                  @click="handleBack"
                >
                  上一步
                </bk-button>
              </template>
              <bk-button
                class="ml10"
                style="width: 100px"
                @click="handleCancel"
              >
                取消
              </bk-button>
            </div>
          </div>
        </div>
      </template>
    </bk-sideslider>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

const isShow = ref(false);

// 版本日志
const versionLog = ref('');

const stepsConfig = ref({
  objectSteps: [{ title: '发布信息' }, { title: '差异确认' }],
  curStep: 1,
  controllable: true,
});

// 显示侧边栏
const showReleaseSideslider = () => {
  isShow.value = true;
};

// 下一步
const handleNext = () => {
  stepsConfig.value.curStep = 2;
};

// 上一步
const handleBack = () => {
  stepsConfig.value.curStep = 1;
};

// 取消
const handleCancel = () => {
  isShow.value = false;
};

defineExpose({
  showReleaseSideslider,
});
</script>

<style lang="scss" scoped>
.sideslider-content {
  width: 100%;
  .top-steps {
    width: 100%;
    padding: 16px 300px;
    border-bottom: 1px solid #dcdee5;
  }
  .main {
    padding: 0 80px;

    .add {
      color: #34d97b;
    }
    .update {
      color: #ffb400;
    }
    .delete {
      color: #ff5656;
    }
  }
}
</style>
