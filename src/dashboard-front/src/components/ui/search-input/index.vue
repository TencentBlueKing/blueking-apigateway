<template>
  <div class="search-input">
    <bk-input
      v-model="localValue"
      :placeholder="placeholder"
      @enter="handleEnter">
      <template slot="append">
        <bk-button theme="primary" @click="handleSearch"> {{ $t('搜索') }} </bk-button>
      </template>
    </bk-input>
  </div>
</template>

<script>
  import i18n from '@/language/i18n.js'
  export default {
    name: 'search-input',
    props: {
      value: {
        type: String,
        default: ''
      },
      placeholder: {
        type: String,
        default: i18n.t('请输入查询条件')
      }
    },
    data () {
      return {
        localValue: this.value
      }
    },
    watch: {
      value (value) {
        this.localValue = value
      },
      localValue (localValue) {
        this.$emit('input', localValue)
      }
    },
    methods: {
      handleEnter () {
        this.$emit('search', this.localValue)
      },
      handleSearch () {
        this.$emit('search', this.localValue)
      }
    }
  }
</script>

<style lang="postcss" scoped>
    .search-input {
        /deep/ .control-append-group {
            .bk-form-input {
                border-bottom-right-radius: 0;
                border-top-right-radius: 0;
                border-right: 0;
            }

            .bk-button {
                border-top-left-radius: 0;
                border-bottom-left-radius: 0;
            }

            .group-box {
                height: auto;
                border: none;
                border-radius: 0;
            }
        }
    }
</style>
