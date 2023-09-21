<script setup lang="ts">
import { TreeApplicationShape } from 'bkui-vue/lib/icon';
import TableDemo from '@/components/table-demo.vue';
import UserInfo from '@/components/user-info.vue';
</script>

<template>
  <bk-navigation
    class="navigation-demo-content"
    navigation-type="left-right"
    side-title="游戏平台"
    :default-open="true"
  >
    <template #menu>
      <bk-menu
        :opened-keys="['光子']"
        active-key="和平精英"
      >
        <bk-menu-item key="QQ音乐">
          QQ音乐
        </bk-menu-item>
        <bk-menu-group name="光子">
          <bk-menu-item key="和平精英">
            和平精英
          </bk-menu-item>
          <bk-menu-item key="黎明觉醒">
            黎明觉醒
          </bk-menu-item>
          <bk-menu-item key="自由幻想">
            自由幻想
          </bk-menu-item>
          <bk-menu-item key="欢乐斗地主">
            欢乐斗地主
          </bk-menu-item>
        </bk-menu-group>
      </bk-menu>
    </template>
    <template #side-icon>
      <tree-application-shape />
    </template>
    <div class="content-demo">
      <table-demo />
    </div>
    <template #header>
      <div
        class="header-demo"
      >
        数据统计
        <user-info />
      </div>
    </template>
  </bk-navigation>
</template>

<style lang="scss" scoped>
.navigation-demo-content {

  .content-demo {
    background: #fff;
    font-size: 24px;
    height: calc(100% - 20px);
    margin-bottom: 20px;
  }

  .header-demo {
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 20px;
  }
}
</style>
