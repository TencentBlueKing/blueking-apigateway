<template>
  <!--  页面右侧的网关详情/组件详情  -->
  <div v-if="basics" class="intro-side-content-wrap">
    <header class="intro-header">
      <article v-if="curTab === 'apigw'" class="title">{{ t('网关详情') }}</article>
      <article v-else-if="curTab === 'component'" class="title">{{ t('组件详情') }}</article>
      <aside>
        <chat
          v-if="userStore.featureFlags?.ALLOW_CREATE_APPCHAT"
          :default-user-list="userList"
          :owner="curUser.username"
          :name="chatName"
          :content="chatContent"
          :is-query="true"
        >
        </chat>
      </aside>
    </header>
    <main v-if="curTab === 'apigw'" class="component-content">
      <div class="ag-markdown-view" id="markdown">
        <article>
          <header class="content-title">{{ t('网关描述') }}</header>
          <main class="content-main">{{ basics.description }}</main>
        </article>
        <article>
          <header class="content-title">{{ t('网关负责人') }}</header>
          <main class="content-main">{{ basics.maintainers.join(', ') }}</main>
        </article>
        <article>
          <header class="content-title">{{ t('网关访问地址') }}</header>
          <main class="content-main">{{ basics.api_url }}</main>
        </article>
        <template v-if="userStore.featureFlags?.ENABLE_SDK">
          <article>
            <header class="content-title">{{ t('网关 SDK') }}</header>
            <LangSelector :width="90" :margin-bottom="12" @select="handleLangSelect"></LangSelector>
          </article>
        </template>
      </div>

      <!--  网关SDK信息表格  -->
      <template v-if="userStore.featureFlags?.ENABLE_SDK && curTab === 'apigw'">
        <bk-table
          :data="sdks"
          show-overflow-tooltip
          :border="['outer']"
          :size="'small'"
        >
          <!-- <template #empty>
          <table-empty
            :abnormal="isAbnormal"
            @reacquire="getApigwSDK('python')"
          />
        </template> -->

          <bk-table-column :label="t('网关环境')" field="stage_name">
            <template #default="{ row }: { row: IApiGatewaySdkDoc }">
              {{ row.stage?.name || '--' }}
            </template>
          </bk-table-column>

          <bk-table-column :label="t('网关API资源版本')" field="resource_version_display">
            <template #default="{ row }: { row: IApiGatewaySdkDoc }">
              {{ row.resource_version?.version || '--' }}
            </template>
          </bk-table-column>

          <bk-table-column :label="t('SDK 版本号')" field="sdk_version_number">
            <template #default="{ row }: { row: IApiGatewaySdkDoc }">
              {{ row.sdk?.version || '--' }}
            </template>
          </bk-table-column>

          <bk-table-column :label="t('SDK下载')">
            <template #default="{ row }: { row: IApiGatewaySdkDoc }">
              <template v-if="row.sdk?.url">
                <bk-button theme="primary" text @click="handleDownload(row)"> {{ t('下载') }}</bk-button>
              </template>
              <template v-else>
                {{ t('未生成-doc') }}
              </template>
            </template>
          </bk-table-column>
        </bk-table>

        <p class="ag-tip mt5">
          <info-line style="margin-right: 8px;" />
          {{ t('若资源版本对应的SDK未生成，可联系网关负责人生成SDK') }}
        </p>
      </template>
    </main>

    <main v-else-if="curTab === 'component'" class="component-content">
      <div class="ag-markdown-view">
        <article>
          <header class="content-title">{{ t('网关描述') }}</header>
          <main class="content-main">{{ basics.comment }}</main>
        </article>
        <article>
          <header class="content-title">{{ t('网关负责人') }}</header>
          <main class="content-main">{{ basics.maintainers.join(', ') }}</main>
        </article>
        <article>
          <header class="content-title">
            {{ t('组件 API SDK') }}
            <bk-tag class="ml20 fw-normal" theme="info">Python</bk-tag>
          </header>
          <main class="content-main">
            <SdkDetail :sdk="sdks[0]"></SdkDetail>
          </main>
        </article>
      </div>
    </main>
  </div>
</template>

<script lang="ts" setup>
import {
  computed,
  inject,
  Ref,
  toRefs,
} from 'vue';
import { useI18n } from 'vue-i18n';
import chat from '@/components/chat/index.vue';
import SdkDetail from './sdk-detail.vue';
import { InfoLine } from 'bkui-vue/lib/icon';
import { useUser } from '@/store';
import {
  IApiGatewayBasics,
  IApiGatewaySdkDoc,
  IComponentSdk,
  ISystemBasics,
  LanguageType,
  TabType,
} from '@/views/apiDocs/types';
import LangSelector from '@/views/apiDocs/components/lang-selector.vue';

const { t } = useI18n();

// 注入当前的总 tab 变量
const curTab = inject<Ref<TabType>>('curTab');

interface IProps {
  basics: IApiGatewayBasics & ISystemBasics | null;
  sdks: IApiGatewaySdkDoc[] & IComponentSdk[];
}

const props = withDefaults(defineProps<IProps>(), {
  basics: () => null,
  sdks: () => [],
});

const {
  basics,
  sdks,
} = toRefs(props);

const emit = defineEmits<{
  'lang-change': [language: LanguageType]
}>();

const userStore = useUser();

const curUser = computed(() => userStore?.user);
const userList = computed(() => {
  // 去重
  const set = new Set([
    curUser.value?.username,
    ...basics.value?.maintainers,
  ]);
  return [...set];
});
const chatName = computed(() => `${t('[蓝鲸网关API咨询] 网关')}${basics.value?.name}`);
const chatContent = computed(() => `${t('网关API文档')}:${location.href}`);

const handleDownload = (row: IApiGatewaySdkDoc) => {
  window.open(row.sdk?.url);
};

const handleLangSelect = (language: LanguageType) => {
  emit('lang-change', language);
};

</script>

<style lang="scss" scoped>
.intro-side-content-wrap {
  padding: 0 24px 12px 24px;

  .intro-header {
    margin-bottom: 12px;
    height: 48px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .component-content {
    width: auto;

    .ag-markdown-view {
      .content-title,
      .content-main {
        font-size: 14px;
        color: #63656e;
        letter-spacing: 0;
        line-height: 22px;
      }

      .content-title {
        margin-bottom: 12px;
        font-weight: 700;
      }

      .content-main {
        margin-bottom: 32px;
      }
    }
  }
}
</style>
