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
  <AgSideSlider
    v-model="sliderConfig.isShow"
    ext-cls="alarm-strategy-slider"
    :width="640"
    :title="t(strategyId ? '编辑告警策略' : '新建告警策略')"
    :init-data="initData"
    @compare="handleCompare"
    @closed="handleCancel"
  >
    <template #default>
      <div class="strategy-form">
        <BkForm
          ref="strategyFormRef"
          :model="formData"
          form-type="vertical"
        >
          <div class="form-content">
            <div class="content-panel single">
              <BkFormItem
                class="mb-0!"
                :label="t('告警策略名称')"
                :property="'name'"
                :rules="rules.name"
                error-display-type="normal"
                label-position="left"
                required
              >
                <BkInput
                  ref="nameRef"
                  v-model="formData.name"
                  :placeholder="t('请输入')"
                  :maxlength="128"
                />
              </BkFormItem>
            </div>
            <div class="content-panel mb-0!">
              <dt class="panel-title">
                {{ t('触发条件') }}
              </dt>
              <div class="panel-content">
                <BkFormItem
                  class="mb-16px"
                  :label="t('告警规则')"
                  required
                  :rules="rules.alarm_subtype"
                  :property="'alarm_subtype'"
                  :error-display-type="'normal'"
                >
                  <BkSelect
                    ref="alarmTypeRef"
                    v-model="formData.alarm_subtype"
                    :clearable="false"
                  >
                    <BkOption
                      v-for="option in alarmStrategyOptions.alarmSubType"
                      :key="option.value"
                      :value="option.value"
                      :label="option.name"
                    />
                  </BkSelect>
                </BkFormItem>
                <BkFormItem
                  :label="t('告警范围')"
                  class="m-b-20px"
                >
                  <div class="flex-group">
                    <div class="item flex-none">
                      <BkSelect
                        v-model="formData.gateway_label_ids"
                        :prefix="t('资源标签包含')"
                        filterable
                        multiple
                        :input-search="false"
                      >
                        <BkOption
                          v-for="option in labelOption"
                          :key="option.id"
                          :value="option.id"
                          :label="option.name"
                        />
                      </BkSelect>
                    </div>
                  </div>
                </BkFormItem>
                <BkFormItem
                  :label="t('检测算法')"
                  class="mb-16px"
                >
                  <div class="flex-groups">
                    <div class="flex-group flex-2">
                      <div class="item w-87px custom-select-class">
                        <BkSelect
                          v-model="formData.config.detect_config.duration"
                          disabled
                          :clearable="false"
                        >
                          <BkOption
                            v-for="option in alarmStrategyOptions?.detectConfig?.duration"
                            :key="option.value"
                            :value="option.value"
                            :label="option.name"
                          />
                        </BkSelect>
                      </div>
                      <div class="item label min-w-131px">
                        {{ t('内命中规则次数') }}
                      </div>
                      <div class="item flex-none w-67px custom-select-class">
                        <BkSelect
                          v-model="formData.config.detect_config.method"
                          disabled
                          :clearable="false"
                        >
                          <BkOption
                            v-for="option in alarmStrategyOptions.detectConfig.method"
                            :key="option.value"
                            :value="option.value"
                            :label="option.name"
                          />
                        </BkSelect>
                      </div>
                    </div>
                    <div class="flex-group">
                      <div class="item w-120px">
                        <BkInput
                          v-model="formData.config.detect_config.count"
                          disabled
                          :placeholder="t('请输入')"
                          type="number"
                          :min="0"
                          :suffix="t('时触发')"
                        />
                      </div>
                    </div>
                  </div>
                </BkFormItem>
                <BkFormItem
                  :label="t('告警收敛')"
                  class="m-b-24px"
                >
                  <div class="flex-group">
                    <div class="item flex-1! custom-select-class">
                      <BkSelect
                        v-model="formData.config.converge_config.duration"
                        :prefix="t('告警产生后')"
                        :suffix="t('内不再发送告警')"
                        disabled
                        :clearable="false"
                      >
                        <BkOption
                          v-for="option in alarmStrategyOptions.convergeConfig.duration"
                          :key="option.value"
                          :value="option.value"
                          :label="option.name"
                        />
                      </BkSelect>
                    </div>
                    <div class="item label">
                      {{ t('内不再发送告警') }}
                    </div>
                  </div>
                </BkFormItem>
                <BkFormItem
                  :label="t('生效环境')"
                  :rules="rules.effective_stages"
                  class="mb-0 effective-stages"
                  property="effective_stages"
                >
                  <BkRadioGroup
                    v-model="effectiveStageType"
                    class="effective-stages-radio"
                    @change="handleEffectiveStageTypeChange"
                  >
                    <BkRadio label="all">
                      {{ t('所有环境') }}
                    </BkRadio>
                    <BkRadio label="custom">
                      {{ t('自定义环境') }}
                    </BkRadio>
                  </BkRadioGroup>
                  <div
                    v-if="['custom'].includes(effectiveStageType)"
                    class="mt-14px"
                  >
                    <BkSelect
                      ref="effectiveRef"
                      v-model="formData.effective_stages"
                      :placeholder="t('请选择环境')"
                      filterable
                      multiple
                    >
                      <BkOption
                        v-for="stage in stageOption"
                        :key="stage.id"
                        :label="stage.name"
                        :value="stage.name"
                      />
                    </BkSelect>
                    <div
                      class="stage-select-tips"
                      :class="['all'].includes(effectiveStageType) ? 'mt-4px' : 'mt-8px'"
                    >
                      {{
                        t(['all'].includes(effectiveStageType)
                          ? '选择后，当前所有环境及后续新增环境都将生效'
                          : '仅对已选择的环境生效'
                        )
                      }}
                    </div>
                  </div>
                </BkFormItem>
              </div>
            </div>

            <div class="content-panel keyword-filter">
              <div class="keyword-filter-header">
                <div class="header-left">
                  <div class="filter-icon">
                    <AgIcon
                      size="24"
                      color="#3a84ff"
                      name="filter"
                    />
                  </div>
                  <div class="header-text">
                    <div class="header-title">
                      {{ t('关键字过滤') }}
                    </div>
                    <div class="header-desc">
                      {{ t('根据关键字匹配告警内容，决定是否推送') }}
                    </div>
                  </div>
                </div>
                <BkSwitcher
                  v-model="filterEnabled"
                  theme="primary"
                />
              </div>
              <div
                v-show="filterEnabled"
                class="keyword-filter-content"
              >
                <BkForm
                  ref="filter-config-form"
                  :model="filterConfig"
                  :rules="filterConfigRules"
                  form-type="vertical"
                >
                  <BkFormItem
                    :label="t('过滤模式')"
                    class="mb-16px"
                  >
                    <div class="filter-mode-wrapper">
                      <BkRadioGroup v-model="filterConfig.type">
                        <BkRadio label="black_list">
                          {{ t('黑名单') }}
                        </BkRadio>
                        <BkRadio label="white_list">
                          {{ t('白名单') }}
                        </BkRadio>
                      </BkRadioGroup>
                      <span class="filter-mode-tip">
                        {{ filterModeTip }}
                      </span>
                    </div>
                  </BkFormItem>
                  <BkFormItem
                    :label="t('匹配方式')"
                    class="mb-16px"
                  >
                    <BkRadioGroup v-model="filterConfig.match">
                      <BkRadio label="contains">
                        {{ t('包含匹配') }}
                      </BkRadio>
                      <BkRadio label="regex_match">
                        {{ t('正则匹配') }}
                      </BkRadio>
                    </BkRadioGroup>
                  </BkFormItem>
                  <BkFormItem
                    :label="t('添加关键字')"
                    class="mb-16px"
                    property="items"
                    required
                  >
                    <BkTagInput
                      v-model="filterConfig.items"
                      allow-create
                      :copyable="false"
                      has-delete-icon
                    />
                  </BkFormItem>
                  <div class="keyword-filter-summary">
                    {{ filterSummary }}
                  </div>
                </BkForm>
              </div>
            </div>

            <div class="content-panel">
              <div class="panel-title">
                {{ t('通知方式') }}
              </div>
              <div class="notice-way-form">
                <BkForm
                  ref="notice-config-form"
                  :model="noticeConfig"
                  :rules="noticeConfigRules"
                  form-type="vertical"
                >
                  <BkFormItem
                    :label="t('通知方式')"
                    property="notice_way"
                    class="mb-16px"
                    required
                  >
                    <BkCheckboxGroup
                      ref="noticeWayRef"
                      v-model="noticeConfig.notice_way"
                    >
                      <BkCheckbox label="wechat">
                        {{ t('微信') }}
                      </BkCheckbox>
                      <BkCheckbox label="im">
                        {{ t('企业微信') }}
                      </BkCheckbox>
                      <BkCheckbox label="mail">
                        {{ t('邮箱') }}
                      </BkCheckbox>
                    </BkCheckboxGroup>
                  </BkFormItem>
                  <BkFormItem
                    required
                    :label="t('通知对象')"
                    class="mb-14px"
                    property="notice_role"
                  >
                    <BkCheckboxGroup v-model="noticeConfig.notice_role">
                      <BkCheckbox label="maintainer">
                        {{ t('网关维护者') }}
                      </BkCheckbox>
                      <BkCheckbox label="custom">
                        {{ t('自定义') }}
                      </BkCheckbox>
                    </BkCheckboxGroup>
                  </BkFormItem>
                  <BkFormItem
                    v-if="noticeConfig.notice_role.includes('custom')"
                    label=""
                    property="notice_extra_receiver"
                  >
                    <BkTagInput
                      v-model="noticeConfig.notice_extra_receiver"
                      :placeholder="t('请输入用户')"
                      allow-create
                      has-delete-icon
                      collapse-tags
                    />
                  </BkFormItem>
                </BkForm>
              </div>
            </div>
          </div>
        </BkForm>
      </div>
    </template>
    <template #footer>
      <div class="pl-40px pt-16px">
        <BkButton
          :loading="saveLoading"
          class="mr-8px w-88px"
          theme="primary"
          @click="handleSave"
        >
          {{ t('提交') }}
        </BkButton>
        <BkButton
          class="w-88px"
          @click="handleCancel"
        >
          {{ t('取消') }}
        </BkButton>
      </div>
    </template>
  </AgSideSlider>
</template>

<script lang="ts" setup>
import { cloneDeep, isEqual } from 'lodash-es';
import { Checkbox, Form, Input, Message, Select } from 'bkui-vue';
import { useAccessLog, useGateway } from '@/stores';
import type { IFormMethod } from '@/types/common';
import type { IStageListItem } from '@/services/source/stage';
import {
  type IAlarmStrategy,
  createStrategy,
  updateStrategy,
} from '@/services/source/monitor';
import AgSideSlider from '@/components/ag-sideslider/Index.vue';

type ISliderParams = {
  isShow: boolean
  title: string
};

interface IProps {
  sliderParams?: ISliderParams
  strategy?: IAlarmStrategy
  initData?: {
    form?: IAlarmStrategy
    effectiveStage?: string
  }
  labelList?: {
    name: string
    id: number
  }[]
  stageList?: IStageListItem[]
}

interface IEmits {
  'update:sliderParams': [value: ISliderParams]
  'done': [void]
}

const effectiveStageType = defineModel('effectiveStage', {
  type: String,
  default: 'all',
});

const {
  sliderParams = {},
  strategy = {},
  initData = {},
  labelList = [],
  stageList = [],
} = defineProps<IProps>();

const emits = defineEmits<IEmits>();

const { t } = useI18n();
const gatewayStore = useGateway();
const accessLogStore = useAccessLog();
const { alarmStrategyOptions } = accessLogStore;

const formData = ref<any>({
  name: '',
  alarm_type: 'resource_backend',
  alarm_subtype: '',
  gateway_label_ids: [],
  config: {
    detect_config: {
      duration: 300,
      method: 'gte',
      count: 3,
    },
    filter_config: null,
    converge_config: { duration: 86400 },
    notice_config: {
      notice_way: ['im'],
      notice_role: ['maintainer'],
      notice_extra_receiver: [],
    },
  },
  effective_stages: [],
});
const saveLoading = ref(false);

const nameRef = ref<InstanceType<typeof Input>>();
const alarmTypeRef = ref<InstanceType<typeof Select>>();
const effectiveRef = ref<InstanceType<typeof Select>>();
const noticeWayRef = ref<InstanceType<typeof Checkbox.Group>>();
const strategyFormRef = ref<InstanceType<typeof Form> & IFormMethod>();
const filterConfigFormRef = useTemplateRef<InstanceType<typeof Form> & IFormMethod>('filter-config-form');
const noticeConfigFormRef = useTemplateRef<InstanceType<typeof Form> & IFormMethod>('notice-config-form');

// 关键字过滤相关
const filterEnabled = ref(false);

const filterConfig = ref({
  type: 'black_list',
  match: 'contains',
  items: [] as string[],
});

// 通知方式相关
const noticeConfig = ref<{
  notice_way: string[]
  notice_role: string[]
  notice_extra_receiver: string[]
}>({
  notice_way: [],
  notice_role: [],
  notice_extra_receiver: [],
});

const sliderConfig = computed({
  get: () => sliderParams,
  set: (form) => {
    emits('update:sliderParams', form);
  },
});
const apigwId = computed(() => gatewayStore.apigwId);
const strategyId = computed(() => formData.value?.id);
const labelOption = computed(() => labelList);
const stageOption = computed(() => stageList);

const filterModeTip = computed(() => {
  return filterConfig.value.type === 'black_list'
    ? t('命中关键字的告警不会推送')
    : t('仅命中关键字的告警才会推送');
});

const filterSummary = computed(() => {
  const count = filterConfig.value.items.length;
  const mode = filterConfig.value.type === 'black_list' ? t('黑名单') : t('白名单');
  return t('已配置关键字：{mode}{count}个', {
    mode,
    count,
  });
});

const rules = {
  name: [
    {
      required: true,
      message: t('必填项'),
      trigger: 'blur',
    },
  ],
  alarm_subtype: [
    {
      required: true,
      message: t('必填项'),
      trigger: 'blur',
    },
  ],
  effective_stages: [
    {
      validator: (value: string[]) => {
        return ['all'].includes(effectiveStageType.value) || value.length > 0;
      },
      message: t('自定义环境不能为空'),
      trigger: 'change',
    },
  ],
};

const filterConfigRules = {
  items: [
    {
      validator: () => !!filterConfig.value.items.length,
      message: t('必填项'),
      trigger: 'change',
    },
  ],
};

const noticeConfigRules = {
  notice_way: [
    {
      validator: () => !!noticeConfig.value.notice_way.length,
      message: t('必填项'),
      trigger: 'change',
    },
  ],
  notice_role: [
    {
      validator: () => !!noticeConfig.value.notice_role.length,
      message: t('通知对象和自定义通知对象至少勾选一个'),
      trigger: 'change',
    },
  ],
  notice_extra_receiver: [
    {
      validator: () => {
        if (noticeConfig.value.notice_role.includes('custom')) {
          return noticeConfig.value.notice_extra_receiver.length > 0;
        }
        return true;
      },
      message: t('请填写自定义通知对象'),
      trigger: 'change',
    },
  ],
};

watch(() => strategy, () => {
  if (strategy) {
    formData.value = cloneDeep(strategy);

    if (strategy.config?.filter_config) {
      filterEnabled.value = true;
      filterConfig.value = cloneDeep(strategy.config.filter_config);
    }
    else {
      filterEnabled.value = false;
      filterConfig.value = {
        type: 'black_list',
        match: 'contains',
        items: [] as string[],
      };
    }

    if (strategy.config?.notice_config) {
      noticeConfig.value = cloneDeep(strategy.config.notice_config);

      if (strategy.config.notice_config.notice_extra_receiver?.length) {
        noticeConfig.value.notice_role.push('custom');
      }
    }
  }
}, { deep: true });

const handleScrollView = (el: HTMLInputElement | HTMLElement) => {
  el.scrollIntoView({
    behavior: 'smooth',
    block: 'center',
  });
};

const handleSave = async () => {
  try {
    await Promise.all([
      strategyFormRef.value?.validate(),
      filterConfigFormRef.value?.validate(),
      noticeConfigFormRef.value?.validate(),
    ]);
  }
  catch {
    const {
      name,
      alarm_subtype,
      effective_stages,
      config,
    } = formData.value;
    if (!name) {
      nameRef.value?.focus();
      handleScrollView(nameRef?.value?.$el);
      return;
    }
    if (!alarm_subtype) {
      handleScrollView(alarmTypeRef?.value?.$el);
      return;
    }
    if (['custom'].includes(effectiveStageType.value) && !effective_stages?.length) {
      handleScrollView(effectiveRef?.value?.$el);
      return;
    }
    if (!config?.notice_config?.notice_way.length) {
      handleScrollView(noticeWayRef?.value?.$el);
      return;
    }
    return;
  }

  const params = cloneDeep(formData.value);

  if (filterEnabled.value) {
    params.config.filter_config = filterConfig.value;
  }
  else {
    params.config.filter_config = null;
  }

  params.config.notice_config = cloneDeep(noticeConfig.value);
  if (params.config.notice_config?.notice_role.includes('custom')) {
    params.config.notice_config.notice_role = params.config.notice_config.notice_role.filter(item => item !== 'custom');
  }
  else {
    params.config.notice_config.notice_extra_receiver = [];
  }

  // 如果内容一致无需调用编辑接口
  if (Boolean(strategyId.value) && isEqual(initData.form, params)) {
    handleCancel();
    return;
  }

  saveLoading.value = true;

  try {
    if (strategyId.value) {
      await updateStrategy(apigwId.value, strategyId.value, params);
    }
    else {
      await createStrategy(apigwId.value, params);
    }
    Message({
      message: t(strategyId.value ? '编辑成功' : '新建成功'),
      theme: 'success',
    });
    sliderConfig.value.isShow = false;
    emits('done');
  }
  finally {
    saveLoading.value = false;
  }
};

const handleEffectiveStageTypeChange = (type: string) => {
  if (['all'].includes(type)) {
    formData.value.effective_stages = [];
  }
};

const handleCompare = (callback) => {
  const params = {
    form: formData.value,
    effectiveStage: effectiveStageType.value,
  };
  callback(cloneDeep(params));
};

const handleCancel = () => {
  strategyFormRef?.value?.clearValidate();
  effectiveStageType.value = 'all';
  sliderConfig.value = Object.assign(sliderConfig.value, { isShow: false });
};
</script>

<style lang="scss" scoped>

.alarm-strategy-slider {

  .strategy-form {
    padding: 24px 24px 0 40px;

    .form-content {

      .content-panel {
        margin-bottom: 16px;

        .bk-form-label {
          color: #4d4f56;
        }

        .bk-form-content {
           line-height: 22px;
        }

        .bk-form-item.is-required .bk-form-label::after {
           top: 3px;
        }

        .panel-title {
          margin-bottom: 20px;
          font-size: 14px;
          font-weight: 700;
          color: #000;
        }

        .stage-select-tips {
          font-size: 12px;
          line-height: 17px;
          color: #979ba5;
        }

        &.single {
          margin-bottom: 24px;
          border: none;

          .bk-form-item {

            .bk-form-label {
              font-size: 14px;
              font-weight: 500;
            }

            .bk-input {
              border-bottom-left-radius: unset;
              border-top-left-radius: unset;
            }

            .tooltips-icon {
              top: 11px;
            }
          }
        }

        .effective-stages {

          .bk-form-label {

            &::after {
              position: absolute;
              top: 3px;
              width: 14px;
              color: #ea3636;
              text-align: center;
              content: "*";
            }
          }

          .effective-stages-radio {
            margin-top: 5px;
            line-height: 22px;
          }
        }

        .notice-way-form {

          .bk-form-label {
            line-height: 22px;
          }

          .bk-form-content {
            line-height: 22px;
          }
        }

        &.last-child {
          margin-bottom: 0;
        }
      }
    }
  }

  .flex-group {
    display: flex;
    height: 32px;
    color: #4d4f56;
    align-items: flex-end;

    .item {
      flex: 1;

      &.label {
        height: 32px;
        padding: 4px 7px 6px;
        font-size: 14px;
        line-height: 22px;
        color: #4d4f56;
        text-align: center;
        background-color: #fafbfd;
        border: 1px solid #c4c6cc;
        border-radius: 2px 0 0 2px;
        flex: none;
      }

      & + .item {
        margin-left: -1px;
      }

      &.custom-select-class {

        .bk-select.is-disabled .bk-input--text {
          font-size: 14px;
          background-color: #fff;
        }
      }
    }

    &.flex-2 {
      flex: 2;
    }
  }

  .flex-groups {
    display: flex;
    height: 32px;

    .flex-group {

      & + .flex-group {
        margin-left: 8px;
      }
    }
  }
}

.notice-tip {
  font-size: 12px;
  line-height: 17px;
  color: #979ba5;
}

.keyword-filter {
  margin-top: 32px;
  border: 1px solid #DCDEE5;
  border-radius: 2px;

  .keyword-filter-header {
    display: flex;
    padding: 16px;
    background-color: #fff;
    align-items: center;
    justify-content: space-between;

    .header-left {
      display: flex;
      align-items: center;

      .filter-icon {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 36px;
        height: 36px;
        margin-right: 12px;
        background-color: #e1ecff;
        border-radius: 2px;
      }

      .header-text {

        .header-title {
          font-size: 14px;
          font-weight: 500;
          line-height: 22px;
          color: #313238;
        }

        .header-desc {
          font-size: 12px;
          line-height: 20px;
          color: #979ba5;
        }
      }
    }
  }

  .keyword-filter-content {
    padding: 16px 12px 12px;
    background: #FAFBFD;
    border-top: 1px solid #DCDEE5;

    .filter-mode-wrapper {
      display: flex;
      align-items: center;

      .filter-mode-tip {
        margin-left: 8px;
        font-size: 12px;
        color: #979ba5;
      }
    }

    .keyword-filter-summary {
      font-size: 12px;
      line-height: 20px;
      color: #979BA5;
    }
  }
}
</style>
