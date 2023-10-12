<template>
  <div class="navigation-main">
    <bk-navigation
      class="navigation-main-content"
      :default-open="collapse"
      :navigation-type="navigationType"
      @toggle="handleCollapse"
    >
      <template #menu>
        <bk-menu
          :collapse="collapse"
          :opened-keys="['环境管理', '内容']"
          active-key="资源配置"
        >
          <bk-submenu
            key="环境管理"
            title="环境管理"
          >
            <bk-menu-item key="资源配置">
              资源配置
            </bk-menu-item>
            <bk-menu-item key="腾讯云">
              腾讯云
            </bk-menu-item>
            <bk-menu-item key="微众银行">
              微众银行
            </bk-menu-item>
            <bk-menu-item key="腾讯体育">
              腾讯体育
            </bk-menu-item>
            <bk-menu-item key="腾讯看点">
              腾讯看点
            </bk-menu-item>
          </bk-submenu>
          <bk-submenu
            key="内容"
            title="内容"
          >
            <bk-menu-item key="腾讯影业">
              腾讯影业
            </bk-menu-item>
            <bk-menu-item key="腾讯新闻">
              腾讯新闻
            </bk-menu-item>
            <bk-menu-item key="腾讯动漫">
              腾讯动漫
            </bk-menu-item>
            <bk-menu-item key="阅文集团">
              阅文集团
            </bk-menu-item>
            <bk-menu-item key="腾讯电竞">
              腾讯电竞
            </bk-menu-item>
          </bk-submenu>
        </bk-menu>
      </template>
      <template #side-icon>
        test
      </template>
      <div class="content-demo">
        这里填写内容
      </div>
      <template #header>
        <div
          class="header"
        >
          这里是头部导航
        </div>
      </template>
    </bk-navigation>
  </div>
</template>

<script setup>
import { ref } from 'vue';
const collapse = ref(true);
const navigationType = ref('left-right');
const handleCollapse = (v) => {
  collapse.value = !v;
};
</script>
<style lang="scss" scoped>
.navigation-main {
  height: calc(100vh - 52px);
  &-radio {
    margin: 10px 0 20px 0;
  }

  :deep(.navigation-nav) {
      .nav-slider{
        background: #fff !important;
      }
      .bk-menu{
        background: #fff !important;
        .bk-menu-item{
          color: rgb(99, 101, 110);
          .item-icon{
            .default-icon{
              background-color: rgb(197, 199, 205);
            }
          }
        }
        .bk-menu-item.is-active {
          color: rgb(58, 132, 255);
          background: rgb(225, 236, 255);
          .item-icon{
            .default-icon{
              background-color: rgb(58, 132, 255);
            }
          }
        }
      }
      .submenu-header-content{
        color: rgb(99, 101, 110);
      }
      .bk-menu-submenu.is-opened {
        background: #fff !important;
      }
    }

  &-content {
    border: 1px solid #ddd;

    .content-demo {
      font-size: 24px;
    }

    .header {
      margin-right: auto;
      color: #313238;
      font-size: 16px;
    }
  }
}
</style>
