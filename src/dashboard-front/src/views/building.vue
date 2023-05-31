<template>
  <div class="exception-box">
    <img src="@/images/building.png" alt="">
    <p> {{ $t('正在建设中...') }} </p>
  </div>
</template>

<script>
  export default {
    data () {
      return {}
    }
  }
</script>

<style scoped lang="postcss">
    .exception-box {
        text-align: center;
        margin: auto;
        img {
            width: 300px;
            margin-top: 150px;
        }
        p {
            font-size: 20px;
            color: #979797;
            margin: 32px 0;
            font-weight: 400;
        }
    }
</style>
