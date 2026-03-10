<template>
  <div class="chat-view">
    <video class="background-video" autoplay muted loop playsinline>
      <source src="@/asserts/video/chat.mp4" type="video/mp4">
    </video>
    
    <!-- 错误提示组件 -->
    <ErrorToast
      v-model:visible="uiStore.errorToast.visible"
      :title="uiStore.errorToast.title"
      :message="uiStore.errorToast.message"
      :type="uiStore.errorToast.type"
    />
    
    <div class="chat-content">
    <div class="chat-header">
      <div class="header-left">
        <h1 class="app-title">八重樱</h1>
      </div>
      
      <div class="header-right">
        <el-button @click="toggleTheme" :icon="isDarkMode ? Sunny : Moon" circle />
        <!-- TTS 自动播放开关 -->
        <el-tooltip :content="ttsAutoPlay ? '自动播放语音: 开' : '自动播放语音: 关'" placement="bottom">
          <el-button
            @click="toggleTtsAutoPlay"
            :icon="ttsAutoPlay ? Headset : Mute"
            circle
            :type="ttsAutoPlay ? 'primary' : 'default'"
          />
        </el-tooltip>
        <!-- 导出记忆按钮 -->
        <el-tooltip content="导出记忆数据" placement="bottom">
          <el-button
            @click="exportMemory"
            :icon="Download"
            :loading="isExporting"
            circle
          />
        </el-tooltip>
        <!-- 导入记忆按钮 -->
        <el-tooltip content="导入记忆数据" placement="bottom">
          <el-button
            @click="importMemory"
            :icon="Upload"
            :loading="isImporting"
            circle
          />
        </el-tooltip>
        <!-- 隐藏的文件输入 -->
        <input
          ref="fileInput"
          type="file"
          accept=".json"
          style="display: none"
          @change="handleFileSelect"
        />
        <!-- 珍藏此刻按钮 -->
        <el-button
          @click="archiveAndClear"
          :icon="Files"
          :loading="isArchiving"
          type="primary"
          plain
        >珍藏此刻</el-button>
      </div>
    </div>
    
    <div class="chat-container">
      <div class="messages-container" ref="messagesContainer">
        <div v-if="messages.length === 0" class="empty-state">
          <el-icon class="empty-icon"><ChatDotRound /></el-icon>
          <p>开始你的第一次对话吧！</p>
        </div>
        
        <ChatMessage
          v-for="message in messages"
          :key="message.id"
          :message="message"
          @retry="retryMessage"
          @delete="deleteMessage"
        />
      </div>
      
      <div class="input-container">
        <ChatInput
          :is-loading="isLoading"
          @send="handleSendMessage"
        />
      </div>
    </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, computed, watch } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import { Sunny, Moon, Files, ChatDotRound, Headset, Mute, Upload, Download } from '@element-plus/icons-vue'
import ChatMessage from '@/components/chat/ChatMessage.vue'
import ChatInput from '@/components/chat/ChatInput.vue'
import ErrorToast from '@/components/common/ErrorToast.vue'
import { useChatStore } from '@/stores/chat'
import { useUIStore } from '@/stores/ui'
import { chatApi } from '@/api/chat'
import { parseError } from '@/utils/errorHandler'
import type { MemoryInfo } from '@/api/chat'

const chatStore = useChatStore()
const uiStore = useUIStore()

const messagesContainer = ref<HTMLElement>()
const fileInput = ref<HTMLInputElement>()

const messages      = computed(() => chatStore.messages)
const isLoading     = computed(() => chatStore.isLoading)
const isDarkMode    = computed(() => uiStore.isDarkMode)
const ttsAutoPlay   = computed(() => uiStore.ttsAutoPlay)
const isArchiving   = ref(false)
const isExporting   = ref(false)
const isImporting   = ref(false)

const toggleTheme        = () => uiStore.toggleDarkMode()
const toggleTtsAutoPlay  = async () => {
  // 如果是要开启 TTS，先测试服务是否可用
  if (!ttsAutoPlay.value) {
    const testResult = await chatApi.testTts()
    if (!testResult.available) {
      uiStore.showError({
        title: 'TTS 服务不可用',
        message: testResult.error || 'TTS 服务未启动或配置错误',
        type: 'warning'
      })
      return // 不开启 TTS
    }
  }
  
  uiStore.toggleTtsAutoPlay()
}

// 监听消息变化，自动滚动到底部
watch(
  () => messages.value.length,
  () => {
    scrollToBottom()
  }
)

onMounted(() => {
  chatStore.fetchHistory().then(() => {
    scrollToBottom()
  })
  uiStore.initializeTheme()
})

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

const getMemoryTypeLabel = (type: string): string => {
  const labels: Record<string, string> = {
    'name': '姓名',
    'hobby': '爱好',
    'dislike': '厌恶',
    'family': '家人',
    'friend': '朋友',
    'birthday': '生日',
    'age': '年龄',
    'location': '居住地',
    'occupation': '职业',
    'experience': '经历',
    'manual': '通用记忆'
  }
  return labels[type] || type
}

const handleMemoryConfirm = async (memoryInfo: MemoryInfo) => {
  try {
    const typeLabel = getMemoryTypeLabel(memoryInfo.memory_type)
    
    let message = ''
    let title = ''
    
    if (memoryInfo.action === 'update') {
      title = '更新记忆'
      message = `检测到【${typeLabel}】信息，是否更新？\n\n旧值：${memoryInfo.old_value}\n新值：${memoryInfo.new_value}`
    } else {
      title = '保存记忆'
      message = `检测到【${typeLabel}】信息，是否保存？\n\n内容：${memoryInfo.value}`
    }
    
    await ElMessageBox.confirm(message, title, {
      confirmButtonText: memoryInfo.action === 'update' ? '更新' : '保存',
      cancelButtonText: '取消',
      type: 'info',
      distinguishCancelAndClose: true,
      dangerouslyUseHTMLString: false,
    })
    
    // 用户确认保存
    const response = await chatStore.confirmMemory(memoryInfo, true)
    if (response.status === 'ok') {
      ElMessage.success(response.msg)
    }
  } catch (action) {
    // 用户取消
    if (action === 'cancel') {
      const response = await chatStore.confirmMemory(memoryInfo, false)
      ElMessage.info(response.msg || '已取消保存')
    }
  }
}

const handleSendMessage = async (content: string) => {
  try {
    const response = await chatStore.sendMessage(content)

    // 自动播放：仅当 ttsAutoPlay 开启且有 audio_url 时播放
    if (ttsAutoPlay.value && response.audio_url) {
      try {
        chatApi.playAudio(response.audio_url)
      } catch (audioError) {
        // 音频播放失败不显示错误，静默处理
        console.warn('音频播放失败:', audioError)
      }
    }

    // 检查是否有记忆信息需要确认
    if (response.memory_info) {
      await handleMemoryConfirm(response.memory_info)
    }
  } catch (error) {
    // 使用错误处理工具解析错误
    const errorInfo = parseError(error)
    uiStore.showError(errorInfo)
  }
}

const retryMessage = async (messageId: string) => {
  try {
    await chatStore.retryMessage(messageId)
    // scrollToBottom 会由 watch 自动触发
  } catch (error) {
    const errorInfo = parseError(error)
    uiStore.showError(errorInfo)
  }
}

const deleteMessage = async (messageId: string) => {
  try {
    await ElMessageBox.confirm('确定要删除这条消息吗？', '确认删除', {
      type: 'warning',
    })
    chatStore.deleteMessage(messageId)
  } catch {
    // 用户取消删除
  }
}

const archiveAndClear = async () => {
  try {
    await ElMessageBox.confirm(
      '将当前所有对话压缩总结后归档为长期记忆，并清空当前对话列表。\n\n此操作需要调用 LLM，可能需要几秒钟。',
      '归档记忆',
      {
        confirmButtonText: '确认归档',
        cancelButtonText: '取消',
        type: 'info',
      }
    )

    isArchiving.value = true
    const result = await chatApi.archiveMemory()

    if (result.success) {
      // 归档成功：清空前端消息列表
      chatStore.clearMessages()
      ElMessage.success(`✅ ${result.message}`)
    } else {
      ElMessage.warning(result.message)
    }
  } catch (action) {
    // 用户取消或发生错误
    if (action !== 'cancel' && action !== 'close') {
      const errorInfo = parseError(action)
      uiStore.showError(errorInfo)
    }
  } finally {
    isArchiving.value = false
  }
}

const exportMemory = async () => {
  try {
    isExporting.value = true
    
    // 调用导出API
    const blob = await chatApi.exportMemory()
    
    // 创建下载链接
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `memory_export_${new Date().toISOString().slice(0, 10)}.json`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('记忆导出成功！')
  } catch (error) {
    const errorInfo = parseError(error)
    uiStore.showError(errorInfo)
  } finally {
    isExporting.value = false
  }
}

const importMemory = () => {
  // 触发文件选择
  fileInput.value?.click()
}

const handleFileSelect = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  
  if (!file) return
  
  // 验证文件类型
  if (!file.name.endsWith('.json')) {
    ElMessage.error('请选择 JSON 文件')
    return
  }
  
  // 验证文件大小（50MB）
  const maxSize = 50 * 1024 * 1024
  if (file.size > maxSize) {
    ElMessage.error('文件大小超过限制（50MB）')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      `确认导入记忆文件：${file.name} (${(file.size / 1024).toFixed(2)} KB)？\n\n导入后将重建向量索引，可能需要几分钟。`,
      '导入记忆',
      {
        confirmButtonText: '确认导入',
        cancelButtonText: '取消',
        type: 'info',
      }
    )
    
    isImporting.value = true
    
    const result = await chatApi.importMemory(file)
    
    if (result.status === 'ok') {
      ElMessage.success({
        message: `✅ ${result.msg}`,
        duration: 5000
      })
      // 刷新对话列表
      await chatStore.fetchHistory()
    } else {
      ElMessage.error(result.msg)
    }
  } catch (action) {
    if (action !== 'cancel' && action !== 'close') {
      const errorInfo = parseError(action)
      uiStore.showError(errorInfo)
    }
  } finally {
    isImporting.value = false
    // 清空文件输入
    if (target) target.value = ''
  }
}

const rebuildIndex = async () => {
  try {
    // 先查询未建立索引的条目数
    const unindexedResult = await chatApi.getUnindexedEntries()
    
    if (unindexedResult.count === 0) {
      ElMessage.info('所有记忆已建立索引，无需重建')
      return
    }

    await ElMessageBox.confirm(
      `发现 ${unindexedResult.count} 条未建立索引的记忆。\n\n是否重建索引？`,
      '重建记忆索引',
      {
        confirmButtonText: '重建',
        cancelButtonText: '取消',
        type: 'info',
      }
    )

    isRebuilding.value = true
    const result = await chatApi.rebuildMemoryIndex()

    if (result.status === 'ok') {
      ElMessage.success({
        message: `✅ ${result.msg}\n新建: ${result.stats.new} 条，更新: ${result.stats.updated} 条`,
        duration: 5000
      })
    } else {
      ElMessage.error(result.msg)
    }
  } catch (action) {
    // 用户取消或发生错误
    if (action !== 'cancel' && action !== 'close') {
      const errorInfo = parseError(action)
      uiStore.showError(errorInfo)
    }
  } finally {
    isRebuilding.value = false
  }
}
</script>

<style lang="scss" scoped>
.chat-view {
  height: 100vh;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
}

.background-video {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  z-index: -1;
  filter: brightness(0.96);
}

.chat-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  // background-color: rgba(255, 255, 255, 0.95);
  // backdrop-filter: blur(15px);
}

.chat-header {
  flex-shrink: 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  // border-bottom: 1px solid var(--el-border-color-lighter);
  // background-color: var(--el-bg-color);
}

.header-left {
  .app-title {
    margin: 0;
    font-size: 20px;
    font-weight: 600;
    color: #f3648c;
  }
}

.header-right {
  display: flex;
  gap: 12px;
  align-items: center;
}

.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  min-height: 0;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 16px 24px;
  scroll-behavior: smooth;
  width: 100%;
  max-width: 1200px;

  &::-webkit-scrollbar {
    display: none;
  }
  
  /* Firefox */
  scrollbar-width: none;
  
  /* IE and Edge */
  -ms-overflow-style: none;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--el-text-color-secondary);

  .empty-icon {
    font-size: 64px;
    margin-bottom: 16px;
    opacity: 0.5;
  }

  p {
    margin: 0;
    font-size: 16px;
  }
}

.input-container {
  flex-shrink: 0;
  width: 100%;
  max-width: 1200px;
  padding: 16px 24px;
  box-sizing: border-box;
  // background-color: var(--el-bg-color);
}

.dark-theme {
  .chat-content {
    background-color: rgba(0, 0, 0, 0.7);
  }

  .chat-header,
  .input-container {
    background-color: var(--el-bg-color);
    border-color: var(--el-border-color);
  }
}

@media (max-width: 768px) {
  .chat-header {
    padding: 12px 16px;

    .app-title {
      font-size: 18px;
    }

    .header-right {
      gap: 8px;
    }
  }

  .messages-container {
    padding: 12px 16px;
  }
}
</style>
