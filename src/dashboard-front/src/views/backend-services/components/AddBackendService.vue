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
  <div>
    <AgSideslider
      v-model="sliderConfig.isShow"
      ext-cls="backend-service-slider"
      :init-data="initData"
      @closed="handleCancel"
      @compare="handleCompare"
    >
      <template #header>
        <div class="custom-side-header">
          <div class="title">
            {{ t(editId ? "编辑后端服务" : "新建后端服务") }}
          </div>
          <template v-if="editId">
            <span />
            <div class="subtitle">
              {{ baseInfo.name }}
            </div>
          </template>
        </div>
      </template>
      <template #default>
        <div class="slider-content">
          <BkAlert
            v-if="gatewayStore.isProgrammableGateway"
            :title="
              t(
                '发布可编程网关后，系统将在蓝鲸开发者中心部署一个 SaaS 以提供 API 后端服务，并自动获取其访问地址。'
              )
            "
            class="service-tips"
          />
          <BkAlert
            v-if="editId && isPublish"
            :title="
              t('如果环境和资源已经发布，服务配置修改后，将立即对所有已发布资源生效')
            "
            class="service-tips"
            theme="warning"
          />

          <BkCollapse
            v-model="activeKey"
            class="bk-collapse-service"
          >
            <BkCollapsePanel name="base-info">
              <template #header>
                <div class="flex items-center panel-header">
                  <AngleUpFill
                    :class="[
                      activeKey?.includes('base-info')
                        ? 'panel-header-show'
                        : 'panel-header-hide',
                    ]"
                  />
                  <div class="title">
                    {{ t("基础信息") }}
                  </div>
                </div>
              </template>
              <template #content>
                <div>
                  <BkForm
                    ref="baseInfoRef"
                    class="base-info-form"
                    :model="baseInfo"
                    form-type="vertical"
                  >
                    <BkFormItem
                      :label="t('服务名称')"
                      property="name"
                      required
                      :rules="baseInfoRules.name"
                    >
                      <BkInput
                        ref="nameRef"
                        v-model="baseInfo.name"
                        :disabled="Boolean(editId) || disabled"
                        :placeholder="
                          t('请输入 1-20 字符的字母、数字、连字符(-)，以字母开头')
                        "
                      />
                      <p class="alert-text">
                        {{ t("后端服务唯一标识，创建后不可修改") }}
                      </p>
                    </BkFormItem>
                    <BkFormItem
                      :label="t('描述')"
                      property="description"
                      class="m-t-12px"
                    >
                      <BkInput
                        v-model="baseInfo.description"
                        :disabled="disabled"
                        :placeholder="t('请输入描述')"
                      />
                    </BkFormItem>
                  </BkForm>
                </div>
              </template>
            </BkCollapsePanel>

            <BkCollapsePanel name="stage-config">
              <template #header>
                <div class="flex items-center panel-header">
                  <AngleUpFill
                    :class="[
                      activeKey?.includes('stage-config')
                        ? 'panel-header-show'
                        : 'panel-header-hide',
                    ]"
                  />
                  <div class="title">
                    {{ t('各环境的服务配置') }}
                  </div>
                </div>
              </template>
              <template #content>
                <div class="stage">
                  <BkCollapse
                    v-model="activeIndex"
                    :list="stageConfig"
                    header-icon="right-shape"
                  >
                    <template #title="slotProps">
                      <span class="stage-name">
                        {{ slotProps.name || slotProps.configs?.stage?.name }}
                      </span>
                    </template>
                    <template #content="slotProps">
                      <BkForm
                        :ref="(el:HTMLElement) => getStageConfigRef(el, slotProps.$index)"
                        class="stage-config-form"
                        :model="slotProps"
                        form-type="vertical"
                      >
                        <BkFormItem
                          :label="t('负载均衡类型')"
                          property="configs.loadbalance"
                          class="mt-20px relative"
                          required
                          :rules="configRules.loadbalance"
                        >
                          <BkSelect
                            v-model="slotProps.configs.loadbalance"
                            :clearable="false"
                            :disabled="disabled"
                            @change="(value: string) => handleLoadBalanceChange(value, slotProps.id)"
                          >
                            <BkOption
                              v-for="option of loadbalanceList"
                              :key="option.id"
                              :value="option.id"
                              :label="option.name"
                            />
                          </BkSelect>
                          <BkLink
                            class="absolute right-0 top--30px"
                            theme="primary"
                            :href="envStore.env.DOC_LINKS.LOADBALANCE"
                            target="_blank"
                          >
                            <AgIcon
                              name="jump"
                              size="12"
                              class="mr-4px"
                            />
                            <span class="text-12px">{{ t('帮助文档') }}</span>
                          </BkLink>
                        </BkFormItem>

                        <!-- hash_on -->
                        <BkFormItem
                          v-if="slotProps.configs.loadbalance === 'chash'"
                          :label="t('哈希位置')"
                          property="configs.hash_on"
                          required
                        >
                          <BkSelect
                            v-model="slotProps.configs.hash_on"
                            :clearable="false"
                            :filterable="false"
                            :disabled="disabled"
                            @change="(value: string) => handleHashOnChange(value, slotProps.id)"
                          >
                            <BkOption
                              v-for="type in hashOnOptions"
                              :id="type.id"
                              :key="type.id"
                              :name="type.name"
                            />
                          </BkSelect>
                        </BkFormItem>

                        <KeyFormItem
                          v-if="slotProps.configs.loadbalance === 'chash'"
                          :stage-config="slotProps"
                          label="Key"
                          property="configs.key"
                          :disabled="disabled"
                          required
                          @change="handleHashOnKeyChange"
                        />

                        <BkFormItem
                          v-for="(hostItem, i) in slotProps.configs.hosts"
                          :key="i"
                          :label="t('后端服务地址')"
                          :rules="configRules.host"
                          :property="`configs.hosts.${i}.host`"
                          class="backend-item-cls"
                          :class="[{ 'form-item-special': i !== 0 }]"
                          required
                        >
                          <div class="flex items-center host-item">
                            <BkInput
                              :key="i"
                              v-model="hostItem.host"
                              :disabled="disabled"
                              :placeholder="t('格式如：host:port')"
                            >
                              <template #prefix>
                                <BkSelect
                                  v-model="hostItem.scheme"
                                  class="scheme-select-cls w-80px"
                                  :filterable="false"
                                  :clearable="false"
                                  :disabled="disabled"
                                >
                                  <BkOption
                                    v-for="(item, index) in schemeList"
                                    :key="index"
                                    :value="item.value"
                                    :label="item.value"
                                  />
                                </BkSelect>
                                <div class="slash">
                                  ://
                                </div>
                              </template>
                              <template
                                v-if="
                                  ['weighted-roundrobin'].includes(
                                    slotProps?.configs?.loadbalance
                                  )
                                "
                                #suffix
                              >
                                <BkFormItem
                                  :rules="configRules.weight"
                                  :property="`configs.hosts.${i}.weight`"
                                  label=""
                                  class="weight-input"
                                >
                                  <BkInput
                                    v-model="hostItem.weight"
                                    :disabled="disabled"
                                    class="suffix-slot-cls weights-input"
                                    :placeholder="t('权重')"
                                    type="number"
                                    :min="1"
                                    :max="10000"
                                  />
                                </BkFormItem>
                              </template>
                            </BkInput>
                            <i
                              class="add-host-btn apigateway-icon icon-ag-plus-circle-shape"
                              @click="() => handleAddServiceAddress(slotProps.name)"
                            />
                            <i
                              class="delete-host-btn apigateway-icon icon-ag-minus-circle-shape"
                              :class="{ disabled: slotProps.configs.hosts.length < 2 }"
                              @click="() => handleDeleteServiceAddress(slotProps.name, i)"
                            />
                          </div>
                        </BkFormItem>
                        <BkFormItem
                          :label="t('超时时间')"
                          :property="'configs.timeout'"
                          class="timeout-item"
                          required
                          :rules="configRules.timeout"
                          :error-display-type="'normal'"
                        >
                          <BkInput
                            v-model="slotProps.configs.timeout"
                            type="number"
                            :min="1"
                            :max="300"
                            :disabled="disabled"
                            class="time-input"
                          >
                            <template #suffix>
                              <div
                                class="group-text group-text-style"
                                :class="locale === 'en' ? 'long' : ''"
                              >
                                {{ t('秒') }}
                              </div>
                            </template>
                          </BkInput>
                          <span
                            class="timeout-tip"
                            :class="locale === 'en' ? 'long' : ''"
                          >
                            {{ t('最大 300 秒') }}
                          </span>
                        </BkFormItem>
                      </BkForm>
                    </template>
                  </BkCollapse>
                </div>
              </template>
            </BkCollapsePanel>
          </BkCollapse>
        </div>
      </template>
      <template #footer>
        <div class="pl-40px">
          <BkButton
            :disabled="disabled"
            :loading="isSaveLoading"
            class="mr-8px w-88px"
            theme="primary"
            @click="handleConfirm"
          >
            {{ t("确定") }}
          </BkButton>
          <BkButton
            class="w-88px"
            @click="handleCancel"
          >
            {{ t("取消") }}
          </BkButton>
        </div>
      </template>
    </AgSideslider>

    <!-- 提示弹窗 -->
    <BkDialog
      v-model:is-show="publishDialog.isShow"
      class="custom-main-dialog"
      width="500"
    >
      <div class="dialog-content">
        <div class="publish-icon">
          <Success fill="#3FC06D" />
        </div>
        <div class="dialog-title">
          {{ t("内容保存成功，正在发布至对应环境...") }}
        </div>
        <div class="dialog-main">
          <div class="publish-tips">
            {{ t("当前服务") }} <span>{{ baseInfo.name }}</span>{{ t("，") }} {{ t("已绑定以下") }}
            <span>{{ publishDialog.stageNames?.length }}</span>
            {{ t("个环境，所有修改都将发布到这些环境中：") }}
          </div>
          <div class="flex flex-wrap publish-stages">
            <div
              v-for="stage in publishDialog.stageNames"
              :key="stage"
              class="stage-item"
            >
              {{ stage }}
            </div>
          </div>
        </div>
        <div class="dialog-footer">
          <BkButton
            theme="primary"
            @click="toStageReleaseRecord"
          >
            {{ t("去查看发布记录") }}
          </BkButton>
          <BkButton
            class="ml-10px"
            @click="publishDialog.isShow = false"
          >
            {{ t("关闭") }}
          </BkButton>
        </div>
      </div>
    </BkDialog>
  </div>
</template>

<script lang="ts" setup>
import { cloneDeep, isEqual } from 'lodash-es';
import { Form, Input, Message } from 'bkui-vue';
import { AngleUpFill, Success } from 'bkui-lib/icon';
import {
  useEnv,
  useGateway,
} from '@/stores';
import type { IFormMethod } from '@/types/common';
import {
  type IBackendServicesConfig,
  createBackendService,
  getBackendServiceDetail,
  updateBackendService,
} from '@/services/source/backendServices';
import { type IStageListItem, getStageList } from '@/services/source/stage';
import AgSideslider from '@/components/ag-sideslider/Index.vue';
import KeyFormItem from '@/views/backend-services/components/KeyFormItem.vue';

interface IProps {
  editId?: number
  disabled?: boolean
  base: Record<string, any>
}

interface Emits { (e: 'done'): void }

const { editId = 0, base } = defineProps<IProps>();
const emits = defineEmits<Emits>();

const { t, locale } = useI18n();
const router = useRouter();
const gatewayStore = useGateway();
const envStore = useEnv();

const hostReg = /^(?=^.{3,255}$)[a-zA-Z0-9][-a-zA-Z0-9]{0,62}(\.[a-zA-Z0-9][-a-zA-Z0-9]{0,62})*(:\d+)?$|^\[([0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}\](:\d+)?$/;
const activeKey = ref(['base-info', 'stage-config']);
// 基础信息
const baseInfo = ref({
  name: '',
  description: '',
});
const curServiceDetail = ref({
  id: 0,
  name: '',
  description: '',
  configs: [],
});
const initData = ref();
const stageConfig = ref([]);
const activeIndex = ref([]);
const stageList = ref([]);
const stageConfigRef = ref([]);
const isPublish = ref(false);
const isSaveLoading = ref(false);
const finalConfigs = ref([]);
const nameRef = ref<InstanceType<typeof Input>>(null);
const baseInfoEl = useTemplateRef<InstanceType<typeof Form> & IFormMethod>(
  'baseInfoRef',
);
let publishDialog = reactive({
  isShow: false,
  stageNames: [],
});
const sliderConfig = reactive({
  isShow: false,
  title: '',
});
// scheme 类型
const schemeList = [{ value: 'http' }, { value: 'https' }];
// 基础信息校验规则
const baseInfoRules = {
  name: [
    {
      required: true,
      message: t('必填项'),
      trigger: 'blur',
    },
    {
      validator: (value: string) => {
        const reg = /^[a-zA-Z][a-zA-Z0-9-]{0,19}$/;
        return reg.test(value);
      },
      message: t('请输入 1-20 字符的字母、数字、连字符(-)，以字母开头'),
      trigger: 'blur',
    },
  ],
};
// 服务配置校验规则
const configRules = {
  loadbalance: [
    {
      required: true,
      message: t('必填项'),
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
        return hostReg.test(value);
      },
      message: t('请输入合法Host，如：example.com'),
      trigger: 'blur',
    },
  ],
  weight: [
    {
      required: true,
      message: t('必填项'),
      trigger: 'change',
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
// 负载均衡类型
const loadbalanceList = [
  {
    id: 'roundrobin',
    name: t('轮询（Round-Robin）'),
  },
  {
    id: 'weighted-roundrobin',
    name: t('加权轮询（Weighted Round-Robin）'),
  },
  {
    id: 'chash',
    name: t('一致性哈希（CHash）'),
  },
  {
    id: 'ewma',
    name: t('指数加权移动平均法（EWMA）'),
  },
  {
    id: 'least_conn',
    name: t('最小连接数（least_conn）'),
  },
];

const hashOnOptions = [
  {
    id: 'vars',
    name: 'vars',
  },
  {
    id: 'header',
    name: 'header',
  },
  {
    id: 'cookie',
    name: 'cookie',
  },
];

const apigwId = computed<number>(() => gatewayStore.apigwId);

watch(
  () => base,
  (val) => {
    baseInfo.value = val;
  },
  { immediate: true },
);

// 获取所有stage服务配置的ref
const getStageConfigRef = (el: HTMLElement, index: number) => {
  if (el) stageConfigRef.value[index] = el;
};

const handleScrollView = (el: HTMLInputElement | HTMLElement) => {
  el.scrollIntoView({
    behavior: 'smooth',
    block: 'center',
  });
};

// 增加服务地址
const handleAddServiceAddress = (name: string) => {
  const isAddItem = stageConfig.value;
  isAddItem.forEach((item) => {
    if (item.name === name) {
      item.configs.hosts.push({
        scheme: 'http',
        host: '',
        weight: 100,
      });
    }
  });
};

// 删除服务地址
const handleDeleteServiceAddress = (name: string, index: number) => {
  const isDeleteItem = stageConfig.value;
  isDeleteItem.forEach((item: IBackendServicesConfig) => {
    if (item.name === name && item.configs.hosts.length !== 1) {
      item.configs.hosts.splice(index, 1);
    }
  });
};

const handleCancel = () => {
  sliderConfig.isShow = false;
  stageConfigRef.value = [];
  baseInfoEl.value?.clearValidate();
};

const handleConfirm = async () => {
  let emptyHostIndex = -1;
  // 基础信息校验
  try {
    await baseInfoEl.value?.validate();
  }
  catch {
    nameRef.value?.focus();
    handleScrollView(nameRef?.value?.$el);
    return;
  }
  // 逐个stage服务配置的校验
  try {
    for (const item of stageConfigRef.value) {
      if (!item) break;
      const { hosts, timeout } = item.model.configs;
      const isEmpty = hosts.some(config => !config.host || !hostReg.test(config.host)) || !String(timeout);
      if (isEmpty) {
        emptyHostIndex = item.model.$index;
      }
      await item.validate();
    }
  }
  catch {
    if (emptyHostIndex > -1) {
      handleScrollView(stageConfigRef.value[emptyHostIndex]?.$el);
    }
    return;
  }
  finalConfigs.value = stageConfig.value.map((item) => {
    const id = !editId ? item.id : item.configs.stage.id;
    const results = {
      timeout: item.configs.timeout,
      loadbalance: item.configs.loadbalance,
      hosts: item.configs.hosts,
      stage_id: id,
    };
    if (item.configs.hash_on) {
      Object.assign(results, { hash_on: item.configs.hash_on });
    }
    if (item.configs.key) {
      Object.assign(results, { key: item.configs.key });
    }
    return results;
  });
  const { name, description } = baseInfo.value;
  const params = {
    name,
    description,
    configs: finalConfigs.value,
  };
  if (editId) {
    const detailContent = {
      name: curServiceDetail.value.name,
      description: curServiceDetail.value.description,
      configs: curServiceDetail.value.configs.map((item) => {
        return {
          timeout: item.timeout,
          loadbalance: item.loadbalance,
          hosts: item.hosts,
          stage_id: item.stage.id,
        };
      }),
    };
    // 如果内容一致无需调用编辑接口
    if (isEqual(detailContent, params)) {
      handleCancel();
      return;
    }
  }
  isSaveLoading.value = true;
  try {
    let res = {};
    res = editId
      ? await updateBackendService(apigwId.value, curServiceDetail.value.id, params)
      : await createBackendService(apigwId.value, params);
    if (isPublish.value && editId) {
      sliderConfig.isShow = false;
      if (res?.updated_stages?.length) {
        publishDialog = Object.assign(publishDialog, {
          isShow: true,
          stageNames: res?.updated_stages?.map(item => item.name),
        });
      }
      else {
        Message({
          message: t('保存成功'),
          theme: 'success',
        });
      }
    }
    else {
      Message({
        message: t(!editId ? '新建成功' : '更新成功'),
        theme: 'success',
      });
      sliderConfig.isShow = false;
    }
    stageConfigRef.value = [];
    emits('done');
  }
  finally {
    isSaveLoading.value = false;
  }
};

const toStageReleaseRecord = () => {
  router.push({ name: 'StageReleaseRecord' });
};

const setInit = () => {
  stageConfig.value = stageList.value.map((item: Record<string, string | number>) => {
    const { name, id, description } = item;
    const newItem = {
      name,
      id,
      description,
      configs: {
        loadbalance: 'roundrobin',
        timeout: 30,
        hosts: [
          {
            scheme: 'http',
            host: '',
            weight: 100,
          },
        ],
        stage_id: id,
      },
    };
    return newItem;
  });
  const sliderParams = {
    curServiceDetail: curServiceDetail.value,
    stageConfig: stageConfig.value,
    baseInfo: baseInfo.value,
  };
  initData.value = cloneDeep(sliderParams);
};

const handleCompare = (callback) => {
  const sliderParams = {
    curServiceDetail: curServiceDetail.value,
    stageConfig: stageConfig.value,
    baseInfo: baseInfo.value,
  };
  callback(cloneDeep(sliderParams));
};

const getStageListData = async () => {
  const res = await getStageList(apigwId.value);
  res?.forEach((item: IStageListItem, index: number) => {
    activeIndex.value.push(index);
  });
  isPublish.value = res?.some(item => item.publish_id !== 0);
  stageList.value = [...res];
};

const getInfo = async () => {
  const res = await getBackendServiceDetail(apigwId.value, editId);
  curServiceDetail.value = cloneDeep(res);
  stageConfig.value = res.configs.map((item) => {
    return {
      configs: item,
      name: item?.stage?.name,
      id: item?.stage?.id,
    };
  });
  const sliderParams = {
    curServiceDetail: curServiceDetail.value,
    stageConfig: stageConfig.value,
    baseInfo: baseInfo.value,
  };
  initData.value = cloneDeep(sliderParams);
};

const handleLoadBalanceChange = (value: string, stageId: number) => {
  const stage = stageConfig.value.find(item => item.id === stageId);
  if (stage) {
    if (value === 'chash') {
      stage.configs.hash_on = 'vars';
      stage.configs.key = 'remote_addr';
    }
    else {
      delete stage.configs.hash_on;
      delete stage.configs.key;
    }
  }
};

const handleHashOnChange = (value: string, stageId: number) => {
  const stage = stageConfig.value.find(item => item.id === stageId);
  if (stage) {
    if (value === 'vars') {
      stage.configs.key = 'remote_addr';
    }
    else {
      stage.configs.key = '';
    }
  }
};

const handleHashOnKeyChange = (config: any) => {
  const stage = stageConfig.value.find(item => item.id === config.id);
  if (stage) {
    stage.configs.key = config.configs.key;
  }
};

const show = async () => {
  await getStageListData();
  if (editId) {
    await getInfo();
  }
  else {
    setInit();
  }
  sliderConfig.isShow = true;
};

defineExpose({ show });
</script>

<style lang="scss" scoped>
.backend-service-slider {

  :deep(.bk-modal-content) {
    overflow-y: auto;
    scrollbar-gutter: stable;
  }

  :deep(.bk-sideslider-footer) {
    margin-top: 0;
  }

  .title {
    margin-left: 8px;
    font-size: 14px;
    font-weight: 700;
    color: #323237;

    .icon {
      font-size: 18px;
      color: #4d4f56;
    }
  }

  .slider-content {
    padding: 20px 34px 32px 40px;

    .bk-form-label {
      line-height: 22px;
    }

    .alert-text {
      font-size: 12px;
      line-height: 22px;
      color: #979ba5;
    }
  }

  .service-tips {
    margin-bottom: 12px;
  }

  .host-item {

    i {
      margin-left: 10px;
      font-size: 14px;
      color: #979ba5;

      &.add-host-btn {
        margin-left: 13px;
      }

      &:hover {
        color: #63656e;
        cursor: pointer;
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

  .form-item-special {

    :deep(.bk-form-label) {
      display: none;
    }
  }

  .weight-input {
    margin-bottom: 0;
    border-left: 1px solid #c4c6cc !important;
  }

  .suffix-slot-cls {
    width: 80px;
    height: 28px;
    font-size: 12px;
    line-height: 28px;
    color: #63656e;
    text-align: center;
    border: none;
    box-shadow: none !important;

    :deep(.bk-input--text) {
      border-radius: 0;
    }
  }

  .scheme-select-cls {
    overflow: hidden;
    color: #63656e;

    :deep(.bk-input--default) {
      border: none;
      border-right: 1px solid #c4c6cc;
    }
  }

  .timeout-item {
    position: relative;
    width: 200px;

    .timeout-tip {
      position: absolute;
      top: 0;
      right: -70px;

      &.long {
        right: -120px;
      }
    }

    .group-text {
      width: 20px;

      &.long {
        width: 50px;
      }
    }
  }

  .slash {
    padding: 0 10px;
    color: #63656e;
    background-color: #fafbfd;
    border-right: 1px solid #c4c6cc;
  }
}

.backend-config-item {

  .item-content {
    padding: 20px 32px;
    background: #f5f7fa;

    .host-item {

      i {
        font-size: 14px;
        color: #979ba5;
        cursor: pointer;

        &.disabled {
          color: #dcdee5;
        }
      }

      :deep(.bk-form-error) {
        position: relative;
      }
    }
  }
}

.bk-collapse-service {

  .panel-header {
    margin-bottom: 16px;
    cursor: pointer;

    .title {
      margin-left: 8px;
      font-size: 14px;
      font-weight: 700;
      color: #313238;
    }

    .panel-header-show,
    .panel-header-hide {
      color: #4d4f56;
      transform: rotate(0deg);
      transition: 0.2s;
    }

    .panel-header-hide {
      transform: rotate(-90deg);
    }
  }

  :deep(.bk-collapse-content) {
    padding: 0;
  }

  .stage {

    .stage-name {
      font-size: 14px;
      font-weight: 700;
      color: #63656e;
    }

    :deep(.bk-collapse-title) {
      margin-left: 23px;
      font-size: 14px;
      font-weight: 700;
      color: #63656e;
    }

    :deep(.bk-collapse-item) {
      margin-bottom: 24px;
      background-color: #f5f7fb;

      .bk-collapse-header {
        height: 40px;
        line-height: 40px;
        background-color: #f0f1f5;
      }

      .bk-collapse-content {
        padding: 0 32px;
      }

      &:last-child {
        margin-bottom: 0;
      }
    }

    :deep(.bk-collapse-icon) {
      left: 17px;
      color: #979aa2;

      svg {
        font-size: 13px;
      }
    }
  }
}

.custom-main-dialog {

  :deep(.bk-dialog-title) {
    display: none;
  }

  :deep(.bk-modal-footer) {
    display: none;
  }

  .dialog-content {

    .publish-icon {
      margin-bottom: 18px;
      font-size: 42px;
      line-height: 32px;
      text-align: center;
    }

    .dialog-title {
      margin-bottom: 16px;
      font-size: 20px;
      color: #313238;
      text-align: center;
    }

    .dialog-main {
      padding: 12px 16px 18px;
      margin-bottom: 25px;
      background-color: #f5f6fa;
      border-radius: 2px;

      .publish-tips {
        margin-bottom: 10px;
        font-size: 14px;
        color: #63656e;

        span {
          font-weight: 700;
        }
      }

      .publish-stages {

        .stage-item {
          position: relative;
          width: 33%;
          padding-left: 12px;
          font-size: 14px;
          color: #63656e;

          &::after {
            position: absolute;
            top: 10px;
            left: 0;
            width: 4px;
            height: 4px;
            background-color: #63656e;
            border-radius: 50%;
            content: " ";
          }
        }
      }
    }

    .dialog-footer {
      text-align: center;
    }
  }
}
</style>
