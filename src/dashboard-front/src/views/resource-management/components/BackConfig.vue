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
  <BkForm
    ref="backRef"
    :model="backConfigData"
    :rules="rules"
    class="back-config-container"
    @validate="setInvalidPropId"
  >
    <BkFormItem
      :label="t('服务')"
      required
      class="item-service"
    >
      <BkSelect
        v-model="backConfigData.id"
        :input-search="false"
        class="service"
        :popover-options="{ extCls: 'service-select-popover' }"
        @change="handleServiceChange"
      >
        <BkOption
          v-for="(item, index) in servicesData"
          :key="index"
          :value="item.id"
          :label="item.name"
        >
          <div class="service-select-item">
            <span>{{ item.name }}</span>
            <template v-if="item.description">
              <span
                class="desc"
                :title="item.description"
              >（{{ item.description }}）</span>
            </template>
          </div>
        </BkOption>
      </BkSelect>
      <BkButton
        v-if="isEditService"
        theme="primary"
        class="ml-10px"
        @click="editService"
      >
        {{ t('编辑服务') }}
      </BkButton>
    </BkFormItem>
    <BkAlert
      v-if="isEditService"
      theme="error"
      title="后端服务地址不允许为空，请更新"
      class="table-warning"
    />
    <BkTable
      v-if="backConfigData.id"
      class="table-layout"
      :data="servicesConfigs"
      :border="['outer']"
      @row-mouse-enter="handleMouseEnter"
      @row-mouse-leave="handleMouseLeave"
    >
      <BkTableColumn
        :label="t('环境名称')"
        :resizable="false"
      >
        <template #default="{ data }">
          {{ data?.stage?.name }}
        </template>
      </BkTableColumn>
      <BkTableColumn
        :label="t('后端服务地址')"
        :resizable="false"
      >
        <template #default="{ data }">
          <div v-if="data.hosts.length">
            <div
              v-for="host in data.hosts"
              :key="host.host"
              class="lh-22px"
            >
              {{ host.scheme }}://{{ host.host }}
            </div>
          </div>
          <span v-else>--</span>
        </template>
      </BkTableColumn>
      <BkTableColumn
        :label="renderTimeOutLabel"
        prop="timeout"
        :resizable="false"
      >
        <template #default="{ row }">
          <!-- <span class="time-wrapper"  v-clickOutSide="(e:Event) => handleClickTableOutSide(e, row)">
            <template v-if="!row.isEditTime">
            <span>{{ row.timeout || '0' }}s</span>
            <BkTag theme="warning" v-if="row.isCustom">{{ t('自定义') }}</BkTag>
            <i
            v-show="row?.isTime"
            class="icon apigateway-icon icon-ag-edit-small edit-icon"
            @click.stop="handleEditTime(row)"
            />
            </template>
            <div v-else ref="timeInputRef">
            <BkInput
            v-model="row.timeout"
            :max-length="3"
            :placeholder="t('请输入超时时间')"
            :class="row.timeout === '' ? 'time-out-input-error' : ''"
            :autofocus="true"
            @input="(value:string) => handleTableTimeOutInput(value, row)"
            @blur="handleTableTimeOutBlur"
            @keypress="(value:string) => { value = value.replace(/\d/g, '') }"
            v-bk-tooltips="`${t('初始值')}: ${formatDefaultTime(row)}s`"
            />
            <div class='time-input-error' v-if="row.timeout === ''">{{ t('超时时间不能为空') }}</div>
            </div>
            </span> -->
          <span>{{ row.timeout || '0' }}s</span>
          <BkTag
            v-if="row.isCustom"
            theme="warning"
          >
            {{ t('自定义') }}
          </BkTag>
        </template>
      </BkTableColumn>
    </BkTable>
    <BkFormItem
      :label="t('请求方法')"
      required
    >
      <BkSelect
        v-model="backConfigData.config.method"
        :input-search="false"
        :clearable="false"
        class="method"
      >
        <BkOption
          v-for="item in HTTP_METHODS"
          :key="item.id"
          :value="item.id"
          :label="item.name"
        />
      </BkSelect>
    </BkFormItem>
    <BkFormItem
      :label="t('请求路径')"
      property="config.path"
      required
    >
      <div class="flex items-center">
        <BkInput
          id="back-config-path"
          v-model="backConfigData.config.path"
          :placeholder="t('斜线(/)开头的合法URL路径，不包含http(s)开头的域名')"
          clearable
          class="w568"
          @change="isPathValid = false"
          @input="isPathValid = false"
        />
        <BkButton
          theme="primary"
          outline
          class="ml-10px"
          :disabled="!backConfigData.id || !backConfigData.config.path"
          @click="handleCheckPath"
        >
          {{ t('校验并查看地址') }}
        </BkButton>
        <BkCheckbox
          v-model="backConfigData.config.match_subpath"
          class="ml-12px!"
          disabled
        >
          {{ t('追加匹配的子路径') }}
        </BkCheckbox>
      </div>
      <div class="text-12px! color-#979ba5!">
        <!-- {{ t("后端接口地址的 Path，不包含域名或 IP，支持路径变量、环境变量，变量包含在\{\}中，比如：/users/{id}/{env.type}/。") }} -->
        {{ t("后端接口地址的 Path，不包含域名或 IP，支持路径变量、环境变量，变量包含在{'{}'}中") }}
        <!-- <a :href="GLOBAL_CONFIG.DOC.TEMPLATE_VARS" target="_blank" class="ag-primary">{{ t('更多详情') }}</a> -->
      </div>
      <div v-if="servicesCheckData.length && isPathValid">
        <BkAlert
          theme="success"
          class="w-70% max-w-700px mt-10px"
          :title="t('路径校验通过，路径合法，请求将被转发到以下地址')"
        />
        <BkTable
          class="w-70% max-w-700px mt-10px"
          :data="servicesCheckData"
          :border="['outer', 'col']"
        >
          <BkTableColumn
            :label="t('环境名称')"
            :rowspan="({ row }) => row.rowSpan"
          >
            <template #default="{ data }">
              {{ data.stage?.name }}
            </template>
          </BkTableColumn>
          <BkTableColumn
            :label="t('请求类型')"
            width="100"
          >
            <template #default="{ data }">
              {{ backConfigData?.config?.method || data?.stage?.name }}
            </template>
          </BkTableColumn>
          <BkTableColumn :label="t('请求地址')">
            <template #default="{ data }">
              <span v-bk-tooltips="{ content: data.backend_url, disabled: !data.backend_url }">
                {{ data.backend_url }}
              </span>
            </template>
          </BkTableColumn>
        </BkTable>
      </div>
    </BkFormItem>
  </BkForm>

  <AddBackendService
    ref="addBackendServiceRef"
    :base="baseInfo"
    :edit-id="backConfigData.id"
    @done="() => handleServiceChange(backConfigData.id)"
    @close="() => handleServiceChange(backConfigData.id)"
  />
</template>

<script setup lang="tsx">
import { cloneDeep } from 'lodash-es';
import { Message } from 'bkui-vue';
import {
  useEnv,
  useGateway,
} from '@/stores';
import {
  getBackendServiceDetail,
  getBackendServiceList,
} from '@/services/source/backend-services.ts';
import { backendsPathCheck } from '@/services/source/resource.ts';
// import mitt from '@/common/event-bus';
import AddBackendService from '@/views/backend-services/components/AddBackendService.vue';
import { HTTP_METHODS } from '@/constants';

interface IProps {
  detail?: any
  frontConfig: {
    path: string
    method: string
    match_subpath: boolean
    enable_websocket: boolean
  }
}

const {
  detail = {},
  frontConfig,
} = defineProps<IProps>();

// 获取到服务数据后抛出一个事件
const emit = defineEmits(['service-init']);

const { t } = useI18n();
const gatewayStore = useGateway();
const envStore = useEnv();

const backRef = ref();
const frontPath = ref('');
const backConfigData = ref<any>({
  id: '',
  name: '',
  config: {
    path: '',
    method: 'GET',
    match_subpath: false,
    timeout: 0,
  },
});
const baseInfo = ref({
  name: '',
  description: '',
});
// 服务列表下拉框数据
const servicesData = ref([]);
// 服务详情
const servicesConfigs = ref([]);
// 服务详情缓存数据
const servicesConfigsStorage = ref([]);
// 校验列表
const servicesCheckData = ref<{
  stage: {
    id: number
    name: string
  }
  backend_url: string
  rowSpan: number
}[]>([]);
const popoverConfirmRef = ref();
const timeOutValue = ref('');
const isShowPopConfirm = ref(false);
const isTimeEmpty = ref(false);
// const timeInputRef = ref(null);
const addBackendServiceRef = ref(null);
const isServiceInit = ref(false);

const rules = {
  'config.path': [
    {
      required: true,
      message: t('请填写请求路径'),
      trigger: 'blur',
    },
    {
      validator: (value: string) => /^\/[\w{}/.!-]*$/.test(value),
      message: t('斜线(/)开头的合法URL路径，不包含http(s)开头的域名'),
      trigger: 'blur',
    },
  ],
};

// 后端地址是否校验通过
const isPathValid = ref(false);

// 错误表单项的 #id
const invalidFormElementIds = ref<string[]>([]);

const gatewayId = computed(() => gatewayStore.apigwId);

const isEditService = computed(() => {
  let flag = false;
  for (let i = 0; i < servicesConfigs.value?.length; i++) {
    const item = servicesConfigs.value[i];
    if (!item?.hosts[0].host) {
      flag = true;
      break;
    }
  }
  return flag;
});

watch(
  () => detail,
  () => {
    if (Object.keys(detail).length) {
      const { backend } = detail;
      backConfigData.value = {
        ...backConfigData.value,
        ...backend,
      };
      if (backend?.id) {
        handleServiceChange(backend.id);
      }
    }
  },
  { immediate: true },
);

watch(
  () => frontConfig,
  () => {
    frontPath.value = frontConfig.path;
    backConfigData.value.config.match_subpath = frontConfig.match_subpath;
  },
  {
    immediate: true,
    deep: true,
  },
);

const handleTimeOutTotal = (value: any[]) => {
  backConfigData.value.config.timeout = Number(value[0].timeout);
  // backConfigData.value.config.timeout = value.reduce((curr,next) => {
  //   return curr + Number(next.timeout || 0)
  // },0)
};

const handleRefreshTime = () => {
  servicesConfigs.value = cloneDeep(servicesConfigsStorage.value);
  // handleTimeOutTotal(servicesConfigs.value);
  backConfigData.value.config.timeout = 0;
  timeOutValue.value = '';
  isTimeEmpty.value = false;
};

const handleShowPopover = () => {
  isShowPopConfirm.value = true;
  isTimeEmpty.value = false;
  servicesConfigs.value.forEach((item) => {
    item.isEditTime = false;
  });
};

const handleConfirmTime = () => {
  if (!timeOutValue.value) {
    isTimeEmpty.value = true;
    return;
  }
  servicesConfigs.value.forEach((item: Record<string, string | boolean>) => {
    item.isCustom = true;
    item.timeout = timeOutValue.value;
  });
  handleTimeOutTotal(servicesConfigs.value);
  isShowPopConfirm.value = false;
  timeOutValue.value = '';
};

const handleCancelTime = () => {
  isTimeEmpty.value = false;
  isShowPopConfirm.value = false;
  timeOutValue.value = '';
};

const handleTimeOutInput = (value: string) => {
  value = value.replace(/\D/g, '');
  if (Number(value) > 300) {
    value = '300';
  }
  timeOutValue.value = value.replace(/\D/g, '');
  isTimeEmpty.value = !value;
};

const handleClickOutSide = (e: Event) => {
  if (
    isShowPopConfirm.value
    && !unref(popoverConfirmRef)
      .content
      .el
      .contains(e.target)
  ) {
    handleCancelTime();
  }
};

const renderTimeOutLabel = () => {
  return (
    <div>
      <div class="back-config-timeout">
        <span>{t('超时时间')}</span>
        <bk-pop-confirm
          width="280"
          trigger="manual"
          ref={popoverConfirmRef}
          title={t('批量修改超时时间')}
          extCls="back-config-timeout-popover"
          is-show={isShowPopConfirm.value}
          content={(
            <div class="back-config-timeout-wrapper">
              <div class="back-config-timeout-content">
                <div class="back-config-timeout-input">
                  <bk-input
                    v-model={timeOutValue.value}
                    maxlength={3}
                    overMaxLengthLimit={true}
                    class={isTimeEmpty.value ? 'time-empty-error' : ''}
                    placeholder={t('请输入超时时间')}
                    onInput={(value: string) => {
                      handleTimeOutInput(value);
                    }}
                    // nativeOnKeypress={(value: string) => {
                    //   value = value.replace(/\d/g, '');
                    // }}
                    autofocus={true}
                    suffix="s"
                    onEnter={() => handleConfirmTime()}
                  />
                </div>
                <div class="back-config-timeout-tip">{t('最大 300s')}</div>
              </div>
              {
                isTimeEmpty.value
                  ? (
                    <div class="time-empty-error">
                      {t('超时时间不能为空')}
                      {isTimeEmpty.value}
                    </div>
                  )
                  : ''
              }
            </div>
          )}
          onConfirm={() => handleConfirmTime()}
          onCancel={() => handleCancelTime()}
        >
          <i
            class="apigateway-icon icon-ag-bulk-edit edit-action"
            v-bk-tooltips={{
              content: (
                <div>
                  {t('自定义超时时间')}
                </div>
              ),
            }}
            onClick={() => handleShowPopover()}
            v-clickOutSide={(e: any) => handleClickOutSide(e)}
          />
        </bk-pop-confirm>
        <i
          class="apigateway-icon icon-ag-undo-2 refresh-icon"
          v-bk-tooltips={{
            content: (
              <div>{t('恢复初始值')}</div>
            ),
          }}
          onClick={() => handleRefreshTime()}
        />
      </div>
    </div>
  );
};

// 选择服务获取服务详情数据
async function handleServiceChange(backendId: number) {
  const res = await getBackendServiceDetail(gatewayId.value, backendId);
  const resStorage: any = cloneDeep(res);
  const detailTimeout = detail?.backend?.config?.timeout;
  if (detailTimeout !== 0 && detailTimeout !== undefined && detailTimeout !== null) {
    res.configs.forEach((item: any) => {
      item.timeout = detailTimeout;
    });
  }
  [
    servicesConfigs.value,
    servicesConfigsStorage.value,
  ] = [
    cloneDeep(res.configs || []),
    cloneDeep(resStorage.configs || []),
  ];
  backConfigData.value.name = res.name;
  // 第一次加载服务数据后，抛出事件
  if (!isServiceInit.value) {
    emit('service-init');
    isServiceInit.value = true;
  }
}

const editService = () => {
  const service = servicesData.value?.filter((item: any) => item.id === backConfigData.value.id)[0];
  if (service) {
    baseInfo.value = {
      name: service.name,
      description: service.description,
    };

    addBackendServiceRef.value?.show();
  }
};

// 校验路径
const handleCheckPath = async () => {
  try {
    const params = {
      path: frontPath.value,
      backend_id: backConfigData.value.id,
      backend_path: backConfigData.value.config.path,
    };
    const response = await backendsPathCheck(gatewayId.value, params);
    servicesCheckData.value = response.reduce<{
      stage: {
        id: number
        name: string
      }
      backend_url: string
      rowSpan: number
    }[]>((acc, item) => {
      acc = [
        ...acc,
        ...item.backend_urls.map((url, index) => {
          const rowSpan = index === 0 ? item.backend_urls.length : 0;
          // path 需要去掉第一个斜杠
          const path = backConfigData.value.config.path.startsWith('/') ? backConfigData.value.config.path.slice(1) : backConfigData.value.config.path;
          const backendUrl = envStore.env.BK_API_RESOURCE_URL_TMPL
            .replace('{api_name}', gatewayStore.currentGateway?.name || '')
            .replace('{stage_name}', item.stage.name)
            .replace('{resource_path}', path);
          return {
            stage: item.stage,
            backend_url: backendUrl,
            rowSpan,
          };
        }),
      ];
      return acc;
    }, []);
    isPathValid.value = true;
  }
  catch {
    servicesCheckData.value = [];
    isPathValid.value = false;
  }
};

// const handleTableTimeOutInput = (value: string, row: Record<string, any>) => {
//   value = value.replace(/\D/g, '');
//   if (Number(value) > 300) {
//     value = '300';
//   }
//   row.timeout = Number(value);
//   // 判断数据是否有变动，如有更新需要显示自定义标签
//   const configData = servicesConfigsStorage.value.find((item: any) => item?.stage?.id === row?.stage?.id);
//   if (configData) {
//     row.isCustom = String(row.timeout) !== String(configData.timeout) ? true : false;
//   }
// };

// const handleTableTimeOutBlur = () => {
//   handleTimeOutTotal(servicesConfigs.value);
// };

// const handleClickTableOutSide = (e: Event, row: Record<string, number | string | boolean>) => {
//   if (timeInputRef.value && !unref(timeInputRef)
//     ?.contains(e.target)) {
//     if (!row.timeout) {
//       return;
//     }
//     row.isEditTime = false;
//   }
// };

// const handleEditTime = (payload: Record<string, number | string | boolean>) => {
//   servicesConfigs.value.forEach((item) => {
//     item.isEditTime = false;
//   });
//   payload = Object.assign(payload, {
//     isCustom: false,
//     isEditTime: true,
//   });
// };

const handleMouseEnter = (e: Event, row: Record<string, number | string | boolean>) => {
  setTimeout(() => {
    row.isTime = true;
  }, 100);
};

const handleMouseLeave = (e: Event, row: Record<string, number | string | boolean>) => {
  setTimeout(() => {
    row.isTime = false;
  }, 100);
};

const init = async () => {
  const res = await getBackendServiceList(gatewayId.value, {
    offset: 0,
    limit: 1000,
  });
  servicesData.value = res.results;
  // 检查传进来的资源的 backend 有没有 id，没有的话用 name 匹配一下以正确获取服务数据
  if (!detail?.backend?.id) {
    const backendId = servicesData.value.find(s => s.name === detail?.backend?.name)?.id;
    if (backendId) {
      backConfigData.value.id = backendId;
      await handleServiceChange(backendId);
    }
  }
};

// 监听表单校验时间，收集 #id
const setInvalidPropId = (property: string, result: boolean) => {
  if (!result) {
    let _property = '';
    if (property.includes('.')) {
      const paths = property.split('.');
      _property = paths[paths.length - 1];
    }
    invalidFormElementIds.value.push(`back-config-${_property}`);
  }
};

const validate = async () => {
  invalidFormElementIds.value = [];
  let isHost = true;
  for (let i = 0; i < servicesConfigs.value?.length; i++) {
    const item = servicesConfigs.value[i];
    if (!item?.hosts[0]?.host) {
      isHost = false;
      break;
    }
  }
  if (isHost) {
    await backRef.value?.validate();
  }
  else {
    Message({
      theme: 'warning',
      message: '请先配置后端服务地址',
    });
    return Promise.reject('请先配置后端服务地址');
  }
};

onMounted(() => {
  setTimeout(() => {
  // 事件总线监听重新获取环境列表
  // mitt.on('front-config', (value: any) => {
  //   frontPath.value = value.path;
  //   backConfigData.value.config.match_subpath = value.match_subpath;
  // });
    init();
  });
});

defineExpose({
  backConfigData,
  invalidFormElementIds,
  validate,
});
</script>

<style lang="scss" scoped>
.back-config-container {

  .table-layout {
    width: auto !important;
    max-width: 700px !important;
    margin: 0 0 20px 150px;

    // width: 700px !important;
  }

  .table-warning {
    max-width: 700px !important;
    margin: 0 0 8px 150px;
  }

  .public-switch {
    height: 32px;
  }

  .item-service {

    :deep(.bk-form-content) {
      display: flex;
    }
  }

  .service,
  .method {
    max-width: 700px !important;
  }

  .service {
    display: inline-block;
    flex: 1;
  }

  .w700 {
    max-width: 700px !important;

    // width: 70% !important;
  }

  .w568 {
    max-width: 568px !important;

    // width: 55% !important;
  }

  .ag-primary {
    color: #3a84ff;
  }

  :deep(.bk-checkbox-label) {
    white-space: nowrap;
  }

  .time-wrapper {
    position: relative;

    .edit-icon {
      position: absolute;
      top: -2px;
      font-size: 24px;
      color: #3a84ff;
      cursor: pointer;
    }
  }
}

.service-select-popover {

  .service-select-item {
    display: flex;
  }

  .desc {
    display: inline-block;
    width: 560px;
    margin-left: 6px;
    overflow: hidden;
    color: #979ba5;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}

:deep(.back-config-timeout) {
  display: inline-block;

  .edit-action,
  .refresh-icon {
    margin-left: 8px;
    font-size: 16px;
    color: #3a84ff;
    vertical-align: middle;
    cursor: pointer;
  }

  // .refresh-icon {
  //   margin-left: 15px;
  // }
}

.time-out-input-error {
  border-color: #ff5656;
}

.time-input-error {
  margin-bottom: 10px;
  line-height: 1;
  color: #ea3636;
}
</style>

<style lang="scss">
.back-config-timeout-wrapper {

  .back-config-timeout-content {
    display: flex;
    align-items: center;

    .back-config-timeout-input {
      display: flex;
      min-width: 182px;
      align-items: center;

      .bk-input {
        width: 100%;
      }

      .bk-input--number-control {
        display: none;
      }
    }

    .back-config-timeout-tip {
      margin-left: 10px;
      font-size: 12px;
      color: #63656E;
    }
  }

  .time-empty-error {
    color: #ea3636;
    border-color: #ea3636;
  }
}

.back-config-timeout-popover {
  padding: 16px !important;
}
</style>
