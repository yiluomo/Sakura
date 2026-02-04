<template>
  <div class="memory-view">
    <div class="memory-header">
      <div class="header-left">
        <el-button @click="$router.back()" :icon="ArrowLeft">返回</el-button>
        <h1 class="page-title">记忆管理</h1>
      </div>
      
      <div class="header-right">
        <el-button type="primary" @click="showCreateDialog = true" :icon="Plus">
          添加记忆
        </el-button>
      </div>
    </div>
    
    <div class="memory-content">
      <div class="search-bar">
        <el-input
          v-model="searchQuery"
          placeholder="搜索记忆..."
          :prefix-icon="Search"
          clearable
          @input="handleSearch"
        />
      </div>
      
      <div class="memory-filters">
        <el-select
          v-model="selectedCategory"
          placeholder="选择分类"
          clearable
          @change="handleFilter"
        >
          <el-option
            v-for="category in categories"
            :key="category"
            :label="category"
            :value="category"
          />
        </el-select>
      </div>
      
      <div v-loading="isLoading" class="memory-list">
        <div v-if="filteredMemories.length === 0" class="empty-state">
          <el-icon class="empty-icon"><Collection /></el-icon>
          <p>{{ searchQuery ? '没有找到匹配的记忆' : '还没有任何记忆' }}</p>
        </div>
        
        <div
          v-for="memory in filteredMemories"
          :key="memory.id"
          class="memory-item"
        >
          <div class="memory-header-info">
            <div class="memory-category">
              <el-tag :type="getCategoryType(memory.category)">
                {{ memory.category }}
              </el-tag>
            </div>
            <div class="memory-date">
              {{ formatDate(memory.updatedAt) }}
            </div>
          </div>
          
          <div class="memory-content-text">
            {{ memory.content }}
          </div>
          
          <div class="memory-keywords">
            <el-tag
              v-for="keyword in memory.keywords"
              :key="keyword"
              size="small"
              class="keyword-tag"
            >
              {{ keyword }}
            </el-tag>
          </div>
          
          <div class="memory-actions">
            <el-button size="small" @click="editMemory(memory)">
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
            <el-button size="small" type="danger" @click="deleteMemory(memory.id)">
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </div>
        </div>
      </div>
    </div>
    
    <MemoryDialog
      v-model="showCreateDialog"
      :memory="editingMemory"
      @confirm="handleMemorySave"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import {
  ArrowLeft,
  Plus,
  Search,
  Collection,
  Edit,
  Delete,
} from '@element-plus/icons-vue'
import MemoryDialog from '@/components/memory/MemoryDialog.vue'
import { useMemoryStore } from '@/stores/memory'
import type { Memory } from '@/types'

const memoryStore = useMemoryStore()

const searchQuery = ref('')
const selectedCategory = ref('')
const showCreateDialog = ref(false)
const editingMemory = ref<Memory | null>(null)

const memories = computed(() => memoryStore.memories)
const isLoading = computed(() => memoryStore.isLoading)

const categories = computed(() => {
  const cats = new Set(memories.value.map(m => m.category))
  return Array.from(cats)
})

const filteredMemories = computed(() => {
  let filtered = memories.value

  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(memory =>
      memory.content.toLowerCase().includes(query) ||
      memory.keywords.some(keyword => keyword.toLowerCase().includes(query))
    )
  }

  if (selectedCategory.value) {
    filtered = filtered.filter(memory => memory.category === selectedCategory.value)
  }

  return filtered.sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime())
})

const handleSearch = () => {
  // 搜索逻辑已在 computed 中处理
}

const handleFilter = () => {
  // 过滤逻辑已在 computed 中处理
}

const getCategoryType = (category: string) => {
  const typeMap: Record<string, string> = {
    '工作': 'primary',
    '学习': 'success',
    '生活': 'info',
    '技术': 'warning',
    '创意': 'danger',
    '重要': 'primary',
    '备忘': 'info',
  }
  return typeMap[category] || 'default'
}

const formatDate = (date: Date) => {
  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

const editMemory = (memory: Memory) => {
  editingMemory.value = { ...memory }
  showCreateDialog.value = true
}

const deleteMemory = async (id: string) => {
  try {
    await ElMessageBox.confirm('确定要删除这条记忆吗？', '确认删除', {
      type: 'warning',
    })
    await memoryStore.deleteMemory(id)
    ElMessage.success('记忆已删除')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleMemorySave = async (memoryData: Omit<Memory, 'id' | 'createdAt' | 'updatedAt'>) => {
  try {
    if (editingMemory.value) {
      await memoryStore.updateMemory(editingMemory.value.id, memoryData)
      ElMessage.success('记忆已更新')
    } else {
      await memoryStore.addMemory(memoryData)
      ElMessage.success('记忆已添加')
    }
    editingMemory.value = null
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

onMounted(() => {
  memoryStore.loadMemories()
})
</script>

<style lang="scss" scoped>
.memory-view {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: var(--el-bg-color);
}

.memory-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  background-color: var(--el-bg-color);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;

  .page-title {
    margin: 0;
    font-size: 20px;
    font-weight: 600;
    color: var(--el-text-color-primary);
  }
}

.header-right {
  display: flex;
  gap: 12px;
}

.memory-content {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}

.search-bar {
  margin-bottom: 16px;
}

.memory-filters {
  margin-bottom: 16px;
}

.memory-list {
  display: grid;
  gap: 16px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 300px;
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

.memory-item {
  background-color: var(--el-bg-color-overlay);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  padding: 16px;
  transition: all 0.2s ease;

  &:hover {
    border-color: var(--el-color-primary-light-7);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }
}

.memory-header-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.memory-date {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.memory-content-text {
  line-height: 1.6;
  margin-bottom: 12px;
  color: var(--el-text-color-primary);
  white-space: pre-wrap;
  word-break: break-word;
}

.memory-keywords {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 12px;

  .keyword-tag {
    font-size: 12px;
  }
}

.memory-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.dark-theme {
  .memory-view {
    background-color: var(--el-bg-color-overlay);
  }

  .memory-header {
    background-color: var(--el-bg-color);
    border-color: var(--el-border-color);
  }

  .memory-item {
    background-color: var(--el-bg-color);
    border-color: var(--el-border-color);

    &:hover {
      border-color: var(--el-color-primary);
    }
  }
}

@media (max-width: 768px) {
  .memory-header {
    padding: 12px 16px;
  }

  .memory-content {
    padding: 16px;
  }

  .memory-item {
    padding: 12px;
  }
}
</style>
