<template>
  <div class="bk-login-dialog" v-if="isShow">
    <div class="bk-login-wrapper">
      <iframe :src="iframeSrc" scrolling="no" border="0" :width="iframeWidth" :height="iframeHeight" />
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref } from 'vue';
import { ILoginData } from '@/common/auth';
/**
 * app-auth
 * @desc 统一登录
 * @example1 <app-auth type="404"></app-auth>
 */
const loginCallbackURL = ref(`${window.SITE_URL}static/login_success.html?is_ajax=1`);
const iframeSrc = ref(`${window.BK_LOGIN_URL}/?app_code=1&c_url=${loginCallbackURL.value}`);
const isShow = ref(false);
const iframeWidth = ref(400);
const iframeHeight = ref(400);

const hideLoginModal = () => {
  isShow.value = false;
};

const showLoginModal = (payload: ILoginData) => {
  const { login_plain_url, width, height } = payload;
  const version = +new Date();
  iframeSrc.value = `${login_plain_url}&ver=${version}`;
  iframeWidth.value = width || 400;
  iframeHeight.value = height || 400;
  console.log(iframeSrc.value);
  setTimeout(() => {
    isShow.value = true;
  }, 1000);
};

defineExpose({
  showLoginModal,
  hideLoginModal,
});
</script>

<style langs="scss" scoped>
.bk-login-dialog {
  position: fixed;
  left: 0;
  top: 0;
  width: 100%;
  height: 100%;
  z-index: 999999999;
  background: rgba(0, 0, 0, 0.7);
  .close-btn {
    position: absolute;
    width: 20px;
    height: 20px;
    background: #fff;
    top: -10px;
    right: -10px;
    border-radius: 50%;
    text-align: center;
    line-height: 20px;
    font-size: 13px;
    cursor: pointer;
    border: 1px solid #ddd;
    .bk-icon {
      margin-left: 1px;
    }
    &:hover {
      background-color: #3c96ff;
      color: #fff;
      border-color: #3c96ff;
    }
  }
  .close-btn {
    &:hover {
      box-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
    }
  }
  .closeBtn img {
    width: 8px;
    margin-top: 0;
    display: inline-block;
    position: relative;
    top: -1px;
  }
  .bk-login-wrapper {
    display: inline-block;
    background: #fff;
    border: 0;
    width: 400px;
    height: 400px;
    padding-right: 5px;
    margin: -225px auto auto -225px;
    top: 50%;
    left: 50%;
    position: relative;
    z-index: 10002;
    border-radius: 4px;
    iframe {
      text-align: center;
      border: none;
    }
  }
}
</style>
