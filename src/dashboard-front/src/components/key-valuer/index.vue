<template>
  <div class="bk-keyer">
    <div class="biz-keys-list mb10">
      <div class="label" v-if="label">{{label}}</div>
      <div class="values">
        <template v-if="list.length">
          <div class="biz-key-item" v-for="(keyItem, index) in list" :key="index">
            <bk-form :ref="`key-${index}`" style="width: 190px; display: inline-block;" :label-width="0" :model="keyItem">
              <bk-form-item :rules="rules.key" :property="'key'" :error-display-type="'normal'">
                <bk-input
                  type="text"
                  :readonly="keyReadonly"
                  :placeholder="keyPlaceholder || $t('键')"
                  v-model="keyItem.key"
                  @keyup="valueChange">
                </bk-input>
              </bk-form-item>
            </bk-form>

            <span class="operator">:</span>

            <bk-form
              class="mr5"
              :ref="`value-${index}`"
              style="width: 190px; display: inline-block;"
              :label-width="0"
              :model="keyItem">
              <bk-form-item :rules="rules.value" :property="'value'" :error-display-type="'normal'">
                <bk-input
                  type="text"
                  :placeholder="valuePlaceholder || $t('值')"
                  v-model="keyItem.value"
                  @keyup="valueChange">
                </bk-input>
              </bk-form-item>
            </bk-form>
            <template v-if="buttons">
              <bk-button class="mr5 ag-icon-btn" v-if="buttons.includes('add')" @click.stop.prevent="addKey">
                <i class="apigateway-icon icon-ag-plus"></i>
              </bk-button>
              <bk-button class="ag-icon-btn" v-if="buttons.includes('remove')" @click.stop.prevent="removeKey(keyItem, index)">
                <i class="apigateway-icon icon-ag-minus"></i>
              </bk-button>
            </template>
          </div>
        </template>
        <div v-else>
          <bk-button class="ag-icon-btn" v-if="buttons && buttons.includes('add')" @click.stop.prevent="addKey">
            <i class="apigateway-icon icon-ag-plus"></i>
          </bk-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
  import { bkForm, bkFormItem, bkInput, bkButton } from 'bk-magic-vue'

  export default {
    components: {
      bkForm,
      bkFormItem,
      bkInput,
      bkButton
    },
    props: {
      value: {
        type: Object,
        default () {
          return {}
        }
      },
      tip: {
        type: String,
        default: ''
      },
      keyPlaceholder: {
        type: String,
        default: ''
      },
      keyReadonly: {
        type: Boolean
      },
      keyRegexRule: {
        type: Object,
        default () {
          return {
            regex: /^[a-zA-Z0-9-]+$/,
            message: this.$t('键由英文字母、数字、连接符（-）组成')
          }
        }
      },
      valuePlaceholder: {
        type: String,
        default: ''
      },
      label: {
        type: String,
        default: ''
      },
      buttons: {
        type: [Array, Boolean],
        default () {
          return ['add', 'remove']
        }
      }
    },
    data () {
      return {
        itemIndex: 0,
        list: [],
        rules: {
          key: [
            {
              required: true,
              message: this.$t('必填项'),
              trigger: 'blur'
            },
            {
              regex: this.keyRegexRule.regex,
              message: this.keyRegexRule.message,
              trigger: 'blur'
            },
            {
              validator: (value) => {
                const matches = this.list.filter(item => value && (item.key === value))
                if (matches.length < 2) {
                  return true
                }
                return false
              },
              message: this.$t('键不允许重复'),
              trigger: 'blur'
            }
          ],

          value: [
            {
              required: true,
              message: this.$t('必填项'),
              trigger: 'blur'
            }
          ]
        }
      }
    },
    watch: {
      value: {
        immediate: true,
        handler (value) {
          this.list.splice(0, this.list.length, ...[])

          for (const key in value) {
            this.list.push({
              id: this.itemIndex,
              key: key,
              value: value[key]
            })
            this.itemIndex++
          }
        }
      }
    },
    methods: {
      addKey () {
        const params = {
          id: this.itemIndex,
          key: '',
          value: ''
        }
        this.itemIndex++
        this.list.push(params)
        const obj = this.getKeyObject()
        this.$emit('change', this.list, obj)
        this.$emit('toggle-height')
      },
      removeKey (item, index) {
        this.list.splice(index, 1)
        const obj = this.getKeyObject()
        this.validate()
        this.$emit('input', obj)
        this.$emit('change', this.list, obj)
        // 触发监听
        this.$emit('toggle-height')
      },
      valueChange () {
        this.$nextTick(() => {
          const obj = this.getKeyObject()
          this.$emit('input', obj)
          this.$emit('change', this.list, obj)
        })
      },
      getValue () {
        return this.getKeyObject()
      },
      pasteKey (item, event) {
        const cache = item.key
        const clipboard = event.clipboardData
        const text = clipboard.getData('Text')

        if (text && text.indexOf('=') > -1) {
          this.paste(event)
          item.key = cache
          setTimeout(() => {
            item.key = cache
          }, 0)
        }
      },
      paste (event) {
        const clipboard = event.clipboardData
        const text = clipboard.getData('Text')
        const items = text.split('\n')
        items.forEach(item => {
          if (item.indexOf('=') > -1) {
            const arr = item.split('=')
            this.list.push({
              key: arr[0],
              value: arr[1]
            })
          }
        })
        setTimeout(() => {
          this.formatData()
        }, 10)

        return false
      },
      formatData () {
        // 去掉空值
        if (this.list.length) {
          const results = []
          const keyObj = {}
          const length = this.list.length
          this.list.forEach((item, i) => {
            if (item.key || item.value) {
              if (!keyObj[item.key]) {
                results.push(item)
                keyObj[item.key] = true
              }
            }
          })
          const patchLength = results.length - length
          if (patchLength > 0) {
            for (let i = 0; i < patchLength; i++) {
              results.push({
                key: '',
                value: ''
              })
            }
          }
          this.list.splice(0, this.list.length, ...results)
          this.$emit('change', this.list)
        }
      },
      getList () {
        return this.list.filter(item => item.key || item.value)
      },
      checkRepeat () {
        const keys = this.list.filter(item => item.key).map(item => {
          return item.key
        })
        const uniqueKeys = [...new Set(keys)]
        if (uniqueKeys.length < keys.length) {
          this.validate()
          return false
        }
        return true
      },
      getKeyObject () {
        const results = this.list.filter(item => item.key || item.value)
        if (results.length === 0) {
          return {}
        } else {
          const obj = {}
          results.forEach(item => {
            obj[item.key] = item.value
          })
          return obj
        }
      },
      validate () {
        this.list.forEach((item, index) => {
          this.$refs[`key-${index}`][0].validate()
          this.$refs[`value-${index}`][0].validate()
        })
      }
    }
  }
</script>

<style scoped lang="postcss">
    @import '../../css/variable.css';

    .bk-keyer {
        margin-bottom: 10px;
    }
    .biz-key-item {
        display: flex;
        width: 100%;
        margin-bottom: 5px;

        /deep/ .bk-label {
            display: none;
        }
    }
    .biz-keys-list {
        display: flex;

        .label {
            font-size: 14px;
            font-weight: bold;
            color: #313238;
            width: 50px;
        }
        .operator {
            width: 20px;
            font-size: 14px;
            font-weight: bold;
            text-align: center;
            display: inline-block;
            color: #313238;
            vertical-align: middle;
        }
    }
    .biz-keys-list .action-btn {
        width: auto;
        padding: 0;
        margin-left: 5px;
        &.disabled {
            cursor: default;
            color: #ddd !important;
            border-color: #ddd !important;
            .bk-icon {
                color: #ddd !important;
                border-color: #ddd !important;
            }
        }
        &:hover {
            color: $primaryColor;
            border-color: $primaryColor;
            .bk-icon {
                color: $primaryColor;
                border-color: $primaryColor;
            }
        }
    }
    .is-danger {
        color: $dangerColor;
    }
    .bk-input-box {
        display: inline-block;
        position: relative;
    }
</style>
