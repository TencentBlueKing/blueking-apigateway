<template>
  <bk-dialog
    :is-show="isShow"
    :height="240"
    :theme="'primary'"
    dialog-type="show"
    quick-close
    class="version-dialog-cls"
  >
    <template #header></template>
    <template #default>
      <div class="success-icon flex-row align-items-center">
        <i :class="`icon apigateway-icon icon-ag-${icon}`"></i>
      </div>
      <div class="title pt10 pb20">{{ title }}</div>
      <span class="desc pb10">{{ subTitle }}</span>
      <section class="dialog-footer mt30">
        <bk-button
          theme="primary" class="btn-width" @click="handleComfirm"
          :loading="loading">
          {{ $t('确定') }}
        </bk-button>
        <bk-button class="ml10 btn-width" @click="handleCancel">
          {{ $t('取消') }}
        </bk-button>
      </section>
    </template>
  </bk-dialog>
</template>
<script setup lang="ts">
import { ref, toRefs } from 'vue';

const props = defineProps({
  icon: { type: [String], default: () => 'check-1' },
  isShow: { type: [Boolean], default: () => true },
  title: { type: [String], default: () => 'title' },
  subTitle: { type: [String], default: () => 'subTitle' },
});

const emit = defineEmits(['comfirm', 'cancel']);

const loading = ref(false);

const { isShow, title, subTitle, icon } = toRefs(props);

const handleComfirm = () => {
  loading.value = true;
  emit('comfirm');
  setTimeout(() => {
    loading.value = false;
  }, 1000);
};
const handleCancel = () => {
  emit('cancel');
};
</script>
<style lang="scss" scoped>
  .version-dialog-cls{
    text-align: center;
    :deep(.bk-dialog-header) {
      padding: 0
    }
    :deep(.bk-modal-content) {
      height: calc(100% - 30px) !important;
      max-height: 100vh !important;
      overflow-y: auto;
    }
    .success-icon{
      background: #F2FFF4;
      width: 40px;
      height: 40px;
      border-radius: 50%;
      color: #14A568;
      text-align: center;
      margin: 0 auto;
      i{
        font-size: 40px;
      }
    }
    .title{
      color: #313238;
      font-size: 18px;
    }
    .desc{
      font-size: 14px;
      color:#63656E ;
    }
    .btn-width{
        min-width: 100px;
    }
  }
</style>
