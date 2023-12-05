<template>
  <div class="searcher" v-if="curVersionList.length">
    <bk-dropdown ref="dropdown" :popover-options="popoverOptions">
      <div class="dropdown-trigger-btn">
        <span>{{ curVersion.board_label }}</span>
        <i class="ag-doc-icon doc-down-shape apigateway-icon icon-ag-down-shape"></i>
      </div>
      <template #content>
        <bk-dropdown-menu class="bk-dropdown-list">
          <bk-dropdown-item v-for="item in curVersionList" :key="item.board_label">
            <a href="javascript:;" @click="triggerHandler(item)" class="f14">{{ item.board_label }}</a>
          </bk-dropdown-item>
        </bk-dropdown-menu>
      </template>
    </bk-dropdown>
    <div class="input-wrapper bk-dropdown-menu search-result-box">
      <input
        type="text" v-model="keyword" class="input w400" :placeholder="t('请输入API名称')" @input="handleSearch"
        @keydown="handleKeyup">
      <div class="bk-dropdown-content is-show left-align" v-if="keyword">
        <bk-loading :loading="isLoading" opacity="1">
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
                    <strong class="mr5" v-html="hightlightSystemName(item)"></strong>
                    <!-- eslint-disable-next-line vue/no-v-html -->
                    <span v-html="hightlight(item)"></span>
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
  dropdown?.value.hide();
};
// 跳转指定组件
const handleShowDoc = (version: any) => {
  router.push({
    name: 'componentAPIDetailDoc',
    params: {
      version: curVersion.value.board,
      id: version.system_name,
      componentId: version.name,
    },
  });
};
// 搜索
const handleSearch = async () => {
  try {
    isLoading.value = true;
    selectIndex.value = 0;
    const curKeyword = keyword.value ? keyword.value : '';
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

  switch (curKeyCode) {
    // 上
    case 38:
      e.preventDefault();
      if (selectIndex.value === -1 || selectIndex.value === 0) {
        selectIndex.value = curLength - 1;
        searchListContainer.value.scrollTop = searchListContainer.value.scrollHeight;
      } else {
        // eslint-disable-next-line no-plusplus
        selectIndex.value--;
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
      e.preventDefault();
      if (selectIndex.value < curLength - 1) {
        // eslint-disable-next-line no-plusplus
        selectIndex.value++;
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
      e.preventDefault();
      // eslint-disable-next-line no-case-declarations
      const curSelectIndex: any = selectIndex.value;
      if (resultList[curSelectIndex as keyof typeof resultList]) {
        handleShowDoc(resultList[curSelectIndex as keyof typeof resultList]);
      }
      break;
    default:
      break;
  }
};

</script>

<style lang="scss" scoped>
.w400 {
  width: 400px;
}

.search-empty {
  text-align: center;
  line-height: 41px;
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
  width: 700px;
  height: 40px;
  background: #FFF;
  border-radius: 2px;
  position: inherit;
  display: flex;

  .dropdown-trigger-btn {
    height: 40px;
    line-height: 40px;
    padding: 0 15px;
    color: #63656E;
    font-size: 14px;
  }

  .input-wrapper {
    flex: 1;
    line-height: 40px;
  }

  .input {
    color: #000;
    outline: none;
    border: none;
    line-height: 16px;
    font-size: 14px;
    background: transparent;
    padding-left: 20px;
    border-left: 1px solid #c4c6cc;
    position: relative;
  }
}


.bk-dropdown-content {
  box-shadow: none !important;
  -webkit-box-shadow: none !important;

  .bk-dropdown-list {
    width: 105px;

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
  line-height: 41px !important;
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


