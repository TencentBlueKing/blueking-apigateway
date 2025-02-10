<template>
  <!--  组件搜索器  -->
  <div class="searcher">
    <bk-dropdown ref="dropdown" :popover-options="popoverOptions" :disabled="curVersionList.length < 2">
      <div class="dropdown-trigger-btn">
        <span>{{ curVersion.board_label }}</span>
        <i v-if="curVersionList.length > 1" class="ag-doc-icon doc-down-shape apigateway-icon icon-ag-down-shape"></i>
      </div>
      <template #content>
        <bk-dropdown-menu class="dropdown-trigger-content bk-dropdown-list">
          <bk-dropdown-item v-for="item in curVersionList" :key="item.board_label" :title="item.board_label">
            <a href="javascript:;" @click="triggerHandler(item)" class="f14">{{ item.board_label }}</a>
          </bk-dropdown-item>
        </bk-dropdown-menu>
      </template>
    </bk-dropdown>
    <div class="input-wrapper bk-dropdown-menu search-result-box">
      <bk-input
        v-model="keyword" class="input" :placeholder="t('请输入 API 名称')" @input="handleSearch"
        @keydown="handleKeyup"
      />
      <div class="bk-dropdown-content is-show left-align" v-if="keyword">
        <bk-loading :loading="isLoading" :opacity="1">
          <ul
            ref="searchListContainer" id="result-list" class="bk-dropdown-list"
            :style="{ 'max-height': `${contentMaxHeight}px` }">
            <template v-if="resultList.length">
              <li
                v-for="(item, index) of resultList" :key="index" :class="selectIndex === index ? 'cur' : ''"
                @click="handleShowDoc(item)">
                <a href="javascript:;">
                  <p class="name">
                    <!-- eslint-disable-next-line vue/no-v-html -->
                    <strong class="mr5" v-dompurify-html="hightlightSystemName(item)"></strong>
                    <!-- eslint-disable-next-line vue/no-v-html -->
                    <span v-dompurify-html="hightlight(item)"></span>
                  </p>
                  <p class="desc">{{ item.description || t('暂无描述') }}</p>
                </a>
              </li>
            </template>
            <template v-else>
              <li>
                <a href="javascript:;" class="search-empty">
                  {{ t('没有找到相应记录') }}
                </a>
              </li>
            </template>
          </ul>
        </bk-loading>

      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';
import {
  searchAPI,
} from '@/http';
const { t } = useI18n();
const router = useRouter();

const props = defineProps({
  versionList: {
    type: Array,
    default() {
      return [{
        board: '',
        board_label: '',
        categories: [],
      }];
    },
  },
});

const curVersionList = ref([]);
const resultList = ref([]);
const keyword = ref<string>('');
const contentMaxHeight = ref<number>(410);
const selectIndex = ref<number>(0);
const isLoading = ref<boolean>(false);
const dropdown = ref(null);
const searchListContainer = ref(null);
const curVersion = ref<any>({
  board: '',
  board_label: '',
  categories: [],
});
const popoverOptions = {
  boundary: 'body',
  placement: 'bottom-start',
};

watch(
  () => props.versionList,
  () => {
    if (props.versionList.length) {
      // eslint-disable-next-line prefer-destructuring
      curVersion.value = props.versionList[0];
      curVersionList.value = props.versionList;
    }
  },
  {
    immediate: true,
  },
);

const hightlight = (node: any) => {
  if (keyword.value) {
    return node.name.replace(new RegExp(`(${keyword.value})`), '<em class="keyword">$1</em>');
  }
  return node.name;
};
const hightlightSystemName = (node: any) => {
  if (keyword.value) {
    return node.system_name.replace(new RegExp(`(${keyword.value.toUpperCase()})`), '<em class="keyword">$1</em>');
  }
  return node.system_name;
};

const triggerHandler = (version: any) => {
  curVersion.value = version;
  dropdown.value?.hide?.();
};
// 跳转指定组件
const handleShowDoc = (version: any) => {
  router.push({
    name: 'apiDocDetail',
    params: {
      curTab: 'component',
      targetName: version.system_name,
      componentName: version.name,
    },
  });
};
// 搜索
const handleSearch = async () => {
  try {
    isLoading.value = true;
    selectIndex.value = 0;
    const curKeyword = keyword.value || '';
    const curBoard = curVersion.value.board;
    const res = await searchAPI(curBoard, '-', { keyword: curKeyword });
    isLoading.value = false;
    resultList.value = res;
  } catch (error) {
    console.log('error', error);
  }
};
const handleKeyup = (e: any) => {
  const curKeyCode = e.keyCode;
  const curLength = resultList.value.length;
  e.preventDefault();
  switch (curKeyCode) {
    // 上
    case 38:
      if (selectIndex.value === -1 || selectIndex.value === 0) {
        selectIndex.value = curLength - 1;
        searchListContainer.value.scrollTop = searchListContainer.value.scrollHeight;
      } else {
        selectIndex.value -= 1;
        nextTick(() => {
          const curSelectNode = searchListContainer.value.querySelector('li.cur');
          const { offsetTop } = curSelectNode;
          if (offsetTop < searchListContainer.value.scrollTop) {
            searchListContainer.value.scrollTop -= 41;
          }
        });
      }
      break;
    // 下
    case 40:
      if (selectIndex.value < curLength - 1) {
        selectIndex.value += 1;
        nextTick(() => {
          const curSelectNode = searchListContainer.value.querySelector('li.cur');
          const { offsetTop } = curSelectNode;
          // searchListContainer 上下各有 6px 的 padding
          if (offsetTop > contentMaxHeight.value - 2 * 6) {
            // 每一个 item 是 41px height
            searchListContainer.value.scrollTop += 41;
          }
        });
      } else {
        selectIndex.value = 0;
        searchListContainer.value.scrollTop = 0;
      }
      break;
    case 13:
      if (resultList.value[selectIndex.value]) {
        handleShowDoc(resultList.value[selectIndex.value]);
      }
      break;
    default:
      break;
  }
};

</script>

<style lang="scss" scoped>

.search-empty {
  text-align: center;
  line-height: 30px;
}

.bk-dropdown-content {
  background: #fff;
  padding: 4px 0;
  width: 300px;
  min-width: 300px;
  top: 43px;
  max-height: 550px;
  overflow: auto;
  border: 1px solid #dcdee5;

  .bk-dropdown-list {
    width: 100%;
  }
}

.searcher {
  position: relative;
  width: 320px;
  height: 30px;
  display: flex;
  align-items: center;
  background: #FFF;
  border: 1px solid #C4C6CC;
  border-radius: 2px;
  z-index: 1;

  .dropdown-trigger-btn {
    height: 30px;
    line-height: 28px;
    padding-inline: 6px;
    color: #63656E;
    font-size: 12px;
  }

  .input-wrapper {
    flex: 1;
    width: 220px;
    line-height: 28px;
    position: relative;

    .bk-dropdown-content {
      position: absolute;
      top: 28px;
      left: 0;
    }
  }

  .input {
    color: #000;
    outline: none;
    border: none;
    line-height: 12px;
    font-size: 12px;
    background: transparent;
    border-left: 1px solid #c4c6cc;
    border-top-left-radius: 0;
    border-bottom-left-radius: 0;
    position: relative;
    height: 28px;

    &::placeholder {
      color: #c4c6cc;
    }
  }
}

.dropdown-trigger-content {
  :deep(.bk-dropdown-item) {
    max-width: 300px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}


.bk-dropdown-content {
  box-shadow: none !important;
  -webkit-box-shadow: none !important;

  .bk-dropdown-list {
    a {
      color: #63656e;

      &:hover {
        background-color: #eaf3ff;
        color: #3a84ff
      }
    }
  }
}

.search-empty{
  text-align: center;
  line-height: 30px !important;
}

.search-result-box {
  :deep(.bk-dropdown-list) {
    font-size: 12px;
    width: 100%;

    li {
      width: 100%;
      a {
        height: auto;
        line-height: 1;
        padding: 6px 10px;
        margin-bottom: 9px;
        display: block;
        white-space: nowrap;
        color: #63656e;

        &:hover {
          background-color: #eaf3ff;
          color: #3a84ff
        }

        .name {
          margin-bottom: 5px;
          color: #63656E;
          display: block;

          .keyword {
            color: #3a84ff;
            font-style: normal;
          }
        }

        .desc {
          color: #C4C6CC;
          max-width: 290px;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

      }
    }
  }


}
</style>
