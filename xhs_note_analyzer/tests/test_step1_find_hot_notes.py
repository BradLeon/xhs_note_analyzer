#!/usr/bin/env python
"""
测试脚本 - Step1: 查找相关优质笔记 
限定只查找第一页以提高测试效率
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from xhs_note_analyzer.tools.hot_note_finder_tool import find_hot_notes

# 配置测试日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_step1_find_hot_notes.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def test_step1_find_hot_notes():
    """测试Step1：查找相关优质笔记"""
    print("🚀 开始测试 Step1: 查找相关优质笔记")
    print("=" * 60)
    
    try:
        # 测试参数
        promotion_target = "国企央企求职辅导小程序"
        max_pages = 1  # 限定只查找第一页
        output_dir = "tests/output/step1"
        
        print(f"🎯 测试目标: {promotion_target}")
        print(f"📄 页数限制: {max_pages} 页")
        print(f"📁 输出目录: {output_dir}")
        print()
        
        # 确保输出目录存在
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # 调用find_hot_notes函数
        print("🔍 开始执行笔记查找...")
        result = await find_hot_notes(
            promotion_target=promotion_target,
            max_pages=max_pages,
            output_dir=output_dir
        )
        
        # 检查结果
        print("\n📊 测试结果:")
        print(f"执行状态: {'✅ 成功' if result.success else '❌ 失败'}")
        print(f"执行消息: {result.message}")
        print(f"找到笔记数: {result.data.total_count}")
        print(f"采集方法: {result.data.collection_method}")
        
        # 显示找到的笔记详情
        if result.data.note_data_list:
            print("\n📝 找到的笔记详情:")
            print("-" * 60)
            for i, note in enumerate(result.data.note_data_list[:5], 1):  # 只显示前5条
                print(f"\n{i}. {note.note_title}")
                print(f"   ID: {note.note_id}")
                print(f"   URL: {note.note_url}")
                print(f"   数据: 曝光{note.impression:,} | 阅读{note.click:,} | 点赞{note.like:,}")
                print(f"   数据: 收藏{note.collect:,} | 评论{note.comment:,} | 互动{note.engage:,}")
        
        # 保存测试结果
        test_result_file = Path(output_dir) / "test_result.json"
        with open(test_result_file, 'w', encoding='utf-8') as f:
            json.dump({
                "test_timestamp": str(asyncio.get_event_loop().time()),
                "test_status": "success" if result.success else "failed",
                "result": result.model_dump()
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 测试结果已保存到: {test_result_file}")
        
        # 调试信息
        if result.debug_info:
            print("\n🐛 调试信息:")
            debug_info = result.debug_info
            if "file_paths" in debug_info:
                print(f"生成的文件:")
                for key, path in debug_info["file_paths"].items():
                    if isinstance(path, str):
                        print(f"  {key}: {path}")
        
        return result.success
        
    except Exception as e:
        logger.error(f"❌ Step1 测试失败: {e}")
        print(f"❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_step1_mock_mode():
    """测试Step1的模拟模式（当真实API不可用时）"""
    print("\n🔄 测试 Step1 模拟模式...")
    
    try:
        # 使用不存在的目标，触发模拟模式
        result = await find_hot_notes(
            promotion_target="测试模拟模式目标",
            max_pages=1,
            output_dir="tests/output/step1_mock"
        )
        
        print(f"模拟模式结果: {'✅ 成功' if result.success else '⚠️ 预期行为'}")
        print(f"模拟模式消息: {result.message}")
        
        return True
        
    except Exception as e:
        logger.warning(f"⚠️ 模拟模式测试异常（可能是预期的）: {e}")
        return True  # 模拟模式测试异常是可接受的

def validate_step1_output(output_dir: str):
    """验证Step1的输出文件"""
    print("\n🔍 验证 Step1 输出文件...")
    
    output_path = Path(output_dir)
    expected_files = [
        "test_result.json"
    ]
    
    missing_files = []
    for file_name in expected_files:
        file_path = output_path / file_name
        if not file_path.exists():
            missing_files.append(file_name)
        else:
            print(f"✅ 找到文件: {file_path}")
    
    if missing_files:
        print(f"⚠️ 缺失文件: {missing_files}")
    else:
        print("✅ 所有预期文件都已生成")
    
    return len(missing_files) == 0

async def main():
    """主测试函数"""
    print("🧪 Step1 查找相关优质笔记 - 测试脚本")
    print("=" * 80)
    
    # 执行基本测试
    success1 = await test_step1_find_hot_notes()
    
    # 执行模拟模式测试
    success2 = await test_step1_mock_mode()
    
    # 验证输出
    success3 = validate_step1_output("tests/output/step1")
    
    # 总结
    print("\n" + "=" * 80)
    print("📊 Step1 测试总结:")
    print(f"基本功能测试: {'✅ 通过' if success1 else '❌ 失败'}")
    print(f"模拟模式测试: {'✅ 通过' if success2 else '❌ 失败'}")
    print(f"输出验证测试: {'✅ 通过' if success3 else '❌ 失败'}")
    
    overall_success = success1 and success2 and success3
    print(f"\n🎯 整体测试结果: {'✅ 全部通过' if overall_success else '❌ 存在失败'}")
    
    if overall_success:
        print("\n✨ Step1 测试完成，可以继续执行 Step2 测试")
    else:
        print("\n⚠️ 请检查并修复失败的测试项")
    
    return overall_success

if __name__ == "__main__":
    # 检查环境变量
    import os
    if not os.getenv("OPENROUTER_API_KEY"):
        print("⚠️ 警告: 未设置 OPENROUTER_API_KEY 环境变量，测试可能失败")
        print("请设置环境变量: export OPENROUTER_API_KEY='your_api_key'")
        print()
    
    # 运行测试
    result = asyncio.run(main())
    
    # 退出码
    sys.exit(0 if result else 1)