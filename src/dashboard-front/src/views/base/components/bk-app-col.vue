<template>
  <div>
    <bk-col :span="2">
      <div class="ag-form-label"> {{ $t('关联蓝鲸应用') }} </div>
    </bk-col>
    <bk-col :span="col">
      <div class="ag-form-content">
        <bk-popover placement="right" v-if="data.bk_app_codes && data.bk_app_codes.length">
          <p :class="['ag-field-text', { 'col-max-width': col <= 4 }]" style="margin-top: -3px;">{{data.bk_app_codes.join('; ')}}</p>
          <div slot="content" style="white-space: normal;">
            {{data.bk_app_codes.join('; ')}}
          </div>
        </bk-popover>
        <span v-else>--</span>
      </div>
    </bk-col>
  </div>
</template>
<script>
  export default {
    props: {
      data: {
        type: Object,
        default: () => {}
      },
      col: {
        type: Number,
        default: 4
      }
    }
  }
</script>
<style lang="postcss" scoped>
.col-max-width {
    max-width: 200px;
}
</style>
