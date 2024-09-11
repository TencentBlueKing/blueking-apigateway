<template>
  <div class="docs-main" ref="docsMain">
    <!--  顶部 网关 / 组件 Tab  -->
    <header class="page-tabs">
      <nav class="tabs-group">
        <section
          class="page-tab"
          :class="{ 'active': curTab === 'apigw' }"
          @click="curTab = 'apigw'"
        >{{ t('网关 API 文档') }}
        </section>
        <section
          class="page-tab"
          :class="{ 'active': curTab === 'component' }"
          @click="curTab = 'component'"
        >{{ t('组件 API 文档') }}
        </section>
      </nav>
    </header>
    <!--  正文  -->
    <main class="docs-main-content">
      <!--  当选中 网关API文档 时  -->
      <div v-if="curTab === 'apigw'" class="content-of-apigw">
        <!--  搜索栏和 SDK使用说明  -->
        <header class="top-bar">
          <bk-input
            type="search"
            :placeholder="t('请输入网关名称或描述')"
            v-model="filterData.keyword"
            clearable
            style="width: 400px"
          />
          <bk-link theme="primary" class="f12 ml24" @click.prevent="isSdkInstructionSliderShow = true">
            <i class="apigateway-icon icon-ag-document f14"></i>
            {{ t('SDK 使用说明') }}
          </bk-link>
          <!-- <bk-button
            theme="primary"
            @click="handleGoApigw"
          >
            {{ t('网关管理') }}
          </bk-button> -->
        </header>
        <!--  网关列表  -->
        <main class="docs-list">
          <bk-loading :loading="isLoading">
            <bk-table
              :data="tableData"
              remote-pagination
              :pagination="pagination"
              show-overflow-tooltip
              @page-limit-change="handlePageSizeChange"
              @page-value-change="handlePageChange"
              :border="['outer']"
            >
              <bk-table-column
                :label="t('网关名称')"
                field="name"
              >
                <template #default="{ row }: { row: IApiGatewayBasics }">
                  <span class="link-name" @click="gotoDetails(row)">{{ row.name || '--' }}</span>
                  <bk-tag theme="success" v-if="row.is_official">
                    {{ t('官方') }}
                  </bk-tag>
                </template>
              </bk-table-column>
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
                :label="t('网关负责人')"
                field="maintainers"
              >
                <template #default="{ row }">
                  {{ row.maintainers?.join(', ') || '--' }}
                </template>
              </bk-table-column>
              <!--  <bk-table-column
                :label="t('SDK 包名称')"
                field="maintainers"
              >
                <template #default="{ row }">
                  {{ row?.sdk?.name || '&#45;&#45;' }}
                </template>
              </bk-table-column>
              <bk-table-column
                :label="t('SDK 最新版本')"
                field="maintainers"
              >
                <template #default="{ row }">
                  {{ row?.sdk?.version || '&#45;&#45;' }}
                </template>
              </bk-table-column>-->
              <bk-table-column
                :label="t('操作')"
                width="180"
                fixed="right"
              >
                <template #default="{ row }: { row: IApiGatewayBasics }">
                  <bk-button
                    text
                    theme="primary"
                    :disabled="!row.sdks?.length"
                    v-bk-tooltips="{ content: t('SDK未生成，可联系负责人生成SDK'), disabled: row.sdks?.length }"
                    @click="handleSdkDetailClick(row)"
                  >
                    {{ t('查看 SDK') }}
                  </bk-button>
                  <!--                  <a-->
                  <!--                    class="ag-link pl10 pr10"-->
                  <!--        :href="row?.sdk_download_url ?? ''"-->
                  <!--                  >-->
                  <!--                    {{ t('下载 SDK') }}-->
                  <!--                  </a>-->
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
      <div v-else-if="curTab === 'component'" class="content-of-component">
        <main class="category-list">
          <article class="category-wrap" v-for="systemBoard in componentSystemList" :key="systemBoard.board">
            <!--  system 类别 title 和搜索栏  -->
            <header class="top-bar">
              <main class="bar-title">
                <span class="title">{{ systemBoard.board_label }}</span>
                <bk-link theme="primary" class="f12" @click.prevent="isSdkInstructionSliderShow = true">
                  <i class="apigateway-icon icon-ag-document f14"></i>
                  {{ t('查看 SDK') }}
                </bk-link>
                <bk-link
                  :href="systemBoard.sdk?.sdk_download_url"
                  :disabled="!systemBoard.sdk?.sdk_download_url"
                  theme="primary"
                  v-bk-tooltips="{ content: t('SDK未生成，可联系负责人生成SDK'), disabled: systemBoard.sdk?.sdk_download_url }"
                  class="f12"
                >
                  <i class="apigateway-icon icon-ag-download f14"></i>
                  {{ t('下载 SDK') }}
                </bk-link>
              </main>
              <aside v-if="componentSystemList.length > 0">
                <ComponentSearcher class="ag-searcher-box" :version-list="componentSystemList"></ComponentSearcher>
              </aside>
            </header>
            <!--  组件  -->
            <main class="components-wrap">
              <!--  组件分类  -->
              <article
                class="component-group"
                v-for="cat in systemBoard.categories"
                :key="cat.id"
                :data-_nav-id="`${systemBoard.board}-${cat.id}`"
                :ref="categoryRefs.set"
              >
                <header class="group-title">
                  <span class="name">{{ cat.name }}</span>
                  <span class="count">{{ `(${cat.systems.length})` }}</span>
                </header>
                <!--  分类中的组件卡片  -->
                <main class="group-items">
                  <article
                    class="item"
                    v-for="system in cat.systems"
                    :key="system.name"
                    @click="gotoDetails(system)"
                  >
                    <main class="title">
                      <div class="name">{{ system.description }}</div>
                      <div class="name-en">{{ system.name }}</div>
                    </main>
                    <aside class="background-image">
                      <i class="apigateway-icon icon-ag-component-intro"></i>
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
              class="collapse-cls"
              v-model="navPanelNamesList"
              use-card-theme
            >
              <bk-collapse-panel
                v-for="systemBoard in componentSystemList"
                :key="systemBoard.board"
                :name="systemBoard.board"
              >
                <template #header>
                  <div class="panel-header">
                    <main class="flex-row align-items-center">
                      <angle-up-fill
                        :class="[
                          navPanelNamesList.includes(systemBoard.board) ? 'panel-header-show' : 'panel-header-hide'
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
                    >{{ cat.name }}
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
    <SdkInstructionSlider v-model="isSdkInstructionSliderShow"></SdkInstructionSlider>
    <!--  网关 SDK 地址 dialog  -->
    <SdkDetailDialog v-model="isSdkDetailDialogShow" :sdks="curSdks" :apigw-name="curTargetName"></SdkDetailDialog>
  </div>
</template>

<script lang="ts" setup>
import {
  onBeforeMount,
  onMounted,
  provide,
  ref,
  watch,
} from 'vue';
import { useQueryList } from '@/hooks';
import { useI18n } from 'vue-i18n';
import {
  getComponentSystemList,
  getGatewaysDocs,
} from '@/http';
import {
  useRoute,
  useRouter,
} from 'vue-router';
import useMaxTableLimit from '@/hooks/use-max-table-limit';
import TableEmpty from '@/components/table-empty.vue';
import SdkInstructionSlider from '@/views/apiDocs/components/sdk-instruction-slider.vue';
import SdkDetailDialog from '@/views/apiDocs/components/sdk-detail-dialog.vue';
import ComponentSearcher from '@/views/apiDocs/components/component-searcher.vue';
import {
  IApiGatewayBasics,
  ICategory,
  ISdk,
  IBoard,
  TabType,
  ISystem,
} from '@/views/apiDocs/types';
import { AngleUpFill } from 'bkui-vue/lib/icon';
import { useTemplateRefsList } from '@vueuse/core';

const { t } = useI18n();
const route = useRoute();
const router = useRouter();

const filterData = ref({ keyword: '' });

const {
  tableData,
  pagination,
  isLoading,
  handlePageChange,
  handlePageSizeChange,
  getList,
} = useQueryList(getGatewaysDocs, filterData, null, true);

// 组件分类模板引用列表
const categoryRefs = useTemplateRefsList<HTMLElement>();

// 当前视口高度能展示最多多少条表格数据
const maxTableLimit = ref(10);
maxTableLimit.value = useMaxTableLimit(271);

// 注意，pagination 的 limit 必须在 limitList 里才能生效
// 所以要先放进 limitList 里
pagination.value.limitList.unshift(maxTableLimit.value);
pagination.value.limit = maxTableLimit.value;

const tableEmptyConf = ref<{ keyword: string, isAbnormal: boolean }>({
  keyword: '',
  isAbnormal: false,
});

// 当前展示的是 网关 | 组件 相关内容
const curTab = ref<TabType>('apigw');
const curTargetName = ref('');
const board = ref('default');
const curCategoryNavId = ref('');
const navPanelNamesList = ref<string[]>([]);
const isSdkInstructionSliderShow = ref(false);
const isSdkDetailDialogShow = ref(false);
const componentSystemList = ref<IBoard[]>([]); // 组件系统列表
const curSdks = ref<ISdk[]>([]);

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

const gotoDetails = (row: IApiGatewayBasics | ISystem) => {
  router.push({
    name: 'apiDocDetail',
    params: {
      targetName: row.name,
      curTab: curTab.value,
    },
  });
};

const handleClearFilterKey = () => {
  filterData.value = { keyword: '' };
  getList();
  updateTableEmptyConfig();
};

const updateTableEmptyConfig = () => {
  const searchParams = {
    ...filterData.value,
  };
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
    const res = await getComponentSystemList(board.value) as IBoard[];
    res.forEach((system) => {
      // 给组件分类添加一个跳转用的 _navId
      system.categories.forEach((cat) => {
        cat._navId = `${system.board}-${cat.id}`;
      });
      componentSystemList.value.push(system);
      navPanelNamesList.value.push(system.board);
    });
  } catch {
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
};

onBeforeMount(() => {
  const { params } = route;
  // 记录返回到此页时选中的 tab
  curTab.value = params.curTab as TabType || 'apigw';
});

onMounted(async () => {
  await fetchComponentSystemList();
});

</script>

<style lang="scss" scoped>
$primary-color: #3a84ff;

.docs-main {

  .page-tabs {
    height: 52px;
    margin-bottom: 24px;
    position: sticky;
    top: 0;
    display: flex;
    justify-content: center;
    align-items: center;
    background: #fff;
    box-shadow: 0 3px 4px 0 #0000000a;
    z-index: 2;

    .tabs-group {
      display: flex;
      justify-content: center;

      .page-tab {
        width: 135px;
        height: 52px;
        display: flex;
        justify-content: center;
        align-items: center;
        cursor: pointer;

        &:hover {
          color: #3a84ff;
        }

        &.active {
          background-color: #f0f5ff;
          border-top: 3px solid #3a84ff;
          color: #3a84ff;
        }
      }
    }
  }

  .docs-main-content {
    width: 1280px;
    margin: auto;

    .content-of-apigw {
      .top-bar {
        margin-bottom: 16px;
        display: flex;
        justify-content: flex-end;
        align-items: center;
      }

      .link-name {
        color: #3a84ff;
        cursor: pointer;
      }
    }

    .content-of-component {
      padding-bottom: 12px;
      display: flex;

      .category-list {
        width: 1000px;

        .category-wrap {
          margin-bottom: 4px;

          .top-bar {
            margin-bottom: 16px;
            height: 32px;
            display: flex;
            justify-content: space-between;
            align-items: center;

            .bar-title {
              display: flex;
              align-items: center;
              gap: 24px;

              .title {
                font-weight: 700;
                font-size: 16px;
                color: #313238;
                letter-spacing: 0;
                line-height: 24px;
              }
            }
          }

          .components-wrap {
            .component-group {
              margin-bottom: 16px;
              scroll-margin-top: 68px;

              .group-title {
                padding-inline: 16px;
                margin-bottom: 16px;
                height: 32px;
                display: flex;
                align-items: center;
                border-radius: 2px;
                background: #eaebf0;

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
                  padding: 16px;
                  width: 238px;
                  height: 80px;
                  background: #fff;
                  box-shadow: 0 2px 4px 0 #1919290d;
                  border-radius: 2px;
                  transition: box-shadow .2s ease-in-out;

                  .title {
                    .name, .name-en {
                      font-size: 14px;
                      letter-spacing: 0;
                      line-height: 22px;
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
                    width: 40px;
                    height: 40px;
                    display: flex;
                    align-items: center;
                    font-size: 40px;
                    color: #f0f5ff;
                  }

                  &:hover {
                    box-shadow: 0 2px 4px 0 #0000001a, 0 2px 4px 0 #1919290d;
                    cursor: pointer;

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
        padding-left: 24px;
        width: 187px;

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
          padding-left: 9px;
          padding-bottom: 7px;
          display: flex;
          align-items: center;
          border-left: 1px solid #dcdee5;
          cursor: pointer;

          .title {
            height: 22px;
          }

          .panel-header-show {
            transition: .2s;
            transform: rotate(0deg);
          }

          .panel-header-hide {
            transition: .2s;
            transform: rotate(-90deg);
          }
        }

        .panel-content {

          .panel-content-cat-item {
            padding-left: 40px;
            padding-block: 7px;
            line-height: 22px;
            border-left: 1px solid #dcdee5;
            cursor: pointer;

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
