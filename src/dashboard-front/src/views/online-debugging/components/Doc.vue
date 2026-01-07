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
  <div class="component-doc">
    <div class="component-content">
      <div class="component-mate mb-10px">
        <strong
          v-bk-tooltips.top="curComponent.name"
          class="name mr-5px"
        >{{ curComponent.name || '--' }}</strong>
        <span
          v-bk-tooltips.top="{
            content: curComponent.description,
            disabled: !curComponent.description,
            allowHTML: false,
          }"
          class="label"
        >
          ({{ curComponent.description || t('暂无描述') }})
        </span>
      </div>
      <div class="h-24px position-relative">
        <Chat
          v-if="featureFlagStore.flags.ALLOW_CREATE_APPCHAT"
          :default-user-list="userList"
          :owner="curUser.username"
          :name="chatName"
          :content="chatContent"
          is-query
        />
      </div>

      <BkTab
        v-model:active="active"
        class="bk-special-tab"
      >
        <BkTabPanel
          :name="'doc'"
          :label="t('文档')"
        >
          <div class="ag-kv-box mb-30px">
            <div class="kv-row">
              <div class="k">
                {{ t('更新时间') }}：
              </div>
              <div class="v">
                {{ curDocUpdated || '--' }}
              </div>
            </div>
            <div class="kv-row">
              <div class="k">
                {{ t('应用认证') }}：
                <i
                  v-bk-tooltips="t('应用访问该网关API时，是否需提供应用认证信息')"
                  class="ml-5px bk-icon icon-question-circle"
                />
              </div>
              <div class="v">
                {{ curComponent.verified_app_required ? t('是') : t('否') }}
              </div>
            </div>
            <div class="kv-row">
              <div class="k">
                {{ t('用户认证') }}：
                <i
                  v-bk-tooltips="t('应用访问该组件API时，是否需要提供用户认证信息')"
                  class="ml-5px bk-icon icon-question-circle"
                />
              </div>
              <div class="v">
                {{ curComponent.verified_user_required ? t('是') : t('否') }}
              </div>
            </div>
            <div class="kv-row">
              <div class="k">
                {{ t('是否需申请权限') }}：
                <i
                  v-bk-tooltips="t('应用访问该网关API前，是否需要在开发者中心申请该网关API权限')"
                  class="ml-5px bk-icon icon-question-circle"
                />
              </div>
              <div class="v">
                {{ curComponent.allow_apply_permission ? t('是') : t('否') }}
              </div>
            </div>
          </div>
          <!-- eslint-disable-next-line vue/no-v-html -->
          <div
            id="markdown"
            :key="renderHtmlIndex"
            v-bk-xss-html="curComponent.markdownHtml"
            class="ag-markdown-view"
          />
        </BkTabPanel>
      </BkTab>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  useFeatureFlag,
  useGateway,
  useUserInfo,
} from '@/stores';
import { copy } from '@/utils';
import MarkdownIt from 'markdown-it';
import hljs from 'highlight.js';
import {
  getApigwResourceDocDocs,
  getApigwResourceSDKDocs,
  // getApigwSDKDocs,
  getGatewaysDetailsDocs,
} from '@/services/source/docs';
import { getResourcesOnline } from '@/services/source/online-debugging';
import Chat from '@/components/chat/Index.vue';

interface IProps {
  stageName?: string
  stageId?: number
  resourceName?: string
}

const {
  stageName = '',
  stageId = 0,
  resourceName = '',
} = defineProps<IProps>();

const { t } = useI18n();
const userStore = useUserInfo();
const gatewayStore = useGateway();
const featureFlagStore = useFeatureFlag();

const active = ref('doc');
const curComponent = ref({
  id: '',
  name: '',
  label: '',
  content: '',
  innerHtml: '',
  markdownHtml: '',
});
const curApigw = ref({
  name: '',
  label: '',
  maintainers: [],
});
const curDocUpdated = ref('');
const sdkMarkdownHtml = ref('');
const renderHtmlIndex = ref(0);
// const curSdk = ref({});
// const sdks = ref([]);

const curUser = computed(() => userStore.info);
const userList = computed(() => {
  // 去重
  const set = new Set([curUser.value?.username, ...curApigw.value?.maintainers]);
  return [...set];
});
const chatName = computed(() => `${t('[蓝鲸网关API咨询] 网关')}${curApigw.value?.name}`);
const chatContent = computed(() => `${t('网关API文档')}:${location.href}`);
// const SDKInfo = computed(() => t('网关当前环境【{curStageText}】对应的资源版本未生成 SDK，可联系网关负责人生成 SDK', { curStageText: stageName }));

const md = new MarkdownIt({
  linkify: false,
  html: true,
  breaks: true,
  highlight(str: string, lang: string) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return hljs.highlight(lang, str, true).value;
      }
      catch (err) {
        console.error(err);
      }
    }

    return '';
  },
});

const initMarkdownHtml = (box: string) => {
  nextTick(() => {
    const markdownDom = document.getElementById(box);
    // 右侧导航
    // const titles = markdownDom?.querySelectorAll('h3');
    if (box === 'sdk-markdown') {
      // sdkNavList.value = [];
      // const sdkNavArr = [];
      // titles?.forEach((item) => {
      //   const name = String(item?.firstChild?.nodeValue).trim();
      //   const id = slugify(name);
      //   item.id = `${curComponentName.value}?${id}`;
      //   sdkNavArr.push({
      //     id: `${curComponentName.value}?${id}`,
      //     name,
      //   });
      // });
      // sdkNavList.value = sdkNavArr;
    }
    else {
      // componentNavList.value = [];
      // const componentNavArr = [];
      // titles?.forEach((item) => {
      //   const name = String(item?.innerText).trim();
      //   const id = slugify(name);
      //   item.id = `${curComponentName.value}?${id}`;
      //   componentNavArr.push({
      //     id: `${curComponentName.value}?${id}`,
      //     name,
      //   });
      // });
      // componentNavList.value = componentNavArr;
    }

    // 复制代码
    markdownDom?.querySelectorAll('a')?.forEach((item) => {
      item.target = '_blank';
    });
    markdownDom?.querySelectorAll('pre')?.forEach((item) => {
      const parentDiv = document.createElement('div');
      const btn = document.createElement('button');
      const codeBox = document.createElement('div');
      const code = item?.querySelector('code')?.innerText;
      parentDiv.className = 'pre-wrapper';
      btn.className = 'ag-copy-btn';
      codeBox.className = 'code-box';
      btn.innerHTML = '<span title="复制"><i class="apigateway-icon icon-ag-copy-info"></i></span>';
      btn.setAttribute('data-copy', code as string);
      parentDiv?.appendChild(btn);
      codeBox?.appendChild(item?.querySelector('code') as Node);
      item?.appendChild(codeBox);
      item?.parentNode?.replaceChild(parentDiv, item);
      parentDiv?.appendChild(item);
    });

    setTimeout(() => {
      const copyDoms = Array.from(document.getElementsByClassName('ag-copy-btn'));

      const handleCopy = function (this) {
        copy(this.dataset?.copy);
      };

      copyDoms.forEach((dom) => {
        dom.onclick = handleCopy;
      });
    }, 1000);
  });
};

const getApigwAPIDetail = async () => {
  curApigw.value = await getGatewaysDetailsDocs(gatewayStore.currentGateway?.name, { source: 'api_debug' });
};

const getApigwResourceDetail = async () => {
  const query = {
    limit: 10000,
    offset: 0,
  };
  const res = await getResourcesOnline(gatewayStore.currentGateway?.id, stageId, query);

  const match = res?.find((item) => {
    return item.name === resourceName;
  });
  if (match) {
    curComponent.value = {
      ...curComponent.value,
      ...match,
    };
  }
};

const getApigwResourceDoc = async () => {
  const query = {
    stage_name: stageName,
    source: 'api_debug',
  };
  const res = await getApigwResourceDocDocs(gatewayStore.currentGateway?.name, resourceName, query);
  const { content } = res;
  curComponent.value.content = content;
  curComponent.value.markdownHtml = md.render(content);
  renderHtmlIndex.value += 1;
  curDocUpdated.value = res.updated_time;

  initMarkdownHtml('markdown');
};

const getApigwResourceSDK = async () => {
  const query = {
    language: 'python',
    stage_name: stageName,
    resource_name: resourceName,
    source: 'api_debug',
  };
  const res = await getApigwResourceSDKDocs(gatewayStore.currentGateway?.name, query);
  const { content } = res;
  sdkMarkdownHtml.value = md.render(content);
  initMarkdownHtml('sdk-markdown');
};

// const getApigwSDK = async (language: string) => {
// const query = {
//   limit: 10000,
//   offset: 0,
//   language,
// };
// const res = await getApigwSDKDocs(gatewayStore.currentGateway?.name, query);
// sdks.value = res;
// const match = sdks.value?.find(item => item?.stage?.name === stageName);
// curSdk.value = match || {};
// getApigwResourceSDK();
// };

const init = () => {
  getApigwAPIDetail();
  getApigwResourceDetail();
  getApigwResourceDoc();
  getApigwResourceSDK();
};

defineExpose({ init });

</script>

<style lang="scss" scoped>
@use "sass:color";

.simple-side-nav {
  width: 260px;
  height: 100%;
  min-height: 500px;
  background: #fff;
  border-radius: 2px;
  box-shadow: 0 2px 6px 0 rgb(0 0 0 / 10%);

  .metedata {
    position: relative;
    padding: 11px 16px;
    border-bottom: 1px solid #dcdee5;

    .name {
      font-size: 16px;
      color: #313238;
      text-align: left;
    }

    .desc {
      font-size: 12px;
      color: #c4c6cc;
    }

    .more {
      position: absolute;
      top: 15px;
      right: 10px;
      font-size: 24px;
      color: #3a84ff;
      cursor: pointer;
    }
  }

  .component-list-box {

    .span {
      display: block;
      height: 42px;
      padding: 0 21px;
      margin: 7px 0;
      font-size: 14px;
      line-height: 42px;
      color: #63656e;
      text-align: left;

      &.active {
        color: #3a84ff;
        background: #e1ecff;
      }
    }

    .list-data {
      position: relative;
      height: 40px;
      padding: 0 16px;
      font-size: 14px;
      line-height: 40px;
      color: #63656e;
      border-top: 1px solid #f0f1f5;
    }

    .search {
      margin: 0 16px 15px;
    }

    .component-list {
      /* max-height: 1000px;
      overflow: auto; */

      &::-webkit-scrollbar {
        width: 4px;
        background-color: color.scale(#C4C6CC, $lightness: 80%);
      }

      &::-webkit-scrollbar-thumb {
        height: 5px;
        background-color: #c4c6cc;
        border-radius: 2px;
      }

      > li {
        height: 42px;
        padding: 0 16px;
        margin-bottom: 15px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        cursor: pointer;

        &:hover,
        &.active {
          background-color: #e1ecff;

          .name {
            color: #3a84ff;
          }
        }
      }

      .name {
        margin: 2px 0;
        overflow: hidden;
        font-size: 14px;
        line-height: 18px;
        color: #63656e;
        text-align: left;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .label {
        overflow: hidden;
        font-size: 12px;
        line-height: 18px;
        color: #979ba5;
        text-align: left;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
    }
  }
}

.component-content {
  position: relative;
  width: 750px;
  max-height: calc(100vh - 150px);
  min-height: 500px;
  padding: 20px 25px;

  /* 滚动条 */
  overflow-y: auto;
  background: #fff;
  border-radius: 2px;
  box-shadow: 0 2px 6px 0 rgb(0 0 0 / 10%);

  &::-webkit-scrollbar {
    width: 4px;
    background-color: color.scale(#C4C6CC, $lightness: 80%);
  }

  &::-webkit-scrollbar-thumb {
    height: 5px;
    background-color: #c4c6cc;
    border-radius: 2px;
  }

  .component-mate {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;

    .name {
      font-size: 22px;
      line-height: 30px;
      color: #313238;
      text-align: left;
    }

    .label {
      font-size: 14px;
      line-height: 30px;
      color: #63656e;
      text-align: left;
    }
  }
}

.support-btn {
  position: absolute;
  top: 60px;
  right: 26px;
  font-size: 12px;
  color: #3a84ff;
}

.ag-badge {
  position: absolute;
  top: 11px;
  right: 16px;
  display: inline-block;
  height: 18px;
  min-width: 30px;
  padding: 0 5px;
  font-size: 12px;
  line-height: 18px;
  color: #979ba5;
  text-align: center;
  background: #f0f1f5;
  border-radius: 2px;
}

.component-doc {
  display: flex;
}

.component-nav-box {
  height: auto;
  margin-left: 15px;
  flex: 1;

  .component-nav {
    position: fixed;
    width: 160px;
    padding-left: 15px;
    font-size: 12px;
    line-height: 28px;
    color: #979ba5;
    text-align: left;
    border-left: 1px solid #dcdee5;
  }
}

.nav-panel {
  position: absolute;
  top: 0;
  left: 262px;
  z-index: 100;
  width: 870px;
  max-height: 640px;
  min-height: 400px;
  overflow: auto;
  background: #fff;
  border: 1px solid #dcdee5;
  box-shadow: 0 2px 6px 0 rgb(0 0 0 / 10%);

  .category-icon {
    width: 20px;
    height: 20px;
  }

  .version-name {
    height: 32px;
    padding: 0 10px;
    line-height: 32px;

    &:hover {
      min-width: 140px;
      background: #f0f1f5;
      border-radius: 2px;
    }

    > strong {
      font-size: 16px;
      font-weight: normal;
      color: #313238;
    }
  }

  .searcher {
    position: absolute;
    top: 16px;
    right: 16px;
    width: 400px;
  }

  .ag-card {
    padding: 18px 30px 10px;
    margin-top: 0 !important;
    box-shadow: none;

    .systems {

      > li {
        margin-bottom: 10px;
      }
    }
  }
}

.my-menu {
  max-height: calc(100vh - 400px);
  overflow: auto;

  :deep(.icon-angle-right) {
    display: none;
  }

  &::-webkit-scrollbar {
    width: 4px;
    background-color: color.scale(#C4C6CC, $lightness: 80%);
  }

  &::-webkit-scrollbar-thumb {
    height: 5px;
    background-color: #c4c6cc;
    border-radius: 2px;
  }

  .custom-icon {
    display: inline-block;
    margin: -3px 6px 0 0;
    font-size: 13px;
    vertical-align: middle;
  }

  :deep(.bk-collapse-content) {
    padding: 5px 24px;
  }

  .list {
    padding: 0;
    margin: 0;
    list-style: none;

    > li {
      position: relative;
      height: 36px;
      padding-left: 60px;
      font-size: 14px;
      line-height: 36px;
      color: #63656e;
    }
  }
}

.column-key {
  font-size: 14px;
  line-height: 22px;
  color: #63656e;
}

.column-value {
  display: inline-block;
  max-width: 90%;
  overflow: hidden;
  font-size: 14px;
  line-height: 22px;
  color: #313238;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.wrapper {
  padding: 10px 5px;
  margin-top: 10px;
  background: #fafbfd;
}

.ag-doc-icon {
  margin-right: 5px;
  font-size: 16px;
  color: #979ba5;
  cursor: pointer;

  &:hover {
    color: #3a84ff;
  }
}

.select-custom {
  margin-bottom: 10px !important;
  border: none !important;
  border-bottom: 1px solid #f0f1f5 !important;

  &.bk-select.is-focus {
    box-shadow: none;
  }

  :deep(.bk-input) {
    border: none !important;
  }

  :deep(.bk-input--text) {
    padding-left: 0;
    font-size: 14px;
    font-weight: bold;
    color: #63656e;
  }
}

.intro-doc {
  display: flex;
}

:deep(.ag-apigw-select) {

  &.bk-select {
    border: none;

    &.is-focus {
      box-shadow: none;
    }

    &.is-default-trigger.is-unselected::before {
      line-height: 56px;
    }
  }

  .bk-input {
    border: none;
  }

  .bk-input--text {
    height: 56px;
    padding: 0 36px 0 20px;
    font-size: 16px;
    line-height: 56px;
    color: #313238;
  }

  .angle-up {
    top: 10px;
    right: 10px;
    font-size: 26px;
    color: #979ba5;
  }
}

.ag-container {
  display: flex;
  width: 1200px;
  margin: 16px auto 20px;
  align-items: stretch;

  > .left {
    position: relative;
    width: 260px;
    margin-right: 16px;
  }

  > .right {
    flex: 1;
    height: auto;

    > div {
      height: 100%;
    }

    .intro-doc,
    .component-doc {
      height: 100%;
    }

    .version-name {
      padding: 10px 0 15px;
      font-size: 16px;
      font-weight: 700;
      line-height: 21px;
      color: #313238;
      text-align: left;

      svg {
        width: 20px;
        height: 20px;
        margin-right: 3px;
        vertical-align: middle;
      }

      span {
        vertical-align: middle;
      }
    }
  }

  .ag-kv-box {

    .kv-row {
      display: flex;
      font-size: 14px;
      line-height: 30px;

      .k {
        width: 175px;
        color: #979ba5;
        text-align: left;
      }

      .v {
        color: #313238;
      }
    }
  }
}

h3 {
  margin: 16px 0;
  font-weight: bold;
  color: #333;
}

.bk-special-tab.bk-tab {

  :deep(.bk-tab-content) {
    padding-top: 20px;
  }
}

.f16 {
  font-size: 16px !important;
}

.ag-tip {
  display: flex;
  align-items: center;
}

.component-content {
  width: 100%;
  max-height: 100%;
}
</style>
