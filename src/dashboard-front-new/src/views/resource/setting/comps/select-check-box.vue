<template>
  <bk-select
    style="width: 235px;"
    class="select-wrapper mt5"
    filterable
    multiple
    multiple-mode="tag"
    ref="selectRef"
    show-on-init
    v-model="curLabelIds"
    selected-style="checkbox"
    @toggle="handleToggle">
    <bk-option v-for="option in labelsData" :key="option.name" :id="option.id" :name="option.name">
      <template #default>
        <div
          v-bk-tooltips="{
            content: $t('标签最多只能选择10个'),
            disabled: !(!curLabelIds.includes(option.id) && curLabelIds.length >= 10) }"
          :disabled="!curLabelIds.includes(option.id) && curLabelIds.length >= 10"
          class="flex-row align-items-center justify-content-between" style="width: 100%;"
          v-if="!option.isEdited">
          {{ option.name }}
          <div>
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
                @click.stop="handleDeleteOptionItem(option)"></i>
            </bk-pop-confirm>
          </div>
        </div>
        <div v-else @click.stop="handleInputFocus">
          <bk-input
            style="width: 180px"
            ref="inputRef"
            v-model="option.name"
            size="small"
            @enter="addOption"
            :placeholder="t('请输入标签')"
          />
        </div>
      </template>
    </bk-option>
    <template #extension>
      <div class="custom-extension" style="margin: 0 auto;">
        <div
          v-if="showEdit"
          style="display: flex; align-items: center;"
        >
          <bk-input
            style="width: 220px"
            ref="inputRef"
            v-model="optionName"
            size="small"
            @enter="addOption"
            :placeholder="t('请输入标签')"
          />
        </div>
        <div v-else class="flex-row align-items-center justity-content-center" style="cursor: pointer;">
          <div
            class="flex-row align-items-center"
            @click="handleShowEdit"
          >
            <plus style="font-size: 18px;" />
            {{ t('新建标签') }}
          </div>
          <div class="flex-row align-items-center" style="position: absolute; right: 12px;">
            <bk-divider
              direction="vertical"
              type="solid"
            />
            <!-- <spinner
              v-if="isLoading"
              style="font-size: 14px;color: #3A84FF;"
            />
            <right-turn-line
              v-else
              style="font-size: 14px;cursor: pointer;"
              @click="refresh"
            /> -->
          </div>
        </div>
      </div>
    </template>
  </bk-select>
</template>
<script setup lang="ts">
import { ref, computed, toRefs, PropType, watch } from 'vue';
import { Plus } from 'bkui-vue/lib/icon';
import { Message } from 'bkui-vue';
import { useI18n } from 'vue-i18n';

import { updateResourcesLabels, createResourcesLabels, deleteResourcesLabels } from '@/http';

import { useCommon } from '@/store';

const emit = defineEmits(['close', 'update-success', 'label-add-success']);
const common = useCommon();
const { t } = useI18n();
const { apigwId } = common; // 网关id

const props = defineProps({
  curSelectLabelIds: { type: Array, default: [] },   // 当前选中的label
  resourceId: { type: Number, default: 0 },
  labelsData: { type: Array as PropType<any>, default: [] },
});

const { curSelectLabelIds, resourceId, labelsData } = toRefs(props);

const curLabelIds = ref(curSelectLabelIds.value);
const showEdit = ref(false);
const optionName = ref('');
const inputRef = ref(null);
const selectRef = ref(null);

const curLabelIdsbackUp = ref(curLabelIds.value);

// 相同的标签
const isSameLabels = computed(() => {
  const curLabelIdsString = JSON.stringify(curLabelIds.value.sort());
  const curLabelIdsbackUpString = JSON.stringify(curLabelIdsbackUp.value.sort());
  return curLabelIdsString === curLabelIdsbackUpString;
});


//
const handleToggle = async (v: boolean) => {
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
          });
          emit('update-success');
        } catch (error) {}
      } else {
        emit('close');
      }
    }
  }, 500);
};

const addOption = async () => {
  if (optionName.value.trim()) {
    await createResourcesLabels(apigwId, { name: optionName.value });
    Message({
      message: t('标签新建成功'),
      theme: 'success',
    });
    optionName.value = '';
  }
  showEdit.value = false;
  emit('label-add-success');
};

// const refresh = () => {
//   isLoading.value = true;
//   setTimeout(() => {
//     isLoading.value = false;
//   }, 2000);
// };

const handleShowEdit = () => {
  showEdit.value = true;
  setTimeout(() => {
    inputRef.value.focus();
  });
};

const handleEditOptionItem = (e: any) => {
  e.isEdited = true;
};

const handleDeleteOptionItem = (e: any) => {
  console.log(1111, e);
};

// 删除某个标签
const handleDeleteOptionItemConfirm = async (e: any) => {
  console.log(1111111, e);
  try {
    await deleteResourcesLabels(apigwId, e.id);
    Message({
      message: t('删除标签成功'),
      theme: 'success',
    });
    selectRef.value.showPopover();
    emit('update-success');
  } catch (error) {}
};

const handleInputFocus = () => {
  console.log(111111);
};

watch(
  () => curLabelIds,
  (v: any) => {
    console.log('vvvvv', v);
  },
  { deep: true, immediate: true },
);
</script>

