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
  <div class="docs-main">
    <!--  顶部 网关 / 组件 Tab  -->
    <header
      v-if="!featureFlagStore.isTenantMode"
      class="page-tabs"
    >
      <nav class="tabs-group">
        <section
          class="page-tab"
          :class="{ 'active': curTab === 'gateway' }"
          @click="curTab = 'gateway'"
        >
          {{ t('网关 API 文档') }}
        </section>
        <section
          class="page-tab"
          :class="{ 'active': curTab === 'component' }"
          @click="curTab = 'component'"
        >
          {{ t('组件 API 文档') }}
        </section>
      </nav>
    </header>
    <!--  正文  -->
    <main
      :class="[{ 'pt-24px': featureFlagStore.isTenantMode}, routerViewWrapperClass]"
      class="docs-main-content"
    >
      <!--  当选中 网关API文档 时  -->
      <div
        v-if="curTab === 'gateway'"
        class="content-of-apigw"
      >
        <!--  搜索栏和 SDK使用说明  -->
        <header class="top-bar">
          <BkInput
            v-model="filterData.keyword"
            type="search"
            :placeholder="t('请输入网关名称或描述')"
            clearable
            style="width: 400px"
          />
          <BkLink
            theme="primary"
            class="text-12px ml-24px"
            @click.prevent="isSdkInstructionSliderShow = true"
          >
            <AgIcon name="document" />
            {{ t('SDK 使用说明') }}
          </BkLink>
        </header>
        <!--  网关列表  -->
        <main class="docs-list">
          <AgTable
            ref="tableRef"
            show-settings
            resizable
            :api-method="getTableData"
            :columns="columns"
            @clear-filter="handleClearFilterKey"
          />
        </main>
      </div>
      <!--  当选中 组件API文档 时  -->
      <div
        v-else-if="curTab === 'component'"
        class="content-of-component"
      >
        <main class="category-list">
          <article
            v-for="(systemBoard, index) in componentSystemList"
            :key="systemBoard.board"
            class="category-wrap"
          >
            <!--  system 类别 title 和搜索栏  -->
            <header class="top-bar">
              <main class="bar-title">
                <span class="title">{{ systemBoard.board_label }}</span>
                <BkLink
                  v-bk-tooltips="{ content: t('SDK未生成，可联系负责人生成SDK'), disabled: systemBoard.sdk?.sdk_download_url }"
                  :href="systemBoard.sdk?.sdk_download_url"
                  :disabled="!systemBoard.sdk?.sdk_download_url"
                  target="_blank"
                  theme="primary"
                  class="text-12px"
                  @click.prevent="handleESBSdkDetailClick(systemBoard)"
                >
                  {{ t('查看 SDK') }}
                </BkLink>
              </main>
              <aside
                v-if="index === 0"
                class="bar-aside"
              >
                <ComponentSearcher
                  v-if="componentSystemList.length > 0"
                  class="ag-searcher-box"
                  :version-list="componentSystemList"
                />
                <BkLink
                  theme="primary"
                  class="text-12px"
                  @click.prevent="isSdkInstructionSliderShow = true"
                >
                  <AgIcon name="document" />
                  {{ t('SDK 使用说明') }}
                </BkLink>
              </aside>
            </header>
            <!--  组件  -->
            <main class="components-wrap">
              <!--  组件分类  -->
              <article
                v-for="cat in systemBoard.categories"
                :key="cat.id"
                :ref="categoryRefs.set"
                class="component-group"
                :data-_nav-id="`${systemBoard.board}-${cat.id}`"
              >
                <header class="group-title">
                  <span class="name">{{ cat.name }}</span>
                  <span class="count">{{ `(${cat.systems.length})` }}</span>
                </header>
                <!--  分类中的组件卡片  -->
                <main class="group-items">
                  <article
                    v-for="system in cat.systems"
                    :key="system.name"
                    class="item"
                    @click="gotoDetails(system, systemBoard.board)"
                  >
                    <main class="title">
                      <div class="name">
                        {{ system.description }}
                      </div>
                      <div class="name-en">
                        {{ system.name }}
                      </div>
                    </main>
                    <aside class="background-image">
                      <i class="apigateway-icon icon-ag-component-intro" />
                    </aside>
                  </article>
                </main>
              </article>
            </main>
          </article>
        </main>
        <!--  右侧导航目录  -->
        <BkAffix :offset-top="128">
          <aside class="component-nav-list">
            <BkCollapse
              v-model="navPanelNamesList"
              class="collapse-cls"
              use-card-theme
            >
              <BkCollapsePanel
                v-for="systemBoard in componentSystemList"
                :key="systemBoard.board"
                :name="systemBoard.board"
                :model-value="isActiveNavPanel(systemBoard.board)"
              >
                <template #header>
                  <div class="panel-header">
                    <main class="flex items-center">
                      <AngleUpFill
                        :class="[
                          isActiveNavPanel(systemBoard.board) ? 'panel-header-show' : 'panel-header-hide'
                        ]"
                      />
                      <div class="title ml4">
                        {{ systemBoard.board_label }}
                      </div>
                    </main>
                  </div>
                </template>
                <template #content>
                  <nav class="panel-content">
                    <article
                      v-for="cat in systemBoard.categories"
                      :key="cat.id"
                      class="panel-content-cat-item"
                      :class="{ 'active': curCategoryNavId === cat._navId }"
                      @click="handleNavClick(cat)"
                    >
                      {{ cat.name }}
                    </article>
                  </nav>
                </template>
              </BkCollapsePanel>
            </BkCollapse>
          </aside>
        </BkAffix>
      </div>
    </main>
    <!--  SDK使用说明 Slider  -->
    <SDKInstructionSlider v-model="isSdkInstructionSliderShow" />
    <!--  网关/组件 SDK 地址 dialog  -->
    <SDKDetailDialog
      v-model="isSdkDetailDialogShow"
      :sdks="curSdks"
      :languages="curTab === 'component' ? ['python'] : undefined"
      :target-name="curTargetName"
      :maintainers="curTargetMaintainers"
    />
  </div>
</template>

<script lang="tsx" setup>
import {
  getComponentSystemList,
  getESBSDKlist,
} from '@/services/source/docs-esb';
import { getGatewaysDocs } from '@/services/source/docs';
import SDKInstructionSlider from './components/SDKInstructionSlider.vue';
import SDKDetailDialog from './components/SDKDetailDialog.vue';
import ComponentSearcher from './components/ComponentSearcher.vue';
import type {
  IApiGatewayBasics,
  IBoard,
  ICategory,
  IComponentSdk,
  ISdk,
  ISystem,
  TabType,
} from './types.d.ts';
import { AngleUpFill } from 'bkui-vue/lib/icon';
import { useTemplateRefsList } from '@vueuse/core';
import { TENANT_MODE_TEXT_MAP } from '@/enums';
import { useFeatureFlag } from '@/stores';
import type { PrimaryTableProps } from '@blueking/tdesign-ui';
import AgTable from '@/components/ag-table/Index.vue';

const { t } = useI18n();
const route = useRoute();
const router = useRouter();
const featureFlagStore = useFeatureFlag();

const filterData = ref({ keyword: '' });

const tableRef = ref();
// 组件分类模板引用列表
const categoryRefs = useTemplateRefsList<HTMLElement>();

// 当前展示的是 网关 | 组件 相关内容
const curTab = ref<TabType>('gateway');
const curTargetName = ref('');
const board = ref('default');
const curCategoryNavId = ref('');
const navPanelNamesList = ref<string[]>([]);
const isSdkInstructionSliderShow = ref(false);
const isSdkDetailDialogShow = ref(false);
const componentSystemList = ref<IBoard[]>([]); // 组件系统列表
const curSdks = ref<ISdk[]>([]);
const curTargetMaintainers = ref<string[]>([]);

// 提供当前 tab 的值
// 注入时请使用：const curTab = inject<Ref<TabType>>('curTab');
provide('curTab', curTab);

const columns = computed<PrimaryTableProps['columns']>(() => [
  {
    colKey: 'name',
    title: t('网关名称'),
    width: 300,
    cell: (h, { row }) => (
      <div>
        <span
          class="color-#3a84ff cursor-pointer"
          onClick={() => gotoDetails(row)}
        >
          { row.name || '--' }
        </span>
        {
          row.is_official
            ? (
              <bk-tag theme="success">
                { t('官方') }
              </bk-tag>
            )
            : ''
        }
      </div>
    ),
  },
  ...(featureFlagStore.isTenantMode
    ? [
      {
        colKey: 'tenant_mode',
        title: t('租户模式'),
        width: 120,
        cell: (h, { row }) => <span>{ TENANT_MODE_TEXT_MAP[row.tenant_mode as string] || '--' }</span>,
      },
      {
        colKey: 'tenant_id',
        title: t('租户 ID'),
        width: 120,
        cell: (h, { row }) => <span>{ row.tenant_id || '--' }</span>,
      },
    ]
    : []),
  {
    colKey: 'description',
    title: t('网关描述'),
    width: 500,
    cell: (h, { row }) =>
      <span>{ row.description || '--' }</span>,
  },
  ...(!featureFlagStore.isTenantMode
    ? [
      {
        colKey: 'maintainers',
        title: t('网关负责人'),
        width: 180,
        cell: (h, { row }) => (
          row.maintainers?.length
            ? (
              <div>
                {
                  !featureFlagStore.isEnableDisplayName
                    ? <span>{ row.maintainers.join(', ') }</span>
                    : (
                      <span>
                        {
                          row.maintainers.map((maintainer, index) => (
                            <span
                              key={maintainer.login_name}
                            >
                              <bk-user-display-name userId={maintainer} />
                              {
                                index !== (row.maintainers.length - 1)
                                  ? <span>,</span>
                                  : ''
                              }
                            </span>
                          ))
                        }
                      </span>
                    )
                }
              </div>
            )
            : '--'

        ),
      },
    ]
    : []),
  {
    colKey: 'actions',
    title: t('操作'),
    width: 100,
    fixed: 'right',
    cell: (h, { row }) => (
      <bk-button
        v-bk-tooltips={{
          content: t('SDK未生成，可联系负责人生成SDK'),
          disabled: row.sdks?.length,
        }}
        text
        theme="primary"
        disabled={!row.sdks?.length}
        onClick={() => handleSdkDetailClick(row)}
      >
        {t('查看 SDK')}
      </bk-button>
    ),
  },
]);

const isShowNoticeAlert = computed(() => featureFlagStore.isEnabledNotice);

const routerViewWrapperClass = computed(() => {
  const initClass = 'default-header-view';
  const displayBkuiTable = ['ApiDocs'].includes(route.name as string) ? 'need-bkui-table-wrapper' : '';
  if (isShowNoticeAlert.value) {
    return `${initClass} show-notice ${displayBkuiTable}`;
  }
  return `${initClass} ${displayBkuiTable}`;
});

watch(
  filterData,
  () => {
    tableRef.value!.fetchData(filterData.value);
  },
  { deep: true },
);

const getTableData = async (params: Record<string, any> = {}) => getGatewaysDocs(params);

const gotoDetails = (row: IApiGatewayBasics | ISystem, systemBoard?: string) => {
  const params = {
    targetName: row.name,
    curTab: curTab.value,
  };

  if (curTab.value === 'component') {
    Object.assign(params, { board: systemBoard || 'default' });
  }

  router.push({
    name: 'ApiDocDetail',
    params,
  });
};

const handleClearFilterKey = () => {
  filterData.value = { keyword: '' };
};

const fetchComponentSystemList = async () => {
  try {
    const systemList = await getComponentSystemList(board.value) as IBoard[];
    // esb 的 sdk 语言，目前只有 python
    const language = 'python';
    const sdkResponse = await getESBSDKlist(board.value, { language }) as IComponentSdk[];
    const sdkList = sdkResponse || [];
    sdkList.forEach((sdk) => {
      sdk.language = language;
    });
    systemList.forEach((system) => {
      // 给组件分类添加一个跳转用的 _navId
      system.categories.forEach((category) => {
        category._navId = `${system.board}-${category.id}`;
      });
      // 找到组件的 sdk
      system.sdk = sdkList.find(sdk => sdk.board_label === system.board_label);
      componentSystemList.value.push(system);
      navPanelNamesList.value.push(system.board);
    });
  }
  catch {
    componentSystemList.value = [];
  }
};

const handleNavClick = (cat: ICategory) => {
  const { _navId } = cat;
  curCategoryNavId.value = _navId;
  const categoryRef = categoryRefs.value.find(item => item.dataset?._navId === _navId);
  if (categoryRef?.scrollIntoView) {
    categoryRef.scrollIntoView({ behavior: 'smooth' });
  }
};

const handleSdkDetailClick = (row: IApiGatewayBasics) => {
  curTargetName.value = row.name;
  curSdks.value = row.sdks ?? [];
  isSdkDetailDialogShow.value = true;
  curTargetMaintainers.value = row.maintainers || [];
};

const handleESBSdkDetailClick = (board: IBoard) => {
  curTargetName.value = board.sdk?.board_label ?? '';
  curSdks.value = board.sdk ? [board.sdk] : [];
  curTargetMaintainers.value = [];
  isSdkDetailDialogShow.value = true;
};

// 判断导航目录是否为已展开状态
const isActiveNavPanel = (panelName: string) => {
  return navPanelNamesList.value.includes(panelName);
};

onBeforeMount(() => {
  const { params } = route;
  // 如果是多租户模式，直接跳转到网关API文档
  if (featureFlagStore.isTenantMode) {
    curTab.value = 'gateway';
    return;
  }
  // 记录返回到此页时选中的 tab
  curTab.value = params.curTab as TabType || 'gateway';
});

onMounted(async () => {
  // 如果是多租户模式，不需要获取 esb 列表
  if (!featureFlagStore.isTenantMode) {
    await fetchComponentSystemList();
  }
});

</script>

<style lang="scss" scoped>
$primary-color: #3a84ff;

.docs-main {

  .page-tabs {
    position: sticky;
    top: 0;
    z-index: 2;
    display: flex;
    height: 52px;
    margin-bottom: 24px;
    background: #fff;
    box-shadow: 0 3px 4px 0 #0000000a;
    justify-content: center;
    align-items: center;

    .tabs-group {
      display: flex;
      justify-content: center;

      .page-tab {
        display: flex;
        height: 52px;
        min-width: 135px;
        cursor: pointer;
        justify-content: center;
        align-items: center;
        padding-inline: 6px;

        &:hover {
          color: #3a84ff;
        }

        &.active {
          color: #3a84ff;
          background-color: #f0f5ff;
          border-top: 3px solid #3a84ff;
        }
      }
    }
  }

  .docs-main-content {
    width: 1280px;
    margin: auto;

    .content-of-apigw {

      .top-bar {
        display: flex;
        margin-bottom: 16px;
        justify-content: flex-end;
        align-items: center;
      }
    }

    .content-of-component {
      display: flex;
      padding-bottom: 12px;

      .category-list {
        width: 1000px;

        .category-wrap {
          margin-bottom: 4px;

          .top-bar {
            display: flex;
            height: 32px;
            margin-bottom: 16px;
            justify-content: space-between;
            align-items: center;

            .bar-title {
              display: flex;
              align-items: center;
              gap: 24px;

              .title {
                font-size: 16px;
                font-weight: 700;
                line-height: 24px;
                letter-spacing: 0;
                color: #313238;
              }
            }

            .bar-aside {
              display: flex;
              align-items: center;
              gap: 12px;
            }
          }

          .components-wrap {
            max-height: calc(100vh - 200px);
            padding-bottom: 16px;
            overflow-y: auto;

            &::-webkit-scrollbar {
              width: 6px;
              height: 6px;
            }

            &::-webkit-scrollbar-thumb {
              background-color: #dcdee5;
              border-radius: 3px;
            }

            &::-webkit-scrollbar-track {
              background-color: transparent;
              border-radius: 3px;
            }

            .component-group {
              margin-bottom: 16px;
              scroll-margin-top: 68px;

              .group-title {
                display: flex;
                height: 32px;
                margin-bottom: 16px;
                background: #eaebf0;
                border-radius: 2px;
                padding-inline: 16px;
                align-items: center;

                .name {
                  margin-right: 8px;
                  font-size: 14px;
                  color: #313238;
                }

                .count {
                  color: #979ba5;
                }
              }

              .group-items {
                display: flex;
                flex-wrap: wrap;
                gap: 16px;

                .item {
                  position: relative;
                  width: 238px;
                  height: 80px;
                  padding: 16px;
                  background: #fff;
                  border-radius: 2px;
                  box-shadow: 0 2px 4px 0 #1919290d;
                  transition: box-shadow .2s ease-in-out;

                  .title {

                    .name,
                    .name-en {
                      font-size: 14px;
                      line-height: 22px;
                      letter-spacing: 0;
                    }

                    .name {
                      margin-bottom: 5px;
                      color: #313238;
                      transition: color .2s ease-in-out;
                    }

                    .name-en {
                      color: #c4c6cc;
                    }
                  }

                  .background-image {
                    position: absolute;
                    top: 20px;
                    right: 16px;
                    display: flex;
                    width: 40px;
                    height: 40px;
                    font-size: 40px;
                    color: #f0f5ff;
                    align-items: center;
                  }

                  &:hover {
                    cursor: pointer;
                    box-shadow: 0 2px 4px 0 #0000001a, 0 2px 4px 0 #1919290d;

                    .title {

                      .name {
                        color: $primary-color;
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }

      .component-nav-list {
        width: 187px;
        padding-left: 24px;

        :deep(.collapse-cls) {

          .bk-collapse-item {
            box-shadow: none;
          }
        }

        :deep(.bk-collapse-content) {
          padding: 0 !important;
          font-size: 14px;
        }

        .panel-header {
          display: flex;
          padding-bottom: 7px;
          padding-left: 9px;
          cursor: pointer;
          border-left: 1px solid #dcdee5;
          align-items: center;

          .title {
            height: 22px;
          }

          .panel-header-show {
            transform: rotate(0deg);
            transition: .2s;
          }

          .panel-header-hide {
            transform: rotate(-90deg);
            transition: .2s;
          }
        }

        .panel-content {

          .panel-content-cat-item {
            padding-left: 40px;
            line-height: 22px;
            cursor: pointer;
            border-left: 1px solid #dcdee5;
            padding-block: 7px;

            &:hover {
              color: $primary-color;
            }

            &.active {
              border-color: $primary-color;
            }
          }
        }
      }
    }

    &.default-header-view {
      height: calc(100vh - 105px);
      overflow: hidden;

      &.show-notice {
        height: calc(100vh - 145px);

        .components-wrap {
          max-height: calc(100vh - 200px);
        }
      }

      &.need-bkui-table-wrapper {
        overflow-y: hidden;

        :deep(.bk-table-body) {

          &.bk-scrollbar {

            .bk__rail-x,
            .bk__rail-y {
              display: none !important;
            }
          }
        }
      }
    }
  }
}
</style>
