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
  <div
    v-bkloading="{ loading: isLoading || initLoading, opacity: 1, color: '#f5f7fb' }"
    class="home-loading"
  >
    <div
      v-if="!isGuide"
      class="home-container"
    >
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
            class="min-w-150px"
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
                <AgIcon
                  name="exchange-line"
                  class="pb-5px"
                />
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

      <div class="table-container">
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
            <div class="flex-grow-1 of1">
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
            >
              <div
                class="flex-grow-1 flex items-center"
                :class="featureFlagStore.isTenantMode ? 'of2' : 'of3'"
              >
                <div
                  :class="item.status ? '' : 'deact'"
                  class="name-logo"
                  @click="() => handleGoPage('StageManagement', item)"
                >
                  <span
                    v-if="item.kind === 1"
                    v-bk-tooltips="{ content: t('可编程网关') }"
                    class="kind-program"
                  >
                    <AgIcon
                      name="program"
                      size="12"
                    />
                  </span>
                  {{ item.name[0].toUpperCase() }}
                </div>
                <span
                  :class="item.status ? '' : 'deact-name'"
                  class="name"
                  @click="() => handleGoPage('StageManagement', item)"
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
                <span v-if="!featureFlagStore.isEnableDisplayName">{{ item.created_by }}</span>
                <span v-else><bk-user-display-name :user-id="item.created_by" /></span>
              </div>
              <div
                :class="featureFlagStore.isEnableDisplayName ? 'of2' : 'of3'"
                class="env flex-grow-1"
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
                class="flex-grow-1 of1 pl-4"
                :class="[
                  { 'color-#3A84FF': item.hasOwnProperty('resource_count') }
                ]"
              >
                <template v-if="item.kind === 0">
                  {{ item.resource_count }}
                <!--                <RouterLink -->
                <!--                  :to="{ name: 'ResourceSetting', params: { id: item.id } }" -->
                <!--                  target="_blank" -->
                <!--                > -->
                <!--                  <span :style="{ color: item.resource_count === 0 ? '#c4c6cc' : '#3a84ff' }"> -->
                <!--                    {{ item.resource_count }} -->
                <!--                  </span> -->
                <!--                </RouterLink> -->
                </template>
                <template v-else>
                  <span class="none">{{ item.resource_count }}</span>
                </template>
              </div>
              <div class="flex-grow-1 of2">
                <BkButton
                  text
                  theme="primary"
                  @click="() => handleGoPage('StageOverview', item)"
                >
                  {{ t('环境概览') }}
                </BkButton>
                <BkButton
                  text
                  theme="primary"
                  class="ml-20px"
                  :disabled="item?.kind === 1"
                  @click="() => handleGoPage('ResourceSetting', item)"
                >
                  {{ t('资源配置') }}
                </BkButton>
                <BkButton
                  text
                  theme="primary"
                  class="ml-20px"
                  @click="() => handleGoPage('AccessLog', item)"
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
            <div class="flex-grow-1 of1">
              {{ t('资源数量') }}
            </div>
            <div class="flex-grow-1 of2">
              {{ t('操作') }}
            </div>
          </div>
          <TableEmpty
            background="#f5f7fa"
            :empty-type="tableEmptyConf.emptyType"
            :abnormal="tableEmptyConf.isAbnormal"
            @refresh="getGatewaysListData"
            @clear-filter="handleClearFilterKey"
          />
        </div>
      </div>
    </div>

    <div
      v-else
      class="gateway-empty"
    >
      <div class="create-guide">
        <div class="guide-title">
          {{ t('当前暂无网关，请先创建') }}
        </div>
        <div class="guide-describe">
          {{ t('蓝鲸 API 网关（ APIGateway ），是一种高性能、高可用的 API 托管服务，可以帮助开发者创建、发布、维护、监控和保护 API ，') }}
          {{ t('以快速、低成本、低风险地对外开放蓝鲸应用或其他系统的数据或服务。') }}
        </div>
        <div class="guide-opt">
          <BkButton
            theme="primary"
            class="mr8"
            @click="showAddDialog"
          >
            {{ t('新建网关') }}
          </BkButton>
          <bk-button @click="handleViewDoc">
            {{ t('查看 API 文档') }}
          </bk-button>
        </div>
      </div>

      <div class="work-progress">
        <div class="progress-img">
          <img
            :src="progressImg"
            :alt="t('网关工作流')"
          >
        </div>
        <div class="steps">
          <div
            v-for="item in envStore.env.EDITION === 'te' ? steps : steps?.filter(item => item.name !== t('可观测：'))"
            :key="item.name"
            class="step"
          >
            <div class="name">
              {{ item.name }}
            </div>
            <BkLink
              v-if="item.link"
              :href="item.link"
              target="_blank"
              class="describe link"
            >
              {{ item.describe }}
            </BkLink>
            <div
              v-else
              class="describe"
            >
              {{ item.describe }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <div
    class="footer-container "
    :class="{'empty': isGuide}"
  >
    <p class="contact">
      <BkLink
        class="text-12px color-#3a84ff!"
        :href="contacts[0].link"
        target="_blank"
      >
        {{ contacts[0].text }}
      </BkLink>
      |
      <BkLink
        class="text-12px color-#3a84ff!"
        :href="contacts[1].link"
        target="_blank"
      >
        {{ contacts[1].text }}
      </BkLink>
      |
      <BkLink
        class="text-12px color-#3a84ff!"
        :href="contacts[2].link"
        target="_blank"
      >
        {{ contacts[2].text }}
      </BkLink>
    </p>
    <p class="copyright">
      {{ copyright }}
    </p>
  </div>

  <CreateGateway
    v-model="createGatewayShow"
    @done="init"
  />
</template>

<script setup lang="ts">
// import { isAfter24h } from '@/utils';
import {
  useEnv,
  useFeatureFlag,
} from '@/stores';
import { useGatewaysList } from '@/hooks';
import { TENANT_MODE_TEXT_MAP } from '@/enums';
import { getGatewayList } from '@/services/source/gateway';
import AgIcon from '@/components/ag-icon/Index.vue';
import CreateGateway from '@/components/create-gateway/Index.vue';
import TableEmpty from '@/components/table-empty/Index.vue';
import type { IApiGateway } from '@/types/gateway';
import GatewayEmpty from '@/images/gateway-empty.png';
import GatewayEmpty2 from '@/images/gateway-empty2.png';

type GatewayType = Awaited<ReturnType<typeof getGatewayList>>['results'][number];

type ConvertedGatewayType = GatewayType & {
  // isAfter24h: boolean
  tagOrder: string
  labelTextData: {
    name: string
    released: boolean
  }[]
};

const { t } = useI18n();
const router = useRouter();
const featureFlagStore = useFeatureFlag();
const envStore = useEnv();

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
// 获取网关数据方法
const {
  getGatewaysListData,
  dataList,
  pagination,
  isLoading,
} = useGatewaysList(filterNameData);

const tableEmptyConf = ref<{
  emptyType: string
  isAbnormal: boolean
}>({
  emptyType: '',
  isAbnormal: false,
});

const initLoading = ref<boolean>(false);
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

const contacts = [
  {
    text: t('技术支持'),
    link: 'https://wpa1.qq.com/KziXGWJs?_type=wpa&qidian=true',
  },
  {
    text: t('社区论坛'),
    link: 'https://bk.tencent.com/s-mart/community/',
  },
  {
    text: t('产品官网'),
    link: 'https://bk.tencent.com/index/',
  },
];

const steps = [
  {
    name: t('API 全生命周期管理：'),
    describe: t('涵盖 API 的配置、发布、测试、监控、下线等各个生命周期的管理，并且支持版本控制'),
  },
  {
    name: t('对接业界规范：'),
    describe: t('Swagger 2.0 / OpenAPI 3.0 / 3.1 协议进行导入导出，自动生成档、SDK 以及在线调试参数'),
  },
  {
    name: t('安全：'),
    describe: t('支持身份认证，频率控制，接口权限控制，支持操作审计以及调用审计'),
  },
  {
    name: t('可观测：'),
    describe: t('提供流水日志、统计图表，并支持配置告警策略'),
  },
  {
    name: t('灵活：'),
    describe: t('支持多环境（一个网关存在多个环境），支持多后端服务（多个服务接入同一个网关）'),
  },
  {
    name: t('统一：'),
    describe: t('统一的 API 资源门户，一站式检索各系统 API ，获取在线文档及 SDK'),
  },
  {
    name: t('更多详情见：'),
    describe: t('产品文档'),
    link: envStore.env.DOC_LINKS.GUIDE,
  },
];

const copyright = computed(() => `Copyright © 2012-${new Date().getFullYear()} Tencent BlueKing. All Rights Reserved. V${envStore.env.BK_APIGATEWAY_VERSION}`);

const progressImg = computed(() => {
  if (envStore.env.EDITION === 'te') {
    return GatewayEmpty;
  }
  return GatewayEmpty2;
});

const isGuide = computed(() => {
  const list = Object.values(filterNameData.value).filter(item => (item !== '' && item !== 'all'));
  if (!list?.length && !gatewaysList.value?.length) {
    return true;
  }
  return false;
});

watch(() => dataList.value, (val: IApiGateway[]) => {
  gatewaysList.value = convertGatewaysList(val);
  updateTableEmptyConfig();
});

// 处理列表项
const convertGatewaysList = (arr: GatewayType[]): ConvertedGatewayType[] => {
  if (!arr) {
    return [];
  }

  return arr.map((gateway) => {
    const item: any = { ...gateway };
    // item.isAfter24h = isAfter24h(item.created_time);
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
  initLoading.value = true;
  const response = await getGatewayList({ limit: 10000 });
  gatewaysList.value = convertGatewaysList(response.results || []);
  updateTableEmptyConfig();
  setTimeout(() => {
    initLoading.value = false;
  }, 100);
};

const showAddDialog = () => {
  createGatewayShow.value = true;
};

const handleViewDoc = () => {
  router.push({ name: 'Docs' });
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

const handleClearFilterKey = () => {
  filterNameData.value = {
    keyword: '',
    kind: 'all',
  };
  filterKey.value = 'updated_time';
  getGatewaysListData();
  updateTableEmptyConfig();
};

const updateTableEmptyConfig = () => {
  const searchParams = { ...filterNameData.value };
  const list = Object.values(searchParams).filter(item => item !== '');
  tableEmptyConf.value.isAbnormal = pagination.value.abnormal as boolean;

  if (list.length && !gatewaysList.value.length) {
    tableEmptyConf.value.emptyType = 'searchEmpty';
    return;
  }
  if (list.length) {
    tableEmptyConf.value.emptyType = 'empty';
    return;
  }
  tableEmptyConf.value.emptyType = '';
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

.home-loading {
  min-height: calc(100vh - 110px);
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
    padding: 28px 0;
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
        }

        .environment-tag {
          margin-right: 8px;
        }
      }

      .table-item:nth-of-type(1) {
        margin-top: 0
      };

      // .newly-item {
      //   background: #F2FFF4;
      // }
    }

    .of1 {
      flex: 0 0 10%;
    }

    .of2 {
      flex: 0 0 20%;
    }

    .of3 {
      flex: 0 0 30%;
    }

    .pl-4 {
      padding-left: 4px;
    }

    .empty-table {

      :deep(.bk-table-head) {
        display: none;
      }
    }

    .empty-container {

      .table-header {
        display: flex;
        margin-bottom: 102px;
      }
    }
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

.footer-container {
  position: relative;
  left: 0;
  display: flex;
  height: 50px;
  font-size: 12px;
  line-height: 20px;
  flex-flow: column;
  align-items: center;
  &.empty {
    background: #FFFFFF;
    padding-top: 8px;
    height: 58px;
  }
}

.gateway-empty {
  height: calc(100vh - 110px);
  display: flex;
  flex-direction: column;
  align-items: center;
  &::after {
    content: " ";
    width: calc(100% - 48px);
    height: 1px;
    background: #DCDEE5;
  }
  .create-guide {
    padding: 82px 0;
    background: #F5F7FA;
    display: flex;
    flex-direction: column;
    justify-content: center;
    .guide-title {
      font-size: 20px;
      color: #313238;
    }
    .guide-describe {
      font-size: 14px;
      color: #4d4f56e6;
      margin: 12px 0 20px;
    }
  }
  .work-progress {
    background: #FFFFFF;
    width: 100%;
    padding-top: 86px;
    flex: 1;
    display: flex;
    justify-content: center;
    .progress-img {
      width: 589px;
      margin-right: 52px;
    }
    .step {
      display: flex;
      align-items: center;
      position: relative;
      margin-bottom: 12px;
      padding-left: 12px;
      &::before {
        content: " ";
        position: absolute;
        top: 50%;
        transform: translateY(-50%);
        left: 0;
        width: 4px;
        height: 4px;
        border-radius: 2px;
        background: #4D4F56;
      }
      .name {
        font-size: 14px;
        font-weight: Bold;
        color: #313238;
      }
      .describe {
        font-size: 12px;
        color: #4D4F56;
        &.link {
          color: #3A84FF;
        }
      }
    }
  }
}
</style>
