<template>
  <div class="component-doc">
    <div class="component-content">
      <div class="component-metedata mb10">
        <strong class="name mr5" v-bk-tooltips.top="curComponent.name">{{curComponent.name || '--'}}</strong>
        <span
          class="label"
          v-bk-tooltips.top="{ content: curComponent.description, allowHTML: false }"
        >
          {{curComponent.description || $t('暂无描述')}}
        </span>
      </div>
      <div style="position: relative;">
        <bk-breadcrumb separator-class="bk-icon icon-angle-right" class="mb20">
          <bk-breadcrumb-item :to="{ name: 'apigwDoc' }"> {{ $t('网关API文档') }} </bk-breadcrumb-item>
          <bk-breadcrumb-item>{{curApigw.name || '--'}}</bk-breadcrumb-item>
          <bk-breadcrumb-item>{{curComponent.name || '--'}}</bk-breadcrumb-item>
        </bk-breadcrumb>

        <chat
          class="ag-chat"
          v-if="userStore.featureFlags?.ALLOW_CREATE_APPCHAT"
          :default-user-list="userList"
          :owner="curUser.username"
          :name="chatName"
          :content="chatContent"
          :is-query="true">
        </chat>
      </div>

      <bk-tab v-model:active="active" class="bk-special-tab">
        <bk-tab-panel
          :name="'doc'"
          :label="$t('文档')">
          <div class="ag-kv-box mb30">
            <div class="kv-row">
              <div class="k"> {{ $t('更新时间') }}: </div>
              <div class="v">{{curDocUpdated || '--'}}</div>
            </div>
            <div class="kv-row">
              <div class="k">
                {{ $t('应用认证') }}
                <i class="ml5 bk-icon icon-question-circle" v-bk-tooltips="$t('应用访问该网关API时，是否需提供应用认证信息')">
                </i>：
              </div>
              <div class="v">{{curComponent.app_verified_required ? $t('是') : $t('否')}}</div>
            </div>
            <div class="kv-row">
              <div class="k">
                {{ $t('用户认证') }}
                <i class="ml5 bk-icon icon-question-circle" v-bk-tooltips="$t('应用访问该组件API时，是否需要提供用户认证信息')">
                </i>：
              </div>
              <div class="v">{{curComponent.user_verified_required ? $t('是') : $t('否')}}</div>
            </div>
            <div class="kv-row">
              <div class="k">
                {{ $t('是否需申请权限') }}
                <i class="ml5 bk-icon icon-question-circle" v-bk-tooltips="$t('应用访问该网关API前，是否需要在开发者中心申请该网关API权限')"></i>
                ：
              </div>
              <div class="v">{{curComponent.resource_perm_required ? $t('是') : $t('否')}}</div>
            </div>
          </div>
          <!-- eslint-disable-next-line vue/no-v-html -->
          <div class="ag-markdown-view" id="markdown" :key="renderHtmlIndex" v-html="curComponent.markdownHtml"></div>
        </bk-tab-panel>
        <bk-tab-panel
          :name="'sdk'"
          :label="$t('SDK及示例')"
          v-if="userStore.featureFlags?.ENABLE_SDK"
        >
          <div id="sdk-markdown">
            <div class="bk-button-group">
              <bk-button class="is-selected">Python</bk-button>
            </div>

            <h3 class="f16">
              {{ $t('SDK信息-doc') }}
              <span class="ag-tip ml10" v-if="!curSdk?.sdk?.version">
                ({{ SDKInfo }})
              </span>
            </h3>

            <div>
              <sdk-detail :params="curSdk" :is-apigw="true"></sdk-detail>
            </div>

            <h3 class="f16 mt20"> {{ $t('SDK使用样例') }} </h3>
            <!-- eslint-disable-next-line vue/no-v-html -->
            <div class="ag-markdown-view mt20" :key="renderHtmlIndex" v-html="sdkMarkdownHtml"></div>
          </div>
        </bk-tab-panel>
      </bk-tab>
    </div>

    <div class="component-nav-box">
      <div style="position: fixed;">
        <side-nav :list="componentNavList" v-show="active === 'doc'"></side-nav>
        <side-nav :list="sdkNavList" v-show="active !== 'doc'"></side-nav>
      </div>
    </div>

  </div>
</template>

<script lang="ts" setup>
import { ref, computed, watch, nextTick } from 'vue';
import MarkdownIt from 'markdown-it';
import { slugify } from 'transliteration';
import sdkDetail from '@/components/sdk-detail/index.vue';
import sideNav from '@/components/side-nav/index.vue';
import hljs from 'highlight.js';
import 'highlight.js/styles/monokai-sublime.css';
import { useI18n } from 'vue-i18n';
import { useRoute } from 'vue-router';
import { getApigwResourceSDKDocs, getApigwResourceDocDocs, getApigwResourcesDocs, getApigwSDKDocs, getGatewaysDetailsDocs } from '@/http';
import { copy } from '@/common/util';
import chat from '@/components/chat/index.vue';
import { useUser } from '@/store';

const userStore = useUser();
const route = useRoute();
const { t } = useI18n();

const md = new MarkdownIt({
  linkify: false,
  html: true,
  breaks: true,
  highlight(str: string, lang: string) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return hljs.highlight(lang, str, true).value;
      } catch (__) {}
    }

    return '';
  },
});

const curStage = ref<string>('');
const curApigwId = ref<string>('');
const curResourceId = ref<string>('');
const curComponentName = ref<string>('');
const renderHtmlIndex = ref<number>(0);
const active = ref<string>('doc');
const curDocUpdated = ref<string>('');
const curComponent = ref<any>({
  id: '',
  name: '',
  label: '',
  content: '',
  innerHtml: '',
  markdownHtml: '',
});

const sdkNavList = ref<any>([]);
const sdks = ref<any>([]);
const curSdk = ref<any>({});
const sdkMarkdownHtml = ref<string>('');
const curApigw = ref({
  name: '',
  label: '',
  maintainers: [],
});
const componentNavList = ref<any>([]);

const SDKInfo = computed(() => t(`网关当前环境【${curStage.value}】对应的资源版本未生成 SDK，可联系网关负责人生成 SDK`));
const curUser = computed(() => userStore?.user);
const userList = computed(() => {
  // 去重
  const set = new Set([curUser.value?.username, ...curApigw.value?.maintainers]);
  return [...set];
});
const chatName = computed(() => `${t('[蓝鲸网关API咨询] 网关')}${curApigw.value?.name}`);
const chatContent = computed(() => `${t('网关API文档')}:${location.href}`);

const initMarkdownHtml = (box: string) => {
  nextTick(() => {
    const markdownDom = document.getElementById(box);
    // 右侧导航
    const titles = markdownDom?.querySelectorAll('h3');
    if (box === 'sdk-markdown') {
      sdkNavList.value = [];
      const sdkNavArr: any = [];
      titles?.forEach((item) => {
        const name = String(item?.firstChild?.nodeValue).trim();
        const id = slugify(name);
        item.id = `${curComponentName.value}?${id}`;
        sdkNavArr.push({
          id: `${curComponentName.value}?${id}`,
          name,
        });
      });
      sdkNavList.value = sdkNavArr;
    } else {
      componentNavList.value = [];
      const componentNavArr: any = [];
      titles?.forEach((item) => {
        const name = String(item?.innerText).trim();
        const id = slugify(name);
        item.id = `${curComponentName.value}?${id}`;
        componentNavArr.push({
          id: `${curComponentName.value}?${id}`,
          name,
        });
      });
      componentNavList.value = componentNavArr;
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
      btn.setAttribute('data-copy', code);
      parentDiv?.appendChild(btn);
      codeBox?.appendChild(item?.querySelector('code'));
      item?.appendChild(codeBox);
      item?.parentNode?.replaceChild(parentDiv, item);
      parentDiv?.appendChild(item);
    });


    setTimeout(() => {
      const copyDoms = Array.from(document.getElementsByClassName('ag-copy-btn'));

      const handleCopy = function (this: any) {
        copy(this.dataset?.copy);
      };

      copyDoms.forEach((dom: any) => {
        dom.onclick = handleCopy;
      });
    }, 1000);
  });
};

const getApigwResourceSDK = async () => {
  try {
    const query = {
      language: 'python',
      stage_name: curStage.value,
      resource_name: curResourceId.value,
    };
    const res = await getApigwResourceSDKDocs(curApigwId.value, query);
    const { content } = res;
    sdkMarkdownHtml.value = md.render(content);
    initMarkdownHtml('sdk-markdown');
  } catch (e) {
    console.log(e);
  }
};

const getApigwResourceDoc = async () => {
  try {
    const query = {
      stage_name: curStage.value,
    };
    const res = await getApigwResourceDocDocs(curApigwId.value, curResourceId.value, query);
    const { content } = res;
    curComponent.value.content = content;
    curComponent.value.markdownHtml = md.render(content);
    renderHtmlIndex.value += 1;
    curDocUpdated.value = res.updated_time;

    initMarkdownHtml('markdown');
  } catch (e) {
    console.log(e);
  } finally {
  }
};

const getApigwResourceDetail = async () => {
  try {
    const query = {
      limit: 10000,
      offset: 0,
      stage_name: curStage.value,
    };
    const res = await getApigwResourcesDocs(curApigwId.value, query);

    const match = res?.find((item: any) => {
      return item.name === curResourceId.value;
    });
    if (match) {
      curComponent.value = { ...curComponent.value, ...match };
    }
  } catch (e) {
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
    const res = await getApigwSDKDocs(curApigwId.value, query);
    sdks.value = res;
    const match = sdks.value?.find((item: any) => item?.stage?.name === curStage.value);
    curSdk.value = match || {};
    getApigwResourceSDK();
  } catch (e) {
    console.log(e);
  }
};

const getApigwAPIDetail = async () => {
  try {
    const res = await getGatewaysDetailsDocs(curApigwId.value);
    curApigw.value = res;
  } catch (e) {
    console.log(e);
  }
};

const getRouteData = () => {
  const routeParams = route.params;
  curApigwId.value = routeParams.apigwId as string;
  curStage.value = route.query.stage as string;
  curResourceId.value = routeParams.resourceId as string;
};

const init = () => {
  getRouteData();
  getApigwAPIDetail();
  getApigwResourceDetail();
  getApigwResourceDoc();
  getApigwSDK('python');
};

watch(
  () => route,
  async (payload: any) => {
    if (payload?.params?.apigwId && payload?.params?.resourceId && payload?.query?.stage && ['apigwAPIDetailDoc'].includes(payload.name)) {
      init();
    }
  },
  { immediate: true, deep: true },
);
</script>

<style lang="scss" scoped>
  @import './detail.css';
</style>
