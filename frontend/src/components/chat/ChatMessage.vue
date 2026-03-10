<template>
  <div class="chat-message" :class="`message-${message.role}`">
    <div class="message-avatar">
      <!-- <el-avatar v-if="message.role === 'user'" :size="40" :icon="User" /> -->
      <el-avatar v-if="message.role !== 'user'"  :src="sakuraAvatar" />
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
      
      <!-- 情绪图标（仅 sakura 消息显示） -->
      <div v-if="message.role === 'sakura' && message.emotion" class="emotion-indicator">
        <el-tooltip :content="emotionTooltip" placement="top">
          <span class="emotion-icon">{{ emotionIcon }}</span>
        </el-tooltip>
      </div>
      
      <!-- 语音按钮 + 常规操作 -->
      <div class="message-actions">
        <!-- 常驻语音按钮：仅助手消息显示 -->
        <button
          v-if="message.role === 'sakura'"
          class="voice-btn"
          :class="{ playing: isPlaying, loading: isTtsLoading }"
          @click="handleVoice"
          :title="isPlaying ? '停止播放' : '播放语音'"
        >
          <span v-if="isTtsLoading" class="voice-icon">⏳</span>
          <span v-else-if="isPlaying" class="voice-icon">🔊</span>
          <span v-else class="voice-icon">🔈</span>
        </button>
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
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { User, ArrowDown, ArrowUp, CopyDocument, Refresh, Delete, Warning } from '@element-plus/icons-vue'
import type { Message } from '@/types'
import { chatApi } from '@/api/chat'
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

// 内部维护一份可变的 audio_url（允许按需调接口后回写）
const localAudioUrl = ref<string | null>(props.message.audio_url ?? null)

// 监听 props 变化（讨论列表刷新时同步）
watch(() => props.message.audio_url, (val) => {
  localAudioUrl.value = val ?? null
})

const isPlaying    = ref(false)
const isTtsLoading = ref(false)
let   currentAudio: HTMLAudioElement | null = null

/**
 * 点击语音按钮：
 * - 正在播放 → 停止
 * - 有缓存 → 直接播放
 * - 无缓存 → 调接口生成再播放
 */
const handleVoice = async () => {
  // 当前正在播放 → 停止
  if (isPlaying.value && currentAudio) {
    currentAudio.pause()
    currentAudio = null
    isPlaying.value = false
    return
  }

  // 尝试获取音频 URL
  let url = localAudioUrl.value

  if (!url) {
    // 无缓存 → 调接接口生成
    isTtsLoading.value = true
    try {
      url = await chatApi.generateTts(props.message.content)
      if (url) localAudioUrl.value = url   // 回写到本地，下次直接播放
    } catch (e: any) {
      console.warn('[TTS] 生成失败', e)
      ElMessage.warning({
        message: e.message || '语音合成服务不可用',
        duration: 3000
      })
      isTtsLoading.value = false
      return
    } finally {
      isTtsLoading.value = false
    }
  }

  if (!url) {
    ElMessage.warning('语音合成服务不可用')
    return
  }

  // 播放
  try {
    const audio = chatApi.playAudio(url)
    if (audio) {
      currentAudio    = audio
      isPlaying.value = true
      audio.onended = () => {
        isPlaying.value = false
        currentAudio    = null
      }
      audio.onerror = () => {
        isPlaying.value = false
        currentAudio    = null
        ElMessage.warning('音频播放失败')
      }
    }
  } catch (e) {
    console.warn('[TTS] 播放失败', e)
    ElMessage.warning('音频播放失败')
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

// 情绪图标映射
const emotionIcon = computed(() => {
  if (!props.message.emotion) return ''
  const iconMap = {
    calm: '🌸',
    happy: '😊',
    melancholy: '😔',
    nostalgic: '🍃',
    guarded: '⚔️'
  }
  return iconMap[props.message.emotion.type] || '🌸'
})

// 情绪提示文本
const emotionTooltip = computed(() => {
  if (!props.message.emotion) return ''
  const { type, mood, energy } = props.message.emotion
  const typeLabel = {
    calm: '平静',
    happy: '愉悦',
    melancholy: '忧郁',
    nostalgic: '怀念',
    guarded: '警戒'
  }[type] || '平静'
  return `${typeLabel} | 心情 ${mood}/100 | 精力 ${energy}/100`
})
</script>

<style lang="scss" scoped>
.chat-message {
  display: flex;
  gap: 12px;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 8px;
  transition: all 0.2s ease;

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
  width: auto;
  min-width: 0; /* 防止flex子元素溢出 */
  align-items: flex-start; /* 确保内容左对齐 */
}

.message-header {
  display: flex;
  // justify-content: space-between;
  gap: 4px;
  align-items: center;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.message-role {
  font-weight: 600;
}

.message-body {
  background-color: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border-radius: 8px;
  padding: 12px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
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
  align-items: center;
  opacity: 0;
  transition: opacity 0.2s ease;

  .chat-message:hover & {
    opacity: 1;
  }
}

/* 语音按钮：常驻显示，不受悬停隐藏控制 */
.voice-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.15);
  cursor: pointer;
  transition: all 0.2s ease;
  flex-shrink: 0;

  .voice-icon {
    font-size: 14px;
    line-height: 1;
  }

  &:hover {
    background: rgba(255, 255, 255, 0.3);
    transform: scale(1.1);
  }

  &.playing {
    background: rgba(var(--el-color-primary-rgb), 0.25);
    animation: pulse 1.2s ease-in-out infinite;
  }

  &.loading {
    opacity: 0.6;
    cursor: wait;
  }
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50%       { transform: scale(1.12); }
}

/* 情绪指示器 */
.emotion-indicator {
  margin-top: 6px;
  opacity: 0.75;
  transition: opacity 0.2s ease;
  
  .emotion-icon {
    font-size: 16px;
    cursor: help;
    display: inline-block;
    transition: transform 0.2s ease;
    
    &:hover {
      opacity: 1;
      transform: scale(1.15);
    }
  }
}

.dark-theme {
  .message-body {
    background-color: rgba(0, 0, 0, 0.2);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
  }
}
</style>
