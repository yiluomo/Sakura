<template>
  <Transition name="toast">
    <div v-if="visible" class="error-toast" :class="type">
      <div class="toast-icon">
        <el-icon><WarningFilled v-if="type === 'error'" /><InfoFilled v-else /></el-icon>
      </div>
      <div class="toast-content">
        <div class="toast-title">{{ title }}</div>
        <div class="toast-message">{{ message }}</div>
      </div>
      <div class="toast-close" @click="close">
        <el-icon><Close /></el-icon>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { WarningFilled, InfoFilled, Close } from '@element-plus/icons-vue'

interface Props {
  visible: boolean
  title?: string
  message: string
  type?: 'error' | 'warning' | 'info'
  duration?: number
}

const props = withDefaults(defineProps<Props>(), {
  title: '错误',
  type: 'error',
  duration: 4000
})

const emit = defineEmits<{
  (e: 'update:visible', value: boolean): void
}>()

let timer: number | null = null

watch(() => props.visible, (newVal) => {
  if (newVal && props.duration > 0) {
    if (timer) clearTimeout(timer)
    timer = window.setTimeout(() => {
      close()
    }, props.duration)
  }
})

const close = () => {
  if (timer) {
    clearTimeout(timer)
    timer = null
  }
  emit('update:visible', false)
}
</script>

<style lang="scss" scoped>
.error-toast {
  position: fixed;
  top: 80px;
  right: 24px;
  min-width: 300px;
  max-width: 420px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  display: flex;
  align-items: flex-start;
  gap: 12px;
  z-index: 3000;
  border-left: 4px solid #f56c6c;

  &.warning {
    border-left-color: #e6a23c;
    
    .toast-icon {
      color: #e6a23c;
    }
  }

  &.info {
    border-left-color: #409eff;
    
    .toast-icon {
      color: #409eff;
    }
  }

  .toast-icon {
    font-size: 20px;
    color: #f56c6c;
    flex-shrink: 0;
    margin-top: 2px;
  }

  .toast-content {
    flex: 1;
    min-width: 0;
  }

  .toast-title {
    font-size: 15px;
    font-weight: 600;
    color: #303133;
    margin-bottom: 4px;
  }

  .toast-message {
    font-size: 14px;
    color: #606266;
    line-height: 1.5;
    word-break: break-word;
  }

  .toast-close {
    font-size: 16px;
    color: #909399;
    cursor: pointer;
    flex-shrink: 0;
    transition: color 0.2s;

    &:hover {
      color: #303133;
    }
  }
}

.toast-enter-active {
  animation: toast-in 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.toast-leave-active {
  animation: toast-out 0.25s ease-in;
}

@keyframes toast-in {
  from {
    opacity: 0;
    transform: translateX(100%) scale(0.9);
  }
  to {
    opacity: 1;
    transform: translateX(0) scale(1);
  }
}

@keyframes toast-out {
  from {
    opacity: 1;
    transform: translateX(0) scale(1);
  }
  to {
    opacity: 0;
    transform: translateX(20px) scale(0.95);
  }
}

.dark-theme .error-toast {
  background: rgba(30, 30, 30, 0.98);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);

  .toast-title {
    color: #e5eaf3;
  }

  .toast-message {
    color: #cfd3dc;
  }

  .toast-close {
    color: #909399;

    &:hover {
      color: #e5eaf3;
    }
  }
}

@media (max-width: 768px) {
  .error-toast {
    right: 16px;
    left: 16px;
    min-width: auto;
    max-width: none;
  }
}
</style>
