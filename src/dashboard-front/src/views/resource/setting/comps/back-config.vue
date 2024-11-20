<template>
  <bk-form
    ref="backRef"
    :model="backConfigData"
    :rules="rules"
    class="back-config-container"
    @validate="setInvalidPropId"
  >
    <bk-form-item
      :label="t('服务')"
      required
      class="item-service"
    >
      <bk-select
        :input-search="false"
        class="service"
        :popoverOptions="{ extCls: 'service-select-popover' }"
        v-model="backConfigData.id"
        @change="handleServiceChange"
      >
        <!-- <bk-option v-for="item in servicesData" :key="item.id" :value="item.id" :label="item.name" /> -->
        <bk-option
          v-for="(item, index) in servicesData"
          :value="item.id"
          :key="index"
          :label="item.name"
        >
          <div class="service-select-item">
            <span>{{ item.name }}</span>
            <template v-if="item.description">
              <span class="desc" :title="item.description">（{{ item.description }}）</span>
            </template>
          </div>
        </bk-option>
      </bk-select>
      <bk-button theme="primary" class="ml10" v-if="isEditService" @click="editService">
        {{ t('编辑服务') }}
      </bk-button>
    </bk-form-item>
    <bk-alert
      theme="error"
      title="后端服务地址不允许为空，请更新"
      class="table-warning"
      v-if="isEditService"
    />
    <bk-table
      v-if="backConfigData.id"
      class="table-layout"
      :data="servicesConfigs"
      :border="['outer']"
      @row-mouse-enter="handleMouseEnter"
      @row-mouse-leave="handleMouseLeave"
    >
      <bk-table-column :label="t('环境名称')" :resizable="false">
        <template #default="{ data }">
          {{ data?.stage?.name }}
        </template>
      </bk-table-column>
      <bk-table-column :label="t('后端服务地址')" :resizable="false">
        <template #default="{ data }">
          <span v-if="data?.hosts[0].host">
            {{ data?.hosts[0].scheme }}://{{ data?.hosts[0].host }}
          </span>
          <span v-else>--</span>
        </template>
      </bk-table-column>
      <bk-table-column :label="renderTimeOutLabel" prop="timeout" :resizable="false">
        <template #default="{ row }">
          <!-- <span class="time-wrapper"  v-clickOutSide="(e:Event) => handleClickTableOutSide(e, row)">
            <template v-if="!row.isEditTime">
              <span>{{ row.timeout || '0' }}s</span>
              <bk-tag theme="warning" v-if="row.isCustom">{{ t('自定义') }}</bk-tag>
              <i
                v-show="row?.isTime"
                class="icon apigateway-icon icon-ag-edit-small edit-icon"
                @click.stop="handleEditTime(row)"
              />
            </template>
            <div v-else ref="timeInputRef">
              <bk-input
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
          <bk-tag theme="warning" v-if="row.isCustom">{{ t('自定义') }}</bk-tag>
        </template>
      </bk-table-column>
    </bk-table>
    <bk-form-item :label="t('请求方法')" required>
      <bk-select
        :input-search="false"
        v-model="backConfigData.config.method"
        :clearable="false"
        class="method"
      >
        <bk-option v-for="item in methodData" :key="item.id" :value="item.id" :label="item.name" />
      </bk-select>
    </bk-form-item>
    <bk-form-item :label="t('请求路径')" property="config.path" required>
      <div class="flex-row aligin-items-center">
        <bk-input
          v-model="backConfigData.config.path"
          :placeholder="t('斜线(/)开头的合法URL路径，不包含http(s)开头的域名')"
          clearable
          class="w568"
          id="back-config-path"
          @change="isPathValid = false"
          @input="isPathValid = false"
        />
        <bk-button
          theme="primary"
          outline
          class="ml10"
          @click="handleCheckPath"
          :disabled="!backConfigData.id || !backConfigData.config.path"
        >
          {{ t('校验并查看地址') }}
        </bk-button>
        <bk-checkbox class="ml12" v-model="backConfigData.config.match_subpath" disabled>
          {{ t('追加匹配的子路径') }}
        </bk-checkbox>
      </div>
      <div class="common-form-tips">
        <!-- {{ t("后端接口地址的 Path，不包含域名或 IP，支持路径变量、环境变量，变量包含在\{\}中，比如：/users/{id}/{env.type}/。") }} -->
        {{ t("后端接口地址的 Path，不包含域名或 IP，支持路径变量、环境变量，变量包含在{'{}'}中") }}
        <!-- <a :href="GLOBAL_CONFIG.DOC.TEMPLATE_VARS" target="_blank" class="ag-primary">{{ t('更多详情') }}</a> -->
      </div>
      <div v-if="servicesCheckData.length && isPathValid">
        <bk-alert
          theme="success"
          class="w700 mt10"
          :title="t('路径校验通过，路径合法，请求将被转发到以下地址')"
        />
        <bk-table
          class="w700 mt10"
          :data="servicesCheckData"
          :border="['outer']"
        >
          <bk-table-column
            :label="t('环境名称')"
          >
            <template #default="{ data }">
              {{ data?.stage?.name }}
            </template>
          </bk-table-column>
          <bk-table-column
            :label="t('请求类型')"
          >
            <template #default="{ data }">
              {{ backConfigData?.config?.method || data?.stage?.name }}
            </template>
          </bk-table-column>
          <bk-table-column
            :label="t('请求地址')"
          >
            <template #default="{ data }">
              <span v-bk-tooltips="{ content: data?.backend_urls[0], disabled: !data?.backend_urls[0] }">
                {{ data?.backend_urls[0] }}
              </span>
            </template>
          </bk-table-column>
        </bk-table>
      </div>
    </bk-form-item>
  </bk-form>

  <addBackendService
    :base="baseInfo"
    :edit-id="backConfigData.id"
    ref="addBackendServiceRef"
    @done="handleServiceChange(backConfigData.id)"
    @close="handleServiceChange(backConfigData.id)"
  />
</template>

<script setup lang="tsx">
import {
  ref,
  unref,
  watch,
  computed,
  onMounted,
} from 'vue';
import { useI18n } from 'vue-i18n';
import { cloneDeep } from 'lodash';
import { Message } from 'bkui-vue';
import { getBackendsListData, getBackendsDetailData, backendsPathCheck } from '@/http';
import { useCommon } from '../../../../store';
import { useGetGlobalProperties } from '@/hooks';
import mitt from '@/common/event-bus';
import addBackendService from '@/views/backend-service/add.vue';

const props = defineProps({
  detail: {
    type: Object,
    default: {},
  },
});

// 获取到服务数据后抛出一个事件
const emit = defineEmits(['service-init']);

const backRef = ref(null);
const frontPath = ref('');
const { t } = useI18n();
const common = useCommon();
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
const methodData = ref(common.methodList);
// 服务列表下拉框数据
const servicesData = ref([]);
// 服务详情
const servicesConfigs = ref([]);
// 服务详情缓存数据
const servicesConfigsStorage = ref([]);
// 校验列表
const servicesCheckData = ref([]);
const popoverConfirmRef = ref();
const timeOutValue = ref('');
const isShowPopConfirm = ref(false);
const isTimeEmpty = ref(false);
const timeInputRef = ref(null)
// 全局变量
const globalProperties = useGetGlobalProperties();
const { GLOBAL_CONFIG } = globalProperties;
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
      validator: (value: string) => /^\/[\w{}/.-]*$/.test(value),
      message: t('斜线(/)开头的合法URL路径，不包含http(s)开头的域名'),
      trigger: 'blur',
    },
  ],
};

// 后端地址是否校验通过
const isPathValid = ref(false);

// 错误表单项的 #id
const invalidFormElementIds = ref<string[]>([]);

// 提示默认超时时间
const formatDefaultTime = computed(() => {
  return (payload: any) => {
    const curServices = servicesConfigsStorage.value.find((item) => item?.stage?.id === payload?.stage?.id);
    if (curServices) {
      return curServices.timeout
    }
    return ''
  }
})

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

const handleTimeOutTotal = (value: any[]) => {
  backConfigData.value.config.timeout = Number(value[0].timeout);
  // backConfigData.value.config.timeout = value.reduce((curr,next) => {
  //   return curr + Number(next.timeout || 0)
  // },0)
}

const handleRefreshTime = () => {
  servicesConfigs.value = cloneDeep(servicesConfigsStorage.value);
  handleTimeOutTotal(servicesConfigs.value)
};

const handleShowPopover = () => {
  isShowPopConfirm.value = true;
  isTimeEmpty.value = false;
  servicesConfigs.value.forEach((item) => {
    item.isEditTime = false;
  })
};

const handleConfirmTime = () => {
  if (!timeOutValue.value) {
    isTimeEmpty.value = true;
    return;
  }
  servicesConfigs.value.forEach((item: Record<string, string | boolean>) => {
    item.isCustom = true;
    item.timeout = timeOutValue.value;
  })
  handleTimeOutTotal(servicesConfigs.value);
  isShowPopConfirm.value = false;
  timeOutValue.value = '';
};

const handleCancelTime = () => {
  isTimeEmpty.value = false;
  isShowPopConfirm.value = false;
  timeOutValue.value = '';
}

const handleTimeOutInput = (value: string) => {
  value = value.replace(/\D/g, '')
  if (Number(value) > 300) {
    value = '300';
  }
  timeOutValue.value = value.replace(/\D/g, '');
  isTimeEmpty.value = !value;
}

const handleClickOutSide = (e: Event) => {
  if (
    isShowPopConfirm.value &&
    !unref(popoverConfirmRef)
      .content
      .el
      .contains(e.target)
  ) {
    handleCancelTime();
  }
}

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
          content={
            <div class="back-config-timeout-wrapper">
              <div class="back-config-timeout-content">
                <div class="back-config-timeout-input">
                  <bk-input
                    v-model={timeOutValue.value}
                    maxlength={3}
                    overMaxLengthLimit={true}
                    class={isTimeEmpty ? 'time-empty-error' : ''}
                    placeholder={t('请输入超时时间')}
                    onInput={(value: string) => {
                      handleTimeOutInput(value)
                    }}
                    nativeOnKeypress={(value: string) => {
                      value = value.replace(/\d/g, '')
                    }}
                    autofocus={true}
                    suffix="s"
                    onEnter={() => handleConfirmTime()}
                  />
                </div>
                <div class="back-config-timeout-tip">{t('最大 300s')}</div>
              </div>
              {
                isTimeEmpty.value ? <div class="time-empty-error">{t('超时时间不能为空')}{isTimeEmpty.value}</div> : ''
              }
            </div>
          }
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
const handleServiceChange = async (backendId: number) => {
  try {
    const res = await getBackendsDetailData(common.apigwId, backendId);
    const resStorage: any = cloneDeep(res);
    const detailTimeout = props.detail?.backend?.config?.timeout;
    if (detailTimeout !== 0 && detailTimeout !== undefined && detailTimeout !== null) {
      res.configs.forEach((item: any) => {
        item.timeout = detailTimeout;
      });
    }
    [servicesConfigs.value, servicesConfigsStorage.value] = [cloneDeep(res.configs || []), cloneDeep(resStorage.configs || [])];
    backConfigData.value.name = res.name;
    // 第一次加载服务数据后，抛出事件
    if (!isServiceInit.value) {
      emit('service-init');
      isServiceInit.value = true;
    }
  } catch {
    console.log("=>(back-config.vue:415) handleServiceChange error");
  }
};

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
    servicesCheckData.value = await backendsPathCheck(common.apigwId, params);
    isPathValid.value = true;
  } catch (error) {
    servicesCheckData.value = [];
    isPathValid.value = false;
  }
};

const handleTableTimeOutInput = (value: string, row: Record<string, any>) => {
  value = value.replace(/\D/g, '')
  if (Number(value) > 300) {
    value = '300';
  }
  row.timeout = Number(value);
  // 判断数据是否有变动，如有更新需要显示自定义标签
  const configData = servicesConfigsStorage.value.find((item: any) => item?.stage?.id === row?.stage?.id);
  if (configData) {
    row.isCustom = String(row.timeout) !== String(configData.timeout) ? true : false;
  }
}

const handleTableTimeOutBlur = () => {
  handleTimeOutTotal(servicesConfigs.value);
}

const handleClickTableOutSide = (e: Event, row: Record<string, number | string | boolean>) => {
  if (timeInputRef && !unref(timeInputRef)
    ?.contains(e.target)) {
    if (!row.timeout) {
      return;
    }
    row.isEditTime = false;
  }
}

const handleEditTime = (payload: Record<string, number | string | boolean>) => {
  servicesConfigs.value.forEach((item) => {
    item.isEditTime = false;
  });
  payload = Object.assign(payload, { isCustom: false, isEditTime: true });
}

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
  const res = await getBackendsListData(common.apigwId, { offset: 0, limit: 1000 });
  servicesData.value = res.results;
  // 检查传进来的资源的 backend 有没有 id，没有的话用 name 匹配一下以正确获取服务数据
  if (!props.detail?.backend?.id) {
    const backendId = servicesData.value.find((s) => s.name === props.detail?.backend?.name)?.id;
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
  } else {
    Message({
      theme: 'warning',
      message: '请先配置后端服务地址',
    });
    return Promise.reject('请先配置后端服务地址');
  }
};

watch(
  () => props.detail,
  (val: any) => {
    if (Object.keys(val).length) {
      const { backend } = val;
      backConfigData.value = { ...backConfigData.value, ...backend };
      if (backend?.id) {
        handleServiceChange(backend.id);
      }
    }
  },
  { immediate: true },
);

onMounted(() => {
  // 事件总线监听重新获取环境列表
  mitt.on('front-config', (value: any) => {
    frontPath.value = value.path;
    backConfigData.value.config.match_subpath = value.match_subpath;
  });
  init();
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
    margin: 0 0 20px 150px;
    max-width: 700px !important;
    width: auto !important;
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
      cursor: pointer;
      color: #3a84ff;
    }
  }
}

.service-select-popover {
  .service-select-item {
    display: flex;
  }

  .desc {
    color: #979ba5;
    margin-left: 6px;
    width: 560px;
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
    display: inline-block;
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
  color: #ea3636;
  line-height: 1;
  margin-bottom: 10px;
}
</style>

<style lang="scss">
.back-config-timeout-wrapper {
  .back-config-timeout-content {
    display: flex;
    align-items: center;

    .back-config-timeout-input {
      min-width: 182px;
      display: flex;
      align-items: center;

      .bk-input {
        width: 100%;
      }

      .bk-input--number-control {
        display: none;
      }
    }

    .back-config-timeout-tip {
      font-size: 12px;
      margin-left: 10px;
      color: #63656E;
    }
  }

  .time-empty-error {
    color: #ea3636;
    border-color: #ea3636;
  }
}

.back-config-timeout-popover {
  padding: 16px 16px !important;
}
</style>
