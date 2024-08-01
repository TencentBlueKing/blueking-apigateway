<template>
  <div class="codemirror">
    <div id="monacoEditor" class="monaco-editor" ref="monacoEditor" :style="style"></div>
    <div class="tools">
      <cog-shape class="tool-icon" v-if="showFormat" @click="handleFormat" />
      <copy-shape class="tool-icon" v-if="showCopy" @click="handleCopy" />
      <filliscreen-line class="tool-icon" v-if="showFullScreen" @click="handleFullScreen" />
    </div>
  </div>
</template>
<script setup>
// 引入vue模块
import { ref, onMounted, toRefs, computed, watch, onBeforeMount } from 'vue';
// 引入monaco编辑器
import * as monaco from 'monaco-editor';
import { copy } from '@/common/util';
import { CogShape, CopyShape, FilliscreenLine } from 'bkui-vue/lib/icon';

let editor = null; // 编辑器实例
const monacoEditor = ref(null);
// 编辑器装饰器（高亮效果等）
let decorations = [];
// 可切换字号范围
const fontSizeOptions = [14, 20, 24];
// 可切换行高范围
const lineHeight = [24, 30, 34];
// 当前选中字号的index
const currentFontSizeIndex = ref(0);
// 定义从父组件接收的属性
const props = defineProps({
  modelValue: { type: [String, Object, Array], default: () => 'yaml' },
  language: { type: String, default: 'yaml' },
  readOnly: { type: Boolean, default: false },
  width: { type: [String, Number], default: '100%' },
  height: { type: [String, Number], default: '100%' },
  theme: { type: String, default: 'vs-dark' },
  minimap: { type: Boolean, default: true },
  showFormat: { type: Boolean, default: false },
  showCopy: { type: Boolean, default: false },
  showFullScreen: { type: Boolean, default: false },
});

const { modelValue, language, readOnly, width, height, theme } = toRefs(props);

const emit = defineEmits(['change', 'update:modelValue', 'findStateChanged']);

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
    theme: theme.value, // 主题
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
    lineHeight: 24,
    glyphMargin: true,  // 是否显示行号左侧装饰，用于显示当前行的错误信息等级：error | warning
    minimap: {
      enabled: props.minimap, // 小地图
    },
  });

  editorMounted(); // 编辑器初始化后
  // 初始化编辑器装饰
  decorations = editor.createDecorationsCollection([]);
};

const editorMounted = () => {
  editor.onDidChangeModelContent((event) => {
    const yamlValue = getValue();
    emitChange(yamlValue, event);
  });

  // 监听搜索工具状态变化，把可视状态传递出去
  editor.getContribution('editor.contrib.findController')
    .getState()
    .onFindReplaceStateChange(() => {
      const isVisible = editor.getContribution('editor.contrib.findController')
        .getState().isRevealed;
      emit('findStateChanged', isVisible);
    });
};

// 修改editor的值
const emitChange = (emitValue, event) => {
  emit('change', emitValue, event);
  emit('update:modelValue', emitValue, event);
};

// 更改光标位置
const setCursorPos = ({ lineNumber }) => {
  const model = editor.getModel();

  if (!model) return;

  const lastColumnNumber = model.getLineLastNonWhitespaceColumn(lineNumber);
  editor.focus();
  editor.setPosition(new monaco.Position(lineNumber, lastColumnNumber));
  editor.revealLineInCenter(lineNumber);
};

const genLineDecorations = (decorationOptions) => {
  const decoOptions = decorationOptions.filter(o => o.position)
    .map(o => ({
      range: {
        startLineNumber: o.position.lineNumber,
        endLineNumber: o.position.lineNumber,
        startColumn: o.position.column,
        endColumn: o.position.column,
      },
      options: {
        isWholeLine: true, // 整行高亮
        className:
          `lineHighlight${o.level}`, // 当前行装饰用类名
        glyphMarginClassName:
          `glyphMargin${o.level}`, // 当前行左侧装饰(glyph)用类名
      },
    }));
  decorations = editor.createDecorationsCollection(decoOptions);
};

const setDecorations = () => {
  decorations.set();
};

const clearDecorations = () => {
  decorations.clear();
};

const getModel = () => editor.getModel();

const showFindPanel = () => {
  editor.trigger('', 'actions.find');
};

const closeFindPanel = () => {
  editor.trigger('', 'closeFindWidget');
};

const switchFontSize = () => {
  currentFontSizeIndex.value = (currentFontSizeIndex.value + 1) % fontSizeOptions.length;
  editor.updateOptions({
    fontSize: fontSizeOptions[currentFontSizeIndex.value],
    lineHeight: lineHeight[currentFontSizeIndex.value],
  });
};

const handleFormat = () => {
  if (language.value === 'json') { // 格式化 JSON 文档
    editor.trigger('a', 'editor.action.formatDocument');
  }
  // yaml 格式 需 npm i yamljs 拓展支持
};

const handleCopy = () => {
  copy(editor.getValue());
};

// 全屏开关变量
let isFullScreen = false;
const handleFullScreen = () => {
  const domNode = editor.getDomNode();
  const container = (domNode.parentNode).parentNode;
  const toolsDom = container.querySelector('.tools');

  if (isFullScreen) {
    document.body.style.overflow = '';
    container.style.position = 'relative';
    container.style.zIndex = '0';
    toolsDom.style.zIndex = '0';
    editor.layout();
    isFullScreen = false;
  } else {
    document.body.style.overflow = 'hidden';
    container.style.position = 'fixed';
    container.style.zIndex = '6003';
    container.style.overflow = 'hidden';
    container.style.width = '100%';
    container.style.height = '100%';
    container.style.left = 0;
    container.style.top = 0;
    toolsDom.style.zIndex = '6004';
    editor.layout();
    isFullScreen = true;
  }
};

defineExpose({
  setValue,
  setCursorPos,
  setDecorations,
  clearDecorations,
  genLineDecorations,
  getModel,
  getValue,
  showFindPanel,
  closeFindPanel,
  switchFontSize,
});

</script>
<style scoped lang="scss">
.codemirror,
.monaco-editor {
  width: 100%;
  height: 100%;
}
.codemirror {
  position: relative;
  .tools {
    position: absolute;
    top: 5px;
    right: 28px;
    .tool-icon {
      cursor: pointer;
      font-size: 16px;
      color: #979BA5;
      margin-left: 12px;
    }
  }
}
</style>
