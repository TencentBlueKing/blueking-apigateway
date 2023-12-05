<template>
  <div class="component-doc">
    <div class="component-content">
      <div class="component-metedata mb10">
        <strong class="name mr5" v-bk-tooltips.top="curComponent.name">{{ curComponent.name }}</strong>
        <span class="label" v-bk-tooltips.top-start="{ content: curComponent.description, allowHTML: false }">
          {{ curComponent.description || t('暂无描述') }}
        </span>
      </div>

      <div style="position: relative;">
        <bk-breadcrumb separator-class="bk-icon icon-angle-right" class="mb20">
          <bk-breadcrumb-item :to="{ name: 'componentDoc' }">{{ t('组件API文档') }}</bk-breadcrumb-item>
          <bk-breadcrumb-item>{{ curSystem.description || '--' }}</bk-breadcrumb-item>
          <bk-breadcrumb-item>{{ curComponent.name || '--' }}</bk-breadcrumb-item>
        </bk-breadcrumb>
        <!-- <chat
          class="ag-chat" v-if="GLOBAL_CONFIG.PLATFORM_FEATURE.ALLOW_CREATE_APPCHAT" :default-user-list="userList"
          :owner="curUser.username" :name="chatName" :content="chatContent">
        </chat> -->
      </div>
      <bk-tab v-model:active="active" class="bk-special-tab" @tab-change="handleTabChange">
        <bk-tab-panel :name="'doc'" :label="t('文档')">
          <div class="ag-kv-box mb15">
            <div class="kv-row">
              <div class="k">{{ t('更新时间') }}:</div>
              <div class="v">{{ curDocUpdated || '--' }}</div>
            </div>
            <div class="kv-row">
              <div class="k">{{ t('应用认证') }}<i
                class="ml5 icon apigateway-icon icon-ag-help"
                v-bk-tooltips="t('应用访问该组件API时，是否需提供应用认证信息')"></i>：</div>
              <div class="v">{{ curComponent.app_verified_required ? t('是') : t('否') }}</div>
            </div>
            <div class="kv-row">
              <div class="k">{{ t('用户认证') }}<i
                class="ml5 icon apigateway-icon icon-ag-help"
                v-bk-tooltips="t('应用访问该组件API时，是否需要提供用户认证信息')"></i>：</div>
              <div class="v">{{ curComponent.user_verified_required ? t('是') : t('否') }}</div>
            </div>
            <div class="kv-row">
              <div class="k">{{ t('是否需申请权限') }}<i
                class="ml5 icon apigateway-icon icon-ag-help"
                v-bk-tooltips="t('应用访问该组件API前，是否需要在开发者中心申请该组件API权限')"></i>：</div>
              <div class="v">{{ curComponent.component_permission_required ? t('是') : t('否') }}</div>
            </div>
          </div>
          <!-- eslint-disable-next-line vue/no-v-html -->
          <div class="ag-markdown-view" id="markdown" :key="renderHtmlIndex" v-html="curComponent.markdownHtml"></div>
        </bk-tab-panel>
        <bk-tab-panel :name="'sdk '" :label="t('SDK及示例')">
          <div id="sdk-markdown">
            <div class="bk-button-group mb5">
              <bk-button class="is-selected">Python</bk-button>
              <!-- <bk-button disabled>GO</bk-button> -->
            </div>
            <h3 class="f16 fw700 mt15 mb15 balck">
              {{ t('SDK信息') }}
            </h3>
            <router-link
              style="margin-top: -30px;" :to="{ name: 'esbSDK', query: { tab: 'doc' } }"
              class="ag-link fn f12 fr">{{ t('Python SDK使用说明') }}</router-link>

            <div>
              <sdk-detail :params="curSdk"></sdk-detail>
            </div>
            <h3 class="f16 mt30 fw700 mt15 mb15 balck">{{ t('SDK使用样例') }}</h3>

            <!-- eslint-disable-next-line vue/no-v-html -->
            <div class="ag-markdown-view mt20" :key="renderHtmlIndex" v-html="sdkMarkdownHtml"></div>
          </div>
        </bk-tab-panel>
      </bk-tab>
    </div>

    <div class="component-nav-box">
      <div style="position: fixed;">
        <side-nav :list="componentNavList" v-if="active === 'doc'"></side-nav>
        <side-nav :list="sdkNavList" v-else></side-nav>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRoute } from 'vue-router';
import { slugify } from 'transliteration';
import MarkdownIt from 'markdown-it';
import { copy } from '@/common/util';
import sideNav from '@/components/side-nav/index.vue';
import sdkDetail from '@/components/sdk-detail/index.vue';
import hljs from 'highlight.js';
import 'highlight.js/styles/monokai-sublime.css';
import {
  getComponenSystemDetail,
  getESBSDKDetail,
  getSystemAPIList,
  getSDKDoc,
  getSystemComponentDoc,
} from '@/http';

const { t } = useI18n();
const route = useRoute();

const curVersion = ref<string>('');
const curSystemName = ref<string>('');
const curComponentName = ref<string>('');
const sdkMarkdownHtml = ref<string>('');
const active = ref<string>('doc');
const curDocUpdated = ref<string>('');
const renderHtmlIndex = ref<number>(0);
const curSdk = ref({});
const curComponentList = ref([]);
const sdkNavList = ref([]);
const componentNavList = ref([]);
const curComponent = ref<any>({
  id: '',
  name: '',
  label: '',
  content: '',
  innerHtml: '',
  markdownHtml: '',
  description: '',
});
const curSystem = ref<any>({
  name: '',
  description: '',
});


const md = new MarkdownIt({
  linkify: false,
  html: true,
  breaks: true,
  highlight(str: string, lang: string) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return hljs.highlight(lang, str, true).value;
      } catch (__) { }
    }

    return '';
  },
});

const initMarkdownHtml = (box: string) => {
  if (!box) {
    return false;
  }
  nextTick(() => {
    const markdownDom = document.getElementById(box);
    if (markdownDom.className.indexOf('has-init') > -1) {
      return false;
    }
    markdownDom.className = `${markdownDom.className} has-init`;
    // 右侧导航
    const titles = markdownDom.querySelectorAll('h3');

    if (box === 'sdk-markdown') {
      sdkNavList.value = [];
      titles?.forEach((item: any) => {
        const name = String(item?.firstChild?.nodeValue).trim();
        const id = slugify(name);
        item.id = `${curComponentName.value}?${id}`;
        sdkNavList.value.push({
          id: `${curComponentName.value}?${id}`,
          name,
        });
      });
    } else {
      componentNavList.value = [];
      titles?.forEach((item: any) => {
        const name = String(item?.innerText).trim();
        const id = slugify(name);
        item.id = `${curComponentName.value}?${id}`;
        componentNavList.value.push({
          id: `${curComponentName.value}?${id}`,
          name,
        });
      });
    }

    // 复制代码
    markdownDom?.querySelectorAll('a').forEach((item: any) => {
      item.target = '_blank';
    });
    // markdownDom.querySelectorAll('pre').forEach((item: any) => {
    //   const btn = document.createElement('button');
    //   let code = '';
    //   if (item?.className.indexOf('code') > -1) {
    //     code = item?.innerText;
    //   } else {
    //     code = item?.querySelector('code').innerText;
    //   }

    //   btn.className = 'ag-copy-btn';
    //   btn.innerHTML = '<span title="复制"><i class="bk-icon icon-clipboard mr5"></i></span>';
    //   btn.setAttribute('data-clipboard-text', code);
    //   item?.appendChild(btn);
    // });
    markdownDom?.querySelectorAll('pre')?.forEach((item: any) => {
      const parentDiv = document.createElement('div');
      const btn = document.createElement('button');
      const codeBox = document.createElement('div');
      const code = item?.querySelector('code')?.innerText;
      parentDiv.className = 'pre-wrapper';
      btn.className = 'ag-copy-btn';
      codeBox.className = 'code-box';
      btn.innerHTML = '<span :title="t(`复制`)"><i class="icon apigateway-icon icon-ag-copy" ></i></span>';
      parentDiv?.appendChild(btn);
      codeBox?.appendChild(item?.querySelector('code'));
      item?.appendChild(codeBox);
      console.log(code, btn, item);
      item?.parentNode?.replaceChild(parentDiv, item);
      parentDiv?.appendChild(item);
    });
  });
};

const handleTabChange = () => {
  // if (active.value === 'doc') {
  //   initMarkdownHtml('markdown');
  // } else {
  //   initMarkdownHtml('sdk-markdown');
  // }
};

// 获取当前系统的信息
const getSystemDetail = async () => {
  try {
    const res = await getComponenSystemDetail(curVersion.value, curSystemName.value);
    curSystem.value = res;
  } catch (error) {
    console.log('error', error);
  }
};
// 获取当前SDK的信息
const getSDKDetail = async () => {
  try {
    const res = await getESBSDKDetail(curVersion.value, { language: 'python' });
    curSdk.value = {
      sdk: {
        name: res.sdk_name,
        version: res.sdk_version_number,
        url: res.sdk_download_url,
        install_command: res.sdk_install_command,
      },
    };
  } catch (error) {
    console.log('error', error);
  }
};
// 获取APIlist
const getAPIList = async () => {
  try {
    const res = await getSystemAPIList(curVersion.value, curSystemName.value);
    // console.log(res);
    curComponentList.value = res;
    const match = curComponentList.value.find(item => item.name === curComponentName.value);
    if (match) {
      curComponent.value = { ...curComponent.value, ...match };
    }
  } catch (error) {
    console.log('error', error);
  }
};
// 获取当前组件的文档
const getComponentDoc = async () => {
  try {
    const res = await getSystemComponentDoc(curVersion.value, curSystemName.value, curComponentName.value);
    const data = res ? res : { content: '', type: 'markdown' };
    const { content } = data;
    curComponent.value.content = content;
    curComponent.value.markdownHtml = data.type === 'markdown' ? md.render(content) : content;
    curDocUpdated.value = res.updated_time;
    // eslint-disable-next-line no-plusplus
    renderHtmlIndex.value++;
    initMarkdownHtml('markdown');
  } catch (error) {
    console.log('error', error);
  }
};
// 获取SDK示例
const getSDKExample = async () => {
  const params = {
    language: 'python',
    system_name: curSystemName.value,
    component_name: curComponentName.value,
  };
  try {
    const res = await getSDKDoc(curVersion.value, params);
    const content = res ? res.content : '';
    sdkMarkdownHtml.value = md.render(content);
    initMarkdownHtml('sdk-markdown');
  } catch (error) {
    console.log('error', error);
  }
};

const init = () => {
  console.log(route);
  const routeParams: any = route.params;
  curVersion.value = routeParams.version;
  curSystemName.value = routeParams.id;
  curComponentName.value = routeParams.componentId;
  getSystemDetail();
  getSDKDetail();
  getAPIList();
  getComponentDoc();
  getSDKExample();
};
init();

</script>

<style lang="scss" scoped>
.balck{
  color: #000;
}
.component-doc {
  display: flex;
}

:deep(.bk-special-tab) {
  .bk-tab-content {
    border: none !important;
    padding: 20px 0 !important;
  }
}

.component-nav-box {
  margin-left: 15px;
  height: auto;
  flex: 1;
}

.ag-kv-box {
  .kv-row {
    font-size: 14px;
    line-height: 30px;
    display: flex;

    .k {
      width: 175px;
      text-align: left;
      color: #979BA5;
    }

    .v {
      color: #313238;
    }
  }
}

.component-content {
  width: 750px;
  background: #FFF;
  padding: 20px 25px;
  position: relative;
  border-radius: 2px;
  box-shadow: 0px 2px 6px 0px rgba(0, 0, 0, 0.1);
  overflow-y: auto;
  max-height: calc(100vh - 150px);

  &::-webkit-scrollbar {
    width: 4px;
    background-color: lighten(#C4C6CC, 80%);
  }

  &::-webkit-scrollbar-thumb {
    height: 5px;
    border-radius: 2px;
    background-color: #C4C6CC;
  }

  .component-metedata {
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

:deep(.bk-button-group) {
  .is-selected {
    background-color: #F6F9FF !important;
  }
}

:deep(.ag-markdown-view) {
  font-size: 14px;
  text-align: left;
  color: #63656e;
  line-height: 19px;
  font-style: normal;

  h1,
  h2,
  h3,
  h4,
  h5,
  h6 {
    padding: 0;
    margin: 25px 0 10px 0 !important;
    font-weight: bold;
    text-align: left;
    color: #313238;
    line-height: 21px;
  }

  h1 {
    font-size: 18px;
  }

  h2 {
    font-size: 17px;
  }

  h3 {
    font-size: 16px;
  }

  h4 {
    font-size: 13px;
  }

  h5 {
    font-size: 12px;
  }

  h6 {
    font-size: 12px;
  }

  p {
    font-size: 14px;
    color: #63656E;
    line-height: 22px;
    white-space: normal;
    word-break: break-all;
  }

  ul {
    padding-left: 17px;
    line-height: 22px;

    li {
      list-style: disc;
      margin-bottom: 8px;

      &:last-child {
        margin-bottom: 0;
      }
    }
  }

  ol {
    padding-left: 15px;
    line-height: 22px;

    li {
      list-style: decimal;
      margin-bottom: 8px;

      &:last-child {
        margin-bottom: 0;
      }
    }
  }

  a {
    color: #3A84FF;
  }

  tt {
    margin: 0 2px;
    padding: 0 5px;
    white-space: nowrap;
    border: 1px solid #eaeaea;
    background-color: #f8f8f8;
    border-radius: 3px;
    font-size: 75%;
  }

  table {
    font-size: 14px;
    color: #63656E;
    width: 100%;
    text-align: left;
    border: none;
    margin: 10px 0;
    font-style: normal;
    border: 1px solid #DCDEE5;

    &.field-list {
      th {
        width: 12%;
      }
    }

    em {
      font-style: normal;
    }

    th {
      background: #F0F1F5;
      font-size: 13px;
      font-weight: bold;
      color: #63656E;
      border-bottom: 1px solid #DCDEE5;
      padding: 10px;
      min-width: 70px;

    }

    th:nth-child(1) {
      width: 20%;
    }

    td {
      padding: 10px;
      font-size: 13px;
      color: #63656E;
      border-bottom: 1px solid #DCDEE5;
      max-width: 250px;
      font-style: normal;
      word-break: break-all;
    }
  }

  pre {
    border-radius: 2px;
    background: #23241f;
    padding: 10px;
    font-size: 14px;
    text-align: left;
    color: #FFF;
    line-height: 24px;
    position: relative;
    overflow: auto;
    margin: 14px 0;
    code {
      color: #FFF;
    }

    .hljs {
      margin: -10px;
    }
  }
}
</style>


