#!/usr/bin/env python
"""
测试脚本 - Step3: 多维度内容分析
选择3个note进行分析以提高测试效率
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import List

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from xhs_note_analyzer.crews.content_analyzer_crew import create_content_analyzer
from xhs_note_analyzer.main import NoteContentData, NoteData

# 配置测试日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_step3_multi_dimensional_analysis.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_step2_results(step2_output_dir: str = "tests/output/step2") -> List[NoteContentData]:
    """从Step2的结果中加载笔记内容数据"""
    try:
        # 尝试从step2_content_results.json加载
        result_file = Path(step2_output_dir) / "step2_content_results.json"
        if result_file.exists():
            with open(result_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if "detailed_notes" in data:
                    detailed_notes = []
                    for note_data in data["detailed_notes"]:
                        # 重建NoteContentData对象
                        basic_info = NoteData(**note_data["basic_info"])
                        note = NoteContentData(
                            note_id=note_data["note_id"],
                            title=note_data["title"],
                            basic_info=basic_info,
                            content=note_data["content"],
                            images=note_data.get("images", []),
                            video_url=note_data.get("video_url", ""),
                            author_info=note_data.get("author_info", {}),
                            tags=note_data.get("tags", []),
                            create_time=note_data.get("create_time", "")
                        )
                        detailed_notes.append(note)
                    return detailed_notes
        
        logger.warning("未找到Step2的结果数据，使用模拟数据")
        return create_mock_detailed_notes()
        
    except Exception as e:
        logger.error(f"加载Step2结果失败: {e}")
        return create_mock_detailed_notes()

def create_mock_detailed_notes() -> List[NoteContentData]:
    """创建模拟的详细笔记数据用于测试"""
    mock_notes = []
    
    # 笔记1：求职攻略
    basic_info_1 = NoteData(
        note_id="676a4d0a000000001f00c58a",
        note_title="国企求职攻略分享",
        note_url="https://www.xiaohongshu.com/explore/676a4d0a000000001f00c58a",
        impression=50000, click=8000, like=1200, collect=800, comment=150, engage=2150
    )
    
    note_1 = NoteContentData(
        note_id="676a4d0a000000001f00c58a",
        title="国企求职攻略分享",
        basic_info=basic_info_1,
        content="""🔥国企求职全攻略｜从0到offer的完整路径

📌痛点分析：
很多小伙伴觉得国企门槛高、竞争激烈，不知道从何入手

✨核心策略：
1️⃣简历包装：突出稳定性和团队合作能力
2️⃣笔试准备：行测+专业知识双管齐下  
3️⃣面试技巧：展现价值观匹配度
4️⃣内推渠道：学会利用校友资源

💡实用tips：
• 关注央企官网招聘信息
• 准备标准化简历模板
• 模拟面试练习表达能力

想了解更多求职干货，关注我！每天分享职场成长秘籍～""",
        images=[
            "https://example.com/career-guide-1.jpg",
            "https://example.com/career-tips-2.jpg", 
            "https://example.com/interview-skills-3.jpg"
        ],
        author_info={
            "name": "职场导师小王",
            "followers": 15000,
            "user_id": "career_mentor_wang"
        },
        tags=["国企求职", "面试技巧", "职场攻略", "求职指导", "简历优化"],
        create_time="2024-01-15 14:30:00"
    )
    mock_notes.append(note_1)
    
    # 笔记2：面试技巧
    basic_info_2 = NoteData(
        note_id="676a4d0a000000001f00c58b",
        note_title="央企面试技巧大全",
        note_url="https://www.xiaohongshu.com/explore/676a4d0a000000001f00c58b",
        impression=30000, click=5000, like=800, collect=500, comment=100, engage=1400
    )
    
    note_2 = NoteContentData(
        note_id="676a4d0a000000001f00c58b",
        title="央企面试技巧大全",
        basic_info=basic_info_2,
        content="""央企面试通关秘籍｜让面试官眼前一亮的技巧

🎯面试痛点：
• 紧张到说不出话
• 不知道如何展示自己
• 担心回答不够专业

💪解决方案：
【自我介绍篇】
30秒黄金法则：基本信息+核心优势+匹配度

【专业问题篇】
STAR法则：情境+任务+行动+结果

【压力面试篇】
保持冷静，逐步分析问题

🔥实战演练：
问：为什么选择我们公司？
答：贵公司的企业文化与我的价值观高度匹配，我希望在这里...

记住：面试是双向选择，展现真实的自己！""",
        images=[
            "https://example.com/interview-tips-1.jpg",
            "https://example.com/star-method-2.jpg"
        ],
        author_info={
            "name": "HR小李",
            "followers": 8000,
            "user_id": "hr_expert_li"
        },
        tags=["央企面试", "面试准备", "STAR法则", "自我介绍", "职场技能"],
        create_time="2024-01-20 16:45:00"
    )
    mock_notes.append(note_2)
    
    # 笔记3：简历模板
    basic_info_3 = NoteData(
        note_id="676a4d0a000000001f00c58c",
        note_title="求职简历模板分享",
        note_url="https://www.xiaohongshu.com/explore/676a4d0a000000001f00c58c",
        impression=40000, click=6500, like=1000, collect=600, comment=120, engage=1720
    )
    
    note_3 = NoteContentData(
        note_id="676a4d0a000000001f00c58c",
        title="求职简历模板分享",
        basic_info=basic_info_3,
        content="""📄超实用简历模板免费送｜HR最爱的简历长这样

⚡常见简历问题：
❌内容冗长，重点不突出
❌格式混乱，缺乏逻辑
❌千篇一律，没有亮点

✅优化后的简历模板：
【基本信息区】
姓名、联系方式、求职意向

【教育背景】
学历+GPA+核心课程+获奖情况

【项目经历】 
项目名称+角色+成果+技能

【实习经历】
公司+岗位+业绩+收获

📋模板特色：
🎨简约大气的设计风格
📊清晰的信息层级结构
⭐突出个人核心竞争力

💬评论区回复"简历"即可获取模板
一起助力求职成功！""",
        images=[
            "https://example.com/resume-template-1.jpg",
            "https://example.com/resume-example-2.jpg",
            "https://example.com/resume-tips-3.jpg"
        ],
        author_info={
            "name": "求职助手",
            "followers": 12000,
            "user_id": "job_helper"
        },
        tags=["简历模板", "简历制作", "求职准备", "职场工具", "免费资源"],
        create_time="2024-01-18 10:15:00"
    )
    mock_notes.append(note_3)
    
    return mock_notes

def test_content_analyzer_creation():
    """测试内容分析器创建"""
    print("🔧 测试内容分析器创建...")
    
    try:
        analyzer = create_content_analyzer()
        print("✅ ContentAnalyzerCrew 创建成功")
        
        # 检查LLM配置
        if hasattr(analyzer, 'llm'):
            print(f"✅ LLM配置正常: {analyzer.llm.model_name}")
        else:
            print("⚠️ 无法检查LLM配置")
            
        return True, analyzer
        
    except Exception as e:
        logger.error(f"ContentAnalyzer创建失败: {e}")
        print(f"❌ 创建失败: {e}")
        return False, None

async def test_single_note_analysis(analyzer, note_data: NoteContentData):
    """测试单个笔记分析"""
    print(f"\n🔍 测试单个笔记分析: {note_data.title}")
    
    try:
        # 执行分析
        analysis_result = analyzer.analyze_single_note(note_data)
        
        print("✅ 单笔记分析完成")
        print(f"  综合评分: {analysis_result.overall_score:.1f}/100")
        print(f"  可复制性: {analysis_result.replicability_score:.1f}/100")
        print(f"  成功要素: {len(analysis_result.success_factors)} 个")
        
        # 显示各维度分析结果
        print("  📝 内容结构分析:")
        sa = analysis_result.structure_analysis
        if sa.title_pattern:
            print(f"    标题模式: {sa.title_pattern}")
        if sa.opening_strategy:
            print(f"    开头策略: {sa.opening_strategy}")
        
        print("  💝 情感价值分析:")
        ea = analysis_result.emotional_analysis
        if ea.pain_points:
            print(f"    痛点挖掘: {', '.join(ea.pain_points[:2])}...")
        if ea.value_propositions:
            print(f"    价值主张: {', '.join(ea.value_propositions[:2])}...")
        
        print("  🎨 视觉元素分析:")
        va = analysis_result.visual_analysis
        if va.image_style:
            print(f"    图片风格: {va.image_style}")
        if va.color_scheme:
            print(f"    色彩方案: {va.color_scheme}")
        
        return True, analysis_result
        
    except Exception as e:
        logger.warning(f"单笔记分析失败: {e}")
        print(f"  ❌ 分析失败: {e}")
        return False, None

async def test_step3_multi_dimensional_analysis():
    """测试Step3：多维度内容分析"""
    print("\n🚀 开始测试 Step3: 多维度内容分析")
    print("=" * 60)
    
    try:
        # 加载Step2的结果，限制为3个笔记
        print("📥 加载 Step2 结果数据...")
        detailed_notes = load_step2_results()
        
        # 限制只分析前3个笔记
        if len(detailed_notes) > 3:
            detailed_notes = detailed_notes[:3]
            print(f"✂️ 限制分析数量为3个笔记")
        
        print(f"加载到 {len(detailed_notes)} 条详细笔记数据")
        
        if not detailed_notes:
            print("❌ 没有可用的详细笔记数据")
            return False
        
        # 显示将要分析的笔记
        print("\n📋 待分析的笔记:")
        for i, note in enumerate(detailed_notes, 1):
            print(f"  {i}. {note.title}")
            print(f"     内容长度: {len(note.content)} 字符")
            print(f"     图片数量: {len(note.images)} 张")
        
        # 创建分析器
        analyzer_ok, analyzer = test_content_analyzer_creation()
        if not analyzer_ok:
            print("❌ 分析器创建失败，无法继续测试")
            return False
        
        output_dir = "tests/output/step3"
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # 执行批量分析
        print(f"\n🧠 开始多维度内容分析...")
        
        try:
            # 使用批量分析方法
            analysis_report = analyzer.analyze_multiple_notes(detailed_notes)
            
            print("✅ 批量分析完成")
            print(f"📊 分析摘要:")
            print(f"  分析笔记数: {analysis_report.total_notes}")
            print(f"  平均评分: {analysis_report.average_score:.1f}/100")
            print(f"  识别成功公式: {len(analysis_report.success_formulas)}")
            print(f"  提取共同模式: {len(analysis_report.common_patterns)}")
            
            # 显示成功公式
            if analysis_report.success_formulas:
                print(f"\n🎯 识别的成功公式:")
                for i, formula in enumerate(analysis_report.success_formulas[:3], 1):
                    print(f"  {i}. {formula}")
            
            # 显示共同模式
            if analysis_report.common_patterns:
                print(f"\n🔍 发现的共同模式:")
                for pattern_type, patterns in analysis_report.common_patterns.items():
                    if patterns:
                        print(f"  {pattern_type}: {', '.join(patterns[:2])}...")
            
            # 保存分析结果
            print(f"\n💾 保存分析结果...")
            analyzer.save_analysis_results(analysis_report, output_dir)
            
            # 额外保存测试专用的结果文件
            test_result_file = Path(output_dir) / "step3_analysis_test_results.json"
            with open(test_result_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "test_timestamp": str(asyncio.get_event_loop().time()),
                    "test_status": "success",
                    "analysis_summary": {
                        "total_notes": analysis_report.total_notes,
                        "average_score": analysis_report.average_score,
                        "success_formulas_count": len(analysis_report.success_formulas),
                        "common_patterns_count": len(analysis_report.common_patterns)
                    },
                    "detailed_results": analysis_report.model_dump()
                }, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 测试结果已保存到: {test_result_file}")
            
            return True
            
        except Exception as analysis_error:
            logger.error(f"批量分析失败: {analysis_error}")
            print(f"❌ 批量分析失败: {analysis_error}")
            
            # 尝试单个分析作为fallback
            print("🔄 尝试单个笔记分析...")
            successful_analyses = 0
            
            for note in detailed_notes:
                success, result = await test_single_note_analysis(analyzer, note)
                if success:
                    successful_analyses += 1
            
            print(f"单个分析结果: {successful_analyses}/{len(detailed_notes)} 成功")
            return successful_analyses > 0
        
    except Exception as e:
        logger.error(f"❌ Step3 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def validate_step3_output(output_dir: str):
    """验证Step3的输出文件"""
    print("\n🔍 验证 Step3 输出文件...")
    
    output_path = Path(output_dir)
    expected_files = [
        "content_analysis_results.json",  # ContentAnalyzer保存的文件
        "content_analysis_report.md",
        "content_analysis_summary.txt",
        "step3_analysis_test_results.json"  # 测试专用结果文件
    ]
    
    found_files = []
    missing_files = []
    
    for file_name in expected_files:
        file_path = output_path / file_name
        if file_path.exists():
            found_files.append(file_name)
            file_size = file_path.stat().st_size
            print(f"✅ 找到文件: {file_path} ({file_size} bytes)")
        else:
            missing_files.append(file_name)
    
    if missing_files:
        print(f"⚠️ 缺失文件: {missing_files}")
    else:
        print("✅ 所有预期文件都已生成")
    
    # 检查核心文件的内容
    core_file = output_path / "step3_analysis_test_results.json"
    if core_file.exists():
        try:
            with open(core_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data.get("test_status") == "success":
                    print("✅ 测试结果文件内容验证通过")
                else:
                    print("⚠️ 测试结果文件显示测试失败")
        except Exception as e:
            print(f"⚠️ 无法读取测试结果文件: {e}")
    
    return len(found_files) >= 2  # 至少要有2个关键文件

async def main():
    """主测试函数"""
    print("🧪 Step3 多维度内容分析 - 测试脚本")
    print("=" * 80)
    
    # 执行主要测试
    success1 = await test_step3_multi_dimensional_analysis()
    
    # 验证输出
    success2 = validate_step3_output("tests/output/step3")
    
    # 总结
    print("\n" + "=" * 80)
    print("📊 Step3 测试总结:")
    print(f"多维度分析测试: {'✅ 通过' if success1 else '❌ 失败'}")
    print(f"输出验证测试: {'✅ 通过' if success2 else '❌ 失败'}")
    
    overall_success = success1 and success2
    print(f"\n🎯 整体测试结果: {'✅ 全部通过' if overall_success else '❌ 存在失败'}")
    
    if overall_success:
        print("\n✨ Step3 测试完成，可以继续执行 Step4 测试")
        print("💡 提示: Step3 的分析结果将被 Step4 用于策略制定")
        print("🔍 分析维度包括:")
        print("  1️⃣ 内容结构分析 (标题-开头-正文-结尾)")
        print("  2️⃣ 情感价值分析 (痛点挖掘-价值主张)")  
        print("  3️⃣ 视觉元素分析 (配图风格-排版特点)")
    else:
        print("\n⚠️ 请检查并修复失败的测试项")
        print("🔧 常见问题:")
        print("  - 检查OPENROUTER_API_KEY是否正确设置")
        print("  - 确认网络连接正常")
        print("  - 检查Step2的输出数据是否存在")
    
    return overall_success

if __name__ == "__main__":
    # 检查环境变量
    import os
    if not os.getenv("OPENROUTER_API_KEY"):
        print("❌ 错误: 未设置 OPENROUTER_API_KEY 环境变量")
        print("Step3 需要 OpenRouter API 来进行多维度分析")
        print("请设置环境变量: export OPENROUTER_API_KEY='your_api_key'")
        sys.exit(1)
    else:
        print(f"✅ OpenRouter API Key 已配置")
    
    print()
    
    # 运行测试
    result = asyncio.run(main())
    
    # 退出码
    sys.exit(0 if result else 1)