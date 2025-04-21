<template>
  <div class="stage-card-item">
    <div class="card-header">
      <div class="name">{{ stage.name }}</div>
      <div class="status-indicator">
        <Spinner style="color:#3a84f6; font-size: 16px;" />
      </div>
    </div>
    <div class="card-main">
      <div class="text-info">
        <div class="row">
          <div class="label">{{ t('访问地址') }}：</div>
          <div class="value">{{ getStageUrl(stage.name) }}</div>
        </div>
        <div class="row version">
          <div class="label">{{ t('当前资源版本') }}：</div>
          <div class="value">
            <span>{{ stage.resource_version.version || '--' }}</span>
            <span class="suffix">（{{ stage.release.created_by || '--' }} 于 {{
              stage.release.created_time
            }} 发布成功）</span>
          </div>
        </div>
      </div>
      <div class="main-actions">
        <BkButton
          class="mr8"
          size="small"
          theme="primary"
        >
          {{ t('发布资源') }}
        </BkButton>
        <BkButton
          size="small"
        >
          {{ t('下架') }}
        </BkButton>
      </div>
    </div>
    <div class="divider"></div>
    <div class="card-chart">
      <div :class="{ 'empty-state': !data }" class="request-counter">
        <div class="label">{{ t('总请求数') }}</div>
        <div class="value">{{
          data ? requestCount : t('尚未发布，无数据')
        }}
        </div>
      </div>
      <div v-if="data" class="item-chart-wrapper">
        <StageCardLineChart />
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { useI18n } from 'vue-i18n';
import { ref } from 'vue';
import { useCommon } from '@/store';
import { useGetGlobalProperties } from '@/hooks';
import { Spinner } from 'bkui-vue/lib/icon';
import StageCardLineChart from '@/views/stage/overview/comps/stage-card-line-chart.vue';

interface Release {
  status: string;
  created_time: null | string;
  created_by: string;
}

interface ResourceVersion {
  version: string;
  id: number;
  schema_version: string;
}

interface EnvironmentData {
  id: number;
  name: string;
  description: string;
  description_en: string;
  status: number;
  created_time: string;
  release: Release;
  resource_version: ResourceVersion;
  publish_id: number;
  publish_version: string;
  publish_validate_msg: string;
  new_resource_version: string;
}

const { t } = useI18n();
const common = useCommon();

const data = ref(null);
const stage = ref<EnvironmentData>({
  id: 248,
  name: 'prod',
  description: '正式环境',
  description_en: 'Prod',
  status: 0,
  created_time: '2025-04-15 20:08:36 +0800',
  release: {
    status: 'unreleased',
    created_time: null,
    created_by: '',
  },
  resource_version: {
    version: '0.0.3',
    id: 0,
    schema_version: '',
  },
  publish_id: 0,
  publish_version: '0.0.3',
  publish_validate_msg: '网关环境【prod】中的配置【后端服务 default 地址】不合法。请在网关 `后端服务` 中进行配置。',
  new_resource_version: '1.0.3+stag',
});

const requestCount = ref(32334);

const { GLOBAL_CONFIG } = useGetGlobalProperties();

// 访问地址
const getStageUrl = (name: string) => {
  const keys: any = {
    api_name: common.apigwName,
    stage_name: name,
    resource_path: '',
  };

  let url = GLOBAL_CONFIG.STAGE_DOMAIN;
  for (const name of Object.keys(keys)) {
    const reg = new RegExp(`{${name}}`);
    url = url?.replace(reg, keys[name]);
  }
  return url;
};

</script>

<style lang="scss" scoped>

.stage-card-item {
  font-size: 12px;
  background: #fff;
  padding: 16px 24px 8px 44px;
  box-shadow: 0 2px 4px 0 #1919290d;;
  border-radius: 2px;

  &:hover {
    box-shadow: 0 2px 4px 0 #0000001a, 0 2px 4px 0 #1919290d;
  }

  .card-header {
    position: relative;
    margin-bottom: 4px;

    .name {
      font-weight: 700;
      font-size: 16px;
      color: #313238;
      letter-spacing: 0;
      line-height: 22px;
    }

    .status-indicator {
      position: absolute;
      top: 2px;
      left: -22px;
    }
  }

  .card-main {
    .text-info {
      margin-bottom: 12px;

      .row {
        color: #313238;
        font-size: 12px;
        line-height: 28px;
        display: flex;
        align-items: center;

        .value {
          .suffix {
            color: #979ba5;
          }
        }

        &.version {
          .value {
            font-weight: 700;

            .suffix {
              font-weight: normal;
            }
          }
        }
      }
    }
  }

  .divider {
    height: 1px;
    margin-block: 16px;
    background-color: #eaebf0;
  }

  .card-chart {
    height: 60px;
    display: flex;
    justify-content: space-between;

    .request-counter {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 16px;

      .label {
        line-height: 16px;
        color: #63656e;
      }

      .value {
        font-weight: 700;
        font-size: 16px;
        line-height: 18px;
        color: #313238;
      }

      &.empty-state {
        align-items: flex-start;

        .value {
          font-weight: normal;
          font-size: 12px;
          color: #979ba5;
        }
      }
    }
  }
}

</style>
