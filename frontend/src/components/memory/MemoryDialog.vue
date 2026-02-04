<template>
  <el-dialog
    v-model="visible"
    :title="isEdit ? '编辑记忆' : '添加记忆'"
    width="500px"
    :before-close="handleClose"
  >
    <el-form :model="memoryForm" label-position="top" :rules="rules" ref="formRef">
      <el-form-item label="记忆内容" prop="content">
        <el-input
          v-model="memoryForm.content"
          type="textarea"
          :rows="4"
          placeholder="请输入记忆内容..."
          maxlength="500"
          show-word-limit
        />
      </el-form-item>
      
      <el-form-item label="分类标签" prop="category">
        <el-select
          v-model="memoryForm.category"
          placeholder="选择或输入分类"
          filterable
          allow-create
          style="width: 100%"
        >
          <el-option
            v-for="category in predefinedCategories"
            :key="category"
            :label="category"
            :value="category"
          />
        </el-select>
      </el-form-item>
      
      <el-form-item label="关键词">
        <el-tag
          v-for="keyword in memoryForm.keywords"
          :key="keyword"
          closable
          @close="removeKeyword(keyword)"
          style="margin-right: 8px; margin-bottom: 8px"
        >
          {{ keyword }}
        </el-tag>
        
        <el-input
          v-if="keywordInputVisible"
          ref="keywordInputRef"
          v-model="keywordInput"
          size="small"
          style="width: 120px"
          @keyup.enter="addKeyword"
          @blur="addKeyword"
        />
        <el-button
          v-else
          size="small"
          @click="showKeywordInput"
        >
          + 添加关键词
        </el-button>
      </el-form-item>
    </el-form>
    
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button type="primary" @click="handleConfirm" :loading="isSubmitting">
          {{ isEdit ? '更新' : '保存' }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, nextTick, watch } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import type { Memory } from '@/types'

interface Props {
  modelValue: boolean
  memory?: Memory | null
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'confirm', memory: { content: string; category: string; keywords: string[] }): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})

const isEdit = computed(() => !!props.memory)

const formRef = ref<FormInstance>()
const keywordInputRef = ref()
const isSubmitting = ref(false)
const keywordInputVisible = ref(false)
const keywordInput = ref('')

const predefinedCategories = [
  '工作',
  '学习',
  '生活',
  '技术',
  '创意',
  '重要',
  '备忘',
  '其他',
]

const memoryForm = reactive({
  content: '',
  category: '',
  keywords: [] as string[],
})

const rules: FormRules = {
  content: [
    { required: true, message: '请输入记忆内容', trigger: 'blur' },
    { min: 5, max: 500, message: '内容长度应在 5-500 字符之间', trigger: 'blur' },
  ],
  category: [
    { required: true, message: '请选择或输入分类标签', trigger: 'change' },
  ],
}

const removeKeyword = (keyword: string) => {
  const index = memoryForm.keywords.indexOf(keyword)
  if (index > -1) {
    memoryForm.keywords.splice(index, 1)
  }
}

const showKeywordInput = () => {
  keywordInputVisible.value = true
  nextTick(() => {
    keywordInputRef.value?.focus()
  })
}

const addKeyword = () => {
  const keyword = keywordInput.value.trim()
  if (keyword && !memoryForm.keywords.includes(keyword)) {
    memoryForm.keywords.push(keyword)
  }
  keywordInputVisible.value = false
  keywordInput.value = ''
}

const handleClose = () => {
  visible.value = false
  resetForm()
}

const handleConfirm = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    isSubmitting.value = true

    emit('confirm', {
      content: memoryForm.content,
      category: memoryForm.category,
      keywords: memoryForm.keywords,
    })

    visible.value = false
    resetForm()
  } catch (error) {
    console.error('表单验证失败:', error)
  } finally {
    isSubmitting.value = false
  }
}

const resetForm = () => {
  memoryForm.content = ''
  memoryForm.category = ''
  memoryForm.keywords = []
  keywordInput.value = ''
  keywordInputVisible.value = false
  formRef.value?.resetFields()
}

const initForm = () => {
  if (props.memory) {
    memoryForm.content = props.memory.content
    memoryForm.category = props.memory.category
    memoryForm.keywords = [...props.memory.keywords]
  } else {
    resetForm()
  }
}

watch(() => props.memory, initForm, { immediate: true })
watch(() => props.modelValue, (newVal) => {
  if (newVal) {
    initForm()
  }
})
</script>

<style lang="scss" scoped>
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
