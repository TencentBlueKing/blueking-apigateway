<!-- eslint-disable vue/no-deprecated-slot-attribute -->
<template>
  <div class="sideslider-wrapper">
    <bk-sideslider
      v-model:isShow="isShow"
      :quick-close="true"
      width="960"
      ext-cls="stage-sideslider-cls"
      :before-close="handleBeforeClose"
      @animation-end="handleAnimationEnd"
      @hidden="emit('hidden')"
      :transfer="true"
    >
      <template #header>
        <div class="custom-side-header">
          <div class="title">{{ title }}</div>
          <template v-if="!isAdd">
            <span></span>
            <div class="subtitle">{{ curStageData.name }}</div>
          </template>
        </div>
      </template>
      <template #default>
        <bk-loading :loading="isDialogLoading">
          <div v-if="actionType !== 'check'" class="sideslider-content">
            <bk-collapse v-model="activeKey" class="bk-collapse-service">
              <bk-collapse-panel name="base-info">
                <template #header>
                  <div class="panel-header">
                    <angle-up-fill
                      :class="[activeKey?.includes('base-info') ? 'panel-header-show' : 'panel-header-hide']"
                    />
                    <div class="title">{{ t('基础信息') }}</div>
                  </div>
                </template>
                <template #content>
                  <div class="content">
                    <bk-form
                      ref="baseInfoRef"
                      :label-width="180"
                      :model="curStageData"
                      form-type="vertical"
                    >
                      <bk-form-item
                        :label="t('环境名称')"
                        :required="true"
                        :property="'name'"
                        :rules="rules.name"
                      >
                        <bk-input
                          :placeholder="t('请输入 2-20 字符的字母、数字、连字符(-)、下划线(_)，以字母开头')"
                          v-model="curStageData.name"
                          :disabled="!isAdd"
                        ></bk-input>
                        <p
                          class="ag-tip mt5"
                        >
                          <i class="apigateway-icon icon-ag-info"></i>
                          {{ t('环境唯一标识，创建后不可修改。创建网关成功后可新增环境') }}
                        </p>
                      </bk-form-item>
                      <bk-form-item label="">
                        <div class="address">
                          <label>{{ t('访问地址') }}：</label>
                          <!-- 网关名/环境名 -->
                          <span>{{ stageAddress || '--' }}</span>
                          <i
                            class="apigateway-icon icon-ag-copy-info"
                            @click.self="copy(stageAddress)"
                          ></i>
                        </div>
                      </bk-form-item>
                      <bk-form-item :label="t('描述')" class="last-form-item">
                        <bk-input
                          v-model="curStageData.description"
                          :placeholder="t('请输入描述')"
                        ></bk-input>
                      </bk-form-item>
                    </bk-form>
                  </div>
                </template>
              </bk-collapse-panel>

              <bk-collapse-panel name="stage-config">
                <template #header>
                  <div class="panel-header">
                    <angle-up-fill
                      :class="[activeKey?.includes('stage-config') ? 'panel-header-show' : 'panel-header-hide']"
                    />
                    <div class="title">{{ t('后端服务配置') }}</div>
                  </div>
                </template>
                <template #content>
                  <div class="stage">
                    <bk-collapse :list="curStageData.backends" header-icon="right-shape" v-model="activeIndex">
                      <template #title="backend">
                        <span class="stage-name">
                          {{ backend.name }}
                        </span>
                      </template>
                      <template #content="backend">
                        <bk-form
                          :ref="setBackendConfigRef"
                          :label-width="180"
                          :model="backend"
                          form-type="vertical"
                        >
                          <bk-form-item
                            :required="true"
                            :label="t('负载均衡类型')"
                          >
                            <bk-select
                              :clearable="false"
                              :placeholder="t('负载均衡类型')"
                              v-model="backend.config.loadbalance"
                            >
                              <bk-option
                                v-for="option in loadbalanceList"
                                :key="option.id"
                                :id="option.id"
                                :name="option.name"
                              ></bk-option>
                            </bk-select>
                          </bk-form-item>

                          <bk-form-item
                            label="后端服务地址"
                            v-for="(hostItem, index) of backend.config.hosts"
                            :required="true"
                            :property="`config.hosts.${index}.host`"
                            :key="index"
                            :rules="rules.host"
                            :class="['backend-item-cls', { 'form-item-special': index !== 0 }]"
                          >
                            <div class="host-item">
                              <bk-input
                                :placeholder="$t('格式: host:port')"
                                v-model="hostItem.host"
                                :key="backend.config.loadbalance"
                              >
                                <template #prefix>
                                  <bk-select
                                    v-model="hostItem.scheme"
                                    class="scheme-select-cls"
                                    style="width: 120px"
                                    :clearable="false"
                                  >
                                    <bk-option
                                      v-for="(item, index1) in schemeList"
                                      :key="index1"
                                      :value="item.value"
                                      :label="item.value"
                                    />
                                  </bk-select>
                                  <div class="slash">://</div>
                                </template>
                                <template
                                  #suffix
                                  v-if="backend.config.loadbalance === 'weighted-roundrobin'"
                                >
                                  <bk-form-item
                                    :rules="rules.weight"
                                    :property="`config.hosts.${index}.weight`"
                                    label=""
                                    class="weight-input">
                                    <bk-input
                                      :class="['suffix-slot-cls', 'weights-input', { 'is-error': hostItem.isRoles }]"
                                      :placeholder="$t('权重')"
                                      type="number"
                                      :min="1"
                                      :max="10000"
                                      v-model="hostItem.weight"
                                    ></bk-input>
                                  </bk-form-item>
                                </template>
                              </bk-input>

                              <i
                                class="add-host-btn apigateway-icon icon-ag-plus-circle-shape ml10"
                                @click="handleAddServiceAddress(backend.name)"
                              ></i>
                              <i
                                class="delete-host-btn apigateway-icon icon-ag-minus-circle-shape ml10"
                                :class="{ disabled: backend.config.hosts.length < 2 }"
                                @click="
                                  backend.config.hosts.length < 2 ?
                                    '' :
                                    handleDeleteServiceAddress(backend.name, index)"
                              ></i>
                            </div>
                          </bk-form-item>

                          <bk-form-item
                            :label="$t('超时时间')"
                            :required="true"
                            :property="'config.timeout'"
                            class="timeout-item-cls"
                            :rules="rules.timeout"
                            :error-display-type="'normal'"
                          >
                            <bk-input
                              type="number"
                              :min="1"
                              :max="300"
                              v-model="backend.config.timeout"
                            >
                              <template #suffix>
                                <div class="group-text group-text-style" :class="locale === 'en' ? 'long' : ''">
                                  {{ $t('秒') }}
                                </div>
                              </template>
                            </bk-input>
                            <p class="timeout-tip" :class="locale === 'en' ? 'long' : ''">
                              {{ $t('最大 300 秒') }}
                            </p>
                          </bk-form-item>
                        </bk-form>
                      </template>
                    </bk-collapse>
                  </div>
                </template>
              </bk-collapse-panel>
            </bk-collapse>
          </div>
          <div v-else class="sideslider-content check-mode">
            <p class="title mt15">
              {{ $t("基本信息") }}
            </p>
            <bk-container class="ag-kv-box" :col="14" :margin="6">
              <bk-row>
                <bk-col :span="4">
                  <label class="ag-key">{{ $t("环境名称") }}:</label>
                </bk-col>
                <bk-col :span="10">
                  <div class="ag-value">
                    {{ curStageData.name }}
                  </div>
                </bk-col>
              </bk-row>

              <bk-row>
                <bk-col :span="4" class="mt8">
                  <label class="ag-key">{{ $t("访问地址") }}:</label>
                </bk-col>
                <bk-col :span="10">
                  <div class="ag-value address">
                    <span>{{ stageAddress || '--' }}</span>
                    <i
                      class="apigateway-icon icon-ag-copy-info"
                      @click.self="copy(stageAddress)"
                    ></i>
                  </div>
                </bk-col>
              </bk-row>
            </bk-container>

            <template
              v-for="backend in curStageData.backends"
              :key="backend.name"
            >
              <p class="title mt15">
                {{ `后端服务：${backend.name}` }}
              </p>
              <bk-container class="ag-kv-box" :col="14" :margin="6">
                <bk-row>
                  <bk-col :span="4">
                    <label class="ag-key">{{ $t("负载均衡类型") }}:</label>
                  </bk-col>
                  <bk-col :span="10">
                    <div class="ag-value">
                      {{ getLoadBalanceText(backend.config.loadbalance) }}
                    </div>
                  </bk-col>
                </bk-row>
                <template
                  v-for="host in backend.config.hosts"
                  :key="host.host"
                >
                  <bk-row>
                    <bk-col :span="4">
                      <label class="ag-key">{{ $t("后端服务地址") }}:</label>
                    </bk-col>
                    <bk-col :span="10">
                      <div class="ag-value">
                        {{ `${host.scheme}://${host.host}` }}
                      </div>
                    </bk-col>
                  </bk-row>
                  <bk-row v-if="backend.config.loadbalance === 'weighted-roundrobin'">
                    <bk-col :span="4">
                      <label class="ag-key">{{ $t("权重") }}:</label>
                    </bk-col>
                    <bk-col :span="10">
                      <div class="ag-value">
                        {{ host.weight }}
                      </div>
                    </bk-col>
                  </bk-row>
                </template>
                <bk-row>
                  <bk-col :span="4">
                    <label class="ag-key">{{ $t("超时时间") }}:</label>
                  </bk-col>
                  <bk-col :span="10">
                    <div class="ag-value">
                      {{ `${backend.config.timeout}秒` }}
                    </div>
                  </bk-col>
                </bk-row>
              </bk-container>
            </template>
          </div>

          <div v-if="actionType !== 'check'" class="footer-btn-wrapper">
            <bk-button
              theme="primary"
              style="padding: 0 30px"
              @click="handleConfirm"
            >
              {{ t('确定') }}
            </bk-button>
            <bk-button
              style="padding: 0 30px"
              @click="handleCancel"
            >
              {{ t('取消') }}
            </bk-button>
          </div>

          <div class="fixed-footer-btn-wrapper" v-show="isAdsorb">
            <bk-button
              theme="primary"
              style="padding: 0 30px"
              @click="handleConfirm"
            >
              {{ t('确定') }}
            </bk-button>
            <bk-button
              style="padding: 0 30px"
              @click="handleCancel"
            >
              {{ t('取消') }}
            </bk-button>
          </div>
        </bk-loading>
      </template>
    </bk-sideslider>
    <!-- <bk-dialog
      :is-show="isBackDialogShow"
      class="sideslider-close-back-dialog-cls"
      width="0"
      height="0"
      dialog-type="show">
    </bk-dialog> -->
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRoute } from 'vue-router';
import { getBackendsListData, createStage, getStageDetail, getStageBackends, updateStage } from '@/http';
import { Message } from 'bkui-vue';
import { cloneDeep } from 'lodash';
import { useCommon, useStage } from '@/store';
import { copy } from '@/common/util';
import mitt from '@/common/event-bus';
import { useGetGlobalProperties, useSidebar } from '@/hooks';
import { AngleUpFill } from 'bkui-vue/lib/icon';

const { t, locale } = useI18n();
const common = useCommon();
const stageStore = useStage();
const { initSidebarFormData, isSidebarClosed/* , isBackDialogShow */ } = useSidebar();
const route = useRoute();

const isShow = ref(false);
const isAdsorb = ref<boolean>(false);
const activeKey = ref(['base-info', 'stage-config']);
const activeIndex = ref([0]);
const actionType = ref('add');
const emit = defineEmits(['hidden']);

// 全局变量
const globalProperties = useGetGlobalProperties();
const { GLOBAL_CONFIG } = globalProperties;

// 默认值
const defaultConfig = () => {
  return {
    type: 'node',
    timeout: 30,
    loadbalance: 'weighted-roundrobin',
    hosts: [
      {
        scheme: 'http',
        host: '',
        weight: 100,
      },
    ],
  };
};

const curStageData = ref({
  name: '',
  description: '',
  backends: [
    {
      name: '',
      config: defaultConfig(),
    },
  ],
});

// 负载均衡类型
const loadbalanceList = [
  {
    id: 'roundrobin',
    name: t('轮询(Round-Robin)'),
  },
  {
    id: 'weighted-roundrobin',
    name: t('加权轮询(Weighted Round-Robin)'),
  },
];

// scheme 类型
const schemeList = [{ value: 'http' }, { value: 'https' }];

// slider 标题
const titleTextMap: {[key: string]: string} = {
  add: t('新建环境'),
  edit: t('编辑环境'),
  check: t('查看环境'),
};

// 访问地址
const stageAddress = computed(() => {
  const keys: any = {
    api_name: common.apigwName,
    stage_name: curStageData.value.name,
    resource_path: '',
  };

  let url = GLOBAL_CONFIG.STAGE_DOMAIN;
  for (const name of Object.keys(keys)) {
    const reg = new RegExp(`{${name}}`);
    url = url?.replace(reg, keys[name]);
  }
  return url;
});

// 正则校验
const rules = {
  name: [
    {
      required: true,
      message: t('必填项'),
      trigger: 'blur',
    },
    {
      validator(value: string) {
        const reg = /^[a-zA-Z][a-zA-Z0-9_-]{0,19}$/;
        return reg.test(value);
      },
      message: t('请输入 2-20 字符的字母、数字、连字符(-)、下划线(_)，以字母开头'),
      trigger: 'change',
    },
  ],

  host: [
    {
      required: true,
      message: t('必填项'),
      trigger: 'blur',
    },
    {
      validator(value: string) {
        const reg = /^(?=^.{3,255}$)[a-zA-Z0-9][-a-zA-Z0-9]{0,62}(\.[a-zA-Z0-9][-a-zA-Z0-9]{0,62})*(:\d+)?$|^\[([0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}\](:\d+)?$/;
        return reg.test(value);
      },
      message: t('请输入合法Host，如：http://example.com'),
      trigger: 'blur',
    },
  ],

  weight: [
    {
      required: true,
      message: t('必填项'),
      trigger: 'blur',
    },
  ],

  timeout: [
    {
      required: true,
      message: t('必填项'),
      trigger: 'blur',
    },
    {
      validator(val: number) {
        if (val < 0 || val > 300) {
          return false;
        }
        return true;
      },
      message: t('超时时间不能小于1且不能大于300'),
      trigger: 'blur',
    },
  ],
};

// 侧边loading
const isDialogLoading = ref(true);

// 获取对应Ref
const baseInfoRef = ref(null);
const backendConfigRef = ref([]);

// 网关id
const apigwId = +route.params.id;

// 默认为新建
const isAdd = ref(true);

const title = computed(() => {
  return titleTextMap[actionType.value] ?? t('环境');
});

const setBackendConfigRef = (el: any) => {
  if (el !== null) {
    backendConfigRef.value.push(el);
  }
};

// 新建初始化（新建）
const addInit = async () => {
  isDialogLoading.value = true;
  // 获取当前网关下的backends(获取后端服务列表)
  const res = await getBackendsListData(apigwId);
  console.log('获取all后端服务列表', res);
  activeIndex.value = [];
  curStageData.value.backends = res.results.map((item: any, index: number) => {
    activeIndex.value.push(index);
    // 后端服务配置默认值
    return {
      id: item.id,
      name: item.name,
      config: defaultConfig(),
    };
  });
  isDialogLoading.value = false;
  initSidebarFormData(curStageData.value);
};

// 查看态初始化
const checkInit = async () => {
  isDialogLoading.value = true;
  try {
    const data = await getStageDetail(apigwId, stageStore.curStageData.id);
    curStageData.value.name = data.name;
    curStageData.value.backends = await getStageBackends(common.apigwId, stageStore.curStageData.id);
  } finally {
    isDialogLoading.value = false;
  }
};

// 获取环境详情（编辑）
const getStageDetailFun = async () => {
  try {
    const data = await getStageDetail(apigwId, stageStore.curStageData.id);
    curStageData.value.name = data.name;
    curStageData.value.description = data.description;
  } catch (error) {
    console.error(error);
  }
};

// 获取环境后端服务详情（编辑）
const getStageBackendList = async () => {
  isDialogLoading.value = true;
  const backendList = await getStageBackends(common.apigwId, stageStore.curStageData.id);
  curStageData.value.backends = backendList;
  activeIndex.value = [];
  backendList?.forEach((item: any, index: number) => {
    activeIndex.value.push(index);
  });
  // 数据转换
  isDialogLoading.value = false;
};

// 关闭侧边栏回调
const handleCloseSideSlider = () => {
  // 数据重置
  curStageData.value = {
    name: '',
    description: '',
    backends: [
      {
        name: '',
        config: defaultConfig(),
      },
    ],
  };
  activeIndex.value = [0];
};

// 显示侧边栏
const handleShowSideslider = async (type: string) => {
  // 数据重置
  handleCloseSideSlider();
  actionType.value = type || 'add';
  // 新建环境获取当前网关下的所有后端服务进行配置
  if (type === 'add') {
    isAdd.value = true;
    addInit();
  } else if (type === 'edit') {
    isAdd.value = false;
    // 编辑环境
    await Promise.all([
      getStageDetailFun(),
      // 获取对应环境下的后端服务列表
      getStageBackendList(),
    ]);
    initSidebarFormData(curStageData.value);
  } else if (type === 'check') {
    isAdd.value = false;
    await checkInit();
  }
  isShow.value = true;
};

// 确定
const handleConfirm = async () => {
  try {
    // 表单校验
    await baseInfoRef.value.validate();
    for (const item of backendConfigRef.value) {
      await item.validate();
    }

    isAdd.value ? handleConfirmCreate() : handleConfirmEdit();
  } catch (error) {
    console.error(error);
  }
};

// 新建环境
const handleConfirmCreate = async () => {
  try {
    const params = cloneDeep(curStageData.value);
    // 删除冗余参数
    params.backends.forEach((v: any) => {
      delete v.name;
    });
    await createStage(apigwId, params);
    Message({
      message: t('创建成功'),
      theme: 'success',
    });
    // 重新获取环境列表(全局事件总线实现)
    mitt.emit('rerun-init', true);
    // 数据重置
    handleCloseSideSlider();
    // 关闭dialog
    isShow.value = false;
  } catch (error) {
    console.error(error);
  }
};

// 编辑环境
const handleConfirmEdit = async () => {
  try {
    const stageId = stageStore.curStageData.id;
    const params = cloneDeep(curStageData.value);
    // 删除冗余参数
    params.backends.forEach((v: any) => {
      delete v.name;
    });
    await updateStage(apigwId, stageId, params);
    Message({
      message: t('更新成功'),
      theme: 'success',
    });
    // 重新获取环境列表(全局事件总线实现)
    mitt.emit('rerun-init', true);
    // 关闭dialog
    isShow.value = false;
  } catch (error) {
    console.error(error);
  }
};

const handleBeforeClose = async () => {
  if (actionType.value !== 'check') {
    return isSidebarClosed(JSON.stringify(curStageData.value));
  }
  return true;
};

const handleAnimationEnd = () => {
  handleCancel();
};

// 取消关闭侧边栏
const handleCancel = () => {
  isShow.value = false;
  // 数据重置
  handleCloseSideSlider();
};

// 添加服务地址
const handleAddServiceAddress = (name: string) => {
  curStageData.value.backends.forEach((v) => {
    if (v.name === name) {
      v.config.hosts.push({
        scheme: 'http',
        host: '',
        weight: 100,
      });
    }
  });
  controlToggle();
};

// 删除服务地址
const handleDeleteServiceAddress = (name: string, index: number) => {
  curStageData.value.backends.forEach((v) => {
    if (v.name === name) {
      console.log(v);
      v.config.hosts.splice(index, 1);
    }
  });
  controlToggle();
};

// 获取按钮底部距离
const getDistanceToBottom = (element: any) => {
  const rect = element?.getBoundingClientRect();
  return Math.max(0, window?.innerHeight - rect?.bottom);
};

// 元素滚动判断元素是否吸顶
const controlToggle = () => {
  const el = document.querySelector('.footer-btn-wrapper');
  const bottomDistance = getDistanceToBottom(el);
  const maxDistance = 1000;
  // 是否吸附
  if (bottomDistance < 25 || bottomDistance > maxDistance) {
    isAdsorb.value = true;
    el.classList.add('is-pinned');
  } else {
    isAdsorb.value = false;
    el?.classList?.remove('is-pinned');
  }
};

const getLoadBalanceText = (value: string) => {
  return loadbalanceList.find(item => item.id === value)?.name ?? '--';
};

const observerBtnScroll = () => {
  const container = document.querySelector('.bk-modal-content');
  container?.addEventListener('scroll', controlToggle);
};

const destroyEvent = () => {
  const container = document.querySelector('.bk-modal-content');
  container?.removeEventListener('scroll', controlToggle);
};

watch(
  () => isShow.value,
  (v) => {
    if (v) {
      setTimeout(() => {
        controlToggle();
        observerBtnScroll();
      }, 200);
    } else {
      destroyEvent();
    }
  },
);

// 暴露属性
defineExpose({
  handleShowSideslider,
});
</script>

<style lang="scss" scoped>
.stage-sideslider-cls {
  :deep(.bk-sideslider-footer) {
    position: absolute;
    bottom: 0;
    box-shadow: 0 -1px 0 0 #dcdee5;
  }
  :deep(.bk-modal-content) {
    overflow-y: auto;
  }
}
.sideslider-content {
  padding: 20px 40px 32px;
  .host-item {
    display: flex;
    align-items: center;
    i {
      font-size: 14px;
      color: #979ba5;
      cursor: pointer;
      &:hover {
        color: #63656e;
      }

      &.disabled {
        color: #dcdee5;
        cursor: not-allowed;
      }
    }
    :deep(.bk-form-error) {
      position: relative;
    }
  }
  .address {
    height: 40px;
    line-height: 40px;
    background: #f5f7fa;
    border-radius: 2px;
    padding: 0 16px;

    label {
      height: 22px;
      font-weight: 700;
      font-size: 14px;
      color: #63656e;
      line-height: 22px;
    }
    span {
      font-size: 14px;
      color: #63656e;
    }
    i {
      cursor: pointer;
      color: #3a84ff;
      margin-left: 5px;
      padding: 3px;
    }
  }

  .weights-input {
    :deep(.bk-input--number-control) {
      display: none;
    }
  }

  &.check-mode {
    .title {
      font-size: 13px;
      color: #63656e;
      font-weight: bold;
      padding-bottom: 10px;
      border-bottom: 1px solid #dcdee5;
      margin-bottom: 17px;
    }
    .ag-kv-box {
      .bk-grid-row {
        margin-bottom: 12px;
      }
      .ag-key {
        font-size: 14px;
        color: #63656e;
        display: block;
        text-align: right;
        padding-right: 0;
      }
      .ag-value {
        font-size: 14px;
        color: #313238;
      }
    }
  }
}
.weight-input {
  margin-bottom: 0px;
  border-left: 1px solid #c4c6cc !important;
  :deep(.bk-form-content) {
    margin-top: -1px;
  }
}
.suffix-slot-cls {
  width: 80px;
  line-height: 30px;
  font-size: 12px;
  color: #63656e;
  text-align: center;
  height: 30px;
  border: none;
  box-shadow: none !important;
  :deep(.bk-input--text) {
    border-radius: 0;
  }
}
.group-text-style {
  width: 20px;
  color: #63656e;
  text-align: left;
  background: #f5f7fa;
  &.long {
    width: 50px;
  }
}
.scheme-select-cls {
  color: #63656e;
  width: 120px;
  overflow: hidden;
  :deep(.bk-input--default) {
    border: none;
    border-right: 1px solid #c4c6cc;
  }
}
.slash {
  color: #63656e;
  background: #fafbfd;
  padding: 0 10px;
  border-right: 1px solid #c4c6cc;
}
.timeout-item-cls {
  margin-top: 14px;
  width: 240px;
  position: relative;
  :deep(.bk-form-content) {
    .timeout-tip {
      position: absolute;
      top: 1px;
      right: -77px;
      color: #63656e;
      margin-left: 13px;
      white-space: nowrap;
      font-size: 12px;
      &.long {
        right: -110px;
      }
    }
  }
}
.form-item-special {
  :deep(.bk-form-label) {
    display: none;
  }
}
.backend-item-cls {
  margin-bottom: 18px;
  :deep(.bk-form-error) {
    position: relative;
  }
  &:last-child {
    margin-bottom: 24px;
    background: red;
  }
}
.backend-item-cls:last-child {
  margin-bottom: 50px !important;
  background: #3a84ff;
}

.footer-btn-wrapper {
  bottom: 0;
  height: 52px;
  padding-left: 40px;
}
.fixed-footer-btn-wrapper {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 10px 0;
  padding-left: 40px;
  background: #fff;
  box-shadow: 0 -2px 4px 0 #0000000f;
  z-index: 9;
  transition: .3s;
}
.is-pinned {
  opacity: 0;
}
.bk-collapse-service {
  .panel-header {
    display: flex;
    align-items: center;
    padding: 12px 0px;
    cursor: pointer;
    .title {
      font-weight: 700;
      font-size: 14px;
      color: #313238;
      margin-left: 8px;
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

  :deep(.bk-collapse-content) {
    padding: 0px;
  }

  .stage {
    :deep(.bk-collapse-title) {
      margin-left: 23px;
      font-size: 14px;
      color: #63656E;
      font-weight: 700;
    }
    :deep(.bk-collapse-item) {
      background-color: #F5F7FB;
      &:not(:nth-last-child(1)) {
        margin-bottom: 25px;
      }

      .bk-collapse-content {
        padding: 5px 32px;
      }
    }

    .stage-name {
      color: #63656E;
      font-size: 14px;
      font-weight: 700;
    }

    :deep(.bk-collapse-icon) {
      left: 17px;
      top: 17px;
      color: #979AA2;

      svg {
        font-size: 13px;
      }
    }
  }

  .last-form-item {
    margin-bottom: 12px;
  }
}
</style>
