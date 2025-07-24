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
      :class="{ 'pt-24px': featureFlagStore.isTenantMode }"
      class="docs-main-content"
    >
      <!--  当选中 网关API文档 时  -->
      <div
        v-if="curTab === 'gateway'"
        class="content-of-apigw"
      >
        <!--  搜索栏和 SDK使用说明  -->
        <header class="top-bar">
          <bk-input
            v-model="filterData.keyword"
            type="search"
            :placeholder="t('请输入网关名称或描述')"
            clearable
            style="width: 400px"
          />
          <bk-link
            theme="primary"
            class="text-12px ml-24px"
            @click.prevent="isSdkInstructionSliderShow = true"
          >
            <AgIcon name="document" />
            {{ t('SDK 使用说明') }}
          </bk-link>
        </header>
        <!--  网关列表  -->
        <main class="docs-list">
          <bk-loading :loading="isLoading">
            <bk-table
              :data="tableData"
              remote-pagination
              :pagination="pagination"
              show-overflow-tooltip
              :border="['outer']"
              @page-limit-change="handlePageSizeChange"
              @page-value-change="handlePageChange"
            >
              <bk-table-column
                :label="t('网关名称')"
                field="name"
              >
                <template #default="{ row }: { row: IApiGatewayBasics }">
                  <span
                    class="link-name"
                    @click="gotoDetails(row)"
                  >{{ row.name || '--' }}</span>
                  <bk-tag
                    v-if="row.is_official"
                    theme="success"
                  >
                    {{ t('官方') }}
                  </bk-tag>
                </template>
              </bk-table-column>
              <template v-if="featureFlagStore.isTenantMode">
                <bk-table-column
                  :label="t('租户模式')"
                  field="tenant_mode"
                  :width="120"
                >
                  <template #default="{ row }">
                    {{ TENANT_MODE_TEXT_MAP[row.tenant_mode as string] || '--' }}
                  </template>
                </bk-table-column>
                <bk-table-column
                  :label="t('租户 ID')"
                  field="tenant_id"
                  :width="120"
                >
                  <template #default="{ row }">
                    {{ row.tenant_id || '--' }}
                  </template>
                </bk-table-column>
              </template>
              <bk-table-column
                :label="t('网关描述')"
                field="description"
                :min-width="500"
              >
                <template #default="{ row }">
                  {{ row.description || '--' }}
                </template>
              </bk-table-column>
              <bk-table-column
                v-if="!featureFlagStore.isTenantMode"
                :label="t('网关负责人')"
                field="maintainers"
                :show-overflow-tooltip="false"
                placement="auto-start"
              >
                <template #default="{ row }">
                  <bk-popover
                    :component-event-delay="300"
                    :width="480"
                  >
                    <span v-if="!row.maintainers">
                      --
                    </span>
                    <div
                      v-else
                      style="overflow: hidden;text-overflow: ellipsis;white-space: nowrap;"
                    >
                      <template
                        v-for="(maintainer, index) in row.maintainers"
                        :key="maintainer.login_name"
                      >
                        <span>
                          <bk-user-display-name
                            :user-id="maintainer"
                          /><span v-if="index !== (row.maintainers.length - 1)">,</span>
                        </span>
                      </template>
                    </div>
                    <template #content>
                      <div>
                        <template
                          v-for="(maintainer, index) in row.maintainers"
                          :key="maintainer.login_name"
                        >
                          <bk-user-display-name
                            :user-id="maintainer"
                          />
                          <span v-if="index !== (row.maintainers.length - 1)">,</span>
                        </template>
                      </div>
                    </template>
                  </bk-popover>
                </template>
              </bk-table-column>
              <bk-table-column
                :label="t('操作')"
                width="180"
                fixed="right"
              >
                <template #default="{ row }: { row: IApiGatewayBasics }">
                  <bk-button
                    v-bk-tooltips="{ content: t('SDK未生成，可联系负责人生成SDK'), disabled: row.sdks?.length }"
                    text
                    theme="primary"
                    :disabled="!row.sdks?.length"
                    @click="handleSdkDetailClick(row)"
                  >
                    {{ t('查看 SDK') }}
                  </bk-button>
                </template>
              </bk-table-column>
              <template #empty>
                <TableEmpty
                  :keyword="tableEmptyConf.keyword"
                  :abnormal="tableEmptyConf.isAbnormal"
                  @reacquire="getList"
                  @clear-filter="handleClearFilterKey"
                />
              </template>
            </bk-table>
          </bk-loading>
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
                <bk-link
                  v-bk-tooltips="{ content: t('SDK未生成，可联系负责人生成SDK'), disabled: systemBoard.sdk?.sdk_download_url }"
                  :href="systemBoard.sdk?.sdk_download_url"
                  :disabled="!systemBoard.sdk?.sdk_download_url"
                  target="_blank"
                  theme="primary"
                  class="text-12px"
                  @click.prevent="handleESBSdkDetailClick(systemBoard)"
                >
                  {{ t('查看 SDK') }}
                </bk-link>
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
                <bk-link
                  theme="primary"
                  class="text-12px"
                  @click.prevent="isSdkInstructionSliderShow = true"
                >
                  <AgIcon name="document" />
                  {{ t('SDK 使用说明') }}
                </bk-link>
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
        <bk-affix :offset-top="128">
          <aside class="component-nav-list">
            <bk-collapse
              v-model="navPanelNamesList"
              class="collapse-cls"
              use-card-theme
            >
              <bk-collapse-panel
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
              </bk-collapse-panel>
            </bk-collapse>
          </aside>
        </bk-affix>
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

<script lang="ts" setup>
import { useQueryList } from '@/hooks';
import {
  getComponentSystemList,
  getESBSDKlist,
} from '@/services/source/docs-esb';
import { getGatewaysDocs } from '@/services/source/docs';
import { useMaxTableLimit } from '@/hooks/use-max-table-limit';
import TableEmpty from '@/components/table-empty/index.vue';
import SDKInstructionSlider from './components/SDKInstructionSlider.vue';
import SDKDetailDialog from './components/SDKDetailDialog.vue';
import ComponentSearcher from './components/ComponentSearcher.vue';
import {
  type IApiGatewayBasics,
  type IBoard,
  type ICategory,
  type IComponentSdk,
  type ISdk,
  type ISystem,
  type TabType,
} from './types';
import { AngleUpFill } from 'bkui-vue/lib/icon';
import { useTemplateRefsList } from '@vueuse/core';
import { TENANT_MODE_TEXT_MAP } from '@/enums';
import { useFeatureFlag } from '@/stores';

const { t } = useI18n();
const route = useRoute();
const router = useRouter();
const featureFlagStore = useFeatureFlag();

const filterData = ref({ keyword: '' });

// 当前视口高度能展示最多多少条表格数据
const { maxTableLimit } = useMaxTableLimit({ hasAllocatedHeight: 271 });

const {
  tableData,
  pagination,
  isLoading,
  handlePageChange,
  handlePageSizeChange,
  getList,
} = useQueryList({
  apiMethod: getGatewaysDocs,
  filterData,
  id: null,
  filterNoResetPage: false,
  initialPagination: {
    limitList: [
      maxTableLimit,
      10,
      20,
      50,
      100,
    ],
    limit: maxTableLimit,
  },
});

// 组件分类模板引用列表
const categoryRefs = useTemplateRefsList<HTMLElement>();

const tableEmptyConf = ref<{
  keyword: string
  isAbnormal: boolean
}>({
  keyword: '',
  isAbnormal: false,
});

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

watch(
  tableData,
  () => {
    updateTableEmptyConfig();
  },
  { deep: true },
);

const gotoDetails = (row: IApiGatewayBasics | ISystem, systemBoard?: string) => {
  const params = {
    targetName: row.name,
    curTab: curTab.value,
  };

  if (curTab.value === 'component') {
    Object.assign(params, { board: systemBoard || 'default' });
  }

  router.push({
    name: 'apiDocDetail',
    params,
  });
};

const handleClearFilterKey = () => {
  filterData.value = { keyword: '' };
  getList();
  updateTableEmptyConfig();
};

const updateTableEmptyConfig = () => {
  const searchParams = { ...filterData.value };
  const list = Object.values(searchParams).filter(item => item !== '');
  tableEmptyConf.value.isAbnormal = pagination.value.abnormal;
  if (list.length && !tableData.value.length) {
    tableEmptyConf.value.keyword = 'placeholder';
    return;
  }
  if (list.length) {
    tableEmptyConf.value.keyword = '$CONSTANT';
    return;
  }
  tableEmptyConf.value.keyword = '';
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
        width: 135px;
        height: 52px;
        cursor: pointer;
        justify-content: center;
        align-items: center;

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

      .link-name {
        color: #3a84ff;
        cursor: pointer;
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

                    .name, .name-en {
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

  }
}
</style>
