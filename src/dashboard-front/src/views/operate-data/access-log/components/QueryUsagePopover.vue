/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) Tencent. All rights reserved.
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
  <BkPopover
    trigger="click"
    width="506"
    theme="light"
    placement="bottom"
    ext-cls="access-log-popover"
  >
    <AgIcon
      class="query-usage-trigger"
      name="help"
    />
    <template #content>
      <div class="access-log-search-usage-content">
        <div class="sample">
          <div class="sample-item">
            <p class="mode">
              {{ t("关键字搜索") }}
            </p>
            <p class="value">
              request_id: b3e2497532e54f518b3d1267fb67c83a
              <AgIcon
                v-bk-tooltips="{ content: '引用条件' }"
                name="3-yuan-bohui"
                @click="() => handleClickUsageValue('request_id: b3e2497532e54f518b3d1267fb67c83a')"
              />
            </p>
          </div>
          <div class="sample-item">
            <p class="mode">
              {{ t("多个关键字匹配，支持 OR , AND") }}
            </p>
            <p class="value">
              (app_code: "app-template" AND client_ip: "1.0.0.1") OR resource_name: get_user
              <AgIcon
                v-bk-tooltips="{ content: '引用条件' }"
                name="3-yuan-bohui"
                @click="handleClickUsageValue('')"
              />
            </p>
          </div>
          <div class="sample-item">
            <p class="mode">
              {{ t("排除关键字") }}
            </p>
            <p class="value">
              -status: 200
              <AgIcon
                v-bk-tooltips="{ content: '引用条件' }"
                name="3-yuan-bohui"
                @click="() => handleClickUsageValue('-status: 200')"
              />
            </p>
          </div>
          <div class="sample-item">
            <p class="mode">
              {{ t("配置范围") }}
            </p>
            <p class="value">
              request_duration: [5000 TO 30000]
              <AgIcon
                v-bk-tooltips="{ content: '引用条件' }"
                name="3-yuan-bohui"
                @click="() => handleClickUsageValue('request_duration: [5000 TO 30000]')"
              />
            </p>
          </div>
        </div>
        <div class="more">
          {{ t("更多示例请参阅") }}
          <a
            class="link"
            target="_blank"
            :href="envStore.env.DOC_LINKS.QUERY_USE"
          >
            {{ t("“请求流水查询规则”") }}
          </a>
        </div>
      </div>
    </template>
  </BkPopover>
</template>

<script lang="ts" setup>
import AgIcon from '@/components/ag-icon/Index.vue';
import { useEnv } from '@/stores';

const emit = defineEmits<{
  choose: [data: string]
}>();

const { t } = useI18n();
const envStore = useEnv();

const handleClickUsageValue = (innerText: string) => {
  if (!innerText) {
    innerText = '(app_code: "app-template" AND client_ip: "1.0.0.1") OR resource_name: get_user';
  }
  emit('choose', innerText);
};
</script>

<style lang="scss" scoped>
.query-usage-trigger {
  margin-left: 4px;
  color: inherit;
  cursor: pointer;
  transition: color .2s;
  vertical-align: middle;

  &:hover {
    color: #3A84FF;
  }
}

.access-log-search-usage-content {
  padding: 8px 4px -2px;

  .sample {
    padding-bottom: 12px;
    margin-bottom: 8px;
    border-bottom: 1px solid #DCDEE5;

    .sample-item:not(:nth-last-child(1)) {
      margin-bottom: 16px;
    }

    .mode {
      margin-bottom: 4px;
      font-family: MicrosoftYaHei-Bold;
      font-size: 12px;
      font-weight: bold;
      color: #63656E;
    }

    .value {
      font-size: 12px;
      color: #63656E;

      span {
        margin-left: 2px;
        font-size: 14px;
        color: #3A84FF;
        cursor: pointer;
      }
    }
  }

  .more {
    font-size: 12px;
    color: #63656e;

    .link {
      color: #3a84ff;
      cursor: pointer;
    }
  }
}
</style>
