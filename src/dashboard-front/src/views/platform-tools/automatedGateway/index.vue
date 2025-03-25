<template>
  <div class="platform-tools-automated-guide-page">
    <div class="card-wrapper intro">
      <div class="header-icon-wrapper">
        <ag-icon
          class="icon"
          name="zidongjieru"
          size="64"
        />
      </div>
      <div class="header-title-group">
        <div class="title">{{ t('自动化接入网关') }}</div>
        <div class="sub-title">
          {{
            t('蓝鲸 API 网关提供了 apigw-manager SDK，它是一个用于管理 API 网关的工具，提供了一套完整的工具和功能，可以帮助您更轻松地管理 API 网关，提高系统的安全性和可靠性。')
          }}
        </div>
        <bk-button style="width: 88px;" @click="handleDetailClick">{{ t('查看详情') }}</bk-button>
      </div>
    </div>
    <div class="card-wrapper">
      <div class="title-desc-group">
        <div class="title">Django Command</div>
        <div class="desc">{{
          t('SDK 提供了 Django Command，支持网关注册、同步、发布等功能。' +
            '您可以根据需要编排指令，以满足您的特定需求，并集成到您的项目自动执行 API 网关同步过程，以便更轻松地管理 API 网关。')
        }}
        </div>
      </div>
      <div class="title-desc-group">
        <div class="title">{{ t('Docker 镜像') }}</div>
        <div class="desc">{{
          t('对于非 Django 项目，提供了 Docker 基础镜像，封装了 SDK 同步网关的相关功能，以便非 Django 项目轻松管理 API 网关。')
        }}
        </div>
      </div>
      <div class="title-desc-group">
        <div class="title">{{ t('Django 中间件') }}</div>
        <div class="desc">{{
          t('SDK 还提供了 Django 中间件，' +
            '用于解析 API 网关请求后端接口时添加的请求头 X-Bkapi-JWT，以方便后端服务校验请求是否来自 API 网关。' +
            '这个中间件可以确保只有来自蓝鲸 API 网关的请求才能访问您的后端服务，从而提高系统的安全性。')
        }}
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { useI18n } from 'vue-i18n';
import AgIcon from '@/components/ag-icon.vue';

const { t } = useI18n();

const handleDetailClick = () => {
  window.open('https://github.com/TencentBlueKing/bkpaas-python-sdk/tree/master/sdks/apigw-manager');
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
</style>
