# 2026-03-05 记忆索引重建功能

## 新增功能

### 1. 迁移脚本增强

**文件**: `backend/src/migrate_db.py`

**新增步骤**：

**步骤 2.5**：短期对话自动归档
- 迁移前自动读取 `conversations` 表
- 将所有短期对话归档到 `summaries_1.md`
- 避免短期对话丢失

**步骤 6**：从文件重建数据库索引
- 迁移完成后自动扫描所有 `.md` 文件
- 解析每条记忆条目
- 写入数据库索引表
- 确保迁移后数据库索引完整

**执行流程**：
```
[1/7] 检测旧表结构和数据（包括短期对话）
[2/7] 旧数据写入 .md 文件
[2.5/7] 短期对话自动归档 ← 新增
[3/7] 删除旧表，重建新结构
[4/7] 验证新表字段
[5/7] 初始化默认用户状态
[6/7] 从文件重建数据库索引 ← 新增
[7/7] 检查是否需要保留用户状态
```

**数据保护机制**：
1. **长期记忆**：先备份到文件 → 删除数据库 → 重建索引
2. **短期对话**：先归档到文件 → 删除数据库
3. **用户状态**：重置为默认值（可选保留亲密度）

### 2. 记忆索引重建模块

**文件**: `backend/src/memory/rebuild_index.py`

**核心函数**：

1. `rebuild_all_indexes()` - 重建所有索引
   - 扫描所有 `.md` 文件
   - 解析记忆条目
   - 写入数据库索引
   - 返回统计信息：total, new, updated, skipped

2. `find_unindexed_entries()` - 查找未建立索引的条目
   - 对比文件和数据库
   - 返回未建立索引的记忆列表

3. `index_single_entry()` - 为单个条目建立索引
   - 用于精确控制索引重建

### 3. API 接口

**文件**: `backend/src/api/chat.py`

**新增接口**：

1. `POST /api/memory/rebuild` - 重建记忆索引
   ```json
   响应：
   {
     "status": "ok",
     "msg": "索引重建完成",
     "stats": {
       "total": 10,
       "new": 5,
       "updated": 3,
       "skipped": 2
     }
   }
   ```

2. `GET /api/memory/unindexed` - 查找未建立索引的条目
   ```json
   响应：
   {
     "status": "ok",
     "count": 5,
     "entries": [
       {
         "memory_type": "hobby",
         "key": "我喜欢",
         "content": "...",
         "keywords": [...],
         "importance": 4,
         "file": "preferences.md"
       }
     ]
   }
   ```

### 4. 前端回忆按钮

**文件**: `frontend/src/views/ChatView.vue`

**新增功能**：
- 顶部工具栏新增"回忆"按钮（刷新图标）
- 点击后自动检测未建立索引的记忆数量
- 弹出确认框显示待重建数量
- 确认后调用重建接口
- 显示重建结果统计

**UI 位置**：
```
[主题切换] [TTS开关] [回忆按钮] [珍藏此刻]
```

## 使用场景

### 场景 1：数据库迁移后

```bash
cd backend/src
python migrate_db.py
```

迁移脚本会自动：
1. 备份旧数据到 `.md` 文件
2. 重建数据库表结构
3. 自动重建索引

### 场景 2：手动编辑 .md 文件后

如果你直接编辑了 `memory_store/*.md` 文件，添加了新的记忆条目：

1. 点击前端"回忆"按钮
2. 系统检测到未建立索引的条目
3. 确认重建
4. 索引自动建立

### 场景 3：数据库索引丢失

如果数据库索引意外丢失，但 `.md` 文件完好：

1. 点击"回忆"按钮
2. 系统会重建所有索引
3. 数据完全恢复

### 场景 4：开发调试

通过 API 直接调用：

```bash
# 查看未建立索引的条目
curl http://localhost:8000/api/memory/unindexed

# 重建索引
curl -X POST http://localhost:8000/api/memory/rebuild
```

## 技术细节

### 索引关系

**双轨存储**：
- 文件：完整内容（人类可读）
- 数据库：轻量索引（快速检索）

**索引字段**：
- `memory_type` + `key` - 唯一标识
- `value` - 内容摘要（前100字）
- `keywords` - 关键词（空格分隔）
- `file_path` - 文件路径
- `importance` - 重要度
- `emotion_tag` - 情绪标签
- `emotional_intensity` - 情感强度

### 解析逻辑

通过正则表达式解析 `.md` 文件：
```python
pattern = re.compile(
    r'<!-- entry: (\w+)/(.+?) -->\n'   # type / key
    r'## .+?\n'                         # 标题行
    r'(.*?)'                            # 条目内容
    r'(?=\n<!-- entry:|\Z)',            # 到下一个条目或文件末尾
    re.DOTALL
)
```

提取字段：
- `**内容**` 或 `**摘要**`
- `**关键词**`
- `**重要度**`

### 并发安全

- 使用数据库事务保证一致性
- `ON DUPLICATE KEY UPDATE` 避免重复插入
- 文件写入使用全局锁

## 数据安全保障

### 完整的数据保护流程

**迁移前：**
1. 读取所有长期记忆到内存
2. 读取所有短期对话到内存

**迁移中：**
1. 长期记忆写入 `.md` 文件（人类可读）
2. 短期对话归档到 `summaries_1.md`（保留完整对话）
3. 删除旧表
4. 创建新表
5. 从文件重建索引

**迁移后：**
- 长期记忆：文件 + 数据库索引完整
- 短期对话：已归档到长期记忆
- 用户状态：重置为默认值

### 数据恢复能力

1. **长期记忆**：
   - 文件是主数据源
   - 数据库索引可随时重建
   - 任一损坏都可恢复

2. **短期对话**：
   - 迁移时自动归档
   - 不会丢失任何对话
   - 归档后可通过长期记忆查看

3. **用户状态**：
   - 亲密度重置为 0
   - 情绪状态重置为默认值
   - 如需保留可提前备份

### 悖论解决方案

**问题**：需要启动项目才能归档短期对话，但不迁移数据就无法启动项目

**解决**：迁移脚本自动归档短期对话
- 迁移时自动读取 `conversations` 表
- 将所有对话归档到 `summaries_1.md`
- 格式：`迁移前的对话记录（共 N 条）`
- 无需手动操作，完全自动化

## 测试验证

### 测试 1：迁移后索引完整性

```bash
# 执行迁移
python migrate_db.py

# 检查索引数量
mysql -u root -p sakura_db -e "SELECT COUNT(*) FROM long_term_memory;"

# 检查文件数量
ls -la memory_store/
```

### 测试 2：手动编辑后重建

1. 编辑 `memory_store/notes.md`，添加新条目
2. 点击前端"回忆"按钮
3. 确认显示新增条目数量
4. 重建后查询数据库验证

### 测试 3：API 调用

```bash
# 查看未建立索引的条目
curl http://localhost:8000/api/memory/unindexed

# 重建索引
curl -X POST http://localhost:8000/api/memory/rebuild
```

---

**实施完成时间**: 2026-03-05  
**相关文件**: 
- `backend/src/migrate_db.py`
- `backend/src/memory/rebuild_index.py`
- `backend/src/api/chat.py`
- `frontend/src/api/chat.ts`
- `frontend/src/views/ChatView.vue`
