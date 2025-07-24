/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2025 Tencent. All rights reserved.
 * Licensed under the MIT License (the "License"); you may not use this file except
 * in compliance with the License. You may obtain a copy of the License at
 *
 *     http://opensource.org/licenses/MIT
 *
 * Unless required by applicable law or agreed to in writing, software distributed under
 * the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
 * either express or implied. See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * We undertake not to change the open source license (MIT license) applicable
 * to the current version of the project delivered to anyone in the future.
 */
<template>
  <div class="apigw-component-api-wrapper">
    <div class="title">
      {{ t('蓝鲸 API 网关(API Gateway) 是蓝鲸体系的 API 托管服务。') }}
      {{ t('可以帮助开发者创建、发布、维护，和保护 API，以快速、低成本、低风险地开放系统的数据或服务。') }}
      {{ t('API 网关支持“自助配置接入”和“组件编码接入”两种方式，并提供了统一的用户认证、蓝鲸应用鉴权、请求转发、日志记录等功能。') }}
      {{ t('“自助配置接入”采用网关的方案，具体请参考“我的网关”，“组件编码接入”采用组件 API 的方案。') }}
    </div>
    <div class="item">
      <label>{{ t('API 网关接入方式描述') }}</label>
      <div class="content">
        <div> {{ t('自助配置接入：在“我的网关”中，在线配置接口信息，提供 API 服务。适用于将 HTTP 协议接口直接对接的场景。') }} </div>
        <div> {{ t('组件编码接入：编码组件逻辑，并通过注册系统及组件，提供 API 服务。适用于需自定义处理逻辑的场景。') }} </div>
      </div>
    </div>
    <div class="item">
      <label class="m-b-10px!">
        {{ t('组件编码接入流程') }}
      </label>
      <div class="content">
        <div
          v-for="(item, index) in flowList"
          :key="item.text"
          v-bk-tooltips="item.tips"
          class="flow-item"
          :class="[{ ml: index > 0 }]"
        >
          {{ item.text }}
          <div
            v-if="index < flowList.length - 1"
            class="flow-arrow"
          >
            <span />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
const { t } = useI18n();

const flowList = ref([
  {
    text: t('编码具体组件逻辑'),
    tips: t('根据需求编码组件逻辑'),
  },
  {
    text: t('注册系统'),
    tips: t('点击\'系统管理\'，注册组件所需系统'),
  },
  {
    text: t('添加组件'),
    tips: t('点击\'组件管理\'，注册编码的组件信息'),
  },
  {
    text: t('重启服务'),
    tips: t('按指令\'重启服务\''),
  },
  {
    text: t('完成'),
    tips: t('完成接入'),
  },
]);
</script>

<style lang="scss" scoped>
.apigw-component-api-wrapper {
  padding: 20px;
  width: 1030px;
  font-size: 14px;
  color: #63656e;

  .item {
    margin: 15px 0;

    label {
      display: block;
      margin-bottom: 5px;
      color: #313238;
    }
  }

  .flow-item {
    position: relative;
    display: inline-block;
    width: 150px;
    height: 50px;
    line-height: 50px;
    background: #dff0d8;
    border: 1px solid #ddd;
    text-align: center;

    &.ml {
      margin-left: 60px;
    }

    .flow-arrow {
      position: absolute;
      top: 50%;
      right: -61px;
      left: auto;
      margin-top: -5px;
      width: 60px;

      span {
        display: block;
        border: 5px solid transparent;
        border-left: 10px solid #ddd;
        border-right: none;
        width: 0;
        height: 0;
        float: right;

        &::before {
          display: block;
          content: " ";
          position: absolute;
          left: 0;
          top: 0;
          right: 10px;
          margin-top: 4px;
          border-top-width: 2px;
          border-top-style: solid;
          border-top-color: #ddd;
        }
      }
    }
  }
}
</style>
