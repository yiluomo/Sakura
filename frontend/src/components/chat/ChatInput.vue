<template>
  <div class="chat-input">
    <div class="input-container">
      <el-input
        v-model="inputMessage"
        type="textarea"
        :rows="1"
        :autosize="{ minRows: 1, maxRows: 4 }"
        placeholder="输入消息... (Ctrl+Enter 发送)"
        :disabled="isLoading"
        @keydown="handleKeyDown"
        @input="handleInput"
        resize="none"
      />
      
      <div class="input-actions">
        <el-button
          type="primary"
          :loading="isLoading"
          :disabled="!inputMessage.trim()"
          @click="sendMessage"
        >
          <el-icon><Promotion /></el-icon>
          发送
        </el-button>
      </div>
    </div>
    
    <div class="input-footer">
      <div class="input-tips">
        <span>按 Ctrl+Enter 快速发送</span>
      </div>
      <div class="input-stats">
        <span>{{ inputMessage.length }}/2000</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Promotion } from '@element-plus/icons-vue'

interface Props {
  isLoading?: boolean
  maxLength?: number
}

interface Emits {
  (e: 'send', message: string): void
}

const props = withDefaults(defineProps<Props>(), {
  isLoading: false,
  maxLength: 2000,
})

const emit = defineEmits<Emits>()

const inputMessage = ref('')

const isOverLimit = computed(() => inputMessage.value.length > props.maxLength)

const handleKeyDown = (event: KeyboardEvent) => {
  if (event.key === 'Enter' && event.ctrlKey) {
    event.preventDefault()
    attemptSend()
  } else if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
  }
}

const handleInput = () => {
  if (isOverLimit.value) {
    inputMessage.value = inputMessage.value.slice(0, props.maxLength)
  }
}

const attemptSend = () => {
  if (inputMessage.value.trim() && !props.isLoading) {
    sendMessage()
  }
}

const sendMessage = () => {
  const message = inputMessage.value.trim()
  if (message && !props.isLoading) {
    emit('send', message)
    inputMessage.value = ''
  }
}

watch(() => props.isLoading, (newVal) => {
  if (!newVal) {
    inputMessage.value = ''
  }
})
</script>

<style lang="scss" scoped>
.chat-input {
  border-top: 1px solid var(--el-border-color-lighter);
  padding: 16px;
  background-color: var(--el-bg-color);
}

.input-container {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

:deep(.el-textarea) {
  flex: 1;

  .el-textarea__inner {
    border-radius: 8px;
    border: 1px solid var(--el-border-color);
    transition: all 0.2s ease;

    &:focus {
      border-color: var(--el-color-primary);
      box-shadow: 0 0 0 2px rgba(var(--el-color-primary-rgb), 0.1);
    }

    &:disabled {
      background-color: var(--el-bg-color-page);
      cursor: not-allowed;
    }
  }
}

.input-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.input-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.input-tips {
  display: flex;
  align-items: center;
  gap: 4px;
}

.input-stats {
  font-weight: 500;

  &.over-limit {
    color: var(--el-color-danger);
  }
}

.dark-theme {
  .chat-input {
    background-color: var(--el-bg-color-overlay);
  }

  :deep(.el-textarea__inner) {
    background-color: var(--el-bg-color);
    color: var(--el-text-color-primary);
  }
}
</style>
