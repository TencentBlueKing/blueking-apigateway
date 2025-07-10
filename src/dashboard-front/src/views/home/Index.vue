<template>
  <div class="home-container">
    <div class="title-container">
      <div class="left">
        <BkButton
          theme="primary"
          class="mr-4px"
          @click="showAddDialog"
        >
          {{ t('新建网关') }}
        </BkButton>
      </div>

      <div class="flex flex-grow-1">
        <BkSelect
          v-model="filterNameData.kind"
          class="gateway-kind-sel"
          :clearable="false"
          :filterable="false"
        >
          <BkOption
            v-for="item in gatewayTypes"
            :id="item.value"
            :key="item.value"
            :name="item.label"
          />
        </BkSelect>
        <BkInput
          v-model="filterNameData.keyword"
          class="mx-8px flex-grow-1"
          :placeholder="t('请输入网关名称')"
        />
        <BkSelect
          v-model="filterKey"
          :clearable="false"
          class="select-cls"
          @change="handleChange"
        >
          <template #prefix>
            <div class="prefix-cls">
              <i class="icon apigateway-icon icon-ag-exchange-line pb-5px" />
            </div>
          </template>
          <BkOption
            v-for="(item, index) in filterData"
            :key="index"
            :value="item.value"
            :label="item.label"
          />
        </BkSelect>
      </div>
    </div>

    <div
      v-bkloading="{ loading: isLoading, opacity: 1, color: '#f5f7fb' }"
      class="table-container"
    >
      <section v-if="gatewaysList.length">
        <div class="table-header">
          <div
            :class="featureFlagStore.isTenantMode ? 'of2' : 'of3'"
            class="flex-grow-1"
          >
            {{ t('网关名') }}
          </div>
          <template v-if="featureFlagStore.isTenantMode">
            <div class="flex-grow-1 of1">
              {{ t('租户模式') }}
            </div>
            <div class="flex-grow-1 of1">
              {{ t('租户 ID') }}
            </div>
          </template>
          <div class="flex-grow-1 of1">
            {{ t('创建者') }}
          </div>
          <div
            :class="featureFlagStore.isTenantMode ? 'of2' : 'of3'"
            class="flex-grow-1"
          >
            {{ t('环境列表') }}
          </div>
          <div class="flex-grow-1 of1 text-center">
            {{ t('资源数量') }}
          </div>
          <div class="flex-grow-1 of2">
            {{ t('操作') }}
          </div>
        </div>
        <div class="table-list">
          <div
            v-for="item in gatewaysList"
            :key="item.id"
            class="table-item"
            :class="item.isAfter24h ? '' : 'newly-item'"
          >
            <div
              class="flex-grow-1 flex items-center"
              :class="featureFlagStore.isTenantMode ? 'of2' : 'of3'"
            >
              <div
                :class="item.status ? '' : 'deact'"
                class="name-logo"
                @click="handleGoPage('StageManagement', item)"
              >
                <span
                  v-if="item.kind === 1"
                  v-bk-tooltips="{ content: t('可编程网关') }"
                  class="kind-program"
                >
                  <i class="apigateway-icon icon-ag-program" />
                </span>
                {{ item.name[0].toUpperCase() }}
              </div>
              <span
                :class="item.status ? '' : 'deact-name'"
                class="name"
                @click="handleGoPage('StageManagement', item)"
              >
                {{ item.name }}
              </span>
              <BkTag
                v-if="item.is_official"
                theme="info"
              >
                {{ t('官方') }}
              </BkTag>
              <BkTag v-if="item.status === 0">
                {{ t('已停用') }}
              </BkTag>
            </div>
            <template v-if="featureFlagStore.isTenantMode">
              <div class="flex-grow-1 of1">
                {{ TENANT_MODE_TEXT_MAP[item.tenant_mode as string] || '--' }}
              </div>
              <div class="flex-grow-1 of1">
                {{ item.tenant_id || '--' }}
              </div>
            </template>
            <div class="flex-grow-1 of1">
              <span>{{ item.created_by }}</span>
            </div>
            <div
              :class="featureFlagStore.isTenantMode ? 'of2' : 'of3'"
              class="env"
            >
              <div class="flex">
                <span
                  v-for="(envItem, index) in item.stages"
                  :key="envItem.id"
                >
                  <BkTag
                    v-if="index < 3"
                    class="environment-tag"
                  >
                    <i
                      class="ag-dot"
                      :class="[{ 'success': envItem.released }]"
                    />
                    {{ envItem.name }}
                  </BkTag>
                </span>
                <BkTag
                  v-if="item.stages.length > Number(item.tagOrder)"
                  v-bk-tooltips="{ content: tipsContent(item?.labelTextData), theme: 'light', placement: 'bottom' }"
                  class="tag-cls"
                >
                  +{{ item.stages.length - Number(item.tagOrder) }}
                </BkTag>
              </div>
            </div>
            <div
              class="flex-grow-1 of1 text-center"
              :class="[
                { 'color-#3A84FF': item.hasOwnProperty('resource_count') }
              ]"
            >
              <template v-if="item.kind === 0">
                {{ item.resource_count }}
                <!--                <router-link -->
                <!--                  :to="{ name: 'apigwResource', params: { id: item.id } }" -->
                <!--                  target="_blank" -->
                <!--                > -->
                <!--                  <span :style="{ color: item.resource_count === 0 ? '#c4c6cc' : '#3a84ff' }"> -->
                <!--                    {{ item.resource_count }} -->
                <!--                  </span> -->
                <!--                </router-link> -->
              </template>
              <template v-else>
                <span class="none">{{ item.resource_count }}</span>
              </template>
            </div>
            <div class="flex-grow-1 of2">
              <BkButton
                text
                theme="primary"
                @click="handleGoPage('apigwStageOverview', item)"
              >
                {{ t('环境概览') }}
              </BkButton>
              <BkButton
                text
                theme="primary"
                class="ml-20px"
                :disabled="item?.kind === 1"
                @click="handleGoPage('apigwResource', item)"
              >
                {{ t('资源配置') }}
              </BkButton>
              <BkButton
                text
                theme="primary"
                class="ml-20px"
                @click="handleGoPage('apigwAccessLog', item)"
              >
                {{ t('流水日志') }}
              </BkButton>
            </div>
          </div>
        </div>
      </section>
      <div
        v-else
        class="empty-container"
      >
        <div class="table-header">
          <div class="flex-grow-1 of3">
            {{ t('网关名') }}
          </div>
          <div class="flex-grow-1 of1">
            {{ t('创建者') }}
          </div>
          <div class="flex-grow-1 of3">
            {{ t('环境列表') }}
          </div>
          <div class="flex-grow-1 of1 text-center">
            {{ t('资源数量') }}
          </div>
          <div class="flex-grow-1 of2">
            {{ t('操作') }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { isAfter24h } from '@/utils';
import { useFeatureFlag } from '@/stores';
import { TENANT_MODE_TEXT_MAP } from '@/enums';
import { getGatewayList } from '@/services/source/gateway.ts';

type GatewayType = Awaited<ReturnType<typeof getGatewayList>>['results'][number];

type ConvertedGatewayType = GatewayType & {
  isAfter24h: boolean
  tagOrder: string
  labelTextData: {
    name: string
    released: boolean
  }[]
};

const { t } = useI18n();
const router = useRouter();
const featureFlagStore = useFeatureFlag();

const filterKey = ref('updated_time');
const filterNameData = ref({
  keyword: '',
  kind: 'all',
});
const createGatewayShow = ref(false);
const gatewayTypes = ref([
  {
    label: t('全部'),
    value: 'all',
  },
  {
    label: t('普通网关'),
    value: '0',
  },
  {
    label: t('可编程网关'),
    value: '1',
  },
]);

const isLoading = ref(true);
// 网关列表数据
const gatewaysList = ref<ConvertedGatewayType[]>([]);

const filterData = ref([
  {
    value: 'updated_time',
    label: t('更新时间'),
  },
  {
    value: 'created_time',
    label: t('创建时间'),
  },
  {
    value: 'name',
    label: t('字母 A-Z'),
  },
]);

// 处理列表项
const convertGatewaysList = (arr: GatewayType[]): ConvertedGatewayType[] => {
  if (!arr) {
    return [];
  }

  return arr.map((gateway) => {
    const item: any = { ...gateway };
    item.isAfter24h = isAfter24h(item.created_time);
    item.tagOrder = '3';
    item.stages?.sort((a: any, b: any) => (b.released - a.released));
    item.labelTextData = item.stages.reduce((prev: any, label: any, index: number) => {
      if (index > item.tagOrder - 1) {
        prev.push({
          name: label.name,
          released: label.released,
        });
      }
      return prev;
    }, []);
    return item;
  });
};

// 页面初始化
const init = async () => {
  isLoading.value = true;
  const response = await getGatewayList({ limit: 10000 });
  gatewaysList.value = convertGatewaysList(response.results || []);
  setTimeout(() => {
    isLoading.value = false;
  }, 100);
};

const showAddDialog = () => {
  createGatewayShow.value = true;
};

const handleGoPage = (routeName: string, gateway: GatewayType) => {
  router.push({
    name: routeName,
    params: { id: gateway.id },
  });
};

// 列表排序
const handleChange = (v: string) => {
  switch (v) {
    case 'created_time':
      // @ts-expect-error ignore
      gatewaysList.value.sort((a, b) => new Date(b.created_time) - new Date(a.created_time));
      break;
    case 'updated_time':
      // @ts-expect-error ignore
      gatewaysList.value.sort((a, b) => new Date(b.updated_time) - new Date(a.updated_time));
      break;
    case 'name':
      gatewaysList.value.sort((a, b) => a.name.charAt(0).localeCompare(b.name.charAt(0)));
      break;
    default:
      break;
  }
};

const tipsContent = (data: any[]) => {
  return h('div', {}, [
    data.map((item: any) => h('div', {
      style: 'display: flex; align-items: center; margin-top: 5px',
      class: 'tips-cls',
    }, [h('i', {
      class: `ag-dot ${item.released ? 'success' : ''}`,
      style: 'margin-right: 5px',
    }),
    item.name])),
  ]);
};

onMounted(() => {
  init();
});
</script>

<style lang="scss" scoped>
.create-gw-form {

  .form-item-name {

    :deep(.bk-form-error) {
      position: relative;
    }
  }

  .form-item-name-tips {
    position: relative;
    top: -24px;
  }
}

.home-container {
  width: 80%;
  min-width: 1200px;
  margin: 0 auto;
  font-size: 14px;

  .title-container {
    position: sticky;
    top: 0;
    z-index: 9;
    display: flex;
    justify-content: space-between;
    width: 100%;
    padding: 28px 16px;
    background-color: #f5f7fa;

    .left {
      font-size: 20px;
      color: #313238;
      flex: 0 0 60%;
      flex-grow: 1;
    }
  }

  .gateway-kind-sel {
    width: 150px;
  }

  .select-cls {
    flex-shrink: 0;
    width: 126px;

    :deep(.bk-select-trigger) {
      background-color: #fff;
    }

    :deep(.bk-input) {
      padding: 0 10px;
      font-size: 14px;
    }

    :deep(.angle-up) {
      width: 24px;
      height: 32px;
      font-size: 24px;
    }

    :deep(.bk-input--text) {
      padding-right: 4px;
    }

    .prefix-cls {
      display: flex;
      color: #979ba5;
      background: #fff;
      align-items: center;

      i {
        font-size: 16px;
        transform: rotate(90deg);
      }
    }
  }

  .table-container {
    width: 100%;
    min-height: calc(100vh - 192px);

    .table-header {
      position: sticky;
      top: 88px;
      z-index: 999;
      display: flex;
      width: 100%;
      padding: 0 16px 10px;
      color: #979ba5;
      background-color: #f5f7fa;
    }

    .table-list {
      height: calc(100% - 45px);
      padding-right: 2px;
      overflow-y: auto;

      .table-item {
        display: flex;
        width: 100%;
        height: 80px;
        padding: 0 16px;
        margin: 12px 0;
        background: #FFF;
        border-radius: 2px;
        box-shadow: 0 2px 4px 0 #1919290d;
        align-items: center;

        .name-logo {
          position: relative;
          width: 48px;
          height: 48px;
          margin-right: 10px;
          font-size: 26px;
          font-weight: 700;
          line-height: 48px;
          color: #3A84FF;
          text-align: center;
          cursor: pointer;
          background: #F0F5FF;
          border-radius: 4px;

          .kind-program {
            position: absolute;
            top: 0;
            left: 0;
            font-size: 12px;
            line-height: 12px;
            color: #3A84FF;
          }
        }

        .name {
          margin-right: 10px;
          font-weight: 700;
          color: #313238;
          cursor: pointer;

          &:hover {
            color: #3a84ff;
          }
        }

        .env {
          overflow: hidden;
          flex-grow: 1;
        }

        .environment-tag {
          margin-right: 8px;
        }
      }

      .table-item:nth-of-type(1) {
        margin-top: 0
      };

      .newly-item {
        background: #F2FFF4;
      }
    }

    .of1 {
      flex: 0 0 10%;
    }

    .of3 {
      flex: 0 0 30%;
    }

    .empty-table {

      :deep(.bk-table-head) {
        display: none;
      }
    }

    .empty-container {

      .table-header {
        display: flex;
      }

      .empty-exception {
        padding-bottom: 40px;
        background-color: #fff;
      }
    }
  }

  .footer-container {
    position: relative;
    left: 0;
    display: flex;
    height: 50px;
    font-size: 12px;
    line-height: 20px;
    flex-flow: column;
    align-items: center;
  }

  .deact {
    color: #fff !important;
    background: #EAEBF0 !important;

    .deact-name {
      color: #979BA5 !important;
    }
  }

  .default-c {
    cursor: pointer;
  }

  .none {
    color: #C4C6CC;
    cursor: auto;
  }
}

.ag-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  vertical-align: middle;
  border: 1px solid #c4c6cc;
  border-radius: 50%;
}

.success {
  background: #e5f6ea;
  border: 1px solid #3fc06d;
}

.tips-cls {
  padding: 3px 8px;
  cursor: default;
  background: #f0f1f5;
  border-radius: 2px;

  &:hover {
    background: #d7d9e1 !important;
  }
}
</style>
