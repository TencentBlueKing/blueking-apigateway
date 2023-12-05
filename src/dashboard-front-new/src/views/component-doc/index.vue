<template>
  <div class="index-wrapper">
    <div class="banner">
      <searcher class="ag-searcher-box" :version-list="componentList"></searcher>
    </div>
    <div class="ag-container">
      <template v-if="componentList.length">
        <div class="left">
          <div :class="['side-nav', { 'fixed': isFixed }]">
            <div class="group" v-for="(component, index) of componentList" :key="index">
              <strong class="category-title" @click="handleScrollTo(component.board)" style="cursor: pointer;">{{
                component.board_label }}</strong>
              <!-- <svg aria-hidden="true" class="category-icon">
                <use :xlink:href="`#doc-icon${index % 4}`"></use>
              </svg> -->
              <ul class="list">
                <li
                  :class="{ 'selected': curCategoryId === `${component.board}_${category.id}` }"
                  v-for="(category) of component.categories" :key="category.id"
                  @click="handleScrollTo(component.board, category)">
                  <a href="javascript: void(0);">{{ category.name }}</a>
                </li>
              </ul>
            </div>
          </div>
        </div>
        <div class="right">
          <div class="main-content">
            <div class="version-panel" v-for="(component, i) of componentList" :key="component.board">
              <p class="version-name">
                <svg aria-hidden="true" class="category-icon">
                  <use :xlink:href="`#doc-icon${i % 4}`"></use>
                </svg>
                <strong :id="`version_${component.board}`">{{ component.board_label }}</strong>
              </p>
              <div class="ag-card" v-for="(category, index) of component.categories" :key="index">
                <p class="card-title" :id="`${component.board}_${category.id}`">
                  {{ category.name }}
                  <span class="total">
                    ({{ category.systems.length }})
                  </span>
                </p>
                <div class="card-content">
                  <ul class="systems">
                    <li v-for="item of category.systems" :key="item.name">
                      <router-link
                        :to="{
                          name: 'ComponentAPIDetailIntro',
                          params: {
                            version: component.board,
                            id: item.name,
                          }
                        }">
                        {{ item.description }}
                      </router-link>
                      <p class="desc">{{ item.name }}</p>
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>
      <div class="mt20" v-else style="width: 100%; border-radius: 2px; border: 1px solid #eee; background: #FFF;">
        <table-empty empty />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import searcher from './components/searcher/index.vue';
import {
  getComponentSystemList,
} from '@/http';

const board = ref<string>('default');
const curCategoryId = ref<string>('');
const isFixed = ref<boolean>(false);
const componentList = ref([]);


const handleScrollTo = (version: any, category: any = null) => {
  console.log(category);

  const OFFSET = category ? 87 : 75;
  const categoryId = category ? `${version}_${category.id}` : `version_${version}`;
  const element = document.getElementById(categoryId);
  curCategoryId.value = categoryId;
  if (element) {
    const rect = element.getBoundingClientRect();
    const container = document.querySelector('#app .container-content') || document.documentElement || document.body;
    const top = container.scrollTop + rect.top - OFFSET;
    container.scrollTo({
      top,
      behavior: 'smooth',
    });
  }
};


const init = async () => {
  try {
    const res = await getComponentSystemList(board.value);
    componentList.value = res;
    console.log(res);
  } catch (error) {
    console.log('error', error);
  }
};
init();
</script>

<style lang="scss" scoped>
.index-wrapper {
  .banner {
    height: 160px;
    background: #3E4961;
    position: relative;
    background-image: url('/static/images/bg.png');
    background-size: center 100%;
    background-repeat: no-repeat;
    z-index: 10;
  }

  .ag-searcher-box {
    position: absolute;
    left: 50%;
    top: 50%;
    transform: translate(-50%, -50%);
  }
}

.side-nav {
  width: 260px;
  background: #fff;
  box-shadow: 0px 2px 6px 0px rgba(0, 0, 0, 0.1);
  padding: 17px 0 30px 22px;
  margin-right: 16px;
  position: relative;

  &::-webkit-scrollbar {
    width: 4px;
    background-color: lighten(#e6e9ea, 80%);
  }

  &::-webkit-scrollbar-thumb {
    height: 5px;
    border-radius: 2px;
    background-color: #e6e9ea;
  }

  &.fixed {
    top: 68px;
    position: fixed;
    overflow: auto;
  }

  .group {
    border-left: 1px solid #F0F1F5;
    position: relative;
  }

  .category-title {
    font-size: 14px;
    font-weight: 700;
    text-align: left;
    color: #63656e;
    line-height: 19px;
    margin-bottom: 10px;
    position: relative;
    display: block;
    padding-left: 40px;

    &::after {
      content: '';
      display: inline-block;
      width: 8px;
      height: 8px;
      background: #c4c6cc;
      position: absolute;
      left: -10px;
      top: 0;
      border-radius: 50%;
      border: 6px solid #FFF;
    }
  }

  .group {
    position: relative;

    .category-icon {
      width: 23px;
      height: 23px;
      position: absolute;
      left: 12px;
      top: -2px;
    }
  }

  .list {
    margin-bottom: 10px;

    >li {
      padding-left: 40px;

      &.selected {
        border-left: 1px solid #3A84FF;
        left: -1px;
        position: relative;

        a {
          color: #3A84FF;
        }
      }
    }

    a {
      font-size: 14px;
      text-align: left;
      color: #63656e;
      line-height: 36px;

      &:hover {
        color: #3A84FF;
      }
    }
  }
}

.ag-container {
  width: 1200px;
  display: flex;
  margin: 16px auto 20px auto;
  align-items: stretch;

  >.left {
    width: 260px;
    margin-right: 16px;
    position: relative;
  }

  >.right {
    flex: 1;
    height: auto;

    >div {
      height: 100%;
    }

    .intro-doc,
    .component-doc {
      height: 100%;
    }

    .version-name {
      font-size: 16px;
      font-weight: 700;
      text-align: left;
      color: #313238;
      line-height: 21px;
      padding: 10px 0 15px 0;

      svg {
        width: 20px;
        height: 20px;
        vertical-align: middle;
        margin-right: 3px;
      }

      span {
        vertical-align: middle;
      }
    }
  }
}

.ag-card {
  background: #ffffff;
  padding: 18px 16px 10px 16px;
  box-shadow: 0px 2px 6px 0px rgba(0, 0, 0, 0.1);

  .card-title {
    font-size: 14px;
    font-weight: 700;
    text-align: left;
    color: #63656e;
    line-height: 19px;

    .total {
      font-size: 14px;
      color: #979ba5;
      font-weight: normal;
    }
  }

  .card-content {
    margin-top: 20px;
  }

  &+.ag-card {
    margin-top: 16px;
  }

  .systems {
    display: flex;
    flex-wrap: wrap;

    >li {
      width: 25%;
      margin-bottom: 20px;
    }

    a {
      font-size: 14px;
      display: block;
      margin-bottom: 4px;
      color: #63656e;

      &:hover {
        color: #3a84ff;
      }
    }

    .desc {
      font-size: 12px;
      color: #C4C6CC;
    }
  }
}

.version-panel {
  margin-bottom: 20px;

  &:last-child {
    margin-bottom: 0;
  }
}

.list li {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>


