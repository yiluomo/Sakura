"""
测试长期记忆功能
"""
import asyncio
import sys
import os

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


from memory.long_term import check_memory_trigger, confirm_save_memory, _detect_memory_type

async def test_detect_memory_type():
    """测试记忆类型检测"""
    print("=" * 50)
    print("测试记忆类型检测")
    print("=" * 50)
    
    test_cases = [
        ("我叫依洛沐", "name"),
        ("我喜欢看书", "hobby"),
        ("我讨厌辣的", "dislike"),
        ("我的家人很好", "family"),
        ("我的朋友叫小明", "friend"),
        ("我的生日是3月15日", "birthday"),
        ("我今年25岁", "age"),
        ("我住在北京", "location"),
        ("我的工作是程序员", "occupation"),
        ("我曾经去过日本", "experience"),
        ("今天天气很好", None),  # 无关键词
    ]
    
    for content, expected_type in test_cases:
        result = _detect_memory_type(content)
        detected_type = result["type"] if result else None
        status = "✓" if detected_type == expected_type else "✗"
        print(f"{status} '{content}' -> {detected_type} (期望: {expected_type})")

async def test_maybe_save_long_term():
    """测试长期记忆保存逻辑"""
    print("\n" + "=" * 50)
    print("测试长期记忆保存逻辑")
    print("=" * 50)
    
    test_cases = [
        ("记住我叫依洛沐", True, "name"),
        ("记住我喜欢编程", True, "hobby"),
        ("你好", False, None),  # 不以"记住"开头
        ("记住今天很开心", True, "manual"),  # 无关键词，保存为通用记忆
    ]
    
    for message, should_trigger, expected_type in test_cases:
        result = await check_memory_trigger("test_user", message)
        triggered = result is not None
        detected_type = result["memory_type"] if result else None
        status = "✓" if triggered == should_trigger else "✗"
        
        if should_trigger:
            type_match = "✓" if detected_type == expected_type else "✗"
            print(f"{status} '{message}' -> 触发: {triggered}, 类型: {detected_type} {type_match}")
            if triggered:
                # 确认保存测试
                confirm_res = await confirm_save_memory("test_user", result)
                confirm_status = "✓" if confirm_res else "✗"
                print(f"   {confirm_status} 确认保存: {confirm_res}")
        else:
            print(f"{status} '{message}' -> 触发: {triggered}")

async def main():
    """主测试函数"""
    print("\n开始测试长期记忆功能\n")
    
    # 初始化数据库和模型相关以做真实测试
    from db.database import init_db
    try:
        await init_db()
        print("数据库连接及表创建成功。")
    except Exception as e:
        print(f"数据库连接失败: {e}，将使用内存或 Mock 测试。")
    
    # 测试1：记忆类型检测
    await test_detect_memory_type()
    
    # 测试2：长期记忆保存逻辑
    await test_maybe_save_long_term()
    
    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())

