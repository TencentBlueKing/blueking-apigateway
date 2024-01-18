<template>
  <div class="codemirror">
    <div id="monacoEditor" class="monaco-editor" ref="monacoEditor" :style="style"></div>
  </div>
</template>
<script setup>
// 引入vue模块
import { ref, onMounted, toRefs, computed, watch, onBeforeMount } from 'vue';
// 引入monaco编辑器
import * as monaco from 'monaco-editor';

let editor = null; // 编辑器实例
const monacoEditor = ref(null);
// 定义从父组件接收的属性
const props = defineProps({
  modelValue: { type: [String, Object, Array], default: () => 'yaml' },
  language: { type: String, default: 'yaml' },
  readOnly: { type: Boolean, default: false },
  width: { type: [String, Number], default: '100%' },
  height: { type: [String, Number], default: '100%' },
});

const { modelValue, language, readOnly, width, height } = toRefs(props);

const emit = defineEmits(['change', 'update:modelValue']);

// 挂载
onMounted(() => {
  initEditor();
});

// 卸载
onBeforeMount(() => {
  editor?.dispose();
  editor = null;
});

const style = computed(() => ({
  width: typeof width.value === 'number' ? `${width.value}px` : width.value,
  height: typeof height.value === 'number' ? `${height.value}px` : height.value,
}));

// 设置值
const setValue = (value) => {
  try {
    if (!editor) return null;
    return editor.setValue(value);
  } catch (err) {
    console.log('err', err);
  }
};

// 非只读模式时，建议手动调用setValue方法，watch在双向绑定时会让编辑器抖动
watch(modelValue, () => {
  if (readOnly.value) {
    setValue(modelValue.value);
  }
});

// 获取编辑器中的值
const getValue = () => {
  if (!editor) return '';
  return editor.getValue();
};

// 初始化编辑器
const initEditor = () => {
  editor = monaco.editor.create(monacoEditor.value, {
    value: modelValue.value,
    theme: 'vs-dark', // 主题
    language: language.value,
    folding: true, // 是否折叠
    foldingHighlight: true, // 折叠等高线
    foldingStrategy: 'indentation', // 折叠方式  auto | indentation
    showFoldingControls: 'always', // 是否一直显示折叠 always | mouseover
    disableLayerHinting: true, // 等宽优化
    emptySelectionClipboard: false, // 空选择剪切板
    selectionClipboard: false, // 选择剪切板
    automaticLayout: true, // 自动布局
    codeLens: false, // 代码镜头
    scrollBeyondLastLine: false, // 滚动完最后一行后再滚动一屏幕
    colorDecorators: true, // 颜色装饰器
    accessibilitySupport: 'off', // 辅助功能支持  "auto" | "off" | "on"
    lineNumbers: 'on', // 行号 取值： "on" | "off" | "relative" | "interval" | function
    lineNumbersMinChars: 5, // 行号最小字符   number
    readOnly: readOnly.value, // 是否只读  取值 true | false
  });

  editorMounted(); // 编辑器初始化后
};

const editorMounted = () => {
  editor.onDidChangeModelContent((event) => {
    const yamlValue = getValue();
    emitChange(yamlValue, event);
  });
};

// 修改editor的值
const emitChange = (emitValue, event) => {
  emit('change', emitValue, event);
  emit('update:modelValue', emitValue, event);
};

defineExpose({
  setValue,
});

</script>
<style scoped>
.codemirror,
.monaco-editor {
    width: 100%;
    height: 100%;
}
</style>
