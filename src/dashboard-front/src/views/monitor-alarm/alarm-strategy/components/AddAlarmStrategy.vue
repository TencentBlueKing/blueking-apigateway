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
          :label-width="108"
          :model="formData"
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
                    <div class="item label">
                      {{ t('资源标签包含') }}
                    </div>
                    <div class="item flex-none">
                      <BkSelect
                        v-model="formData.gateway_label_ids"
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
                      <div class="item w-95px">
                        <BkInput
                          v-model="formData.config.detect_config.count"
                          disabled
                          :placeholder="t('请输入')"
                          type="number"
                          :min="0"
                        />
                      </div>
                      <div class="item label min-w-67px">
                        {{ t('时触发') }}
                      </div>
                    </div>
                  </div>
                </BkFormItem>
                <BkFormItem
                  :label="t('告警收敛')"
                  class="m-b-24px"
                >
                  <div class="flex-group">
                    <div class="item label">
                      {{ t('告警产生后') }}，
                    </div>
                    <div class="item flex-none! w-117px custom-select-class">
                      <BkSelect
                        v-model="formData.config.converge_config.duration"
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
                    <div class="item label flex-1!">
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
                  </div>
                  <div
                    class="mb-16px stage-select-tips"
                    :class="['all'].includes(effectiveStageType) ? 'mt-4px' : 'mt-8px'"
                  >
                    {{
                      t(['all'].includes(effectiveStageType)
                        ? '选择后，当前所有环境及后续新增环境都将生效'
                        : '仅对已选择的环境生效'
                      )
                    }}
                  </div>
                </BkFormItem>
              </div>
            </div>
            <div class="content-panel">
              <div class="panel-title">
                {{ t('通知方式') }}
              </div>
              <div class="notice-way-form">
                <BkFormItem
                  :label="t('通知方式')"
                  :rules="rules.notice_way"
                  property="config.notice_config.notice_way"
                  class="mb-10px"
                  required
                >
                  <BkCheckboxGroup
                    ref="noticeWayRef"
                    v-model="formData.config.notice_config.notice_way"
                    class="checkbox-group"
                  >
                    <BkCheckbox :label="'wechat'">
                      <!-- <span class="icon apigateway-icon icon-ag-wechat-color" /> -->
                      {{ t('微信') }}
                    </BkCheckbox>
                    <BkCheckbox :label="'im'">
                      <!-- <span class="icon apigateway-icon icon-ag-qw" /> -->
                      {{ t('企业微信') }}
                    </BkCheckbox>
                    <BkCheckbox :label="'mail'">
                      <!-- <span class="icon apigateway-icon icon-ag-email-color" /> -->
                      {{ t('邮箱') }}
                    </BkCheckbox>
                  </BkCheckboxGroup>
                </BkFormItem>
                <BkFormItem
                  :label="t('通知对象')"
                  class="mb-14px"
                >
                  <BkCheckboxGroup
                    v-model="formData.config.notice_config.notice_role"
                    class="checkbox-group"
                  >
                    <BkCheckbox :label="'maintainer'">
                      {{ t('网关维护者') }}
                    </BkCheckbox>
                  </BkCheckboxGroup>
                </BkFormItem>
                <BkFormItem
                  :label="t('其他通知对象')"
                  class="m-b-0!"
                >
                  <BkTagInput
                    v-model="formData.config.notice_config.notice_extra_receiver"
                    :placeholder="t('请输入用户')"
                    allow-create
                    has-delete-icon
                    collapse-tags
                  />
                  <p class="notice-tip mt-4px">
                    <i class="m-r-4px apigateway-icon icon-ag-info" />
                    <span>{{ t('通知对象、其他通知对象至少一个有效') }}</span>
                  </p>
                </BkFormItem>
              </div>
            </div>
          </div>
        </BkForm>
      </div>
    </template>
    <template #footer>
      <div class="pl-152px pt-16px">
        <BkButton
          :loading="saveLoading"
          class="m-r-8px w-88px"
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
const effectiveStageType = defineModel('effectiveStage', {
  type: String,
  default: 'all',
});
const {
  sliderParams = {},
  detailData = {},
  initData = {},
  labelList = [],
  stageList = [],
} = defineProps<IProps>();
const emits = defineEmits<Emits>();

type ISliderParams = {
  isShow: boolean
  title: string
};

type IDetailData = { detailData: IAlarmStrategy };

interface IProps {
  sliderParams?: ISliderParams
  detailData?: IAlarmStrategy
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

interface Emits {
  (e: 'update:detailData', value: IDetailData)
  (e: 'update:sliderParams', value: ISliderParams)
  (e: 'done'): void
}

const { t } = useI18n();
const gatewayStore = useGateway();
const accessLogStore = useAccessLog();
const { alarmStrategyOptions } = accessLogStore;
const saveLoading = ref(false);
const nameRef = ref<InstanceType<typeof Input>>(null);
const alarmTypeRef = ref<InstanceType<typeof Select>>(null);
const effectiveRef = ref<InstanceType<typeof Select>>(null);
const noticeWayRef = ref<InstanceType<typeof Checkbox.Group>>(null);
const strategyFormRef = ref<InstanceType<typeof Form> & IFormMethod>();
const rules = reactive({
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
  notice_way: [
    {
      validator: () => {
        return formData.value.config?.notice_config?.notice_way.length > 0;
      },
      message: t('必填项'),
      trigger: 'change',
    },
  ],
});

const sliderConfig = computed({
  get: () => sliderParams,
  set: (form) => {
    emits('update:sliderParams', form);
  },
});
const formData = computed({
  get: () => detailData,
  set: (form) => {
    emits('update:detailData', form);
  },
});
const apigwId = computed(() => gatewayStore.apigwId);
const strategyId = computed(() => formData.value.id);
const labelOption = computed(() => labelList);
const stageOption = computed(() => stageList);

const handleScrollView = (el: HTMLInputElement | HTMLElement) => {
  el.scrollIntoView({
    behavior: 'smooth',
    block: 'center',
  });
};

const handleSave = async () => {
  try {
    await strategyFormRef?.value?.validate();
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
  }
  // 如果内容一致无需调用编辑接口
  if (Boolean(strategyId?.value) && isEqual(initData.form, formData.value)) {
    handleCancel();
    return;
  }
  saveLoading.value = true;
  try {
    if (strategyId?.value) {
      await updateStrategy(apigwId.value, strategyId.value, formData.value);
    }
    else {
      await createStrategy(apigwId.value, formData.value);
    }
    Message({
      message: t(strategyId?.value ? '编辑成功' : '新建成功'),
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

<style lang="scss" setup>
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

        .bk-form-item.is-required .bk-form-label:after {
           top: 3px;
        }

        .panel-title {
          font-size: 14px;
          font-weight: 500;
          color: #4d4f56;
          margin-bottom: 12px;
        }

        .stage-select-tips {
          font-size: 12px;
          color: #979ba5;
          line-height: 17px;
        }

        &.single {
          border: none;
          margin-bottom: 24px;

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
            line-height: 22px;
            margin-top: 5px;
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

    .item {
      flex: 1;

      &.label {
        flex: none;
        font-size: 14px;
        color: #4d4f56;
        padding-left: 7px;
        padding-right: 7px;
        padding-top: 4px;
        padding-bottom: 6px;
        border: 1px solid #c4c6cc;
        background-color: #fafbfd;
        border-radius: 2px 0 0 2px;
        line-height: 22px;
        text-align: center;
      }

      & + .item {
        margin-left: -1px;
      }

      &.custom-select-class {
        .bk-select.is-disabled .bk-input--text {
          font-size: 14px;
          background-color: #ffffff;
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
  color: #979ba5;
  font-size: 12px;
  line-height: 17px;
}
</style>
