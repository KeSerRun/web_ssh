<!--
  项目根组件
  -----------
  使用 <router-view> 渲染当前路由对应的页面组件。
  通过 Vue Router 的路由级过渡动画实现页面切换效果。
-->
<script setup>
</script>

<template>
  <router-view v-slot="{ Component, route }">
    <transition :name="route.meta.transition || 'page-fade'" mode="out-in">
      <component :is="Component" />
    </transition>
  </router-view>
</template>

<style scoped>
/* scoped 中的所有样式仅作用于当前组件 */
</style>
