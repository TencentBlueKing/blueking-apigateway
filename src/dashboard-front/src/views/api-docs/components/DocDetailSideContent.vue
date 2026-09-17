/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) Tencent. All rights reserved.
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
  <div class="intro-side-content-wrap">
    <BkCollapse
      v-model="activePanels"
      class="detail-block-collapse"
    >
      <BkCollapsePanel name="basic">
        <template #header>
          <div class="block-header">
            <div class="block-header-left">
              <AgIcon
                name="down-shape"
                class="block-header-icon"
                :class="{ 'is-fold': !activePanels.includes('basic') }"
              />
              <span>{{ t('基本信息') }}</span>
            </div>
            <div
              v-if="curTab === 'gateway'"
              @click.stop
            >
              <DocDetailMaintainerAction :basics="basics" />
            </div>
          </div>
        </template>
        <template #content>
          <template v-if="curTab === 'gateway'">
            <DocDetailField :label="t('网关描述')">
              {{ basics?.description || '--' }}
            </DocDetailField>
            <template v-if="featureFlagStore.isTenantMode">
              <DocDetailField :label="t('租户模式')">
                {{ (basics?.tenant_mode && TENANT_MODE_TEXT_MAP[basics.tenant_mode]) || '--' }}
              </DocDetailField>
              <DocDetailField :label="t('租户 ID')">
                {{ basics?.tenant_id || '--' }}
              </DocDetailField>
            </template>
            <DocDetailField :label="t('网关负责人')">
              <span v-if="!featureFlagStore.isEnableDisplayName">{{ maintainerText }}</span>
              <bk-user-display-name
                v-else
                :user-id="maintainerText"
              />
            </DocDetailField>
            <DocDetailField :label="t('文档联系人')">
              <span v-if="!featureFlagStore.isEnableDisplayName">{{ docMaintainerText }}</span>
              <bk-user-display-name
                v-else
                :user-id="docMaintainerText"
              />
            </DocDetailField>
            <DocDetailField :label="t('网关访问地址')">
              <span>{{ basics?.api_url || '--' }}</span>
              <CopyButton
                v-if="basics?.api_url"
                :source="basics.api_url"
              />
            </DocDetailField>
          </template>
          <template v-else>
            <DocDetailField :label="t('组件描述')">
              {{ basics?.comment || '--' }}
            </DocDetailField>
            <DocDetailField :label="t('组件负责人')">
              {{ basics?.maintainers?.join(', ') || '--' }}
            </DocDetailField>
          </template>
        </template>
      </BkCollapsePanel>
      <BkCollapsePanel
        v-if="featureFlagStore.flags.ENABLE_SDK"
        name="sdk"
      >
        <template #header>
          <div class="block-header">
            <div class="block-header-left">
              <AgIcon
                name="down-shape"
                class="block-header-icon"
                :class="{ 'is-fold': !activePanels.includes('sdk') }"
              />
              <span>{{ curTab === 'gateway' ? t('网关 SDK') : t('组件 API SDK') }}</span>
            </div>
            <div @click.stop>
              <BkSelect
                v-model="sdkLanguage"
                class="sdk-lang-select"
                size="small"
                filterable
                :clearable="false"
                :input-search="false"
              >
                <BkOption
                  v-for="lang in sdkLangList"
                  :key="lang"
                  :value="lang"
                  :label="formatSdkLang(lang)"
                />
              </BkSelect>
            </div>
          </div>
        </template>
        <template #content>
          <DocSdkSection
            v-model:language="sdkLanguage"
            :sdks="sdks"
            :board="board"
          />
        </template>
      </BkCollapsePanel>
    </BkCollapse>
  </div>
</template>

<script lang="ts" setup>
import DocDetailField from './DocDetailField.vue';
import DocDetailMaintainerAction from './DocDetailMaintainerAction.vue';
import DocSdkSection, { type ISdkItem } from './DocSdkSection.vue';
import type {
  IDocsEsbBoardsSystemsReadResponse,
  IDocsGatewaysReadResponse,
} from '@/services/types/responses/docs';
import { docTabKey } from '../utils/doc-context';
import { TENANT_MODE_TEXT_MAP } from '@/enums';
import { useBkUserDisplayName } from '@/hooks';
import { useEnv, useFeatureFlag, useUserInfo } from '@/stores';

// 网关和组件的公共信息必填，各自的详情字段按需提供。
export interface IDocBasics extends Pick<IDocsGatewaysReadResponse, 'name' | 'description' | 'maintainers'>,
  Partial<Omit<IDocsGatewaysReadResponse, 'name' | 'description' | 'maintainers' | 'sdks'>>,
  Partial<Pick<IDocsEsbBoardsSystemsReadResponse, 'comment'>> {}

interface IProps {
  basics?: IDocBasics | null
  sdks?: ISdkItem[]
  board?: string
}

const {
  basics = null,
  sdks = [],
  board = 'default',
} = defineProps<IProps>();

const { t } = useI18n();
const featureFlagStore = useFeatureFlag();
const userStore = useUserInfo();
const { configure: configureDisplayName } = useBkUserDisplayName();

const curTab = inject(docTabKey);
const envStore = useEnv();
const activePanels = ref(['basic', 'sdk']);
const sdkLanguage = ref('python');

const generatedSdkLanguages = computed(() => {
  return sdks.map(item => item.language).filter((language): language is string => !!language);
});
const sdkLangList = computed(() => {
  const fromEnv = envStore.env.BK_SDK_LANGUAGES || [];
  return [...new Set([...generatedSdkLanguages.value, ...fromEnv])];
});

const formatSdkLang = (lang: string) => {
  if (!lang) {
    return '';
  }
  return lang.charAt(0).toUpperCase() + lang.slice(1);
};

const maintainerText = computed(() => basics?.maintainers?.join(', ') || '--');
const docMaintainerText = computed(() => {
  if (basics?.doc_maintainers?.type === 'user') {
    return basics.doc_maintainers.contacts?.join(', ') || '--';
  }
  return basics?.doc_maintainers?.service_account?.name || '--';
});

watch(
  () => basics,
  () => {
    if (basics) {
      configureDisplayName({ tenantId: basics?.tenant_mode === 'global' ? 'system' : (userStore.info.tenant_id ?? undefined) });
    }
  }, {
    deep: true,
    immediate: true,
  });

watch(sdkLangList, (list) => {
  if (!list.includes(sdkLanguage.value)
    || (generatedSdkLanguages.value.length && !generatedSdkLanguages.value.includes(sdkLanguage.value))
  ) {
    sdkLanguage.value = generatedSdkLanguages.value[0] || list[0] || 'python';
  }
}, { immediate: true });
</script>

<style lang="scss" scoped>
.intro-side-content-wrap {
  min-height: calc(100vh - 52px);
  padding: 16px;
  background: #f5f7fa;
}

.block-header {
  display: flex;
  flex: 1;
  min-width: 0;
  align-items: center;
  justify-content: space-between;
  font-size: 14px;
  font-weight: 700;
  color: #313238;
}

.block-header-left {
  display: flex;
  min-width: 0;
  align-items: center;

  > span {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}

.block-header-icon {
  flex-shrink: 0;
  margin-right: 8px;
  font-size: 12px;
  color: #63656e;
  transition: transform 0.2s;

  &.is-fold {
    transform: rotate(-90deg);
  }
}

.block-header > div:last-child {
  flex-shrink: 0;
  margin-left: 12px;
  font-weight: 400;
}

.sdk-lang-select {
  width: 140px;
}

.detail-block-collapse {

  :deep(> .bk-collapse-item) {
    margin-bottom: 16px;
    overflow: visible;
    background: #fff;
    border: none;
    border-radius: 2px;
    box-shadow: none;
  }

  :deep(> .bk-collapse-item:last-child) {
    margin-bottom: 0;
  }

  :deep(> .bk-collapse-item > div:first-child:not(.bk-collapse-content)) {
    display: flex;
    min-height: 48px;
    padding: 0 16px;
    cursor: pointer;
    align-items: center;
  }

  :deep(> .bk-collapse-item > .bk-collapse-content) {
    padding: 0 16px 16px;
  }
}
</style>
