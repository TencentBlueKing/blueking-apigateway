/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2026 Tencent. All rights reserved.
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
  <BkFormItem
    :label="t('环境')"
    property="stage_id"
    :rules="[
      {
        required: true,
        message: t('环境不能为空'),
        trigger: 'blur',
      },
    ]"
    required
  >
    <BkSelect
      v-model="formData.stage_id"
      :clearable="false"
      :disabled="isEditMode || noValidStage"
      @change="handleStageSelectChange"
    >
      <BkOption
        v-for="_stage in stageList"
        :id="_stage.id"
        :key="_stage.id"
        :disabled="!_stage.resource_version?.version"
        :name="_stage.name"
      />
    </BkSelect>
  </BkFormItem>
  <BkFormItem
    :label="t('服务名称')"
    property="name"
    :rules="[
      {
        required: true,
        message: t('服务名称不能为空'),
        trigger: 'change',
      },
      {
        validator: (value: string) => /^[a-z0-9]+(?:-[a-z0-9]+)*$/?.test(value),
        message: t('服务名称只能包含小写字母、数字和短横线'),
        trigger: 'change',
      }
    ]"
    class="custom-form-item-required"
  >
    <BkInput
      ref="nameRef"
      v-model="formData.name"
      :placeholder="t('请输入小写字母、数字、连字符(-)')"
      :disabled="isEditMode || noValidStage"
      :prefix="(isEditMode || noValidStage) ? undefined : serverNamePrefix"
    />
    <div class="text-12px lh-20px color-#979ba5 mt-6px">
      {{ t('唯一标识，以网关名称和环境名称为前缀，创建后不可更改') }}
    </div>
  </BkFormItem>
  <BkFormItem
    :label="t('服务展示名')"
    property="title"
    :rules="[
      {
        validator: (value: string) => value?.trim()?.length >= 3,
        message: t('服务展示名不能小于3个字符'),
        trigger: 'change',
      },
    ]"
    class="custom-form-item-required"
  >
    <BkInput
      ref="titleRef"
      v-model="formData.title"
      :placeholder="t('请输入3-32个字符的服务展示名称')"
      :maxlength="32"
      clearable
    />
  </BkFormItem>
  <BkFormItem
    :label="t('描述')"
    property="description"
    :rules="[
      {
        validator: (value: string) => value?.trim()?.length >= 10,
        message: t('描述不能小于10个字符'),
        trigger: 'change',
      },
    ]"
    class="custom-form-item-required"
  >
    <BkInput
      ref="descriptionRef"
      v-model="formData.description"
      type="textarea"
      :minlength="10"
      :maxlength="2048"
      :rows="4"
      :disabled="noValidStage"
      :placeholder="t('请输入10-2048个字符的描述')"
      clearable
      show-word-limit
      resize
    />
  </BkFormItem>
  <BkFormItem
    :label="t('标签')"
    property="labels"
  >
    <BkTagInput
      v-model="formData.labels"
      :disabled="noValidStage"
      allow-create
      collapse-tags
      has-delete-icon
    />
  </BkFormItem>
  <BkFormItem
    :label="t('分类')"
    property="categories"
    class="custom-form-item-required"
  >
    <BkTagInput
      ref="categoriesRef"
      v-model="formData.categories"
      trigger="focus"
      display-key="display_name"
      search-key="display_name"
      save-key="name"
      has-delete-icon
      :placeholder="t('通过 display_name 或 name 搜索分类')"
      :max-data="1"
      :disabled="noValidStage"
      :list="categoriesList"
      :tag-tpl="renderCategoryTagTpl"
      :tpl="renderCategoryTpl"
      :filter-callback="handleSearchCategory"
      @focus="handleCategoryFocus"
    />
    <div
      v-if="isCategoryEmpty"
      class="color-#ea3636 text-12px pt-4px lh-16px"
    >
      {{ t('分类不能为空') }}
    </div>
  </BkFormItem>
  <BkFormItem
    class="form-protocol-type"
    property="protocol_type"
    required
  >
    <template #label>
      <span class="connect-method">
        {{ t('连接方式') }}
      </span>
      <span class="color-#979ba5 text-12px ml-16px">
        <InfoLine class="v-mid" />
        {{ t('切换连接方式后，客户端需要基于新协议重新建立连接') }}
      </span>
    </template>
    <BkRadioGroup v-model="formData.protocol_type">
      <BkRadio
        v-for="item of MCP_PROTOCOL_TYPE"
        :key="item.value"
        :label="item.value"
      >
        {{ item.label }}
      </BkRadio>
      <div class="text-14px color-#979ba5 lh-32px ml-8px">
        ({{ t('不推荐，建议使用Streamable HTTP') }})
      </div>
    </BkRadioGroup>
    <div class="flex items-center bg-#f5f7fa h-32px text-12px pl-8px url">
      <div class="min-w-55px color-#4d4f56">
        {{ t('访问地址') }}:
      </div>
      <div
        v-bk-tooltips="{
          placement:'top',
          content: previewUrl,
          disabled: !isOverflow,
          extCls: 'max-w-1180px',
        }"
        class="truncate color-#313238"
        @mouseenter="(e: MouseEvent) => handleMouseenter(e)"
        @mouseleave="handleMouseleave"
      >
        {{ previewUrl }}
      </div>
      <div class="ml-8px pr-8px cursor-pointer hover:text-#3a84ff">
        <AgIcon
          name="copy-info"
          @click.stop="handleCopyClick"
        />
      </div>
    </div>
  </BkFormItem>
  <BkFormItem
    :label="t('是否公开')"
    property="is_public"
    required
    class="mb-0!"
  >
    <BkSwitcher
      v-model="formData.is_public"
      :disabled="noValidStage"
      theme="primary"
      class="mr-8px"
    />
    <span class="text-12px color-#979ba5">{{
      t('不公开则不会展示到 MCP 市场，且蓝鲸应用无法申请主动申请权限，只能由网关管理员给应用主动授权')
    }}</span>
  </BkFormItem>
</template>

<script lang="tsx" setup>
import { Input, TagInput } from 'bkui-vue';
import { InfoLine } from 'bkui-lib/icon';
import { escape } from 'lodash-es';
import type { IMCPFormData, IMCPServerCategory } from '@/services/source/mcp-server';
import type { IStageListItem } from '@/services/source/stage.ts';
import { MCP_PROTOCOL_TYPE } from '@/constants';
import { useEnv, useGateway } from '@/stores';
import { copy } from '@/utils';
import { t } from '@/locales';

interface IProps {
  categoriesList?: IMCPServerCategory[]
  stageList?: IStageListItem[]
  noValidStage?: boolean
  isEditMode?: boolean
}

interface IEmits { 'stage-change': [number] }

const formData = defineModel<IMCPFormData>('formData', {
  type: Object,
  required: true,
});

const {
  stageList = [],
  categoriesList = [],
  noValidStage = false,
  isEditMode = false,
} = defineProps<IProps>();

const emit = defineEmits<IEmits>();

const envStore = useEnv();
const gatewayStore = useGateway();

const nameRef = ref<InstanceType<typeof Input>>(null);
const titleRef = ref<InstanceType<typeof Input>>(null);
const descriptionRef = ref<InstanceType<typeof Input>>(null);
const categoriesRef = ref<InstanceType<typeof TagInput>>(null);
const isOverflow = ref(false);
const isCategoryFocus = ref(false);

const isCategoryEmpty = computed(() => !formData.value.categories.length && isCategoryFocus.value);
const stage = computed(() => stageList.find(st => st.id === formData.value.stage_id));
const stageName = computed(() => stage.value?.name || '');
const serverNamePrefix = computed(() => `${gatewayStore.currentGateway!.name}-${stageName.value}-`);
const previewUrl = computed(() => {
  const prefix = envStore.env.BK_API_RESOURCE_URL_TMPL
    .replace('{api_name}', 'bk-apigateway')
    .replace('{stage_name}', 'prod')
    .replace('{resource_path}', 'api/v2/mcp-servers');
  return `${prefix || ''}/${serverNamePrefix.value}${formData.value.name}/${!['sse'].includes(formData.value.protocol_type)
    ? 'mcp'
    : formData.value.protocol_type}/`;
});

const handleStageSelectChange = (value: number) => {
  formData.value.stage_id = value;
  emit('stage-change', value);
};

const renderCategoryTpl = (node, highlightKeyword, h) => {
  // 先转义原始内容，再执行高亮（确保高亮后的 HTML 仅包含安全标签）
  const escapedName = escape(node.name);
  const escapedDisplayName = escape(node.display_name);
  const highlightedName = highlightKeyword(escapedName);
  const innerHTML = `${highlightedName} (${escapedDisplayName})`;

  return h('div', { class: 'bk-selector-node' }, [
    h('span', {
      class: 'text',
      innerHTML,
    }),
  ]);
};

const renderCategoryTagTpl = (node, h) => {
  // 转义所有用户输入内容，避免恶意代码执行
  const escapedName = escape(node.name);
  const escapedDisplayName = escape(node.display_name);
  const innerHTML = `<span>${escapedName}</span> (${escapedDisplayName})`;

  return h('div', { class: 'tag' }, [
    h('span', {
      class: 'text',
      innerHTML,
    }),
  ]);
};

const handleSearchCategory = (tagValue: string, tagKey: string, list: IMCPServerCategory[]) =>
  list.filter((cg: IMCPServerCategory) => {
    if (!tagValue) return list;
    return cg.name?.toLowerCase().indexOf(tagValue) > -1 || cg[tagKey].indexOf(tagValue) > -1;
  });

const handleCategoryFocus = () => {
  isCategoryFocus.value = true;
};

const handleCategoriesBlur = () => {
  isCategoryFocus.value = false;
  setTimeout(() => {
    categoriesRef.value?.handleBlur();
  }, 200);
};

const handleCopyClick = () => {
  copy(previewUrl.value);
};

const validateForm = () => {
  const {
    name,
    title,
    description,
    categories,
  } = formData.value;

  // 自动focus到必填项
  if (!name) {
    nameRef.value?.focus();
    return nameRef.value;
  }
  if (title?.trim().length < 3) {
    titleRef.value?.focus();
    return titleRef.value;
  }
  if (description.length < 10) {
    descriptionRef.value?.focus();
    return descriptionRef.value;
  }

  isCategoryFocus.value = !categories?.length;

  if (isCategoryEmpty.value) {
    return categoriesRef.value;
  }

  return true;
};

const handleMouseenter = (e: MouseEvent) => {
  const target = e.target as HTMLElement;
  isOverflow.value = target.scrollWidth > target.clientWidth;
};

const handleMouseleave = () => {
  isOverflow.value = false;
};

defineExpose({
  validateForm,
  handleCategoriesBlur,
});
</script>

<style lang="scss" scoped>
.form-protocol-type {
  :deep(.bk-form-label) {

    &::after {
      display: none;
    }

    .connect-method {
      position: relative;

      &::after {
        position: absolute;
        top: 0;
        width: 14px;
        color: #ea3636;
        text-align: center;
        content: "*";
      }
    }
  }
}

.custom-form-item-required {
  position: relative;

  :deep(.bk-form-label) {

    &::after {
      position: absolute;
      top: 0;
      width: 14px;
      color: #ea3636;
      text-align: center;
      content: "*";
    }
  }
}
</style>
