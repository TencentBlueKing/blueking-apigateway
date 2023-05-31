<template>
  <div class="bk-breadcrumb-item">
    <span
      :class="['bk-breadcrumb-item-inner', to ? 'is-link' : '']"
      ref="link"
      role="link">
      <slot></slot>
    </span>
    <i v-if="separatorClass" class="bk-breadcrumb-separator" :class="separatorClass"></i>
    <span v-else class="bk-breadcrumb-separator" role="presentation">{{separator}}</span>
  </div>
</template>
<script>
  export default {
    name: 'bk-breadcrumb-item',
    props: {
      to: {
        type: Object,
        default: () => null
      },
      replace: {
        type: Boolean,
        default: false
      }
    },
    data () {
      return {
        separator: '',
        separatorClass: ''
      }
    },

    inject: ['bkBreadcrumb'],

    mounted () {
      this.separator = this.bkBreadcrumb.separator
      this.separatorClass = this.bkBreadcrumb.separatorClass
      const link = this.$refs.link
      link.setAttribute('role', 'link')
      link.addEventListener('click', _ => {
        const { to, $router } = this
        if (!to || !$router) return
        this.replace ? $router.replace(to) : $router.push(to)
      })
    }
  }
</script>
