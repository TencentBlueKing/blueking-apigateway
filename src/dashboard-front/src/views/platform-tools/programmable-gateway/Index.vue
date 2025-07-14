<template>
  <div class="platform-tools-automated-guide-page">
    <div class="card-wrapper intro">
      <div class="header-icon-wrapper">
        <AgIcon
          class="icon"
          name="square-program"
          size="64"
        />
      </div>
      <div class="header-title-group">
        <div class="title">
          {{ t('可编程网关') }}
        </div>
        <div class="sub-title">
          {{
            t('蓝鲸可编程网关，是依托于蓝鲸 PaaS 平台， 用户可以基于可编程网关开发框架，通过编码的方式，实现普通网关插件难以实现的一些需求，例如例如封装多个接口调用、接口编排、协议转换等。')
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
          {{ t('可编程网关的理念') }}
        </div>
        <div class="desc">
          {{ t('Code As Gateway Definition， 所有的 API 接口/插件/逻辑以代码为准；运行时自动生成配置注册到 蓝鲸 API 网关。') }}
        </div>
      </div>
      <div class="title-desc-group">
        <div class="title">
          {{ t('可编程网关的能力') }}
        </div>
        <div class="desc">
          <p>{{ t('通过编码，实现自定义逻辑封装，包括多个接口调用，接口编排，协议转换，再次代理等') }}</p>
          <p>{{ t('通过编码，声明网关接口/插件等，自动化注册并发布到蓝鲸 API 网关') }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import AgIcon from '@/components/ag-icon/Index.vue';

const { t } = useI18n();

const handleDetailClick = () => {
  window.open('https://github.com/TencentBlueKing/bk-apigateway-framework/blob/master/docs/design.md');
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
