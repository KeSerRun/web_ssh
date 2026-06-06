<template>
  <div class="base-upload">
    <!-- 拖拽上传区域 -->
    <a-upload-dragger
      v-model:fileList="fileList"
      name="file"
      :multiple="true"
      :before-upload="beforeUpload"
      class="upload-dragger"
    >
      <p class="upload-icon">
        <InboxOutlined />
      </p>
      <p class="upload-text">点击或拖拽文件到此区域上传</p>
      <p class="upload-hint">
        支持单个或批量上传，请勿上传敏感数据
      </p>
    </a-upload-dragger>

    <!-- 已选文件列表 -->
    <div v-if="fileList.length" class="upload-file-list">
      <div
        v-for="file in fileList"
        :key="file.uid"
        class="upload-file-item"
      >
        <span class="file-name">
          <PaperClipOutlined /> {{ file.name }}
        </span>
        <span class="file-remove" @click="removeFile(file.uid)">
          <DeleteOutlined /> 移除
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { InboxOutlined, PaperClipOutlined, DeleteOutlined } from '@ant-design/icons-vue'

const fileList = defineModel('fileList', { default: [] })
defineProps({ beforeUpload: Function })

const removeFile = (uid) => {
  const idx = fileList.value.findIndex(f => f.uid === uid)
  if (idx > -1) fileList.value.splice(idx, 1)
}
</script>

<style scoped>
.base-upload {
  /* container */
}

.upload-dragger {
  border-radius: var(--radius-md) !important;
  border: 2px dashed var(--color-border) !important;
  transition: border-color var(--transition-fast);
}

.upload-dragger:hover {
  border-color: var(--color-primary) !important;
  background: var(--color-primary-bg) !important;
}

.upload-icon {
  font-size: 40px;
  color: var(--color-primary);
  margin-bottom: var(--space-sm);
}

.upload-text {
  font-size: var(--font-size-md);
  color: var(--color-text-primary);
  margin-bottom: var(--space-xs);
}

.upload-hint {
  font-size: var(--font-size-sm);
  color: var(--color-text-tertiary);
}

/* 已选文件列表 */
.upload-file-list {
  margin-top: var(--space-md);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.upload-file-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-sm) var(--space-md);
  border-bottom: 1px solid var(--color-border-light);
  transition: background var(--transition-fast);
}

.upload-file-item:hover {
  background: var(--color-primary-bg);
}

.file-name {
  color: var(--color-text-primary);
  cursor: default;
  font-size: var(--font-size-base);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

.file-remove {
  color: var(--color-text-tertiary);
  cursor: pointer;
  font-size: var(--font-size-sm);
  flex-shrink: 0;
  transition: color var(--transition-fast);
}

.file-remove:hover {
  color: var(--color-error);
}
</style>
