<template>
  <!--  页面右侧的网关详情/组件详情  -->
  <div v-if="basics" class="intro-side-content-wrap">
    <header class="intro-header">
      <article v-if="curTab === 'gateway'" class="title">{{ t('网关详情') }}</article>
      <article v-else-if="curTab === 'component'" class="title">{{ t('组件详情') }}</article>
      <aside v-if="basics.doc_maintainers?.type === 'user'">
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
      <aside v-else>
        <a target="_blank" class="link-item" :href="basics.doc_maintainers?.service_account?.link">
          <i class="ag-doc-icon doc-qw f16 apigateway-icon icon-ag-qw"></i>
          {{ t('联系') }} {{ basics.doc_maintainers?.service_account?.name }}
        </a>
      </aside>
    </header>
    <main v-if="curTab === 'gateway'" class="component-content">
      <div class="ag-markdown-view" id="markdown">
        <article>
          <header class="content-title">{{ t('网关描述') }}</header>
          <main class="content-main">{{ basics.description }}</main>
        </article>
        <article>
          <header class="content-title">{{ t('网关负责人') }}</header>
          <main class="content-main">
            <bk-user-display-name :user-id="basics.maintainers.join(', ')" style="word-break: break-all;" />
          </main>
        </article>
        <article>
          <header class="content-title">{{ t('租户模式') }}</header>
          <main class="content-main">{{ TENANT_MODE_TEXT_MAP[basics.tenant_mode] || '--' }}</main>
        </article>
        <article>
          <header class="content-title">{{ t('租户 ID') }}</header>
          <main class="content-main">{{ basics.tenant_id || '--' }}</main>
        </article>
        <article>
          <header class="content-title">{{ t('文档联系人') }}</header>
          <main class="content-main">
            {{ basics.doc_maintainers?.type === 'user' ?
              basics.doc_maintainers?.contacts.join(', ') :
              basics.doc_maintainers?.service_account?.name }}
          </main>
        </article>
        <article>
          <header class="content-title">{{ t('网关访问地址') }}</header>
          <main class="content-main">{{ basics.api_url }}</main>
        </article>
        <!--  网关 SDK 信息  -->
        <template v-if="userStore.featureFlags?.ENABLE_SDK">
          <article>
            <header class="content-title">{{ t('网关 SDK') }}</header>
            <LangSelector
              v-model="language"
              :sdk-languages="sdks.map(item => item.language)"
              :width="90"
              :margin-bottom="12"
            />
            <main class="content-main">
              <SdkDetail v-if="curSdk" :sdk="curSdk" is-apigw />
              <p v-else class="ag-tip mt5">
                {{ t('SDK未生成，可联系负责人生成SDK') }}
              </p>
            </main>
          </article>
        </template>
      </div>
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
            <SdkDetail :sdk="sdks[0]" />
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
  onBeforeUnmount,
  ref,
  Ref,
  toRefs,
  watch,
  watchEffect,
} from 'vue';
import { useI18n } from 'vue-i18n';
import chat from '@/components/chat/index.vue';
import SdkDetail from './sdk-detail.vue';
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
import { TENANT_MODE_TEXT_MAP } from '@/enums';
import { useBkUserDisplayName } from '@/hooks';

const props = withDefaults(defineProps<IProps>(), {
  basics: () => null,
  sdks: () => [],
});

const { t } = useI18n();

// 注入当前的总 tab 变量
const curTab = inject<Ref<TabType>>('curTab');

interface IProps {
  basics: IApiGatewayBasics & ISystemBasics | null;
  sdks: IApiGatewaySdkDoc[] & IComponentSdk[];
}

const {
  basics,
  sdks,
} = toRefs(props);

const userStore = useUser();
const { configure: configureDisplayName } = useBkUserDisplayName();

const language = ref<LanguageType>('python');

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

const curSdk = computed(() => {
  return sdks.value.find(item => item.language === language.value) ?? null;
});

watch(basics, () => {
  if (basics.value) {
    configureDisplayName(basics.value.tenant_mode === 'global' ? 'system' : userStore.user.tenant_id);
  }
}, { deep: true, immediate: true });

watchEffect(() => {
  language.value = sdks.value[0]?.language || 'python';
});

onBeforeUnmount(() => {
  configureDisplayName();
});

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
.link-item {
  font-size: 12px;
  color: #3A84FF;
  i {
    margin-right: 3px;
  }
}
</style>
