<template>
  <div class="biz-keys-list">
    <div class="label" v-if="label">{{ label }}</div>
    <div class="values">
      <template v-if="list.length">
        <div class="biz-key-item" v-for="(keyItem, index) in list" :key="index">
          <bk-form
            class="biz-key-form"
            :ref="(el: any) => setRefs(el, `key-${index}`)" :label-width="0" :model="keyItem">
            <bk-form-item
              :rules="rules.key" :property="'key'" :error-display-type="'normal'"
              style="margin-bottom: 0px;">
              <bk-input
                type="text" :readonly="keyReadonly" :placeholder="keyPlaceholder || $t('键')"
                v-model="keyItem.key" @keyup="valueChange">
              </bk-input>
            </bk-form-item>
          </bk-form>

          <span class="operator">:</span>

          <bk-form
            class="mr5 biz-value-form"
            :ref="(el: any) => setRefs(el, `value-${index}`)"
            :label-width="0"
            :model="keyItem">
            <bk-form-item
              :rules="rules.value" :property="'value'" :error-display-type="'normal'"
              style="margin-bottom: 0px;">
              <bk-input
                type="text" :placeholder="valuePlaceholder || $t('值')" v-model="keyItem.value"
                @keyup="valueChange">
              </bk-input>
            </bk-form-item>
          </bk-form>
          <template v-if="buttons">
            <bk-button class="mr5 ag-icon-btn" v-if="buttons.includes('add')" @click.stop.prevent="addKey">
              <i class="apigateway-icon icon-ag-plus"></i>
            </bk-button>
            <bk-button
              class="ag-icon-btn" v-if="buttons.includes('remove')"
              @click.stop.prevent="removeKey(keyItem, index)">
              <i class="apigateway-icon icon-ag-minus"></i>
            </bk-button>
          </template>
        </div>
      </template>
      <div v-else>
        <bk-button class="ag-icon-btn" v-if="buttons && buttons.includes('add')" @click.stop.prevent="addKey">
          <i class="apigateway-icon icon-ag-plus"></i>
        </bk-button>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, reactive, watch, nextTick } from 'vue';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();

const props = defineProps({
  value: {
    type: Object,
    default: () => ({}),
  },
  tip: {
    type: String,
    default: '',
  },
  keyPlaceholder: {
    type: String,
    default: '',
  },
  keyReadonly: {
    type: Boolean,
  },
  keyRegexRule: {
    type: Object,
    default: () => {
      return {
        regex: /^[a-zA-Z0-9-]+$/,
        message: useI18n().t('键由英文字母、数字、连接符（-）组成'),
      };
    },
  },
  valuePlaceholder: {
    type: String,
    default: '',
  },
  label: {
    type: String,
    default: '',
  },
  buttons: {
    type: Array,
    default() {
      return ['add', 'remove'];
    },
  },
});

interface ItemType {
  key: string;
  value: string;
  id?: number;
};

const itemIndex = ref<number>(0);
const list = reactive<ItemType[]>([]);
const rules = {
  key: [
    {
      required: true,
      message: t('必填项'),
      trigger: 'blur',
    },
    {
      regex: props.keyRegexRule.regex,
      message: props.keyRegexRule.message,
      trigger: 'blur',
    },
    {
      validator: (value: string) => {
        const matches = list.filter(item => value && (item.key === value));
        if (matches.length < 2) {
          return true;
        }
        return false;
      },
      message: t('键不允许重复'),
      trigger: 'blur',
    },
  ],

  value: [
    {
      required: true,
      message: t('必填项'),
      trigger: 'blur',
    },
  ],
};

watch(
  () => props.value,
  (value) => {
    list.splice(0, list.length, ...[]);

    for (const key of Object.keys(value)) {
      list.push({
        id: itemIndex.value,
        key,
        value: value[key],
      });
      itemIndex.value += 1;
    }
  },
  {
    immediate: true,
  },
);

const addKey = () => {
  const params = {
    id: itemIndex.value,
    key: '',
    value: '',
  };
  itemIndex.value += 1;
  list.push(params);
  const obj = getKeyObject();
  emit('change', list, obj);
  emit('toggle-height');
};

const removeKey = (item: ItemType, index: number) => {
  list.splice(index, 1);
  const obj = getKeyObject();
  validate();
  emit('input', obj);
  emit('change', list, obj);
  emit('toggle-height');
};

const valueChange = () => {
  nextTick(() => {
    const obj = getKeyObject();
    emit('input', obj);
    emit('change', list, obj);
  });
};

const getValue = () => {
  return getKeyObject();
};

const pasteKey = (item: ItemType, event: any) => {
  const cache = item.key;
  const clipboard = event.clipboardData;
  const text = clipboard.getData('Text');

  if (text?.indexOf('=') > -1) {
    paste(event);
    item.key = cache;
    setTimeout(() => {
      item.key = cache;
    }, 0);
  }
};

const paste = (event: any) => {
  const clipboard = event.clipboardData;
  const text = clipboard.getData('Text');
  const items = text.split('\n');
  items.forEach((item: string) => {
    if (item.indexOf('=') > -1) {
      const arr = item.split('=');
      list.push({
        key: arr[0],
        value: arr[1],
      });
    }
  });
  setTimeout(() => {
    formatData();
  }, 10);

  return false;
};

const formatData = () => {
  // 去掉空值
  if (list.length) {
    const results: ItemType[] = [];
    const keyObj: any = {};
    const { length } = list;
    list.forEach((item) => {
      if (item.key || item.value) {
        if (!keyObj[item.key]) {
          results.push(item);
          keyObj[item.key] = true;
        }
      }
    });
    const patchLength = results.length - length;
    if (patchLength > 0) {
      for (let i = 0; i < patchLength; i++) {
        results.push({
          key: '',
          value: '',
        });
      }
    }
    list.splice(0, list.length, ...results);
    emit('change', list);
  }
};

// const getList = () => {
//   return list.filter(item => item.key || item.value);
// };

const checkRepeat = () => {
  const keys = list.filter(item => item.key).map((item) => {
    return item.key;
  });
  const uniqueKeys = [...new Set(keys)];
  if (uniqueKeys.length < keys.length) {
    validate();
    return false;
  }
  return true;
};

const getKeyObject = () => {
  const results = list.filter(item => item.key || item.value);
  if (results.length === 0) {
    return {};
  }
  const obj: { [propertyName: string]: string } = {};
  results.forEach((item) => {
    obj[item.key] = item.value;
  });
  return obj;
};

const formRefs = ref(new Map());
const setRefs = (el: any, name: string) => {
  if (el) {
    formRefs.value?.set(name, el);
  }
};

const validate = () => {
  list.forEach((item, index) => {
    formRefs.value?.get(`key-${index}`)?.validate();
    formRefs.value?.get(`value-${index}`)?.validate();
  });
};

const emit = defineEmits<{
  (e: 'change', list: Array<ItemType>, obj?: any): void
  (e: 'input', obj: any): void
  (e: 'toggle-height'): void
}>();

defineExpose({
  getValue,
  checkRepeat,
  pasteKey,
});
</script>

<style scoped lang="scss">
.biz-keys-list {
  display: flex;

  .label {
    font-size: 14px;
    font-weight: bold;
    color: #313238;
    width: 50px;
  }

  .values {
    width: 100%;
  }

  .biz-key-item {
    display: flex;
    width: 100%;

    &:not(:nth-last-child(1)) {
      margin-bottom: 18px;
    }

    .biz-key-form,
    .biz-value-form {
      width: 190px;
      display: inline-block;
    }

    .biz-key-form {
      flex: 1;
      -webkit-box-flex: 1;
    }

    .biz-value-form {
      flex: 2;
      -webkit-box-flex: 2;
    }
  }

  .operator {
    width: 20px;
    font-size: 14px;
    font-weight: bold;
    text-align: center;
    display: inline-block;
    color: #313238;
    vertical-align: middle;
  }

  .action-btn {
    width: auto;
    padding: 0;
    margin-left: 5px;

    &.disabled {
      cursor: default;
      color: #ddd !important;
      border-color: #ddd !important;

      .bk-icon {
        color: #ddd !important;
        border-color: #ddd !important;
      }
    }

    &:hover {
      color: #3a84ff;
      border-color: #3a84ff;

      .bk-icon {
        color: #3a84ff;
        border-color: #3a84ff;
      }
    }
  }
}

.is-danger {
  color: #ff5656;
}

.bk-keyer {
  margin-bottom: 10px;
}

.bk-input-box {
  display: inline-block;
  position: relative;
}
</style>
