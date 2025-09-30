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
  <div class="toolbox-page-wrapper">
    <BkResizeLayout
      placement="left"
      initial-divide="320px"
      :max="320"
      :min="320"
      :border="false"
      collapsible
      style="height: 100%;"
    >
      <template #aside>
        <div class="resize-left-wrapper">
          <article
            v-for="tool in toolList"
            :key="tool.id"
            class="tool-nav-item"
            :class="{ active: tool.id === curTool.id }"
            @click="() => handleToolNavClick(tool)"
          >
            <header class="tool-nav-item-name">
              {{ tool.name }}
            </header>
            <main
              v-bk-tooltips="{ content: tool.desc, disabled: tool.id !== 3 }"
              class="tool-nav-item-desc"
            >
              {{ tool.desc }}
            </main>
          </article>
        </div>
      </template>
      <template #main>
        <div class="main-content-wrap">
          <component :is="toolCompMap[curTool.comp]" />
        </div>
      </template>
    </BkResizeLayout>
  </div>
</template>

<script lang="ts" setup>
import QueryLog from './components/QueryLog.vue';
import JwtDecoder from './components/JwtDecoder.vue';
import JsonFormat from './components/JsonFormat.vue';
import UrlDecoder from './components/UrlDecoder.vue';
import Base64Decoder from './components/Base64Decoder.vue';

interface ITool {
  id: number
  name: string
  desc: string
  comp: string
}

const { t } = useI18n();

const toolCompMap: Record<string, any> = {
  queryLog: QueryLog,
  jwtDecoder: JwtDecoder,
  jsonFormat: JsonFormat,
  urlDecoder: UrlDecoder,
  base64Decoder: Base64Decoder,
};

const toolList = ref([
  {
    id: 1,
    name: t('查询日志'),
    desc: t('根据 request_id 查询日志详情'),
    comp: 'queryLog',
  },
  {
    id: 2,
    name: t('JWT 解析'),
    desc: t('根据 JWT 解析出完整的请求头'),
    comp: 'jwtDecoder',
  },
  {
    id: 3,
    name: t('JSON 格式化'),
    desc: t('对 json 进行格式化及高亮'),
    comp: 'jsonFormat',
  },
  {
    id: 4,
    name: t('URL 解析'),
    desc: t('解析出完整的url'),
    comp: 'urlDecoder',
  },
  {
    id: 5,
    name: t('Base64 解析'),
    desc: t('解析出完整的base64'),
    comp: 'base64Decoder',
  },
]);
const curTool = ref<ITool>(toolList.value[0]);

const handleToolNavClick = (tool: ITool) => {
  curTool.value = tool;
};

</script>

<style lang="scss" scoped>

.toolbox-page-wrapper {
  background-color: #f5f7fa;
  height: calc(100vh - 106px);
}

.resize-left-wrapper {
  padding-block: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  max-height: calc(100% - 24px);
  overflow-y: auto;

  .tool-nav-item {
    width: 288px;
    height: 58px;
    background: #fff;
    box-shadow: 0 2px 4px 0 #1919290d;
    border-radius: 2px;
    padding: 8px 16px;
    cursor: pointer;

    &:hover {
      background: #e1ecff;
    }

    &.active {
      background: #e1ecff;

      .tool-nav-item-name {
        color: #3a84ff;
      }

      .tool-nav-item-desc {
        color: #3a84ff;
      }
    }

    .tool-nav-item-name {
      font-weight: 700;
      font-size: 14px;
      color: #313238;
      line-height: 22px;
    }

    .tool-nav-item-desc {
      font-size: 12px;
      color: #979ba5;
      line-height: 20px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
  }
}

.main-content-wrap {
  padding: 20px 24px 0 32px;
  background-color: #fff;
  height: 100%;
}

// 变更伸缩线样式
:deep(.bk-resizeLayout-left > .bk-resizeLayout-aside) {
  border-right: none;
}

</style>
