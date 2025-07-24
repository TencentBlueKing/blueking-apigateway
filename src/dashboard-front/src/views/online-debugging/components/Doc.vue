<template>
  <div class="component-doc">
    <div class="component-content">
      <div class="component-mate mb10">
        <strong
          v-bk-tooltips.top="curComponent.name"
          class="name mr5"
        >{{ curComponent.name || '--' }}</strong>
        <span
          v-bk-tooltips.top="{ content: curComponent.description, allowHTML: false }"
          class="label"
        >
          ({{ curComponent.description || t('暂无描述') }})
        </span>
      </div>
      <div style="position: relative;">
        <chat
          v-if="userStore.featureFlags?.ALLOW_CREATE_APPCHAT"
          class="ag-chat"
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
          <div class="ag-kv-box mb30">
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
                  class="ml5 bk-icon icon-question-circle"
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
                  class="ml5 bk-icon icon-question-circle"
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
                  class="ml5 bk-icon icon-question-circle"
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
            v-dompurify-html="curComponent.markdownHtml"
            class="ag-markdown-view"
          />
        </BkTabPanel>
        <!-- <BkTabPanel
          :name="'sdk'"
          :label="t('SDK及示例')"
          v-if="userStore.featureFlags?.ENABLE_SDK"
          >
          <div id="sdk-markdown">
          <div class="bk-button-group">
          <BkButton class="is-selected">Python</BkButton>
          </div>

          <h3 class="f16">
          {{ t('SDK信息-doc') }}
          <span class="ag-tip ml10" v-if="!curSdk?.sdk?.version">
          ({{ SDKInfo }})
          </span>
          </h3>

          <div>
          <sdk-detail :params="curSdk" :is-apigw="true"></sdk-detail>
          </div>

          <h3 class="f16 mt20"> {{ t('SDK使用样例') }} </h3>
          <div class="ag-markdown-view mt20" :key="renderHtmlIndex" v-dompurify-html="sdkMarkdownHtml"></div>
          </div>
          </BkTabPanel> -->
      </BkTab>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useGateway, useUserInfo } from '@/stores';
import { copy } from '@/utils';
import MarkdownIt from 'markdown-it';
import hljs from 'highlight.js';
import {
  getApigwResourceDocDocs,
  getApigwResourceSDKDocs,
  getApigwResourcesDocs,
  getApigwSDKDocs,
  getGatewaysDetailsDocs,
} from '@/services/source/docs';

interface IProps {
  stageName?: string
  resourceName?: string
}

const {
  stageName = '',
  resourceName = '',
} = defineProps<IProps>();

const { t } = useI18n();
const userStore = useUserInfo();
const gatewayStore = useGateway();

const curSdk = ref({});
const active = ref<string>('doc');
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
const curDocUpdated = ref<string>('');
const sdkMarkdownHtml = ref<string>('');
const renderHtmlIndex = ref<number>(0);
const sdks = ref([]);

const curUser = computed(() => userStore?.user);
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
  try {
    const res = await getGatewaysDetailsDocs(gatewayStore.currentGateway?.name);
    curApigw.value = res;
  }
  catch (e) {
    console.log(e);
  }
};

const getApigwResourceDetail = async () => {
  try {
    const query = {
      limit: 10000,
      offset: 0,
      stage_name: stageName,
    };
    const res = await getApigwResourcesDocs(gatewayStore.currentGateway?.name, query);

    const match = res?.find((item) => {
      return item.name === resourceName;
    });
    if (match) {
      curComponent.value = {
        ...curComponent.value,
        ...match,
      };
    }
  }
  catch (e) {
    console.log(e);
  }
};

const getApigwResourceDoc = async () => {
  try {
    const query = { stage_name: stageName };
    const res = await getApigwResourceDocDocs(gatewayStore.currentGateway?.name, resourceName, query);
    const { content } = res;
    curComponent.value.content = content;
    curComponent.value.markdownHtml = md.render(content);
    renderHtmlIndex.value += 1;
    curDocUpdated.value = res.updated_time;

    initMarkdownHtml('markdown');
  }
  catch (e) {
    console.log(e);
  }
  finally {
  }
};

const getApigwResourceSDK = async () => {
  try {
    const query = {
      language: 'python',
      stage_name: stageName,
      resource_name: resourceName,
    };
    const res = await getApigwResourceSDKDocs(gatewayStore.currentGateway?.name, query);
    const { content } = res;
    sdkMarkdownHtml.value = md.render(content);
    initMarkdownHtml('sdk-markdown');
  }
  catch (e) {
    console.log(e);
  }
};

const getApigwSDK = async (language: string) => {
  try {
    const query = {
      limit: 10000,
      offset: 0,
      language,
    };
    const res = await getApigwSDKDocs(gatewayStore.currentGateway?.name, query);
    sdks.value = res;
    const match = sdks.value?.find(item => item?.stage?.name === stageName);
    curSdk.value = match || {};
    getApigwResourceSDK();
  }
  catch (e) {
    console.log(e);
  }
};

const init = () => {
  getApigwAPIDetail();
  getApigwResourceDetail();
  getApigwResourceDoc();
  getApigwSDK('python');
};
init();
</script>

<style lang="scss" scoped>
@use "sass:color";

.simple-side-nav {
  width: 260px;
  min-height: 500px;
  height: 100%;
  background: #fff;
  box-shadow: 0 2px 6px 0 rgba(0, 0, 0, 0.1);
  border-radius: 2px;

  .metedata {
    padding: 11px 16px;
    position: relative;
    border-bottom: 1px solid #dcdee5;

    .name {
      font-size: 16px;
      text-align: left;
      color: #313238;
    }

    .desc {
      font-size: 12px;
      color: #c4c6cc;
    }

    .more {
      position: absolute;
      font-size: 24px;
      right: 10px;
      top: 15px;
      cursor: pointer;
      color: #3a84ff;
    }
  }

  .component-list-box {
    .span {
      height: 42px;
      line-height: 42px;
      margin: 7px 0;
      padding: 0 21px;
      display: block;
      font-size: 14px;
      text-align: left;
      color: #63656e;

      &.active {
        background: #e1ecff;
        color: #3a84ff;
      }
    }

    .list-data {
      height: 40px;
      line-height: 40px;
      font-size: 14px;
      color: #63656e;
      padding: 0 16px;
      position: relative;
      border-top: 1px solid #f0f1f5;
    }

    .search {
      margin: 0 16px 15px 16px;
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
        border-radius: 2px;
        background-color: #c4c6cc;
      }

      > li {
        height: 42px;
        padding: 0 16px;
        cursor: pointer;
        margin-bottom: 15px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;

        &:hover,
        &.active {
          background-color: #e1ecff;

          .name {
            color: #3a84ff;
          }
        }
      }

      .name {
        font-size: 14px;
        text-align: left;
        color: #63656e;
        line-height: 18px;
        margin: 2px 0;
        overflow: hidden;
        white-space: nowrap;
        text-overflow: ellipsis;
      }

      .label {
        font-size: 12px;
        text-align: left;
        color: #979ba5;
        line-height: 18px;
        overflow: hidden;
        white-space: nowrap;
        text-overflow: ellipsis;
      }
    }
  }
}

.component-content {
  width: 750px;
  min-height: 500px;
  background: #fff;
  padding: 20px 25px;
  position: relative;
  border-radius: 2px;
  box-shadow: 0px 2px 6px 0px rgba(0, 0, 0, 0.1);

  /* 滚动条 */
  overflow-y: auto;
  max-height: calc(100vh - 150px);

  &::-webkit-scrollbar {
    width: 4px;
    background-color: color.scale(#C4C6CC, $lightness: 80%);
  }

  &::-webkit-scrollbar-thumb {
    height: 5px;
    border-radius: 2px;
    background-color: #c4c6cc;
  }

  .component-mate {
    text-overflow: ellipsis;
    overflow: hidden;
    white-space: nowrap;

    .name {
      font-size: 22px;
      text-align: left;
      color: #313238;
      line-height: 30px;
    }

    .label {
      font-size: 14px;
      text-align: left;
      color: #63656e;
      line-height: 30px;
    }
  }
}

.support-btn {
  position: absolute;
  font-size: 12px;
  color: #3a84ff;
  top: 60px;
  right: 26px;
}

.ag-badge {
  min-width: 30px;
  height: 18px;
  background: #f0f1f5;
  border-radius: 2px;
  font-size: 12px;
  color: #979ba5;
  display: inline-block;
  line-height: 18px;
  text-align: center;
  padding: 0 5px;
  position: absolute;
  right: 16px;
  top: 11px;
}

.component-doc {
  display: flex;
}

.component-nav-box {
  margin-left: 15px;
  height: auto;
  flex: 1;

  .component-nav {
    width: 160px;
    padding-left: 15px;
    font-size: 12px;
    text-align: left;
    color: #979ba5;
    line-height: 28px;
    border-left: 1px solid #dcdee5;
    position: fixed;
  }
}

.nav-panel {
  min-height: 400px;
  position: absolute;
  left: 262px;
  top: 0;
  overflow: auto;
  z-index: 100;
  width: 870px;
  max-height: 640px;
  background: #fff;
  border: 1px solid #dcdee5;
  box-shadow: 0px 2px 6px 0px rgba(0, 0, 0, 0.1);

  .category-icon {
    width: 20px;
    height: 20px;
  }

  .version-name {
    line-height: 32px;
    height: 32px;
    padding: 0 10px;

    &:hover {
      min-width: 140px;
      background: #f0f1f5;
      border-radius: 2px;
    }

    > strong {
      font-size: 16px;
      color: #313238;
      font-weight: normal;
    }
  }

  .searcher {
    width: 400px;
    position: absolute;
    right: 16px;
    top: 16px;
  }

  .ag-card {
    box-shadow: none;
    margin-top: 0 !important;
    padding: 18px 30px 10px 30px;

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
    border-radius: 2px;
    background-color: #c4c6cc;
  }

  .custom-icon {
    margin: -3px 6px 0 0;
    font-size: 13px;
    vertical-align: middle;
    display: inline-block;
  }

  :deep(.bk-collapse-content) {
    padding: 5px 24px;
  }

  .list {
    list-style: none;
    margin: 0;
    padding: 0;

    > li {
      font-size: 14px;
      height: 36px;
      line-height: 36px;
      padding-left: 60px;
      position: relative;
      color: #63656e;
    }
  }
}

.column-key {
  font-size: 14px;
  color: #63656e;
  line-height: 22px;
}

.column-value {
  font-size: 14px;
  color: #313238;
  line-height: 22px;
  white-space: nowrap;
  text-overflow: ellipsis;
  overflow: hidden;
  max-width: 90%;
  display: inline-block;
}

.wrapper {
  margin-top: 10px;
  padding: 10px 5px;
  background: #fafbfd;
}

.ag-doc-icon {
  font-size: 16px;
  color: #979ba5;
  cursor: pointer;
  margin-right: 5px;

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
    font-weight: bold;
    color: #63656e;
    font-size: 14px;
    padding-left: 0;
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

    &.is-default-trigger.is-unselected:before {
      line-height: 56px;
    }
  }

  .bk-input {
    border: none;
  }

  .bk-input--text {
    font-size: 16px;
    color: #313238;
    height: 56px;
    padding: 0 36px 0 20px;
    line-height: 56px;
  }

  .angle-up {
    right: 10px;
    top: 10px;
    color: #979ba5;
    font-size: 26px;
  }
}

.ag-container {
  width: 1200px;
  display: flex;
  margin: 16px auto 20px auto;
  align-items: stretch;

  > .left {
    width: 260px;
    margin-right: 16px;
    position: relative;
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
      font-size: 16px;
      font-weight: 700;
      text-align: left;
      color: #313238;
      line-height: 21px;
      padding: 10px 0 15px 0;

      svg {
        width: 20px;
        height: 20px;
        vertical-align: middle;
        margin-right: 3px;
      }

      span {
        vertical-align: middle;
      }
    }
  }

  .ag-kv-box {
    .kv-row {
      font-size: 14px;
      line-height: 30px;
      display: flex;

      .k {
        width: 175px;
        text-align: left;
        color: #979ba5;
      }

      .v {
        color: #313238;
      }
    }
  }
}

h3 {
  font-weight: bold;
  color: #333;
  margin: 16px 0px;
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
