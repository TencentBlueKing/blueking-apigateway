<template>
  <div class="ag-keyer">
    <div class="keyer-label">{{label}}</div>
    <div class="keyer-content">
      <ul class="key-values">
        <li :ref="`item-${index}`" :class="{ focus: item.isFocus }" v-for="(item, index) of keyValueList" :key="item.key" @click="handleEdit(item, index)">
          <span class="text">{{item.key}} : {{item.value}}</span>
          <input :id="`input-${index}`" class="input" type="text" name="" v-model="item.keyValue" @keyup.enter="handleConfirm(item)" @blur="handleBlur(item, index)" @click.stop.prevent="handleFocus">
          <i class="apigateway-icon icon-ag-minus-circle-shape delete-icon" @click.stop.prevent="handleDelete(item, index)"></i>
        </li>
      </ul>
      <bk-button class="fl" icon="icon-plus" type="button" @click="handleAddKeyValue">
      </bk-button>
    </div>
  </div>
</template>

<script>
  export default {
    name: 'app-exception',
    props: {
      value: {
        type: Object,
        defaul () {
          return {}
        }
      },
      label: {
        type: String,
        default: this.$t('标签')
      }
    },
    data () {
      return {
        keyValueList: []
      }
    },
    watch: {
      value (val) {
        this.initKeyValueList()
      }
    },
    created () {
      this.initKeyValueList()
    },
    methods: {
      initKeyValueList () {
        if (JSON.stringify(this.value) !== '{}') {
          this.keyValueList = []
          for (const key in this.value) {
            this.keyValueList.push({
              isFocus: false,
              key: key,
              value: this.value[key],
              keyValue: `${key}:${this.value[key]}`
            })
          }
        }
      },
      handleAddKeyValue () {
        this.keyValueList.push({
          isFocus: true,
          key: '',
          value: '',
          keyValue: ''
        })
        this.$nextTick(() => {
          const index = this.keyValueList.length - 1
          const itemDom = this.$refs[`item-${index}`][0]
          if (itemDom) {
            const input = document.getElementById(`input-${index}`)
            input.focus()
          }
        })
      },

      handleConfirm (item) {
        const values = item.keyValue.split(':')
        const keyReg = /^[a-zA-Z_][a-zA-Z0-9_]*$/g

        if (values[0]) {
          if (keyReg.test(values[0])) {
            item.key = values[0].trim()
          } else {
            this.$bkMessage({
              theme: 'error',
              message: this.$t('KEY值以字母、下划线(_)开头，包含字母、数字、下划线(_)')
            })
            return false
          }
        }

        if (values[1]) {
          item.value = values[1].trim()
        }
                
        item.isFocus = false
        this.update()
      },

      handleDelete (item, index) {
        this.keyValueList.splice(index, 1)
        this.update()
      },

      handleBlur (item, index) {
        // if (item.keyValue.trim() === '') {
        //     this.keyValueList.splice(index, 1)
        // } else {
        //     this.handleConfirm(item)
        // }
      },

      handleEdit (item, index) {
        item.isFocus = true
        this.$nextTick(() => {
          const itemDom = this.$refs[`item-${index}`][0]
          if (itemDom) {
            const input = document.getElementById(`input-${index}`)
            input.focus()
            input.select()
          }
        })
      },

      handleFocus () {},

      update () {
        const data = {}
        this.keyValueList.forEach(item => {
          data[item.key] = item.value
        })
        this.$emit('input', data)
      }
    }
  }
</script>

<style scoped>
    .ag-keyer {
        display: flex;
        .keyer-label {
            width: auto;
            font-size: 14px;
            color: #313238;
            margin-right: 10px;
        }
        .keyer-content {
            flex: 1;
        }

        .key-values {
            float: left;

            li {
                border: 1px solid #DCDEE5;
                border-radius: 2px;
                height: 32px;
                line-height: 30px;
                display: inline-block;
                padding: 0 10px;
                color: #63656E;
                font-size: 12px;
                text-align: center;
                position: relative;
                cursor: pointer;
                float: left;
                margin-right: 10px;

                &:hover {
                    .delete-icon {
                        display: inline-block;
                    }
                }

                &.focus {
                    padding: 0;
                    .text {
                        display: none;
                    }

                    .input {
                        display: inline-block;
                    }

                    .delete-icon {
                        /*display: none !important;*/
                    }
                }
            }

            .input {
                outline: none;
                border: none;
                height: 30px;
                width: 80px;
                display: none;
                padding: 0 5px;
            }

            .delete-icon {
                position: absolute;
                font-size: 14px;
                color: #EA3636;
                right: -6px;
                top: -6px;
                cursor: pointer;
                display: none;
            }
        }
    }
</style>
