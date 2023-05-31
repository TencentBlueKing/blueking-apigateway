<script>
    export default {
        name: 'code-viewer',
        template: `\
            <div class="ag-view-container">
                <div class="ap-nodata fixed" v-if="!value && !isViewerFocus && placeholder" @click="handleViewerFocus">
                    <i class="bk-table-empty-icon bk-icon icon-empty"></i>
                    <p>{{placeholder}}</p>
                </div>
                <div class="code-viewer" :style="{height: calcSize(height), width: calcSize(width)}"></div>
            </div>`,
        props: {
            value: {
                type: String,
                default: ''
            },
            placeholder: {
                type: String,
                default: ''
            },
            width: {
                type: [Number, String],
                default: 500
            },
            height: {
                type: [Number, String],
                default: 300
            },
            lang: {
                type: String,
                default: 'text'
            },
            theme: {
                type: String,
                default: 'monokai'
            },
            readOnly: {
                type: Boolean,
                default: false
            },
            fullScreen: {
                type: Boolean,
                default: false
            },
            hasError: {
                type: Boolean,
                default: false
            }
        },
        data () {
            return {
                $ace: null,
                localValue: '',
                isViewerFocus: false,
                textareEl: null,
                aceCursorEl: null
            }
        },
        watch: {
            value (newVal) {
                if (this.$ace && this.$ace.setValue && newVal !== this.localValue) {
                    this.localValue = newVal
                    this.$ace.setValue(newVal, 1)
                }
            },
            lang (newVal) {
                if (newVal) {
                    import(`brace/mode/${newVal}`).then(langModule => {
                        this.$ace.getSession().setMode(`ace/mode/${newVal}`)
                    })
                }
            },
            fullScreen () {
                this.$el.classList.toggle('ace-full-screen')
                this.$ace.resize()
            }
        },
        methods: {
            calcSize (size) {
                const _size = size.toString()

                if (_size.match(/^\d*$/)) return `${size}px`
                if (_size.match(/^[0-9]?%$/)) return _size

                return '100%'
            },
            handleViewerFocus () {
                this.isViewerFocus = true
                this.$ace.focus()
            },
            // 组合输入
            handleChineseInput () {
                // 输入中文添加类名, 三方库自定义光标隐藏光标
                const isHide = this.aceCursorEl.classList.contains('hide-cursor')
                if (!isHide) {
                    this.aceCursorEl.classList.add('hide-cursor')
                }
            },
            handleEndInput () {
                this.aceCursorEl.classList.remove('hide-cursor')
            },
            bindEvents () {
                this.textareEl = document.querySelector('.code-viewer textarea.ace_text-input')
                this.aceCursorEl = document.querySelector('.ace_content .ace_cursor')
                this.textareEl.addEventListener('compositionstart', this.handleChineseInput)
                this.textareEl.addEventListener('compositionend', this.handleEndInput)
            },
            removeEvents () {
                this.textareEl.removeEventListener('compositionstart', this.handleChineseInput)
                this.textareEl.removeEventListener('compositionend', this.handleEndInput)
                this.textareEl = null
                this.aceCursorEl = null
            }
        },
        mounted () {
            import(
                /* webpackChunkName: 'brace' */
                'brace'
            ).then(ace => {
                const el = this.$el.querySelector('.code-viewer')
                this.$ace = ace.edit(el)
                const {
                    $ace,
                    readOnly
                } = this

                let {
                    lang,
                    theme
                } = this
                const session = $ace.getSession()
                lang = lang || 'javascript'
                theme = theme || 'monokai'
                this.$ace.setFontSize(14)

                this.$emit('init', $ace)

                // require(`brace/mode/${lang}`)
                // require('brace/mode/javascript')
                // require('brace/mode/json')
                // require('brace/mode/yaml')
                // require(`brace/theme/${theme}`)
                import(
                    /* webpackChunkName: 'brace-[request]' */
                    `brace/mode/${lang}`
                ).then(() => {
                    require(`brace/theme/${theme}`)
                    session.setMode(`ace/mode/${lang}`) // 配置语言
                    $ace.setTheme(`ace/theme/${theme}`) // 配置主题
                    session.setUseWrapMode(true) // 自动换行
                    $ace.setValue(this.value, 1) // 设置默认内容
                    $ace.setReadOnly(readOnly) // 设置是否为只读模式
                    $ace.setShowPrintMargin(false) // 不显示打印边距

                    // 绑定输入事件回调
                    $ace.on('change', ($editor, $fn) => {
                        const content = $ace.getValue()
                        if (!this.aceCursorEl) {
                            this.aceCursorEl = document.querySelector('.ace_content .ace_cursor')
                        }
                        this.localValue = content
                        this.$emit('update:hasError', !content)
                        this.$emit('input', content, $editor, $fn)
                    })

                    $ace.on('blur', ($editor, $fn) => {
                        const content = $ace.getValue()
                        this.isViewerFocus = false
                        this.removeEvents()
                        this.$emit('update:hasError', !content)
                        this.$emit('blur', content, $editor, $fn)
                    })

                    $ace.on('focus', ($editor, $fn) => {
                        if (!this.textareEl) {
                            this.bindEvents()
                        }
                        const content = $ace.getValue()
                        this.isViewerFocus = true
                        this.$emit('focus', content, $editor, $fn)
                    })

                    session.on('changeAnnotation', (args, instance) => {
                        const annotations = instance.$annotations
                        if (annotations && annotations.length) {
                            this.$emit('change-annotation', annotations)
                        }
                    })
                })
            })
        }
    }
</script>

<style scoped>
    .ag-view-container {
        position: relative;
    }
    
</style>
<style>
    /* 第三方库样式覆盖 */
    .ace_text-input {
        background: transparent !important;
        padding: 0 !important;
        margin: 0 !important;
        height: 1em !important;
    }
    /* 输入中文时隐藏光标 */
    .ace-monokai .ace_cursor.hide-cursor {
        color: transparent;
    }
</style>
