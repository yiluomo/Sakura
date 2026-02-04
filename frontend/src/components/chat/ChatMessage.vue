<template>
  <div class="chat-message" :class="`message-${message.role}`">
    <div class="message-avatar">
      <el-avatar v-if="message.role === 'user'" :size="40" :icon="User" />
      <el-avatar v-else :size="40" :src="sakuraAvatar" />
    </div>
    
    <div class="message-content">
      <div class="message-header">
        <span class="message-role">{{ message.role === 'user' ? '你' : '八重樱' }}</span>
        <span class="message-time">{{ formatTime(message.timestamp) }}</span>
      </div>
      
      <div class="message-body">
        <div class="message-text" :class="{ 'text-collapsed': isCollapsed && isLongMessage }">
          {{ message.content }}
        </div>
        
        <div v-if="isLongMessage" class="message-toggle" @click="isCollapsed = !isCollapsed">
          <el-icon>
            <component :is="isCollapsed ? ArrowDown : ArrowUp" />
          </el-icon>
          <span>{{ isCollapsed ? '展开' : '收起' }}</span>
        </div>
      </div>
      
      <div v-if="message.error" class="message-error">
        <el-icon><Warning /></el-icon>
        <span>{{ message.error }}</span>
      </div>
      
      <div class="message-actions">
        <el-button size="small" text @click="copyMessage">
          <el-icon><CopyDocument /></el-icon>
        </el-button>
        <el-button v-if="message.role === 'user'" size="small" text @click="$emit('retry', message.id)">
          <el-icon><Refresh /></el-icon>
        </el-button>
        <el-button size="small" text @click="$emit('delete', message.id)">
          <el-icon><Delete /></el-icon>
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { User, ArrowDown, ArrowUp, CopyDocument, Refresh, Delete, Warning } from '@element-plus/icons-vue'
import type { Message } from '@/types'
import sakuraAvatar from '@/asserts/img/sakura_avatar.jpeg'

interface Props {
  message: Message
}

interface Emits {
  (e: 'retry', id: string): void
  (e: 'delete', id: string): void
}

const props = defineProps<Props>()
defineEmits<Emits>()

const isCollapsed = ref(false)

const isLongMessage = computed(() => props.message.content.length > 200)

const formatTime = (date: Date) => {
  const now = new Date()
  const messageDate = new Date(date)
  const isToday = now.toDateString() === messageDate.toDateString()
  
  if (isToday) {
    // 今天的消息只显示时间
    return new Intl.DateTimeFormat('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
    }).format(messageDate)
  } else {
    // 其他日期显示完整日期时间
    return new Intl.DateTimeFormat('zh-CN', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    }).format(messageDate)
  }
}

const copyMessage = async () => {
  try {
    await navigator.clipboard.writeText(props.message.content)
    ElMessage.success('已复制到剪贴板')
  } catch (error) {
    ElMessage.error('复制失败')
  }
}
</script>

<style lang="scss" scoped>
.chat-message {
  display: flex;
  gap: 12px;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 8px;
  transition: all 0.2s ease;

  &:hover {
    background-color: var(--el-bg-color-page);
  }

  &.message-user {
    flex-direction: row-reverse;

    .message-content {
      align-items: flex-end;
    }
  }
}

.message-avatar {
  flex-shrink: 0;
}

.message-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-width: 70%;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.message-role {
  font-weight: 600;
}

.message-body {
  background-color: var(--el-bg-color);
  border-radius: 8px;
  padding: 12px;
  border: 1px solid var(--el-border-color-lighter);
}

.message-text {
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;

  &.text-collapsed {
    max-height: 100px;
    overflow: hidden;
    position: relative;

    &::after {
      content: '';
      position: absolute;
      bottom: 0;
      left: 0;
      right: 0;
      height: 20px;
      background: linear-gradient(transparent, var(--el-bg-color));
    }
  }
}

.message-toggle {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 8px;
  color: var(--el-color-primary);
  cursor: pointer;
  font-size: 12px;

  &:hover {
    opacity: 0.8;
  }
}

.message-error {
  display: flex;
  align-items: center;
  gap: 4px;
  color: var(--el-color-danger);
  font-size: 12px;
  margin-top: 4px;
}

.message-actions {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s ease;

  .chat-message:hover & {
    opacity: 1;
  }
}

.dark-theme {
  .message-body {
    background-color: var(--el-bg-color-overlay);
    border-color: var(--el-border-color);
  }
}
</style>
