/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2025 Tencent. All rights reserved.
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
  <!--  组件搜索器  -->
  <div class="searcher">
    <BkDropdown
      ref="dropdown"
      :popover-options="popoverOptions"
      :disabled="curVersionList.length < 2"
    >
      <div class="dropdown-trigger-btn">
        <span>{{ curVersion.board_label }}</span>
        <i
          v-if="curVersionList.length > 1"
          class="ag-doc-icon doc-down-shape apigateway-icon icon-ag-down-shape"
        />
      </div>
      <template #content>
        <BkDropdownMenu class="dropdown-trigger-content bk-dropdown-list">
          <BkDropdownItem
            v-for="item in curVersionList"
            :key="item.board_label"
            :title="item.board_label"
            @click="() => triggerHandler(item)"
          >
            <a
              href="javascript:;"
              class="f14"
            >{{ item.board_label }}</a>
          </BkDropdownItem>
        </BkDropdownMenu>
      </template>
    </BkDropdown>
    <div class="input-wrapper BkDropdownMenu search-result-box">
      <BkInput
        v-model="keyword"
        class="input"
        :placeholder="t('请输入 API 名称')"
        @input="handleSearch"
        @keydown="handleKeyup"
      />
      <div
        v-if="keyword"
        class="bk-dropdown-content is-show left-align"
      >
        <BkLoading
          :loading="isLoading"
          :opacity="1"
        >
          <ul
            id="result-list"
            ref="searchListContainer"
            class="bk-dropdown-list"
            :style="{ 'max-height': `${contentMaxHeight}px` }"
          >
            <template v-if="resultList.length">
              <li
                v-for="(item, index) of resultList"
                :key="index"
                :class="selectIndex === index ? 'cur' : ''"
                @click="handleShowDoc(item, curVersion.board)"
              >
                <a href="javascript:;">
                  <p class="name">
                    <strong
                      v-bk-xss-html="hightlightSystemName(item)"
                      class="mr-5px"
                    />
                    <span v-bk-xss-html="hightlight(item)" />
                  </p>
                  <p class="desc">{{ item.description || t('暂无描述') }}</p>
                </a>
              </li>
            </template>
            <template v-else>
              <li>
                <a
                  href="javascript:;"
                  class="search-empty"
                >
                  {{ t('没有找到相应记录') }}
                </a>
              </li>
            </template>
          </ul>
        </BkLoading>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { searchAPI } from '@/services/source/docs-esb';

interface IProps { versionList?: any[] }

const {
  versionList = [{
    board: '',
    board_label: '',
    categories: [],
  }],
} = defineProps<IProps>();

const { t } = useI18n();
const router = useRouter();

const curVersionList = ref([]);
const resultList = ref([]);
const keyword = ref<string>('');
const contentMaxHeight = ref<number>(410);
const selectIndex = ref<number>(0);
const isLoading = ref<boolean>(false);
const dropdown = ref();
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
  () => versionList,
  () => {
    if (versionList.length) {
      curVersion.value = versionList[0];
      curVersionList.value = versionList;
    }
  },
  { immediate: true },
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
const handleShowDoc = (version: any, board: string) => {
  router.push({
    name: 'ApiDocDetail',
    params: {
      board,
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
  }
  catch (error) {
    console.log('error', error);
  }
};
const handleKeyup = (e: any) => {
  const curKeyCode = e.keyCode;
  const curLength = resultList.value.length;
  e.preventDefault?.();
  switch (curKeyCode) {
    // 上
    case 38:
      if (selectIndex.value === -1 || selectIndex.value === 0) {
        selectIndex.value = curLength - 1;
        searchListContainer.value.scrollTop = searchListContainer.value.scrollHeight;
      }
      else {
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
      }
      else {
        selectIndex.value = 0;
        searchListContainer.value.scrollTop = 0;
      }
      break;
    case 13:
      if (resultList.value[selectIndex.value]) {
        handleShowDoc(resultList.value[selectIndex.value], curVersion.value.board);
      }
      break;
    default:
      break;
  }
};

</script>

<style lang="scss" scoped>
.search-empty {
  line-height: 30px;
  text-align: center;
}

.bk-dropdown-content {
  top: 43px;
  width: 300px;
  max-height: 550px;
  min-width: 300px;
  padding: 4px 0;
  overflow: auto;
  background: #fff;
  border: 1px solid #dcdee5;

  .bk-dropdown-list {
    width: 100%;
  }
}

.searcher {
  position: relative;
  z-index: 1;
  display: flex;
  width: 320px;
  height: 30px;
  background: #FFF;
  border: 1px solid #C4C6CC;
  border-radius: 2px;
  align-items: center;

  .dropdown-trigger-btn {
    height: 30px;
    font-size: 12px;
    line-height: 28px;
    color: #63656E;
    padding-inline: 6px;
  }

  .input-wrapper {
    position: relative;
    width: 220px;
    line-height: 28px;
    flex: 1;

    .bk-dropdown-content {
      position: absolute;
      top: 28px;
      left: 0;
    }
  }

  .input {
    position: relative;
    height: 28px;
    font-size: 12px;
    line-height: 12px;
    color: #000;
    background: transparent;
    border: none;
    border-left: 1px solid #c4c6cc;
    border-bottom-left-radius: 0;
    border-top-left-radius: 0;
    outline: none;

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

  .bk-dropdown-list {

    a {
      color: #63656e;

      &:hover {
        color: #3a84ff;
        background-color: #eaf3ff
      }
    }
  }
}

.search-empty {
  line-height: 30px !important;
  text-align: center;
}

.search-result-box {

  :deep(.bk-dropdown-list) {
    width: 100%;
    font-size: 12px;

    li {
      width: 100%;

      a {
        display: block;
        height: auto;
        padding: 6px 10px;
        margin-bottom: 9px;
        line-height: 1;
        color: #63656e;
        white-space: nowrap;

        &:hover {
          color: #3a84ff;
          background-color: #eaf3ff
        }

        .name {
          display: block;
          margin-bottom: 5px;
          color: #63656E;

          .keyword {
            font-style: normal;
            color: #3a84ff;
          }
        }

        .desc {
          max-width: 290px;
          overflow: hidden;
          color: #C4C6CC;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

      }
    }
  }

}
</style>
