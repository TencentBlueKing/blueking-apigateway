<template>
  <div class="intro-doc">
    <div class="component-content">
      <div class="component-metedata mb10">
        <strong class="name">{{ t('简介') }}</strong>
      </div>

      <div class="position-relative">
        <bk-breadcrumb separator=">" class="mb20">
          <bk-breadcrumb-item :to="{ name: 'componentDoc' }">{{ t('组件API文档') }}</bk-breadcrumb-item>
          <bk-breadcrumb-item>{{ curSystem.description || '--' }}</bk-breadcrumb-item>
          <bk-breadcrumb-item>{{ t('简介') }}</bk-breadcrumb-item>
        </bk-breadcrumb>
        <chat
          class="ag-chat"
          v-if="userStore.featureFlags?.ALLOW_CREATE_APPCHAT"
          :default-user-list="userList"
          :owner="curUser.username"
          :name="chatName"
          :content="chatContent">
        </chat>
      </div>
      <bk-divider></bk-divider>
      <div class="ag-markdown-view" id="markdown">
        <h3 class="mt10">{{ t('系统描述') }}</h3>
        <p class="mb30">{{ curSystem.comment || t('暂无简介') }}</p>
        <h3>{{ t('系统负责人') }}</h3>
        <p class="mb30">{{ curSystem.maintainers && curSystem.maintainers.join(', ') || '--' }}</p>
        <template v-if="userStore.featureFlags?.ENABLE_SDK">
          <h3>{{ t('组件API SDK') }}</h3>
          <div class="bk-button-group">
            <bk-button class="is-selected">Python</bk-button>
          </div>
          <div>
            <sdk-detail :params="curSdk"></sdk-detail>
          </div>
        </template>
      </div>
    </div>
    <div class="component-nav-box" v-if="componentNavList.length">
      <div class="position-fixed">
        <side-nav :list="componentNavList"></side-nav>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, computed } from 'vue';
import { useI18n } from 'vue-i18n';
// import { useGetGlobalProperties } from '@/hooks';
import { slugify } from 'transliteration';
import { useRoute } from 'vue-router';
import sideNav from '@/components/side-nav/index.vue';
import sdkDetail from '@/components/sdk-detail/index.vue';
import chat from '@/components/chat/index.vue';
import { useUser } from '@/store';
import {
  getComponenSystemDetail,
  getESBSDKDetail,
} from '@/http';

const { t } = useI18n();
const route = useRoute();
const userStore = useUser();
// const globalProperties = useGetGlobalProperties();
// const { GLOBAL_CONFIG } = globalProperties;

const curVersion = ref<string>('');
const curSystemName = ref<string>('');
const curSdk = ref({});
const componentNavList = ref([]);
const curSystem = ref<any>({
  name: '',
  description: '',
});
const curApigw = ref<any>({
  id: 2,
  name: '',
  description: '',
  maintainers: [
  ],
  is_official: '',
  api_url: '',
});

const curUser = computed(() => userStore?.user);
const userList = computed(() => {
  // 去重
  const set = new Set([curUser.value?.username, ...curApigw.value?.maintainers]);
  return [...set];
});
const chatName = computed(() => `${t('[蓝鲸网关API咨询] 网关')}${curApigw.value?.name}`);
const chatContent = computed(() => `${t('网关API文档')}:${location.href}`);


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
    initMarkdownHtml();
  } catch (error) {
    console.log('error', error);
  }
};

const initMarkdownHtml = () => {
  nextTick(() => {
    const markdownDom = document.getElementById('markdown');
    // 右侧导航
    const titles = markdownDom.querySelectorAll('h3');
    componentNavList.value = [];
    titles.forEach((item) => {
      const name = String(item.innerText).trim();
      const newName = slugify(name);
      // const id = `${curComponentName.value}?${newName}`;
      const id = newName;
      componentNavList.value.push({
        id,
        name,
      });
      item.id = id;
    });
  });
};

const init = () => {
  const routeParams: any = route.params;
  curVersion.value = routeParams.version;
  curSystemName.value = routeParams.id;
  getSystemDetail();
  getSDKDetail();
};
init();
</script>

<style lang="scss" scoped>
.position-relative{
  position: relative;
}
.position-fixed{
  position:fixed
}
.intro-doc {
  display: flex;
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

.ag-markdown-view {
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
    margin: 25px 0 10px 0;
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

    code {
      color: #FFF;
    }

    .hljs {
      margin: -10px;
    }
  }
}

.component-nav-box {
  margin-left: 15px;
  height: auto;
  flex: 1;
}

:deep(.bk-button-group) {
  .is-selected {
    background-color: #F6F9FF !important;
  }
}
</style>
