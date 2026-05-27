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
      :max="880"
      :min="locale === 'en' ? 472 : 360"
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
            :style="{ width: locale === 'en' ? '440px' : '328px'}"
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
import { locale, t } from '@/locales';
import { useFeatureFlag } from '@/stores';
import QueryLog from './components/QueryLog.vue';
import QueryTraceChain from './components/QueryTraceChain.vue';
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

const route = useRoute();
const router = useRouter();
const featureFlagStore = useFeatureFlag();

const toolCompMap: Record<string, any> = {
  queryLog: QueryLog,
  queryTraceChain: QueryTraceChain,
  jwtDecoder: JwtDecoder,
  jsonFormat: JsonFormat,
  urlDecoder: UrlDecoder,
  base64Decoder: Base64Decoder,
};

const toolList = shallowRef([
  {
    id: 1,
    name: t('查询日志'),
    desc: t('根据 request_id 查询日志详情'),
    comp: 'queryLog',
  },
  {
    id: 2,
    name: t('MCP Server 调用链查询'),
    desc: t('根据 request_id 或 x_request_id 查询请求调用链'),
    comp: 'queryTraceChain',
  },
  {
    id: 3,
    name: t('JWT 解析'),
    desc: t('根据 JWT 解析出完整的请求头'),
    comp: 'jwtDecoder',
  },
  {
    id: 4,
    name: t('JSON 格式化'),
    desc: t('对 json 进行格式化及高亮'),
    comp: 'jsonFormat',
  },
  {
    id: 5,
    name: t('URL 解析'),
    desc: t('解析出完整的url'),
    comp: 'urlDecoder',
  },
  {
    id: 6,
    name: t('Base64 解析'),
    desc: t('解析出完整的base64'),
    comp: 'base64Decoder',
  },
].filter((item) => {
  if (item.comp.includes('queryTraceChain')) {
    return featureFlagStore.flags.ENABLE_MCP_SERVER_OBSERVABILITY;
  }
  return true;
}));
const curTool = ref<ITool>(toolList.value[0]);

const handleToolNavClick = (tool: ITool) => {
  curTool.value = tool;
};

watch(() => route.query.toolbox_id, (value) => {
  if (value) {
    curTool.value = toolList.value.find(item => item.id === Number(value)) ?? toolList.value[0];
    router.replace({
      query: {
        ...route.query,
        request_id: undefined,
        toolbox_id: undefined,
      },
    });
  }
}, { immediate: true });
</script>

<style lang="scss" scoped>

.toolbox-page-wrapper {
  height: calc(100vh - 106px);
  background-color: #f5f7fa;
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
    height: 58px;
    padding: 8px 16px;
    cursor: pointer;
    background: #fff;
    border-radius: 2px;
    box-shadow: 0 2px 4px 0 #1919290d;

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
      font-size: 14px;
      font-weight: 700;
      line-height: 22px;
      color: #313238;
    }

    .tool-nav-item-desc {
      overflow: hidden;
      font-size: 12px;
      line-height: 20px;
      color: #979ba5;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
  }
}

.main-content-wrap {
  height: 100%;
  padding: 20px 24px 0 32px;
  background-color: #fff;
}

// 变更伸缩线样式

:deep(.bk-resizeLayout-left > .bk-resizeLayout-aside) {
  border-right: none;
}

</style>
