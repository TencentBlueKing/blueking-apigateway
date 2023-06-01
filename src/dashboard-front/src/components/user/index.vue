<template>
  <div>
    <blueking-user-selector
      class="cmdb-form-objuser"
      ref="userSelector"
      :empty-text="$t('无匹配人员')"
      :placeholder="$t('请输入用户')"
      display-list-tips
      :multiple="multiple"
      v-bind="props"
      v-model="localValue"
      fast-clear
      v-if="GLOBAL_CONFIG.USERS_LIST_URL"
      @focus="$emit('focus')"
      @blur="$emit('blur')">
    </blueking-user-selector>
    <bk-member-selector
      v-else
      v-model="localValue"
      :max-data="maxData"
      ref="member_selector">
    </bk-member-selector>
  </div>
</template>

<script>
  import BluekingUserSelector from '@blueking/user-selector'
  export default {
    name: '',
    components: {
      BluekingUserSelector,
      'bk-member-selector': () => {
        return import('./member-selector/member-selector.vue')
      }
    },
    props: {
      value: {
        type: Array,
        default () {
          return []
        }
      },
      maxData: {
        type: Number,
        default: -1
      }
    },
    computed: {
      api () {
        return this.GLOBAL_CONFIG.USERS_LIST_URL
      },
      multiple () {
        return this.maxData !== 1
      },
      localValue: {
        get () {
          return (this.value && this.value.length) ? this.value : []
        },
        set (val) {
          this.$emit('input', val)
          this.$nextTick(() => {
            this.$emit('change', this.value, val.toString)
          })
        }
      },
      props () {
        const props = { ...this.$attrs }
        if (this.api) {
          props.api = this.api
        } else {
          props.fuzzySearchMethod = this.fuzzySearchMethod
          props.exactSearchMethod = this.exactSearchMethod
          props.pasteValidator = this.pasteValidator
        }
        return props
      }
    },
    methods: {
      focus () {
        this.$refs.userSelector.focus()
      },
      handleBlur () {
        this.$refs.userSelector.handleBlur()
      },
      async fuzzySearchMethod (keyword, page = 1) {
        const users = await this.$http.get(this.api, {
          params: {
            fuzzy_lookups: keyword
          },
          config: {
            cancelPrevious: true
          }
        })
        return {
          next: false,
          results: users.map(user => ({
            username: user.english_name,
            display_name: user.chinese_name
          }))
        }
      },
      exactSearchMethod (usernames) {
        const isBatch = Array.isArray(usernames)
        return Promise.resolve(isBatch ? usernames.map(username => ({ username })) : { username: usernames })
      },
      pasteValidator (usernames) {
        return Promise.resolve(usernames)
      }
    }
  }
</script>

<style lang="postcss">
    .cmdb-form-objuser {
        width: 100%;
        vertical-align: middle;
    }
</style>
