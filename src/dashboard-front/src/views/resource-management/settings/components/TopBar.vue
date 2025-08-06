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
  <div
    class="resource-top-bar"
    :style="stage.getNotUpdatedStages?.length ? 'top: 42px' : 'top: -1px'"
  >
    <div class="top-title-wrapper">
      <div class="title">
        {{ t('资源配置') }}
      </div>
      <div
        v-show="showNewTips"
        class="is-latest"
      >
        {{ t('当前最新资源') }}
      </div>
      <div
        v-show="isDetail && currentSource?.name"
        class="current-resource"
      >
        {{ currentSource?.name }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useStage } from '@/stores';

interface IProps {
  latest?: boolean
  currentSource?: any
  isDetail?: boolean
  showNewTips?: boolean
}

const {
  currentSource = {},
  isDetail = false,
  showNewTips = false,
} = defineProps<IProps>();

const { t } = useI18n();
const stage = useStage();

</script>

<style lang="scss" scoped>
.resource-top-bar {
  position: absolute;
  display: flex;
  width: 100%;
  height: 52px;
  padding: 0 24px;
  background: #FFF;
  box-sizing: border-box;
  align-items: center;
  justify-content: space-between;

  .top-title-wrapper {
    display: flex;
    align-items: center;

    .title {
      margin-right: 8px;
      font-size: 16px;
      color: #313238;
    }

    .is-latest {
      padding: 4px 8px;
      margin-right: 4px;
      font-size: 12px;
      color: #3A84FF;
      background: #EDF4FF;
      border-radius: 2px;
    }

    .current-resource {
      padding: 4px 8px;
      font-size: 12px;
      color: #63656E;
      background: #F0F1F5;
      border-radius: 2px;
    }
  }

  .operate-btn-wrapper {

    .operate-btn,
    .operate-btn-primary {
      height: 26px;
      padding: 0 12px;
      font-size: 12px;

      i {
        margin-right: 4px;
        font-size: 16px;
      }
    }

    .operate-btn {
      color: #63656E;

      &.bk-button.is-disabled {
        color: #dcdee5;
        cursor: not-allowed;
        border-color: #dcdee5;
      }
    }
  }
}

.pure-diff {

  :deep(.diff-main) {
    max-height: calc(100vh - 240px) !important;
  }
}
</style>
