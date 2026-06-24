<template>
  <div class="memory-view ry-layout">
    <!-- 左侧侧边栏 -->
    <div class="ry-sidebar">
      <div class="sidebar-logo">
        <span class="logo-emoji">🌸</span>
        <span class="logo-text">樱 · 后台管理中心</span>
      </div>
      
      <el-menu
        :default-active="activeMenu"
        class="sidebar-menu"
        @select="handleMenuSelect"
      >
        <el-menu-item index="agent">
          <el-icon><User /></el-icon>
          <span>Agent个人信息</span>
        </el-menu-item>
        <el-menu-item index="model">
          <el-icon><Setting /></el-icon>
          <span>模型参数配置</span>
        </el-menu-item>
        <el-menu-item index="memory">
          <el-icon><Collection /></el-icon>
          <span>记忆数据管理</span>
        </el-menu-item>
      </el-menu>
    </div>

    <!-- 右侧主容器 -->
    <div class="ry-main-container">
      <!-- 顶部导航栏 -->
      <div class="ry-navbar">
        <div class="navbar-left">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item>后台管理</el-breadcrumb-item>
            <el-breadcrumb-item>{{ currentMenuTitle }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="navbar-right">
          <el-button @click="$router.push('/')" :icon="House" type="primary" plain size="small">
            返回对话主页
          </el-button>
        </div>
      </div>

      <!-- 内容主体区域 -->
      <div class="ry-app-main">
        
        <!-- 1. Agent 个人信息页面 -->
        <div v-if="activeMenu === 'agent'" class="page-container page-agent">
          <el-row :gutter="20">
            <!-- 左侧名片卡 -->
            <el-col :span="8">
              <el-card shadow="hover" class="agent-profile-card">
                <div class="profile-header">
                  <el-avatar :src="sakuraAvatar" :size="100" class="profile-avatar" />
                  <h2 class="profile-name">{{ configForm.agent_info?.name || '八重樱' }}</h2>
                  <el-tag type="danger" effect="plain" class="profile-tag">
                    {{ configForm.agent_info?.identity || '永恒守护者' }}
                  </el-tag>
                </div>
                <div class="profile-details">
                  <div class="detail-item">
                    <span class="detail-label">当前心情:</span>
                    <span class="detail-value text-highlight">
                      {{ configForm.agent_info?.mood || '平静' }}
                    </span>
                  </div>
                  <div class="detail-item">
                    <span class="detail-label">核心冲突:</span>
                    <p class="detail-desc">
                      {{ configForm.agent_info?.consts?.core_contradiction || '-' }}
                    </p>
                  </div>
                </div>
              </el-card>
            </el-col>
            
            <!-- 右侧详情卡 -->
            <el-col :span="16">
              <el-card shadow="hover" class="agent-info-card">
                <template #header>
                  <div class="card-header">
                    <span class="card-header-title">🌸 设定详情（只读）</span>
                  </div>
                </template>
                
                <el-descriptions :column="1" border>
                  <el-descriptions-item label="性格特征">
                    <div class="tag-group">
                      <el-tag
                        v-for="trait in configForm.agent_info?.personality || []"
                        :key="trait"
                        type="success"
                        effect="light"
                        class="info-tag"
                      >
                        {{ trait }}
                      </el-tag>
                    </div>
                  </el-descriptions-item>
                  <el-descriptions-item label="个人爱好">
                    <div class="tag-group">
                      <el-tag
                        v-for="hobby in configForm.agent_info?.hobbies || []"
                        :key="hobby"
                        type="warning"
                        effect="light"
                        class="info-tag"
                      >
                        {{ hobby }}
                      </el-tag>
                    </div>
                  </el-descriptions-item>
                  <el-descriptions-item label="能力设定">
                    <p class="desc-text">{{ configForm.agent_info?.consts?.abilities || '-' }}</p>
                  </el-descriptions-item>
                  <el-descriptions-item label="禁止事项">
                    <p class="desc-text text-danger">{{ configForm.agent_info?.consts?.forbidden || '-' }}</p>
                  </el-descriptions-item>
                </el-descriptions>

                <div class="prompt-box">
                  <h3 class="box-title">出厂内置提示词 (BASE_PERSON)</h3>
                  <el-input
                    v-model="basePromptText"
                    type="textarea"
                    :rows="10"
                    readonly
                    class="readonly-textarea"
                  />
                </div>
              </el-card>
            </el-col>
          </el-row>
        </div>

        <!-- 2. 模型参数配置页面 -->
        <div v-if="activeMenu === 'model'" v-loading="isConfigLoading" class="page-container page-model">
          <el-form :model="configForm" label-position="left" label-width="160px" class="ry-form">
            
            <!-- 2.1 全局服务商密钥配置 (通栏卡片) -->
            <el-card shadow="hover" class="config-section-card" style="margin-bottom: 20px;">
              <template #header>
                <div class="card-header">
                  <span class="card-header-title">🔑 常见 AI 服务商配置中心（手动填写密钥，各功能模块可灵活关联调用）</span>
                </div>
              </template>
              <el-row :gutter="20">
                <el-col :span="8">
                  <el-form-item label="DeepSeek Key">
                    <el-input v-model="configForm.provider_deepseek_key" type="password" show-password placeholder="DeepSeek 密钥" />
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="阿里千问 Key">
                    <el-input v-model="configForm.provider_qwen_key" type="password" show-password placeholder="通义千问 密钥" />
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="字节豆包 Key">
                    <el-input v-model="configForm.provider_doubao_key" type="password" show-password placeholder="火山豆包 密钥" />
                  </el-form-item>
                </el-col>
              </el-row>
              <el-row :gutter="20" style="margin-top: 10px;">
                <el-col :span="8">
                  <el-form-item label="OpenAI Key">
                    <el-input v-model="configForm.provider_openai_key" type="password" show-password placeholder="OpenAI 密钥" />
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="自定义 API Base">
                    <el-input v-model="configForm.provider_custom_base" placeholder="如 https://myproxy.com/v1" />
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="自定义 API Key">
                    <el-input v-model="configForm.provider_custom_key" type="password" show-password placeholder="自定义 API 密钥" />
                  </el-form-item>
                </el-col>
              </el-row>
            </el-card>

            <el-row :gutter="20">
              <!-- 左侧大模型与TTS -->
              <el-col :span="12">
                <el-card shadow="hover" class="config-section-card">
                  <template #header>
                    <div class="card-header">
                      <span class="card-header-title">🤖 文字生成模型 (LLM)</span>
                    </div>
                  </template>
                  <el-form-item label="关联 AI 服务商">
                    <el-select v-model="configForm.llm_provider" style="width: 100%">
                      <el-option label="DeepSeek (推荐)" value="deepseek" />
                      <el-option label="通义千问 (阿里)" value="qwen" />
                      <el-option label="火山豆包 (字节)" value="doubao" />
                      <el-option label="OpenAI" value="openai" />
                      <el-option label="自定义中转/代理 API" value="custom" />
                    </el-select>
                  </el-form-item>
                  <el-form-item label="模型名称 (Model)">
                    <el-select
                      v-model="configForm.llm_model"
                      filterable
                      allow-create
                      placeholder="请选择或输入大模型名称"
                      style="width: 100%"
                    >
                      <el-option
                        v-for="model in getLLMModelsByProvider(configForm.llm_provider)"
                        :key="model"
                        :label="model"
                        :value="model"
                      />
                    </el-select>
                  </el-form-item>
                </el-card>

                <el-card shadow="hover" class="config-section-card" style="margin-top: 20px;">
                  <template #header>
                    <div class="card-header">
                      <span class="card-header-title">🎙️ 语音合成服务 (TTS)</span>
                    </div>
                  </template>
                  <el-form-item label="TTS Engine">
                    <el-select v-model="configForm.tts_engine" style="width: 100%">
                      <el-option label="GPT-SoVITS" value="gpt_sovits" />
                    </el-select>
                  </el-form-item>
                  <el-form-item label="GPT Weights Path">
                    <el-input v-model="configForm.gpt_weights" placeholder="GPT 模型权重绝对/相对路径 (.ckpt)" />
                  </el-form-item>
                  <el-form-item label="SoVITS Weights Path">
                    <el-input v-model="configForm.sovits_weights" placeholder="SoVITS 模型权重绝对/相对路径 (.pth)" />
                  </el-form-item>
                  <el-form-item label="Reference Audio">
                    <el-input v-model="configForm.ref_audio_path" placeholder="参考音频在服务器上的绝对路径" />
                  </el-form-item>
                  <el-form-item label="Reference Text">
                    <el-input v-model="configForm.prompt_text" placeholder="参考音频对应的台词内容" />
                  </el-form-item>
                  <el-row :gutter="10">
                    <el-col :span="12">
                      <el-form-item label="Ref Lang" label-width="90px">
                        <el-input v-model="configForm.prompt_lang" placeholder="zh / ja / en" />
                      </el-form-item>
                    </el-col>
                    <el-col :span="12">
                      <el-form-item label="Out Lang" label-width="90px">
                        <el-input v-model="configForm.text_lang" placeholder="zh / ja / en" />
                      </el-form-item>
                    </el-col>
                  </el-row>
                  <el-form-item label="Speed Factor">
                    <el-slider v-model="configForm.speed_factor" :min="0.5" :max="2.0" :step="0.1" show-input />
                  </el-form-item>
                </el-card>
              </el-col>

              <!-- 右侧视觉与自定义提示词 -->
              <el-col :span="12">
                <el-card shadow="hover" class="config-section-card">
                  <template #header>
                    <div class="card-header">
                      <span class="card-header-title">👁️ 多模态与视觉识别</span>
                    </div>
                  </template>
                  <el-collapse>
                    <el-collapse-item title="图升文模型 (Image-to-Text)" name="img2txt">
                      <el-form-item label="关联 AI 服务商">
                        <el-select v-model="configForm.image_to_text_provider" style="width: 100%">
                          <el-option label="DeepSeek" value="deepseek" />
                          <el-option label="通义千问 (阿里)" value="qwen" />
                          <el-option label="火山豆包 (字节)" value="doubao" />
                          <el-option label="OpenAI" value="openai" />
                          <el-option label="自定义中转/代理 API" value="custom" />
                        </el-select>
                      </el-form-item>
                      <el-form-item label="模型名称 (Model)">
                        <el-select
                          v-model="configForm.image_to_text_model"
                          filterable
                          allow-create
                          placeholder="选择或手输视觉大模型名称"
                          style="width: 100%"
                        >
                          <el-option
                            v-for="model in getVisionModelsByProvider(configForm.image_to_text_provider)"
                            :key="model"
                            :label="model"
                            :value="model"
                          />
                        </el-select>
                      </el-form-item>
                    </el-collapse-item>
                    
                    <el-collapse-item title="画面识别模型 (Scene Recognition)" name="scene">
                      <el-form-item label="关联 AI 服务商">
                        <el-select v-model="configForm.scene_recognition_provider" style="width: 100%">
                          <el-option label="DeepSeek" value="deepseek" />
                          <el-option label="通义千问 (阿里)" value="qwen" />
                          <el-option label="火山豆包 (字节)" value="doubao" />
                          <el-option label="OpenAI" value="openai" />
                          <el-option label="自定义中转/代理 API" value="custom" />
                        </el-select>
                      </el-form-item>
                      <el-form-item label="模型名称 (Model)">
                        <el-select
                          v-model="configForm.scene_recognition_model"
                          filterable
                          allow-create
                          placeholder="选择或手输识别大模型名称"
                          style="width: 100%"
                        >
                          <el-option
                            v-for="model in getVisionModelsByProvider(configForm.scene_recognition_provider)"
                            :key="model"
                            :label="model"
                            :value="model"
                          />
                        </el-select>
                      </el-form-item>
                    </el-collapse-item>
                  </el-collapse>
                </el-card>

                <el-card shadow="hover" class="config-section-card" style="margin-top: 20px;">
                  <template #header>
                    <div class="card-header">
                      <span class="card-header-title">🔗 向量特征提取 (Embedding)</span>
                    </div>
                  </template>
                  <el-form-item label="提取模式">
                    <el-select v-model="configForm.embedding_mode" style="width: 100%">
                      <el-option label="本地提取 (Local)" value="local" />
                      <el-option label="在线 API 提取 (API)" value="api" />
                    </el-select>
                  </el-form-item>
                  
                  <template v-if="configForm.embedding_mode === 'api'">
                    <el-form-item label="关联 AI 服务商">
                      <el-select v-model="configForm.embedding_provider" style="width: 100%">
                        <el-option label="DeepSeek" value="deepseek" />
                        <el-option label="通义千问 (阿里)" value="qwen" />
                        <el-option label="火山豆包 (字节)" value="doubao" />
                        <el-option label="OpenAI" value="openai" />
                        <el-option label="自定义中转/代理 API" value="custom" />
                      </el-select>
                    </el-form-item>
                    <el-form-item label="模型名称 (Model)">
                      <el-select
                        v-model="configForm.embedding_model"
                        filterable
                        allow-create
                        placeholder="选择或手输 Embedding 模型"
                        style="width: 100%"
                      >
                        <el-option
                          v-for="model in getEmbeddingModelsByProvider(configForm.embedding_provider)"
                          :key="model"
                          :label="model"
                          :value="model"
                        />
                      </el-select>
                    </el-form-item>
                    <el-form-item label="维度 (Dimension)">
                      <el-input-number v-model="configForm.embedding_dimension" :min="1" style="width: 100%" />
                    </el-form-item>
                  </template>
                  
                  <template v-else>
                    <el-form-item label="本地模型名称">
                      <el-input v-model="configForm.local_embedding_model" readonly placeholder="BAAI/bge-small-zh-v1.5" />
                    </el-form-item>
                    <el-form-item label="本地模型维度">
                      <el-input-number v-model="configForm.local_embedding_dimension" readonly style="width: 100%" />
                    </el-form-item>
                  </template>
                </el-card>

                <el-card shadow="hover" class="config-section-card" style="margin-top: 20px;">
                  <template #header>
                    <div class="card-header">
                      <span class="card-header-title">✍️ 自定义系统提示词 (Prompt)</span>
                    </div>
                  </template>
                  <el-form-item label-width="0">
                    <p class="prompt-hint">此处的提示词将覆盖出厂默认提示词以热更新其人格设定。</p>
                    <el-input
                      v-model="configForm.system_prompt"
                      type="textarea"
                      :rows="11"
                      placeholder="请输入八重樱的全局系统提示词..."
                      class="prompt-textarea"
                    />
                  </el-form-item>
                </el-card>
              </el-col>
            </el-row>

            <!-- 提交底栏 -->
            <div class="ry-form-actions">
              <el-button type="primary" size="large" :loading="isSavingConfig" @click="saveSystemConfig">
                保存系统配置
              </el-button>
            </div>
          </el-form>
        </div>

        <!-- 3. 记忆数据管理页面 -->
        <div v-if="activeMenu === 'memory'" class="page-container page-memory">
          <el-card shadow="hover" class="memory-table-card">
            <template #header>
              <div class="card-header-between">
                <span class="card-header-title">📊 长期记忆列表 (Excel风格)</span>
                <div class="header-actions">
                  <el-button type="success" @click="exportMemory" :loading="isExporting" :icon="Download">导出</el-button>
                  <el-button type="warning" @click="importMemory" :loading="isImporting" :icon="Upload">导入</el-button>
                  <el-button type="primary" @click="showCreateDialog = true" :icon="Plus">
                    添加新记忆
                  </el-button>
                </div>
              </div>
            </template>

            <!-- 搜索过滤 -->
            <div class="table-search-bar">
              <el-input
                v-model="searchQuery"
                placeholder="关键字搜索记忆..."
                :prefix-icon="Search"
                clearable
                @input="handleSearch"
                style="width: 280px"
              />
              <el-select
                v-model="selectedCategory"
                placeholder="按分类过滤"
                clearable
                @change="handleFilter"
                style="width: 180px; margin-left: 12px"
              >
                <el-option
                  v-for="category in categories"
                  :key="category"
                  :label="category"
                  :value="category"
                />
              </el-select>
            </div>

            <!-- Excel 风格表格 -->
            <el-table
              v-loading="isLoading"
              :data="filteredMemories"
              border
              stripe
              style="width: 100%; margin-top: 15px"
              class="excel-table"
              header-cell-class-name="excel-header-cell"
            >
              <el-table-column label="分类标签" width="130" align="center">
                <template #default="scope">
                  <el-tag :type="getCategoryType(scope.row.category)" size="small">
                    {{ scope.row.category }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="content" label="记忆内容" min-width="320" show-overflow-tooltip />
              <el-table-column label="关键词" min-width="200">
                <template #default="scope">
                  <div class="keyword-tags">
                    <el-tag
                      v-for="keyword in scope.row.keywords"
                      :key="keyword"
                      size="small"
                      class="keyword-tag"
                    >
                      {{ keyword }}
                    </el-tag>
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="更新时间" width="180" align="center">
                <template #default="scope">
                  {{ formatDate(scope.row.updatedAt) }}
                </template>
              </el-table-column>
              <el-table-column label="操作" width="160" align="center" fixed="right">
                <template #default="scope">
                  <el-button size="small" @click="editMemory(scope.row)">
                    编辑
                  </el-button>
                  <el-button size="small" type="danger" @click="deleteMemory(scope.row.id)">
                    删除
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </div>

      </div>
    </div>

    <!-- 添加/编辑记忆弹窗 -->
    <MemoryDialog
      v-model="showCreateDialog"
      :memory="editingMemory"
      @confirm="handleMemorySave"
    />

    <!-- 隐藏的文件输入 -->
    <input
      ref="fileInput"
      type="file"
      accept=".json"
      @change="handleFileSelect"
      style="display: none"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import {
  House,
  User,
  Setting,
  Collection,
  Plus,
  Search,
  Download,
  Upload
} from '@element-plus/icons-vue'
import MemoryDialog from '@/components/memory/MemoryDialog.vue'
import { useMemoryStore } from '@/stores/memory'
import type { Memory } from '@/types'
import { memoryApi, type SystemConfig } from '@/api/memory'
import { chatApi } from '@/api/chat'
import sakuraAvatar from '@/asserts/img/sakura_avatar.jpeg'

const memoryStore = useMemoryStore()

const searchQuery = ref('')
const selectedCategory = ref('')
const showCreateDialog = ref(false)
const editingMemory = ref<Memory | null>(null)

// 菜单激活项：可选 'agent' | 'model' | 'memory'
const activeMenu = ref('agent')

const menuTitles: Record<string, string> = {
  agent: 'Agent 个人信息',
  model: '模型参数配置',
  memory: '记忆数据管理',
}

const currentMenuTitle = computed(() => menuTitles[activeMenu.value] || '')

const handleMenuSelect = (index: string) => {
  activeMenu.value = index
}

const isLoading = computed(() => memoryStore.isLoading)
const memories = computed(() => memoryStore.memories)

// 配置文件状态
const isConfigLoading = ref(false)
const isSavingConfig = ref(false)
const configForm = reactive<SystemConfig>({
  llm_model: '',
  llm_api_key: '',
  llm_api_base: '',
  tts_engine: '',
  gpt_weights: '',
  sovits_weights: '',
  ref_audio_path: '',
  prompt_text: '',
  prompt_lang: '',
  text_lang: '',
  speed_factor: 1.0,
  image_to_text_model: '',
  image_to_text_api_key: '',
  image_to_text_api_base: '',
  scene_recognition_model: '',
  scene_recognition_api_key: '',
  scene_recognition_api_base: '',
  system_prompt: '',
  
  embedding_mode: 'local',
  embedding_api_key: '',
  embedding_api_base: '',
  embedding_model: '',
  embedding_dimension: 1536,
  local_embedding_model: '',
  local_embedding_dimension: 512,
  
  provider_deepseek_key: '',
  provider_qwen_key: '',
  provider_doubao_key: '',
  provider_openai_key: '',
  provider_custom_base: '',
  provider_custom_key: '',
  
  llm_provider: 'deepseek',
  image_to_text_provider: 'deepseek',
  scene_recognition_provider: 'deepseek',
  embedding_provider: 'deepseek',
})

const getLLMModelsByProvider = (provider: string) => {
  if (provider === 'deepseek') return ['deepseek-chat', 'deepseek-reasoner']
  if (provider === 'qwen') return ['qwen-turbo', 'qwen-plus', 'qwen-max']
  if (provider === 'openai') return ['gpt-4o-mini', 'gpt-4o', 'gpt-3.5-turbo']
  if (provider === 'doubao') return ['doubao-pro-4k', 'doubao-pro-32k']
  return []
}

const getVisionModelsByProvider = (provider: string) => {
  if (provider === 'qwen') return ['qwen-vl-plus', 'qwen-vl-max']
  if (provider === 'openai') return ['gpt-4o-mini', 'gpt-4o']
  if (provider === 'deepseek') return ['deepseek-chat']
  return ['minicpm-v']
}

const getEmbeddingModelsByProvider = (provider: string) => {
  if (provider === 'openai') return ['text-embedding-3-small', 'text-embedding-3-large', 'text-embedding-ada-002']
  if (provider === 'qwen') return ['text-embedding-v2', 'text-embedding-v1']
  if (provider === 'deepseek') return ['deepseek-embed']
  return []
}

const basePromptText = computed(() => {
  return configForm.agent_info?.base_prompt || '加载中...'
})

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
    '重要': 'danger',
    '备忘': 'info',
  }
  return typeMap[category] || 'default'
}

const formatDate = (date: any) => {
  if (!date) return '-'
  const d = new Date(date)
  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(d)
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

// 获取配置信息
const loadSystemConfig = async () => {
  try {
    isConfigLoading.value = true
    const config = await memoryApi.getSystemConfig()
    Object.assign(configForm, config)
  } catch (err) {
    ElMessage.error('获取系统配置失败')
  } finally {
    isConfigLoading.value = false
  }
}

// 提交配置修改
const saveSystemConfig = async () => {
  try {
    isSavingConfig.value = true
    await memoryApi.updateSystemConfig({ ...configForm })
    ElMessage.success('系统配置保存成功，服务已热更新！')
  } catch (error) {
    console.error('Save config error:', error)
    ElMessage.error('系统配置保存失败')
  } finally {
    isSavingConfig.value = false
  }
}

// 导入导出功能
const isExporting = ref(false)
const isImporting = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)

const exportMemory = async () => {
  try {
    isExporting.value = true
    const blob = await chatApi.exportMemory()
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `memory_export_${new Date().toISOString().slice(0, 10)}.json`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    ElMessage.success('记忆导出成功！')
  } catch (error: any) {
    ElMessage.error(error.message || '导出失败')
  } finally {
    isExporting.value = false
  }
}

const importMemory = () => {
  fileInput.value?.click()
}

const handleFileSelect = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  if (!file.name.endsWith('.json')) {
    ElMessage.error('请选择 JSON 文件')
    return
  }

  const maxSize = 50 * 1024 * 1024
  if (file.size > maxSize) {
    ElMessage.error('文件大小超过限制（50MB）')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确认导入记忆文件：${file.name} (${(file.size / 1024).toFixed(2)} KB)？\n\n导入后将重建向量索引，可能需要几分钟。`,
      '导入记忆',
      { confirmButtonText: '确认导入', cancelButtonText: '取消', type: 'info' }
    )

    isImporting.value = true
    const result = await chatApi.importMemory(file)
    if (result.status === 'ok') {
      ElMessage.success(`✅ ${result.msg}`)
      await memoryStore.loadMemories() // 刷新列表
    } else {
      ElMessage.error(result.msg)
    }
  } catch (action) {
    // cancelled or error
  } finally {
    isImporting.value = false
    if (target) target.value = ''
  }
}

onMounted(() => {
  memoryStore.loadMemories()
  loadSystemConfig()
})
</script>

<style lang="scss" scoped>
/* 覆盖局部 Element Plus 的主色调为樱花粉 */
.memory-view {
  --el-color-primary: #f47983; /* 樱花粉 */
  --el-color-primary-light-3: #ff99a2;
  --el-color-primary-light-5: #ffb7c0;
  --el-color-primary-light-7: #ffd2d8;
  --el-color-primary-light-9: #fff0f2;
}

/* 若依后台布局风格 */
.ry-layout {
  display: flex;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  background-color: #faf6f7;
}

/* 左侧侧边栏 */
.ry-sidebar {
  width: 240px;
  background-color: #ffffff;
  border-right: 1px solid #ffd2d8;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;

  .sidebar-logo {
    height: 56px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    border-bottom: 1px solid #ffd2d8;
    background-color: #fff0f2;

    .logo-emoji {
      font-size: 20px;
    }
    
    .logo-text {
      font-size: 16px;
      font-weight: 700;
      color: #f47983;
      letter-spacing: 0.5px;
    }
  }

  .sidebar-menu {
    border-right: none;
    flex: 1;
    padding-top: 10px;

    :deep(.el-menu-item) {
      color: #5f5f5f;
      height: 50px;
      line-height: 50px;
      margin: 4px 8px;
      border-radius: 4px;

      &:hover {
        background-color: #fff0f2;
        color: #f47983;
      }

      &.is-active {
        background-color: #ffd2d8 !important;
        color: #f47983 !important;
        font-weight: 600;
      }

      .el-icon {
        color: inherit;
      }
    }
  }
}

/* 右侧主容器 */
.ry-main-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 顶部导航栏 */
.ry-navbar {
  height: 56px;
  background-color: #ffffff;
  border-bottom: 1px solid #ffd2d8;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  flex-shrink: 0;
  box-shadow: 0 1px 4px rgba(244, 121, 131, 0.05);

  .navbar-left {
    display: flex;
    align-items: center;
    
    :deep(.el-breadcrumb__inner) {
      color: #5f5f5f;
      font-weight: 500;
    }
    :deep(.el-breadcrumb__item:last-child .el-breadcrumb__inner) {
      color: #f47983;
      font-weight: 700;
    }
  }
}

/* 内容主体区域 */
.ry-app-main {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

/* 子页面容器 */
.page-container {
  max-width: 1200px;
  margin: 0 auto;
}

/* Card通用样式 */
.el-card {
  border-radius: 8px;
  border: 1px solid #ffd2d8;
  box-shadow: 0 2px 12px 0 rgba(244, 121, 131, 0.03) !important;
  
  :deep(.el-card__header) {
    border-bottom: 1px solid #ffd2d8;
    padding: 14px 20px;
    background-color: #fff8f9;
  }
}

.card-header {
  display: flex;
  align-items: center;
}

.card-header-between {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-header-title {
  font-size: 15px;
  font-weight: 700;
  color: #f47983;
}

/* 1. Agent 个人信息样式 */
.agent-profile-card {
  text-align: center;
  background-image: linear-gradient(180deg, #fff8f9 0%, #ffffff 100%);
  
  .profile-header {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 20px 0;
    border-bottom: 1px dashed #ffd2d8;

    .profile-avatar {
      border: 3px solid #ffd2d8;
      box-shadow: 0 4px 10px rgba(244, 121, 131, 0.15);
      transition: transform 0.3s;
      
      &:hover {
        transform: rotate(5deg) scale(1.05);
      }
    }

    .profile-name {
      margin: 15px 0 8px 0;
      font-size: 18px;
      font-weight: 700;
      color: #333333;
    }

    .profile-tag {
      border-radius: 20px;
      padding: 0 15px;
    }
  }

  .profile-details {
    padding: 20px 0 10px 0;
    text-align: left;

    .detail-item {
      margin-bottom: 15px;

      .detail-label {
        font-weight: 700;
        color: #f47983;
        display: block;
        margin-bottom: 5px;
        font-size: 14px;
      }

      .detail-value {
        font-size: 14px;
        color: #5f5f5f;
      }
      
      .text-highlight {
        color: #e91e63;
        font-weight: 600;
      }

      .detail-desc {
        font-size: 13px;
        color: #7f7f7f;
        line-height: 1.6;
        margin: 0;
        background-color: #fff8f9;
        padding: 8px 12px;
        border-radius: 4px;
        border-left: 3px solid #f47983;
      }
    }
  }
}

.agent-info-card {
  .tag-group {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }

  .info-tag {
    font-size: 13px;
    border-radius: 4px;
  }

  .desc-text {
    margin: 0;
    font-size: 13px;
    line-height: 1.6;
    color: #5f5f5f;
  }

  .text-danger {
    color: #d9534f;
    background-color: #fdf7f7;
    padding: 6px 12px;
    border-radius: 4px;
  }

  .prompt-box {
    margin-top: 20px;
    
    .box-title {
      font-size: 14px;
      font-weight: 700;
      color: #f47983;
      margin: 0 0 10px 0;
    }
    
    .readonly-textarea {
      :deep(.el-textarea__inner) {
        font-family: Consolas, Monaco, monospace;
        font-size: 13px;
        line-height: 1.6;
        background-color: #faf6f7;
        color: #777777;
        cursor: not-allowed;
      }
    }
  }
}

/* 2. 模型配置样式 */
.config-section-card {
  :deep(.el-form-item__label) {
    font-weight: 600;
    color: #5f5f5f;
  }

  .prompt-hint {
    font-size: 12px;
    color: #909399;
    margin: 0 0 8px 0;
  }

  .prompt-textarea {
    width: 100%;
    
    :deep(.el-textarea__inner) {
      font-family: Consolas, Monaco, monospace;
      font-size: 13px;
      line-height: 1.6;
      background-color: #ffffff;
      border: 1px solid #ffd2d8;
      
      &:focus {
        border-color: #f47983;
        box-shadow: 0 0 0 2px rgba(244, 121, 131, 0.2);
      }
    }
  }
}

.ry-form-actions {
  display: flex;
  justify-content: center;
  margin-top: 25px;
  padding-bottom: 30px;
}

/* 3. 记忆管理样式 */
.header-actions {
  display: flex;
  gap: 10px;
}

.memory-table-card {
  .table-search-bar {
    display: flex;
    align-items: center;
    margin-bottom: 15px;
    background-color: #fff8f9;
    padding: 10px 15px;
    border-radius: 6px;
    border: 1px dashed #ffd2d8;
  }
}

/* Excel 风格表格样式 */
.excel-table {
  border-radius: 4px;
  overflow: hidden;
  box-shadow: 0 1px 4px rgba(244, 121, 131, 0.05);
  
  :deep(.excel-header-cell) {
    background-color: #fff0f2 !important;
    color: #f47983;
    font-weight: 700;
  }
}

.keyword-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.keyword-tag {
  border-radius: 4px;
}
</style>
