<template>
  <div class="plugin-info">
    <div class="plugin-detail">
      <span class="cur-icon">1</span>
      <div class="cur-text">
        <p class="cur-name">{{ pluginDetail.name }}</p>
        <ul class="cur-binding-info">
          <li>当前版本：<span class="cur-version">V1.0.0</span></li>
          <li>
            已绑定的资源：
            <span class="cur-resource">1</span>
          </li>
          <li>
            已绑定的环境：
            <span class="cur-stage">1</span>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';

const props = defineProps({
  curPlugin: {
    type: Array,
  },
});
const pluginDetail = ref<any>({});
onMounted(() => {
  console.log(props.curPlugin);
  pluginDetail.value = props.curPlugin;
  console.log(pluginDetail.value);
});
// const pluginCodeFirst = computed(() => (code: string) => {
//   console.log(code);

//   return code.charAt(3).toUpperCase();
// });
</script>

<style lang="scss" scoped>
.plugin-info {
  .plugin-detail {
    background-color: #f5f7fb;
    border-radius: 12px;
    padding: 15px 20px;
    display: flex;
    .cur-icon {
      display: inline-block;
      width: 60px;
      height: 60px;
      border-radius: 50%;
      background-color: #EFF1F5;
      color: #3a84f6;
      text-align: center;
      line-height: 60px;
      font-weight: 600;
      font-size: 30px;
      margin-right: 18px;
    }
    .cur-name{
      font-size: 16px;
      font-weight: 600;
      margin-bottom: 5px;
      margin-top: 10px;
    }
    .cur-binding-info{
      display: flex;
      width: 370px;
      justify-content: space-between;
      color: #B9BAC1;
      .cur-version{
        color: #333539;
        font-weight: 600;
      }
    }
  }
}
</style>
