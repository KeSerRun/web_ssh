<!--
  项目根组件
  -----------
  全局 ConfigProvider 提供中文本地化，所有 Ant Design 组件默认显示中文。
-->
<template>
  <a-config-provider :locale="zhCN">
    <router-view v-slot="{ Component, route }">
      <transition :name="route.meta.transition || 'page-fade'">
        <component :is="Component" />
      </transition>
    </router-view>
  </a-config-provider>
</template>

<script setup>
import zhCN from 'ant-design-vue/es/locale/zh_CN'
</script>
