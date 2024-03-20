<script setup lang="ts">
import { useI18n } from 'vue-i18n';

const { t } = useI18n();

// 跳转去外部页面
const handleToExternal = () => {

}
</script>

<template>
  <bk-popover
    placement="bottom"
    theme="light"
    :arrow="false"
    :padding="0"
  >
    <div class="info-icon">
        <span class="icon apigateway-icon icon-ag-help-document-fill"></span>
    </div>
    <template #content>
      <div
        class="info-item"
        @click="handleToExternal"
      >{{t('产品文档')}}</div>
      <div
        class="info-item"
        @click="handleToExternal"
      >{{t('问题反馈')}}</div>
      <div
        class="info-item"
        @click="handleToExternal"
      >{{t('开源社区')}}</div>
    </template>
  </bk-popover>
</template>

<style lang="scss" scoped>
.info-icon {
  cursor: pointer;
  margin-right: 20px;
}
.info-icon:hover {
  color: #fff;
}
.info-item {
  text-align: center;
  cursor: pointer;
  color: #63656E;
  padding: 8px 15px;
  margin-top: 5px;
}
.info-item:hover {
  background: #f3f6f9;
}
.info-item:nth-of-type(1) {
    margin-top: 0px;
}
</style>
