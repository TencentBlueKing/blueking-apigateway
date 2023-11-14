<template>
  <div class="gateways-edit-textarea" :style="styles">
    <template v-if="!isEditable">
      <div class="edit-wrapper">
        <div class="edit-content" :title="newVal">
          <slot :value="newVal">
            {{ newVal }}
            <template v-if="!newVal && !isLoading">
              --
            </template>
          </slot>
        </div>
        <div class="edit-action-box" v-if="isEditMode">
          <i class="apigateway-icon icon-ag-edit-small edit-action" @click.self.stop="handleEdit" />
        </div>
      </div>
    </template>
    <template v-else>
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
    </template>
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
  remoteHander: {
    type: Function,
    default: () => Promise.resolve(),
  },
  rules: {
    type: Array,
    default: () => [],
  },
  maxLength: {
    type: Number,
    default: 255,
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
const isLoading = ref(false);
const isShowError = ref(false);
const isEditable = ref(false);
const errorTips = ref('');
const newVal = ref(props.content);

const handleValidate = () => {
  isShowError.value = false;
  errorTips.value = '';
  // if (props.rules.length > 0) {
  //     for (let i = 0; i < props.rules.length; i++) {
  //         const validate = props.rules[i];
  //         if (validate?.required && !newVal) {
  //             isShowError.value = true;
  //             errorTips = validate.message;
  //             break;
  //         }
  //         if (validate?.validator && !validate?.validator(newVal.value)) {
  //             this.isShowError = true;
  //             this.errorTips = validate?.message;
  //             break;
  //         }
  //         if ((validate?.required && newVal.value) && (validate?.validator?.(this.newVal))) {
  //             this.isShowError = false;
  //             this.errorTips = '';
  //             break;
  //         }
  //     }
  // }
};

const handleEdit = () => {
  document.body.click();
  isEditable.value = true;
  nextTick(() => {
    // textareaRef.value?.focus();
  });
};

const handleInput = () => {
  isShowError.value = false;
  errorTips.value = '';
};

const handleBlur = () => {
  if (isEditable.value) return;
  handleValidate();
  if (isShowError.value) return;
  triggerChange();
};

const hideEdit = (event: any) => {
  if (event.path && event.path.length > 0) {
    // for (let i = 0; i < event.path.length; i++) {
    //   const target = event.path[i];
    //   if (target.className === 'gateways-edit-textarea') {
    //     return;
    //   }
    // }
  }
  handleValidate();
  if (isShowError.value) return;
  isEditable.value = false;
};

const triggerChange = () => {
  isEditable.value = false;
  if (newVal.value === props.content) {
    return;
  }
  isLoading.value = true;
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

<style lang='scss' scoped>
@keyframes textarea-edit-loading {
    to {
        transform: rotateZ(360deg)
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

        .icon-ag-edit-small{
            font-size: 18px;
            cursor: pointer;
            display: none;

            &:hover {
                color: #3a84ff;
            }
        }
    }

    .edit-input {
        width: 100%;
    }

    .validate-error-tips {
        font-size: 12px;
        color: #ff4d4d;
    }
}
</style>

