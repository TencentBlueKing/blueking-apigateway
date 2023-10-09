<script setup lang="ts">
import { useI18n } from 'vue-i18n';
const { t } = useI18n();
</script>

<template>
  <div class="home-container">
    <div class="table-container">
      <div class="table-header flex-row">
        <div class="flex-1 of4">{{t('网关名')}}</div>
        <div class="flex-1 of1">创建者</div>
        <div class="flex-1 of2">环境列表</div>
        <div class="flex-1 of1 text-c">资源数量</div>
        <div class="flex-1 of2">操作</div>
      </div>
      <div class="table-item flex-row align-items-center">
        <div class="flex-1 of4 name">bktest.paaS.xxx.com</div>
        <div class="flex-1 of1">xxx</div>
        <div class="flex-1 of2 env">
          <div class="flex-row env">
            <bk-tag>MagicBox</bk-tag>
            <bk-tag>dev</bk-tag>
            <bk-tag>MagicBox</bk-tag>
            <bk-tag>dev</bk-tag>
          </div>
        </div>
        <div class="flex-1 of1 text-c">0</div>
        <div class="flex-1 of2 ft-12">
          <bk-button
            text
            theme="primary"
          >
            环境概览
          </bk-button>
          <bk-button
            text
            theme="primary"
            class="pl20"
          >
            资源配额
          </bk-button>
          <bk-button
            text
            theme="primary"
            class="pl20"
          >
            流水日志
          </bk-button>
        </div>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.home-container{
  width: 80%;
  margin: 0 auto;
  font-size: 14px;
  padding-top: 27px;
  .table-container{
    width: 100%;
    .table-header{
      width: 100%;
      color: #979BA5;
      padding: 0 16px;
    }
    .table-item{
      width: 100%;
      height: 80px;
      background: #FFFFFF;
      box-shadow: 0 2px 4px 0 #1919290d;
      border-radius: 2px;
      padding: 0 16px;
      margin: 12px 0px;
      cursor: pointer;
      .name{
        font-weight: 700;
        color: #313238;
        &:hover{
          color: #3a84ff;
        }
      }
      .env{
        overflow: hidden;
      }
    }
    .of1{
        flex: 0 0 10%;
      }
      .of2{
        flex: 0 0 20%;
      }
      .of4{
        flex: 0 0 40%;
      }
  }
}
</style>
