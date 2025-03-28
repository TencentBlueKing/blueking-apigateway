<template>
  <div class="toolbox-page-wrapper">
    <bk-resize-layout
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
            class="tool-nav-item"
            v-for="tool in toolList"
            :key="tool.id"
            :class="{ active: tool.id === curTool.id }"
            @click="handleToolNavClick(tool)"
          >
            <header class="tool-nav-item-name">{{ tool.name }}</header>
            <main class="tool-nav-item-desc" v-bk-tooltips="{ content: tool.desc, disabled: tool.id !== 3 }">
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
    </bk-resize-layout>
  </div>
</template>

<script lang="ts" setup>
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';
import QueryLog from './components/query-log.vue';
import JwtDecoder from './components/jwt-decoder.vue';
import JsonFormat from './components/json-format.vue';

interface ITool {
  id: number;
  name: string;
  desc: string;
  comp: string;
}

const { t } = useI18n();

const toolCompMap: Record<string, any> = {
  queryLog: QueryLog,
  jwtDecoder: JwtDecoder,
  jsonFormat: JsonFormat,
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
:deep(.bk-resize-layout-left > .bk-resize-layout-aside) {
  border-right: none;
}

</style>
