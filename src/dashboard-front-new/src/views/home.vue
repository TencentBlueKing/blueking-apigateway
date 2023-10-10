<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import {
  ref,
} from 'vue';
const { t } = useI18n();

const filterKey = ref('updated_time');
const isShowAdd = ref(false);
const formData = ref({
  name: '',
  user: '',
  desc: '',
  isopen: false,
});

const curYear = (new Date()).getFullYear();

const filterData = ref([
  { value: 'created_time', label: t('创建时间') },
  { value: 'updated_time', label: t('更新时间') },
  { value: 'name', label: t('字母 A-Z') },
]);

// 新建网关弹窗
const showAddDialog = () => {
  isShowAdd.value = true;
};
</script>

<template>
  <div class="home-container">
    <div class="title-container flex-row justify-content-between">
      <div class="flex-1 left">{{ t('我的网关') }} (3)</div>
      <div class="flex-1 flex-row">
        <bk-button
          theme="primary"
          @click="showAddDialog"
        >
          {{ t('新建网关') }}
        </bk-button>
        <bk-input class="ml10 mr10 search-input" placeholder="请输入网关名"></bk-input>
        <bk-select
          v-model="filterKey"
        >
          <bk-option v-for="(item, index) in filterData" :key="index" :value="item.value" :label="item.label" />
        </bk-select>
      </div>
    </div>
    <div class="table-container">
      <div class="table-header flex-row">
        <div class="flex-1 of4">{{t('网关名')}}</div>
        <div class="flex-1 of1">创建者</div>
        <div class="flex-1 of2">环境列表</div>
        <div class="flex-1 of1 text-c">资源数量</div>
        <div class="flex-1 of2">操作</div>
      </div>
      <div class="table-item flex-row align-items-center">
        <div class="flex-1 flex-row align-items-center of4">
          <div class="name-logo mr10">
            B
          </div>
          <span class="name">bktest.paaS.xxx.com</span>
          <bk-tag theme="info" class="ml10">{{ t('官方') }}</bk-tag>
          <bk-tag theme="warning">{{ t('专享') }}</bk-tag>
        </div>
        <div class="flex-1 of1">xxx</div>
        <div class="flex-1 of2 env">
          <div class="flex-row">
            <bk-tag>MagicBox</bk-tag>
            <bk-tag>dev</bk-tag>
            <bk-tag>MagicBox</bk-tag>
            <bk-tag>dev</bk-tag>
          </div>
        </div>
        <div class="flex-1 of1 text-c">0</div>
        <div class="flex-1 of2">
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
    <div class="footer-container">
      <div>
        <bk-link theme="primary">技术支持</bk-link> | <bk-link theme="primary">产品官网</bk-link>
      </div>
      Copyright © 2012-{{curYear}} Tencent BlueKing. All Rights Reserved.
    </div>

    <bk-dialog
      v-model:is-show="isShowAdd"
      width="600"
      :title="t('新建网关')"
      theme="primary"
      quick-close>
      <bk-form ref="formRef" form-type="vertical" :model="formData">
        <bk-form-item
          label="名称"
          property="name"
          required
        >
          <bk-input
            v-model="formData.name"
            placeholder="请输入"
            clearable
          />
        </bk-form-item>
        <bk-form-item
          label="维护人员"
          property="name"
          required
        >
          <bk-input
            v-model="formData.name"
            placeholder="请输入"
            clearable
          />
        </bk-form-item>
        <bk-form-item
          label="描述"
          property="name"
          required
        >
          <bk-input
            type="textarea"
            v-model="formData.name"
            placeholder="请输入"
            clearable
          />
        </bk-form-item>
        <bk-form-item
          label="是否公开"
          property="isopen"
          required
        >
          <bk-switcher v-model="formData.isopen" />
          <span class="common-form-tips">公开，则用户可查看资源文档、申请资源权限；不公开，则网关对用户隐藏</span>
        </bk-form-item>
      </bk-form>
    </bk-dialog>
  </div>
</template>

<style lang="scss" scoped>
.home-container{
  width: 80%;
  margin: 0 auto;
  font-size: 14px;
  .title-container{
    width: 100%;
    padding: 28px 16px;
    .left{
      font-size: 20px;
      color: #313238;
      flex: 0 0 60%;
    }
  }
  .table-container{
    width: 100%;
    height: calc(100vh - 192px);
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
      .name-logo{
        width: 48px;
        height: 48px;
        line-height: 48px;
        text-align: center;
        background: #F0F5FF;
        border-radius: 4px;
        color: #3A84FF;
        font-size: 26px;
        font-weight: 700;
      }
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

  .footer-container{
    text-align: center;
    height: 52px;
  }
}
</style>
