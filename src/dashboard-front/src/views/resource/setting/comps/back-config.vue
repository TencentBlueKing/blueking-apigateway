
<template>
  <bk-form ref="backRef" :model="backConfigData" :rules="rules" class="back-config-container">
    <bk-form-item
      :label="t('服务')"
      required
    >
      <bk-select
        :input-search="false"
        class="service"
        v-model="backConfigData.id" @change="handleServiceChange">
        <bk-option v-for="item in servicesData" :key="item.id" :value="item.id" :label="item.name" />
      </bk-select>
    </bk-form-item>
    <bk-table
      v-if="backConfigData.id"
      class="table-layout"
      :data="servicesConfigs"
      :border="['outer']"
      @row-mouse-enter="handleMouseEnter"
      @row-mouse-leave="handleMouseLeave"
    >
      <bk-table-column
        :label="t('环境名称')"
      >
        <template #default="{ data }">
          {{data?.stage?.name}}
        </template>
      </bk-table-column>
      <bk-table-column
        :label="t('后端服务地址')"
      >
        <template #default="{ data }">
          <span v-if="data?.hosts[0].host">
            {{data?.hosts[0].scheme}}://{{ data?.hosts[0].host }}
          </span>
          <span v-else>--</span>
        </template>
      </bk-table-column>
      <bk-table-column
        :label="renderTimeOutLabel"
        prop="timeout"
      >
        <template #default="{ row }">
          <span class="time-wrapper"  v-clickOutSide="(e:Event) => handleClickTableOutSide(e, row)">
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
          </span>
        </template>
      </bk-table-column>
    </bk-table>
    <bk-form-item
      :label="t('请求方法')"
      required
    >
      <bk-select
        :input-search="false"
        v-model="backConfigData.config.method"
        :clearable="false"
        class="method">
        <bk-option v-for="item in methodData" :key="item.id" :value="item.id" :label="item.name" />
      </bk-select>
    </bk-form-item>
    <bk-form-item
      :label="t('请求路径')"
      property="config.path"
      required
    >
      <div class="flex-row aligin-items-center">
        <bk-input
          v-model="backConfigData.config.path"
          :placeholder="t('斜线(/)开头的合法URL路径，不包含http(s)开头的域名')"
          clearable
          class="w568"
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
        <bk-checkbox class="ml40" v-model="backConfigData.config.match_subpath" disabled>
          {{ t('追加匹配的子路径') }}
        </bk-checkbox>
      </div>
      <div class="common-form-tips">
        <!-- {{ t('后端接口地址的 Path，不包含域名或 IP，支持路径变量、环境变量，变量包含在{}中，比如：/users/{id}/{env.type}/。') }} -->
        <a :href="GLOBAL_CONFIG.DOC.TEMPLATE_VARS" target="_blank" class="ag-primary">{{ t('更多详情') }}</a>
      </div>
      <div v-if="servicesCheckData.length">
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
              {{data?.stage?.name}}
            </template>
          </bk-table-column>
          <bk-table-column
            :label="t('请求类型')"
          >
            <template #default="{ data }">
              {{backConfigData.config.method || data?.stage?.name}}
            </template>
          </bk-table-column>
          <bk-table-column
            :label="t('请求地址')"
          >
            <template #default="{ data }">
              {{data?.backend_urls[0]}}
            </template>
          </bk-table-column>
        </bk-table>
      </div>
    </bk-form-item>
  </bk-form>
</template>

<script setup lang="tsx">
import { ref, unref, watch, computed,  onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { getBackendsListData, getBackendsDetailData, backendsPathCheck } from '@/http';
import { useCommon } from '../../../../store';
import { useGetGlobalProperties } from '@/hooks';
import { cloneDeep } from 'lodash';
import mitt from '@/common/event-bus';

const props = defineProps({
  detail: {
    type: Object,
    default: {},
  },
});

const backRef = ref(null);
const frontPath = ref('');
const { t } = useI18n();
const common = useCommon();
const backConfigData = ref({
  id: '',
  config: {
    path: '',
    method: 'GET',
    match_subpath: false,
    timeout: 0
  },
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

// 提示默认超时时间
const formatDefaultTime = computed(() => {
  return (payload: any) => {
    const curServices = servicesConfigsStorage.value.find((item) => item?.stage?.id === payload?.stage?.id);
    if(curServices) {
      return curServices.timeout
    }
    return ''
  }
})

const handleTimeOutTotal = (value: any[]) => {
  backConfigData.value.config.timeout = value.reduce((curr,next) => {
    return curr + Number(next.timeout || 0)
  },0)
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
  if(!timeOutValue.value) {
    isTimeEmpty.value = true;
    return;
  }
  servicesConfigs.value.forEach((item:Record<string, string | boolean>) => {
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

const handleTimeOutInput = (value:string) => {
  value = value.replace(/\D/g, '')
  if(Number(value) > 300) {
    value = '300';
  }
  timeOutValue.value = value.replace(/\D/g, '');
  isTimeEmpty.value = !value;
}

const handleClickOutSide = (e:Event) => {
  if (
    isShowPopConfirm.value &&
    !unref(popoverConfirmRef).content.el.contains(e.target)
  ) {
    handleCancelTime();
  }
}

const renderTimeOutLabel = () => {
  return (
    <div>
      <div class='back-config-timeout'>
        <span>{t('超时时间')}</span>
        <bk-pop-confirm
          width='280'
          trigger='manual'
          ref={popoverConfirmRef}
          title={t('批量修改超时时间')}
          extCls='back-config-timeout-popover'
          is-show={isShowPopConfirm.value}
          content={
            <div class='back-config-timeout-wrapper'>
              <div class='back-config-timeout-content'>
                <div class='back-config-timeout-input'>
                  <bk-input
                    v-model={timeOutValue.value}
                    maxlength={3}
                    class={isTimeEmpty ? 'time-empty-error' : ''}
                    placeholder={t('请输入超时时间')}
                    onInput={(value:string) => {handleTimeOutInput(value)}}
                    nativeOnKeypress={(value:string) => { value = value.replace(/\d/g, '') }}
                    autofocus={true}
                    suffix='s'
                  />
                </div>
                <div class='back-config-timeout-tip'>{t('最大 300s')}</div>
              </div>
              {
                isTimeEmpty.value ? <div class='time-empty-error'>{t('超时时间不能为空')}{isTimeEmpty.value}</div> : ''
              }
            </div>
          }
          onConfirm={() => handleConfirmTime()}
          onCancel={() => handleCancelTime()}
        >
          <i
            class="apigateway-icon icon-ag-edit-line edit-action"
            v-bk-tooltips={{
              content: (
                <div>
                  {t('自定义超时时间')}
                </div>
              )
            }}
            onClick={() => handleShowPopover()}
            v-clickOutSide={(e:any) => handleClickOutSide(e)}
          />
        </bk-pop-confirm>
        <i
          class="apigateway-icon icon-ag-cc-history refresh-icon"
          v-bk-tooltips={{
            content: (
              <div>
                {t('恢复初始值')}
              </div>
            )
          }}
          onClick={() => handleRefreshTime()}
        />
      </div>
    </div>
  );
};

// 选择服务获取服务详情数据
const handleServiceChange = async (backendId: number) => {
  const res = await getBackendsDetailData(common.apigwId, backendId);
  [servicesConfigs.value, servicesConfigsStorage.value] = [cloneDeep(res.configs || []), cloneDeep(res.configs || [])];
};

// 校验路径
const handleCheckPath = async () => {
  try {
    const params = {
      path: frontPath.value,
      backend_id: backConfigData.value.id,
      backend_path: backConfigData.value.config.path,
    };
    const res = await backendsPathCheck(common.apigwId, params);
    servicesCheckData.value = res;
    console.log('servicesCheckData', servicesCheckData.value);
  } catch (error) {

  }
};

const handleTableTimeOutInput = (value:string, row:Record<string, any>) => {
  value = value.replace(/\D/g, '')
  if(Number(value) > 300) {
    value = '300';
  }
  row.timeout = Number(value);
  // 判断数据是否有变动，如有更新需要显示自定义标签
  const configData = servicesConfigsStorage.value.find((item:any) => item?.stage?.id === row?.stage?.id);
  if(configData) {
    row.isCustom = String(row.timeout) !== String(configData.timeout) ? true : false;
  }
}

const handleTableTimeOutBlur = () => {
  handleTimeOutTotal(servicesConfigs.value);
}

const handleClickTableOutSide = (e:Event, row:Record<string, number | string | boolean>) => {
  if (timeInputRef && !unref(timeInputRef)?.contains(e.target)) {
    if(!row.timeout) {
      return;
    }
    row.isEditTime = false;
  }
}

const handleEditTime = (payload: Record<string, number | string | boolean>) => {
  servicesConfigs.value.forEach((item) => {
    item.isEditTime = false;
  });
  payload = Object.assign(payload, {  isCustom: false, isEditTime: true });
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

watch(
  () => props.detail,
  (val: any) => {
    if (Object.keys(val).length) {
      const { backend } = val;
      backConfigData.value = { ...backend };
      handleServiceChange(backend.id);
    }
  },
  { immediate: true },
);

const init = async () => {
  const res = await getBackendsListData(common.apigwId);
  console.log('res', res);
  servicesData.value = res.results;
};

const validate = async () => {
  await backRef.value?.validate();
};

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

  .public-switch {
    height: 32px;
  }

  .service,
  .method {
    max-width: 700px !important;
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
      color: #3A84FF;
    }
  }
}

:deep(.back-config-timeout) {
  display: inline-block;

  .edit-action,
  .refresh-icon {
    margin-left: 8px;
    font-size: 16px;
    color: #1768ef;
    vertical-align: middle;
    cursor: pointer;
  }
  .refresh-icon {
    margin-left: 15px;
  }
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
