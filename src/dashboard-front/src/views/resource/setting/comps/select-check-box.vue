<template>
  <bk-select
    :style="{ maxWidth: `${width}px` }"
    class="select-wrapper mt5"
    filterable
    multiple
    multiple-mode="tag"
    ref="selectRef"
    :show-on-init="!isAdd"
    v-model="curLabelIds"
    selected-style="checkbox"
    @toggle="handleToggle">
    <bk-option v-for="(option, index) in labelsData" :key="option.name" :id="option.id" :name="option.name">
      <template #default>
        <div
          v-bk-tooltips="{
            content: $t('标签最多只能选择10个'),
            disabled: !(!curLabelIds.includes(option.id) && curLabelIds.length >= 10) }"
          :disabled="!curLabelIds.includes(option.id) && curLabelIds.length >= 10"
          class="flex-row align-items-center justify-content-between item-container" style="width: 100%;"
          v-if="!option.isEdited"
          @mouseenter="handleMouseEnter(index)"
          @mouseleave="handleMouseLeave">
          {{ option.name }}
          <div class="icon-container" v-if="hoverIndex === index">
            <i
              class="icon apigateway-icon icon-ag-edit-line"
              @click.stop="handleEditOptionItem(option)"></i>
            <bk-pop-confirm
              title="确认删除该标签？"
              width="288"
              trigger="click"
              @confirm="handleDeleteOptionItemConfirm(option)"
            >
              <i
                class="icon apigateway-icon icon-ag-delet"
                @click.stop="handleDeleteOptionItem"></i>
            </bk-pop-confirm>
          </div>
        </div>
        <div v-else @click.stop="handleInputFocus">
          <bk-input
            style="width: 180px"
            ref="editInputRef"
            v-model="option.name"
            size="small"
            @enter="updateOption(option.name, option.id)"
            @input="handleInputFocus"
            :placeholder="t('请输入标签， enter保存')"
          />
        </div>
      </template>
    </bk-option>
    <template #extension>
      <div class="custom-extension" style="margin: 0 auto; width: 100%;">
        <div
          v-if="showEdit"
          class="flex-row align-items-center justify-content-center"
        >
          <bk-input
            style="width: 95%"
            ref="inputRef"
            v-model="optionName"
            size="small"
            @enter="addOption"
            :placeholder="t('请输入标签，enter保存')"
          />
        </div>
        <div v-else class="flex-row align-items-center justify-content-center" style="cursor: pointer; color: #63656e;">
          <div
            class="flex-row align-items-center justify-content-center"
            @click="handleShowEdit"
          >
            <plus style="font-size: 18px;" />
            {{ t('新建标签') }}
          </div>
        </div>
      </div>
    </template>
  </bk-select>
</template>
<script setup lang="ts">
import { ref, computed, toRefs, PropType, nextTick, watch } from 'vue';
import { Plus } from 'bkui-vue/lib/icon';
import { Message } from 'bkui-vue';
import { useI18n } from 'vue-i18n';

import { updateResourcesLabels, createResourcesLabels, deleteResourcesLabels, updateResourcesLabelItem } from '@/http';

import { useCommon } from '@/store';

const emit = defineEmits(['close', 'update-success', 'label-add-success', 'update:modelValue']);
const common = useCommon();
const { t } = useI18n();
const { apigwId } = common; // 网关id

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  curSelectLabelIds: { type: Array, default: [] },   // 当前选中的label
  resourceId: { type: Number, default: 0 },
  labelsData: { type: Array as PropType<any>, default: [] },
  width: { type: Number, default: 235 },
  isAdd: { type: Boolean, default: false },
});

const { curSelectLabelIds, resourceId, labelsData, width, isAdd, modelValue } = toRefs(props);

const curLabelIds = ref(curSelectLabelIds.value);
const showEdit = ref(false);
const optionName = ref('');
const inputRef = ref(null);
const selectRef = ref(null);
const editInputRef = ref(null);
const hoverIndex = ref<number>(null);
const isIconClick = ref<boolean>(false);  // 是否点击了icon

const curLabelIdsbackUp = ref(curLabelIds.value);

// 相同的标签
const isSameLabels = computed(() => {
  const curLabelIdsString = JSON.stringify(curLabelIds.value.sort());
  const curLabelIdsbackUpString = JSON.stringify(curLabelIdsbackUp.value.sort());
  return curLabelIdsString === curLabelIdsbackUpString;
});

// 赋值给select curLabelIds
watch(modelValue, () => {
  if (modelValue.value.length) {
    curLabelIds.value = modelValue.value;
  }
});

watch(curLabelIds, () => {
  emit('update:modelValue', curLabelIds.value || []);
});


//
const handleToggle = async (v: boolean) => {
  // 新增标签标识
  if (isAdd.value) return;
  setTimeout(async () => {
    // 关闭下拉框且
    if (!v) {
      // 变更了的标签数据请求接口
      if (!isSameLabels.value) {
        try {
          await updateResourcesLabels(apigwId, resourceId.value, { label_ids: curLabelIds.value });
          Message({
            message: t('修改标签成功'),
            theme: 'success',
            width: 'auto',
          });
          emit('update-success');
        } catch (error) {}
      } else {
        labelsData.value.forEach((item: any) => {
          item.isEdited = false;
        });
        emit('close');
      }
    }
  }, 500);
};

// 新增标签
const addOption = async () => {
  if (optionName.value.trim()) {
    await createResourcesLabels(apigwId, { name: optionName.value });
    Message({
      message: t('标签新建成功'),
      theme: 'success',
      width: 'auto',
    });
    optionName.value = '';
  }
  showEdit.value = false;
  emit('label-add-success');
};

// 更新标签
const updateOption = async (name: string, id: number) => {
  if (name.trim()) {
    await updateResourcesLabelItem(apigwId, id, { name });
    Message({
      message: t('标签修改成功'),
      theme: 'success',
      width: 'auto',
    });
    labelsData.value.forEach((item: any) => {
      item.isEdited = false;
    });
    emit('update-success');
  }
};

// 展示新建标签input
const handleShowEdit = () => {
  showEdit.value = true;
  setTimeout(() => {
    inputRef.value.focus();
  });
};

const handleEditOptionItem = (e: any) => {
  labelsData.value.forEach((item: any) => {
    item.isEdited = false;
  });
  e.isEdited = true;
  setTimeout(() => {
    editInputRef.value[0].focus();
  }, 500);
};

// 点击了删除icon
const handleDeleteOptionItem = () => {
  isIconClick.value = true;
};

// 删除某个标签
const handleDeleteOptionItemConfirm = async (e: any) => {
  try {
    await deleteResourcesLabels(apigwId, e.id);
    Message({
      message: t('删除标签成功'),
      theme: 'success',
      width: 'auto',
    });
    selectRef.value.showPopover();
    emit('update-success');
  } catch (error) {}
};

// 输入框聚焦
const handleInputFocus = () => {
  nextTick(() => {
    editInputRef.value[0].focus();
  });
};
// 鼠标移入事件
const handleMouseEnter = (i: number) => {
  hoverIndex.value = i;
};
// 处理鼠标移出
const handleMouseLeave = () => {
  // 如果点击了icon 则不隐藏icon
  if (isIconClick.value) return;
  hoverIndex.value = null;
};
</script>
<style scoped lang="scss">
  .select-wrapper {
    .item-container {
      width: 100%;
      position: relative;
      .icon-container{
        position: absolute;
        right: -20px;
        .icon{
          &:hover{
            color: #3a84ff;
          }
        }
      }
    }
    :deep(.bk-select-tag) {
      padding-top: 0;
      .bk-tag {
        margin-right: 8px;
        margin-bottom: 4px;
        margin-top: 4px;
      }
    }
  }
</style>
