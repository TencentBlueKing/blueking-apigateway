<template>
  <div class="gateways-edit-textarea" :style="styles">
    <template v-if="!isEditable">
      <div class="edit-wrapper">
        <div class="edit-content" :title="newVal">
          <slot :value="newVal">
            {{ newVal }}
            <template v-if="!newVal"> -- </template>
          </slot>
        </div>
        <div class="edit-action-box" v-if="isEditMode">
          <i
            class="apigateway-icon icon-ag-edit-small edit-action"
            @click.self.stop="handleEdit"
          />
        </div>
      </div>
    </template>
    <div v-else class="edit-mode-content">
      <bk-input
        v-model="newVal"
        ref="textareaRef"
        type="textarea"
        class="edit-input"
        :placeholder="placeholder"
        :maxlength="maxLength"
        :rows="3"
        @input="handleInput"
        @blur="handleBlur"
      />
      <p class="validate-error-tips" v-if="isShowError">{{ errorTips }}</p>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { computed, onMounted, ref, nextTick, watch } from 'vue';
// import { useI18n } from 'vue-i18n';
// const { t } = useI18n();
const props = defineProps({
  field: {
    type: String,
    required: true,
  },
  content: {
    type: String,
    default: '',
  },
  width: {
    type: String,
    default: 'auto',
  },
  placeholder: {
    type: String,
    default: '请输入',
  },
  rules: {
    type: Array,
    default: () => [],
  },
  maxLength: {
    type: Number,
    default: 100,
  },
  mode: {
    type: String,
    default: 'edit',
    validator(value: string) {
      return ['detail', 'edit'].includes(value);
    },
  },
});
const emit = defineEmits(['on-change']);

const textareaRef = ref(null);
const isShowError = ref(false);
const isEditable = ref(false);
const errorTips = ref('');
const newVal = ref(props.content);

const handleValidate = () => {
  isShowError.value = false;
  errorTips.value = '';
};

const handleEdit = () => {
  document.body.click();
  isEditable.value = true;
  nextTick(() => {
    textareaRef.value?.focus();
  });
};

const handleInput = () => {
  isShowError.value = false;
  errorTips.value = '';
};

const handleBlur = () => {
  if (!isEditable.value) return;
  isEditable.value = false;
  triggerChange();
};

const hideEdit = (event: any) => {
  if (event.path && event.path.length > 0) {
    for (const i of event.path) {
      const target = event.path[i];
      if (target.className === 'gateways-edit-textarea') {
        return;
      }
    }
  }
  handleValidate();
};

const triggerChange = () => {
  isEditable.value = false;
  if (newVal.value === props.content) {
    return;
  }
  emit('on-change', {
    [props.field]: newVal.value,
  });
};

const styles = computed(() => {
  return {
    width: props.width,
  };
});

const isEditMode = computed(() => {
  return props.mode === 'edit';
});

watch(
  () => props.content,
  (payload: string) => {
    newVal.value = payload;
  },
);

onMounted(() => {
  document.body.addEventListener('click', hideEdit);
});
</script>

<style lang="scss" scoped>
@keyframes textarea-edit-loading {
  to {
    transform: rotateZ(360deg);
  }
}

.gateways-edit-textarea {
  position: relative;

  .edit-wrapper {
    position: relative;
    display: flex;
    align-items: center;

    &:hover {
      .icon-ag-edit-small {
        display: block;
      }
    }
  }

  .edit-content {
    flex: 0 0 auto;
    max-width: calc(100% - 25px);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .edit-action-box {
    display: flex;
    align-items: center;
    margin-right: auto;
    height: 40px;
    line-height: 40px;

    .icon-ag-edit-small {
      font-size: 26px;
      cursor: pointer;
      display: none;

      &:hover {
        color: #3a84ff;
      }
    }
  }

  .edit-mode-content {
    padding: 20px 0;
    .edit-input {
      width: 100%;
    }
  }

  .validate-error-tips {
    font-size: 12px;
    color: #ff4d4d;
  }
}
</style>
