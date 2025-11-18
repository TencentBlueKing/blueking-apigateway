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
  <div class="platform-tools-automated-guide-page">
    <div class="card-wrapper intro">
      <div class="header-icon-wrapper">
        <AgIcon
          class="icon"
          name="apigateway-logo"
          size="64"
        />
      </div>
      <div class="header-title-group">
        <div class="title">
          {{ t('蓝鲸微网关') }}
        </div>
        <div class="sub-title">
          {{
            t('蓝鲸微网关是蓝鲸基于最新版 APISIX 定制，提供专业的网关解决方案， 支持官方插件 + 蓝鲸插件 + TAPISIX 插件，满足不同业务能自建网关的需求。')
          }}
        </div>
        <BkButton
          class="w-88px"
          @click="handleDetailClick"
        >
          {{ t('查看详情') }}
        </BkButton>
      </div>
    </div>
    <div class="card-wrapper">
      <div class="title-desc-group">
        <div class="title">
          {{ t('微网关控制面') }}
        </div>
        <div class="desc">
          {{ t(
            '提供了统一的控制面 {url} ，可以统一管理所有数据面。支持所有 APISIX 资源生命周期管理，可以非常方便地对资源进行添加，对比，发布。还支持导入导出，自定义插件等扩展能力。',
            { url: envStore.env.BK_APISIX_URL }) }}
        </div>
      </div>
      <div class="title-desc-group">
        <div class="title">
          {{ t('微网关数据面') }}
        </div>
        <div class="desc">
          {{ t('提供了统一的数据面 helm-chart，可以在 BCS 公共仓库中非常便捷地一键部署 BK-APISIX 数据面，降低部署及维护成本。') }}
          {{ t(
            '具体参考：{url} 使用 BCS（TKEx-IEG 容器平台）helm chart 公共仓库部署',
            { url: envStore.env.BK_APISIX_DOC_URL }) }}
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import AgIcon from '@/components/ag-icon/Index.vue';
import { useEnv } from '@/stores';

const envStore = useEnv();
const { t } = useI18n();

const handleDetailClick = () => {
  window.open(`${envStore.env.BK_APISIX_URL}`);
};

</script>

<style lang="scss" scoped>

.platform-tools-automated-guide-page {
  padding: 24px;

  .card-wrapper {
    background: #fff;
    box-shadow: 0 2px 4px 0 #1919290d;
    border-radius: 2px;
    padding: 24px;

    &:not(:last-child) {
      margin-bottom: 16px;
    }
  }

  .intro {
    display: flex;
    gap: 16px;

    .header-icon-wrapper {
      width: 80px;
      height: 80px;
      background: #f0f5ff;
      border-radius: 8px;
      display: flex;
      justify-content: center;
      align-items: center;

      .icon {
        color: #3a84ff;
      }
    }

    .header-title-group {
      margin-top: 16px;

      .title {
        font-weight: 700;
        font-size: 16px;
        color: #313238;
        line-height: 24px;
        margin-bottom: 8px;
      }

      .sub-title {
        margin-bottom: 22px;
        font-size: 12px;
        color: #4d4f56;
        line-height: 20px;
      }
    }
  }

  .title-desc-group {
    &:not(:last-of-type) {
      margin-bottom: 32px;
    }

    .title {
      font-weight: 700;
      font-size: 14px;
      color: #313238;
      letter-spacing: 0;
      margin-bottom: 12px;
    }

    .desc {
      font-size: 12px;
      color: #4d4f56;
      letter-spacing: 0;
      line-height: 20px;
    }
  }
}
.w-88px {
  width: 88px;
}
</style>
