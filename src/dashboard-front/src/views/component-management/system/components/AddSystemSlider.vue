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
    quick-close
    :width="640"
    :init-data="initData"
    @compare="handleCompare"
    @closed="handleCancel"
  >
    <template #header>
      <div class="title">
        {{ sliderConfig.title }}
      </div>
    </template>
    <template #default>
      <BkLoading :loading="sliderConfig.isLoading">
        <BkForm
          v-show="!sliderConfig.isLoading"
          ref="systemFormRef"
          class="p-20px p-b-0"
          :label-width="160"
          :rules="rules"
          :model="formData"
        >
          <BkFormItem
            :label="t('名称')"
            required
            property="name"
            :error-display-type="'normal'"
          >
            <BkInput
              v-model="formData.name"
              :placeholder="t('由英文字母、下划线(_)或数字组成，并且以字母开头，长度小于64个字符')"
              :disabled="isDisabled"
            />
            <p class="tips">
              <i class="apigateway-icon icon-ag-info" />
              {{ t('系统唯一标识') }}
            </p>
          </BkFormItem>
          <BkFormItem
            :label="t('描述')"
            required
            property="description"
            :error-display-type="'normal'"
          >
            <BkInput
              v-model="formData.description"
              :disabled="isDisabled"
              :maxlength="128"
              :placeholder="t('不超过128个字符')"
            />
          </BkFormItem>
          <BkFormItem
            :label="t('文档分类')"
            required
            property="doc_category_id"
            :error-display-type="'normal'"
          >
            <template v-if="isDisabled">
              <BkInput
                v-model="formData.doc_category_name"
                disabled
              />
            </template>
            <BkSelect
              v-else
              v-model="formData.doc_category_id"
              searchable
              :clearable="false"
            >
              <BkOption
                v-for="option in categoryOption"
                :id="option.id"
                :key="option.id"
                :name="option.name"
              />
              <template #extension>
                <div
                  class="create-doc-category"
                  style="cursor: pointer"
                  @click="handleCreateCategory"
                >
                  <i class="paasng-icon paasng-plus-circle" />
                  <span style="margin-left: 4px">{{ t('新建文档分类') }}</span>
                </div>
              </template>
            </BkSelect>
          </BkFormItem>
          <BkFormItem :label="t('系统负责人')">
            <MemberSelector
              v-model="formData.maintainers"
              :placeholder="t('请选择系统负责人')"
              has-delete-icon
            />
          </BkFormItem>
          <BkFormItem :label="t('超时时长')">
            <BkInput
              v-model="formData.timeout"
              type="number"
              :max="600"
              :min="1"
              :precision="0"
            >
              <template #suffix>
                <section class="timeout-append">
                  <div>{{ t('秒') }}</div>
                </section>
              </template>
            </BkInput>
            <p class="tips">
              <i class="apigateway-icon icon-ag-info" />
              {{ t('未设置时，使用默认值30秒，最大600秒') }}
            </p>
          </BkFormItem>
          <BkFormItem :label="t('备注')">
            <BkInput
              v-model="formData.comment"
              type="textarea"
              :disabled="isDisabled"
              :placeholder="t('请输入备注')"
            />
          </BkFormItem>
        </BkForm>
      </BkLoading>
    </template>
    <template #footer>
      <div class="p-l-90px">
        <BkButton
          theme="primary"
          class="w-88px"
          :loading="saveLoading"
          @click="handleSave"
        >
          {{ t('保存') }}
        </BkButton>
        <BkButton
          class="w-88px m-l-8px"
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
import { Form, Message } from 'bkui-vue';
import type { IFormMethod } from '@/types/common';
import { type ICategoryItem } from '@/services/source/category';
import {
  type ISystemItem,
  addSystem,
  updateSystem,
} from '@/services/source/system';
import AgSideSlider from '@/components/ag-sideslider/Index.vue';
import MemberSelector from '@/components/member-selector';

type ISliderParams = {
  isShow: boolean
  isLoading: boolean
  title: string
};

type IDetailData = { detailData: ISystemItem };

interface IProps {
  sliderParams?: ISliderParams
  detailData?: ISystemItem
  initData?: ISystemItem
  categoryList?: ICategoryItem[]
}

interface Emits {
  (e: 'update:detailData', value: IDetailData)
  (e: 'update:sliderParams', value: ISliderParams)
  (e: 'createCategory'): void
  (e: 'done'): void
}

const {
  sliderParams = {},
  detailData = {},
  initData = {},
  categoryList = [],
} = defineProps<IProps>();
const emits = defineEmits<Emits>();

const { t } = useI18n();

const saveLoading = ref(false);
const systemFormRef = ref<InstanceType<typeof Form> & IFormMethod>();
const rules = ref({
  name: [
    {
      required: true,
      message: t('必填项'),
      trigger: 'blur',
    },
  ],
  description: [
    {
      required: true,
      message: t('必填项'),
      trigger: 'blur',
    },
  ],
  doc_category_id: [
    {
      required: true,
      message: t('必填项'),
      trigger: 'blur',
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
const categoryOption = computed(() => categoryList);
const systemId = computed(() => formData.value.id);
const isDisabled = computed(() => formData.value.is_official);

const handleSave = async () => {
  await systemFormRef?.value?.validate();
  // 如果内容一致无需调用编辑接口
  if (systemId?.value && isEqual(initData, formData.value)) {
    handleCancel();
    return;
  }
  saveLoading.value = true;
  const tempData = { ...formData.value };
  if (!tempData.timeout) {
    tempData.timeout = null;
  }
  try {
    if (systemId.value) {
      delete tempData.id;
      await updateSystem(systemId.value, tempData);
    }
    else {
      await addSystem(tempData);
    }
    sliderConfig.value.isShow = false;
    Message({
      theme: 'success',
      message: t('操作成功'),
    });
    emits('done');
  }
  catch (e) {
    Message({
      theme: 'error',
      message: e?.message || t('系统错误，请稍后重试'),
    });
  }
  finally {
    saveLoading.value = false;
  }
};

const handleCompare = (callback) => {
  callback(cloneDeep(formData.value));
};

const handleCreateCategory = () => {
  emits('createCategory');
};

const handleCancel = () => {
  systemFormRef?.value?.clearValidate();
  sliderConfig.value = Object.assign(sliderConfig.value, { isShow: false });
};
</script>

<style lang="scss" setup>
.timeout-append {
  width: 32px;
  color: #63656e;
  text-align: center;
  background: #fafbfd;
  border-left: 1px solid #c4c6cc;
}

.tips {
  line-height: 24px;
  font-size: 12px;
  color: #63656e;

  i {
    position: relative;
    top: -1px;
    margin-right: 3px;
  }
}

.create-doc-category {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  cursor: pointer;
}
</style>
