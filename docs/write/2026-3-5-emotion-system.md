# 2026-03-05 情绪系统实现

## 实施内容

### 第一批：核心架构 ✅

1. **数据库扩展**
   - `user_states` 表新增字段：
     - `emotion_type` VARCHAR(20) - 情绪类型（calm/happy/melancholy/nostalgic/guarded）
     - `mood` INT - 心情值改为整数 0-100
     - `energy_level` INT - 精力值 0-100
     - `emotion_updated_at` DATETIME - 情绪更新时间
   
   - `long_term_memory` 表新增字段（预留）：
     - `emotion_tag` VARCHAR(20) - 保存时的情绪状态
     - `emotional_intensity` INT - 情感强度 0-5

2. **情绪计算核心模块** (`core/emotion.py`)
   - `analyze_message_sentiment()` - LLM 情感分析（-10 到 +10）
   - `detect_sensitive_topics()` - 敏感话题检测（trauma/nostalgia/beauty）
   - `calculate_mood_change()` - 多因素加权计算 mood 变化
   - `calculate_energy_cost()` - 精力消耗计算
   - `determine_emotion_type()` - 情绪类型判定（优先级规则）
   - `update_emotion_state()` - 主入口，更新情绪状态
   - `apply_emotion_decay()` - 情绪衰减（预留给定时任务）
   - `recover_energy()` - 精力恢复（预留给定时任务）

3. **Prompt 系统改造** (`core/prompt.py`)
   - 新增 `EMOTION_TONE_MAP` - 情绪语气映射
   - 修改 `TTS_OUTPUT_RULES` - 增加第4条：禁止非语音内容
   - `build_prompt()` 函数扩展参数：emotion_type, mood, energy
   - 根据情绪动态调整语气描述和回复长度提示

### 第二批：集成 ✅

4. **对话流程改造** (`core/conversation.py`)
   - `calculate_response_delay()` - 响应延迟计算（0.5-3.5秒）
   - `check_greeting()` - 主动问候机制（>6小时/3天）
   - `handle_message()` 集成情绪系统：
     1. 更新情绪状态
     2. 响应延迟（模拟思考）
     3. 检查主动问候
     4. 回忆上下文
     5. 构建提示词（传入情绪）
     6. 生成回复
     7. 保存记忆
     8. 返回情绪数据

5. **API 层改造** (`api/chat.py`)
   - `/chat` 接口返回格式扩展：新增 `emotion` 字段
   - 包含：emotion_type, mood, energy

### 第三批：展示 ✅

6. **前端展示**
   - `types/index.ts` - 新增 `EmotionState` 接口
   - `api/chat.ts` - `ChatResponse` 新增 emotion 字段
   - `stores/chat.ts` - 保存 emotion 到消息对象
   - `ChatMessage.vue` - 情绪图标显示：
     - calm: 🌸
     - happy: 😊
     - melancholy: 😔
     - nostalgic: 🍃
     - guarded: ⚔️
   - 悬停显示详细：心情值/精力值

### 第四批：优化（预留） ✅

7. **记忆系统配合**
   - `long_term.py` - `confirm_save_memory()` 支持情绪标签
   - `_calculate_emotional_intensity()` - 计算记忆情感强度
   - `crud.py` - `save_or_update_long_term_memory()` 扩展参数

8. **定时任务预留**
   - `main.py` - 添加 APScheduler 预留注释
   - 功能：每小时执行情绪衰减和精力恢复

## 情绪系统规则

### 情绪类型（5种）

1. **calm（平静）** - 基准状态
2. **happy（愉悦）** - 积极互动、美好回忆
3. **melancholy（忧郁）** - 触及创伤、孤独感
4. **nostalgic（怀念）** - 回忆过去、熟悉的人事物
5. **guarded（警戒）** - 陌生、不信任、被冒犯

### mood 值计算（多因素加权）

**触发因素：**
- 情感分析（LLM）：积极 +3~8，消极 -3~8
- 敏感话题：
  - trauma（凛/死亡/屠村）：-12
  - nostalgia（卡莲/八重村/过去）：0（触发怀念）
  - beauty（樱花/守护/承诺）：+8
- 时间因素：
  - < 5分钟：+1（陪伴感）
  - 6-24小时：0
  - 1-3天：-3
  - 3-7天：-8
  - > 7天：-15
- 亲密度影响：
  - < 20：mood 上限 60
  - > 50：负面衰减加快，正面增强

### 情绪类型判定（优先级）

1. guarded（警戒）- 预留
2. melancholy（忧郁）- trauma 话题 / mood < 35 / energy < 25
3. nostalgic（怀念）- nostalgia 话题
4. happy（愉悦）- mood > 65 / beauty 话题
5. calm（平静）- 默认

### 情绪影响行为

- **calm**: 回复 30-80字，沉静克制
- **happy**: 回复 40-100字，温和轻松
- **melancholy**: 回复 15-40字，简短多省略号
- **nostalgic**: 回复 30-70字，带回忆感
- **guarded**: 回复 20-50字，冷静保持距离

## 使用说明

### 数据库迁移

```bash
cd backend/src
python migrate_db.py
```

### 测试验证点

1. **情绪计算准确性**
   - 发送"我想起了凛" → melancholy
   - 发送"樱花真美" → happy
   - 发送"还记得卡莲吗" → nostalgic

2. **Prompt 纯净性**
   - 检查回复中无动作描述、心理活动
   - 只有纯文本和标点符号

3. **响应延迟**
   - 短消息：0.5-1秒
   - 长消息：1.5-2.5秒
   - 敏感话题：额外 +1秒

4. **前端图标显示**
   - assistant 消息下方显示情绪图标
   - 悬停显示详细信息

5. **主动问候**
   - 间隔 > 6小时：简单问候
   - 间隔 > 3天：带想念感

## 技术亮点

1. **多维度情绪计算**
   - LLM 情感分析 + 关键词检测 + 时间因素 + 亲密度
   - 避免简单规则匹配

2. **TTS 纯净原则**
   - Prompt 严格禁止非语音内容
   - 只影响语气和风格，不添加描述

3. **渐进式架构**
   - 数据库字段预留
   - 定时任务预留
   - 记忆情感标签预留
   - 便于后续扩展 TTS 和 Live2D

4. **低调展示**
   - 情绪图标小而精致
   - 不干扰对话主体
   - 悬停查看详情

## 后续优化方向

1. **情绪衰减定时任务**
   - 使用 APScheduler 每小时执行
   - melancholy → calm 自然恢复
   - energy 自然恢复 +5/小时

2. **情绪驱动 TTS**
   - 根据 emotion_type 调整语速、音调
   - melancholy：慢速、低沉
   - happy：正常速度、轻快

3. **情绪驱动 Live2D**
   - 根据 emotion_type 选择表情
   - 根据 mood 值调整动作幅度

4. **记忆情感优先**
   - emotional_intensity 高的记忆优先回忆
   - 相同情绪的记忆更容易触发

## 注意事项

1. **数据库迁移必须执行**
   - 否则会因字段不存在报错

2. **LLM 调用增加**
   - 每次对话增加 1 次情感分析调用
   - 注意 API 配额

3. **响应延迟**
   - 用户可能感觉"变慢了"
   - 但这是为了更真实的交互体验

4. **情绪图标**
   - 仅 assistant 消息显示
   - user 消息不显示

---

**实施完成时间**: 2026-03-05  
**实施人员**: Kiro AI Assistant  
**测试状态**: 待用户验证
