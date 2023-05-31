<template>
  <ul class="ag-component-nav">
    <li v-for="item of list" :key="item.id">
      <a :class="{ active: curSideNavId === item.id }" href="javascript: void(0);" @click="handleAnchor(item.id)">{{item.name}}</a>
    </li>
  </ul>
</template>

<script>
  import { throttle } from 'lodash'
  export default {
    props: {
      offsetTop: {
        type: Number,
        default: 60
      },
      containerId: {
        type: String,
        default: '.container-content'
      },
      list: {
        type: Array,
        default () {
          return []
        }
      }
    },
    data () {
      return {
        curSideNavId: '',
        contentHeightList: null,
        triggerFlag: false
      }
    },
    computed: {
      loading () {
        return this.$store.state.mainContentLoading
      }
    },
    watch: {
      loading (value) {
        this.$nextTick(() => {
          this.getChildrenHeigh()
        })
      },
      $route (to, from) {
        this.$nextTick(() => {
          this.getChildrenHeigh()
        })
      }
    },
    mounted () {
      this.$nextTick(() => {
        setTimeout(() => {
          this.getChildrenHeigh()
        }, 1000)
        const content = document.querySelector('.component-content')
        content.addEventListener('scroll', throttle(this.handleScroll, 100), true)

        window.addEventListener('wheel', throttle(this.handleTrolley, 500), true)
      })
    },
    beforeDestroy () {
      window.removeEventListener('wheel', this.handleTrolley, true)
      const content = document.querySelector('.component-content')
      if (content) {
        content.removeEventListener('scroll', this.handleScroll, true)
      }
    },
    methods: {
      handleAnchor (id) {
        const OFFSET = this.offsetTop
        const element = document.getElementById(id)
        this.curSideNavId = id
        this.triggerFlag = true

        if (element) {
          const rect = element.getBoundingClientRect()
          const container = document.querySelector('.component-content') || document.body
          const top = container.scrollTop + rect.top - OFFSET

          container.scrollTo({
            top: top,
            behavior: 'smooth'
          })
        }
      },
      getChildrenHeigh () {
        const container = document.querySelector('.component-content') || document.body
        const OFFSET = this.offsetTop
        const arr = []
        for (let i = 0; i < this.list.length; i++) {
          const child = document.getElementById(`${this.list[i].id}`)
          if (child) {
            const rect = child.getBoundingClientRect()
            arr.push(container.scrollTop + rect.top - OFFSET)
            // arr.push(child.offsetTop - OFFSET)
          }
        }
        this.contentHeightList = arr
      },
      handleScroll () {
        if (this.triggerFlag) {
          return
        }
        const scrollTop = document.querySelector('.component-content').scrollTop || document.documentElement.scrollTop
        if (this.contentHeightList) {
          for (let i = 0; i < this.contentHeightList.length; i++) {
            if (scrollTop >= this.contentHeightList[i] && scrollTop <= this.contentHeightList[i + 1]) {
              this.curSideNavId = this.list[i].id
            }
            if (scrollTop < this.contentHeightList[0]) {
              this.curSideNavId = this.list[0].id
            }
          }
        }
      },

      handleTrolley () {
        this.triggerFlag = false
      }
    }
  }
</script>

<style lang="postcss" scoped>
    .ag-component-nav {
        width: 160px;
        font-size: 12px;
        text-align: left;
        color: #979ba5;
        line-height: 28px;
        border-left: 1px solid #DCDEE5;

        a {
            padding-left: 16px;
            display: block;
            text-decoration: none;
            color: #63656E;

            &.active {
                color: #3A84FF;
                border-left: 1px solid #3A84FF;
                margin-left: -1px;
            }
        }
    }
</style>
