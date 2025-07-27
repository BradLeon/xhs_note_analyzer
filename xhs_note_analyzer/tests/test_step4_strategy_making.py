#!/usr/bin/env python
"""
测试脚本 - Step4: 实战策略制定
基于Step3的内容分析结果制定实战策略
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from xhs_note_analyzer.crews.strategy_maker_crew import create_strategy_maker
from xhs_note_analyzer.crews.content_analyzer_crew.models import ContentAnalysisReport
from xhs_note_analyzer.main import NoteContentData, NoteData

# 配置测试日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_step4_strategy_making.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_step3_results(step3_output_dir: str = "tests/output/step3") -> ContentAnalysisReport:
    """从Step3的结果中加载内容分析报告"""
    try:
        # 尝试从step3_analysis_test_results.json加载
        test_result_file = Path(step3_output_dir) / "step3_analysis_test_results.json"
        if test_result_file.exists():
            with open(test_result_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if "detailed_results" in data:
                    report_data = data["detailed_results"]
                    return ContentAnalysisReport(**report_data)
        
        # 尝试从content_analysis_results.json加载
        analysis_file = Path(step3_output_dir) / "content_analysis_results.json"
        if analysis_file.exists():
            with open(analysis_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return ContentAnalysisReport(**data)
        
        logger.warning("未找到Step3的结果数据，使用模拟数据")
        return create_mock_analysis_report()
        
    except Exception as e:
        logger.error(f"加载Step3结果失败: {e}")
        return create_mock_analysis_report()

def create_mock_analysis_report() -> ContentAnalysisReport:
    """创建模拟的内容分析报告用于测试"""
    from xhs_note_analyzer.crews.content_analyzer_crew.models import (
        ContentAnalysisResult, ContentStructureAnalysis, 
        EmotionalValueAnalysis, VisualElementAnalysis
    )
    from datetime import datetime
    
    # 创建模拟的分析结果
    analysis_results = []
    
    # 笔记1分析结果
    structure_analysis_1 = ContentStructureAnalysis(
        note_id="676a4d0a000000001f00c58a",
        title_pattern="数字+痛点+解决方案",
        opening_strategy="痛点共鸣开头",
        content_framework="问题-方案-总结",
        ending_technique="行动号召",
        structure_score=85.0
    )
    
    emotional_analysis_1 = EmotionalValueAnalysis(
        note_id="676a4d0a000000001f00c58a",
        pain_points=["求职竞争激烈", "不知从何入手", "面试紧张"],
        value_propositions=["完整求职路径", "实用面试技巧", "内推资源"],
        emotional_triggers=["焦虑缓解", "希望激发", "信心建立"],
        emotional_score=82.0
    )
    
    visual_analysis_1 = VisualElementAnalysis(
        note_id="676a4d0a000000001f00c58a",
        image_style="信息图表风格",
        color_scheme="商务蓝+白色",
        layout_style="左图右文",
        visual_score=78.0
    )
    
    result_1 = ContentAnalysisResult(
        note_id="676a4d0a000000001f00c58a",
        note_title="国企求职攻略分享",
        structure_analysis=structure_analysis_1,
        emotional_analysis=emotional_analysis_1,
        visual_analysis=visual_analysis_1,
        overall_score=83.5,
        success_factors=[
            "结构清晰的内容框架",
            "精准的痛点挖掘", 
            "实用的解决方案",
            "专业的视觉呈现"
        ],
        improvement_suggestions=[
            "增加更多具体案例",
            "优化视觉层次"
        ],
        replicability_score=80.0,
        analysis_timestamp=datetime.now().isoformat()
    )
    analysis_results.append(result_1)
    
    # 笔记2分析结果
    structure_analysis_2 = ContentStructureAnalysis(
        note_id="676a4d0a000000001f00c58b",
        title_pattern="场景+技巧+效果",
        opening_strategy="场景代入开头",
        content_framework="问题-技巧-实例",
        ending_technique="信心鼓励",
        structure_score=80.0
    )
    
    emotional_analysis_2 = EmotionalValueAnalysis(
        note_id="676a4d0a000000001f00c58b",
        pain_points=["面试紧张", "不知如何表达", "缺乏专业性"],
        value_propositions=["系统面试方法", "实战技巧", "心理建设"],
        emotional_triggers=["紧张缓解", "自信建立", "专业提升"],
        emotional_score=85.0
    )
    
    visual_analysis_2 = VisualElementAnalysis(
        note_id="676a4d0a000000001f00c58b",
        image_style="实景拍摄",
        color_scheme="温暖橙色系",
        layout_style="单图配文",
        visual_score=75.0
    )
    
    result_2 = ContentAnalysisResult(
        note_id="676a4d0a000000001f00c58b",
        note_title="央企面试技巧大全",
        structure_analysis=structure_analysis_2,
        emotional_analysis=emotional_analysis_2,
        visual_analysis=visual_analysis_2,
        overall_score=81.0,
        success_factors=[
            "贴近用户场景",
            "专业方法论",
            "情感共鸣强",
            "温暖的视觉风格"
        ],
        improvement_suggestions=[
            "增加更多实战案例",
            "优化内容结构"
        ],
        replicability_score=78.0,
        analysis_timestamp=datetime.now().isoformat()
    )
    analysis_results.append(result_2)
    
    # 笔记3分析结果
    structure_analysis_3 = ContentStructureAnalysis(
        note_id="676a4d0a000000001f00c58c",
        title_pattern="工具+免费+价值",
        opening_strategy="问题列举开头",
        content_framework="问题-工具-获取",
        ending_technique="互动引导",
        structure_score=88.0
    )
    
    emotional_analysis_3 = EmotionalValueAnalysis(
        note_id="676a4d0a000000001f00c58c",
        pain_points=["简历不够专业", "格式混乱", "缺乏亮点"],
        value_propositions=["专业模板", "免费获取", "HR偏好"],
        emotional_triggers=["问题解决", "免费获得", "专业提升"],
        emotional_score=87.0
    )
    
    visual_analysis_3 = VisualElementAnalysis(
        note_id="676a4d0a000000001f00c58c",
        image_style="模板展示",
        color_scheme="清新绿色",
        layout_style="多图网格",
        visual_score=85.0
    )
    
    result_3 = ContentAnalysisResult(
        note_id="676a4d0a000000001f00c58c",
        note_title="求职简历模板分享",
        structure_analysis=structure_analysis_3,
        emotional_analysis=emotional_analysis_3,
        visual_analysis=visual_analysis_3,
        overall_score=86.5,
        success_factors=[
            "明确的价值主张",
            "免费资源吸引",
            "专业模板展示",
            "有效的互动设计"
        ],
        improvement_suggestions=[
            "增加使用指导",
            "提供更多样式"
        ],
        replicability_score=85.0,
        analysis_timestamp=datetime.now().isoformat()
    )
    analysis_results.append(result_3)
    
    # 创建分析报告
    report = ContentAnalysisReport(
        analysis_results=analysis_results,
        total_notes=3,
        average_score=83.7,
        common_patterns={
            "标题模式": ["数字+痛点+解决方案", "场景+技巧+效果", "工具+免费+价值"],
            "开头策略": ["痛点共鸣", "场景代入", "问题列举"],
            "视觉风格": ["信息图表", "实景拍摄", "模板展示"],
            "互动技巧": ["行动号召", "信心鼓励", "互动引导"]
        },
        success_formulas=[
            "清晰的内容结构 + 精准的痛点挖掘",
            "专业的解决方案 + 温暖的视觉风格", 
            "免费价值提供 + 有效互动设计"
        ],
        report_timestamp=datetime.now().isoformat(),
        report_summary="基于3篇优质笔记的深度分析，识别核心成功要素"
    )
    
    return report

def test_strategy_maker_creation():
    """测试策略制定器创建"""
    print("🔧 测试策略制定器创建...")
    
    try:
        strategy_maker = create_strategy_maker()
        print("✅ StrategyMakerCrew 创建成功")
        
        # 检查LLM配置
        if hasattr(strategy_maker, 'llm'):
            print(f"✅ LLM配置正常: {strategy_maker.llm.model_name}")
        else:
            print("⚠️ 无法检查LLM配置")
            
        return True, strategy_maker
        
    except Exception as e:
        logger.error(f"StrategyMaker创建失败: {e}")
        print(f"❌ 创建失败: {e}")
        return False, None

async def test_step4_strategy_making():
    """测试Step4：实战策略制定"""
    print("\n🚀 开始测试 Step4: 实战策略制定")
    print("=" * 60)
    
    try:
        # 加载Step3的结果
        print("📥 加载 Step3 内容分析报告...")
        analysis_report = load_step3_results()
        print(f"加载分析报告: {analysis_report.total_notes} 个笔记，平均评分 {analysis_report.average_score:.1f}")
        
        # 显示分析报告概要
        print("\n📊 分析报告概要:")
        print(f"  成功公式数量: {len(analysis_report.success_formulas)}")
        print(f"  共同模式类型: {len(analysis_report.common_patterns)}")
        if analysis_report.success_formulas:
            print(f"  核心成功公式:")
            for i, formula in enumerate(analysis_report.success_formulas[:2], 1):
                print(f"    {i}. {formula}")
        
        # 创建策略制定器
        maker_ok, strategy_maker = test_strategy_maker_creation()
        if not maker_ok:
            print("❌ 策略制定器创建失败，无法继续测试")
            return False
        
        # 准备业务参数
        business_context = """
        我们是一家专注于国企央企求职辅导的教育服务机构。
        主要提供求职指导、面试培训、简历优化等服务。
        目标用户是准备进入国企央企工作的求职者。
        """
        
        target_product = "国企央企求职辅导小程序"
        
        business_goals = {
            "target_audience": "25-35岁准备进入国企央企的求职者",
            "content_volume": "每周发布3-5篇内容",
            "conversion_goal": "小程序注册用户数提升50%",
            "time_frame": "3个月内完成策略实施",
            "budget_constraint": "中等预算，注重ROI"
        }
        
        print(f"\n🎯 策略制定参数:")
        print(f"  目标产品: {target_product}")
        print(f"  目标用户: {business_goals['target_audience']}")
        print(f"  转化目标: {business_goals['conversion_goal']}")
        
        output_dir = "tests/output/step4"
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # 执行策略制定
        print(f"\n🧠 开始实战策略制定...")
        
        try:
            strategy_report = strategy_maker.make_strategy(
                business_context=business_context,
                target_product=target_product,
                content_analysis_report=analysis_report,
                business_goals=business_goals
            )
            
            print("✅ 策略制定完成")
            print(f"📊 策略摘要:")
            print(f"  策略版本: {strategy_report.strategy_version}")
            print(f"  有效期: {strategy_report.validity_period}")
            print(f"  核心建议数: {len(strategy_report.key_recommendations)}")
            print(f"  成功要素数: {len(strategy_report.success_factors)}")
            
            # 显示核心建议
            if strategy_report.key_recommendations:
                print(f"\n🎯 核心建议:")
                for i, rec in enumerate(strategy_report.key_recommendations[:3], 1):
                    print(f"  {i}. {rec}")
            
            # 显示选题策略
            if strategy_report.topic_strategy.trending_topics:
                print(f"\n📝 选题策略:")
                print(f"  热门选题数: {len(strategy_report.topic_strategy.trending_topics)}")
                for i, topic in enumerate(strategy_report.topic_strategy.trending_topics[:3], 1):
                    print(f"    {i}. {topic}")
            
            # 显示TA策略
            if strategy_report.target_audience_strategy.primary_persona:
                print(f"\n👥 目标用户画像:")
                persona = strategy_report.target_audience_strategy.primary_persona
                for key, value in list(persona.items())[:3]:
                    print(f"    {key}: {value}")
            
            # 显示创作指南
            print(f"\n🎨 内容创作指南:")
            guide = strategy_report.content_creation_guide
            if guide.copywriting_guide.title_templates:
                print(f"  标题模板: {len(guide.copywriting_guide.title_templates)} 个")
            if guide.visual_guide.style_direction:
                print(f"  视觉风格: {guide.visual_guide.style_direction}")
            
            # 保存策略结果
            print(f"\n💾 保存策略结果...")
            strategy_maker.save_strategy_results(strategy_report, output_dir)
            
            # 额外保存测试专用的结果文件
            test_result_file = Path(output_dir) / "step4_strategy_test_results.json"
            with open(test_result_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "test_timestamp": str(asyncio.get_event_loop().time()),
                    "test_status": "success",
                    "strategy_summary": {
                        "target_product": strategy_report.target_product,
                        "key_recommendations_count": len(strategy_report.key_recommendations),
                        "success_factors_count": len(strategy_report.success_factors),
                        "differentiation_points_count": len(strategy_report.differentiation_points),
                        "topic_strategy_topics_count": len(strategy_report.topic_strategy.trending_topics)
                    },
                    "detailed_results": strategy_report.model_dump()
                }, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 测试结果已保存到: {test_result_file}")
            
            return True
            
        except Exception as strategy_error:
            logger.error(f"策略制定失败: {strategy_error}")
            print(f"❌ 策略制定失败: {strategy_error}")
            import traceback
            traceback.print_exc()
            return False
        
    except Exception as e:
        logger.error(f"❌ Step4 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def validate_step4_output(output_dir: str):
    """验证Step4的输出文件"""
    print("\n🔍 验证 Step4 输出文件...")
    
    output_path = Path(output_dir)
    expected_files = [
        "strategy_report.json",      # StrategyMaker保存的文件
        "strategy_report.md",
        "strategy_summary.txt",
        "step4_strategy_test_results.json"  # 测试专用结果文件
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
    core_file = output_path / "step4_strategy_test_results.json"
    if core_file.exists():
        try:
            with open(core_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data.get("test_status") == "success":
                    print("✅ 测试结果文件内容验证通过")
                    
                    # 检查策略组件的完整性
                    summary = data.get("strategy_summary", {})
                    print(f"  策略组件检查:")
                    print(f"    核心建议: {summary.get('key_recommendations_count', 0)} 条")
                    print(f"    成功要素: {summary.get('success_factors_count', 0)} 个")
                    print(f"    选题建议: {summary.get('topic_strategy_topics_count', 0)} 个")
                else:
                    print("⚠️ 测试结果文件显示测试失败")
        except Exception as e:
            print(f"⚠️ 无法读取测试结果文件: {e}")
    
    return len(found_files) >= 2  # 至少要有2个关键文件

async def main():
    """主测试函数"""
    print("🧪 Step4 实战策略制定 - 测试脚本")
    print("=" * 80)
    
    # 执行主要测试
    success1 = await test_step4_strategy_making()
    
    # 验证输出
    success2 = validate_step4_output("tests/output/step4")
    
    # 总结
    print("\n" + "=" * 80)
    print("📊 Step4 测试总结:")
    print(f"策略制定测试: {'✅ 通过' if success1 else '❌ 失败'}")
    print(f"输出验证测试: {'✅ 通过' if success2 else '❌ 失败'}")
    
    overall_success = success1 and success2
    print(f"\n🎯 整体测试结果: {'✅ 全部通过' if overall_success else '❌ 存在失败'}")
    
    if overall_success:
        print("\n✨ Step4 测试完成，四步骤测试全部完成！")
        print("🎉 完整的XHS内容分析与策略制定流程测试通过")
        print("🔍 策略制定包括:")
        print("  1️⃣ 选题策略 - 热门选题挖掘、关键词策略、竞争分析")
        print("  2️⃣ TA策略 - 用户画像、需求分析、触达策略")  
        print("  3️⃣ 内容创作指导 - 文案指南、配图指南、视频脚本")
    else:
        print("\n⚠️ 请检查并修复失败的测试项")
        print("🔧 常见问题:")
        print("  - 检查OPENROUTER_API_KEY是否正确设置")
        print("  - 确认网络连接正常")
        print("  - 检查Step3的分析报告数据是否存在")
    
    return overall_success

if __name__ == "__main__":
    # 检查环境变量
    import os
    if not os.getenv("OPENROUTER_API_KEY"):
        print("❌ 错误: 未设置 OPENROUTER_API_KEY 环境变量")
        print("Step4 需要 OpenRouter API 来进行策略制定")
        print("请设置环境变量: export OPENROUTER_API_KEY='your_api_key'")
        sys.exit(1)
    else:
        print(f"✅ OpenRouter API Key 已配置")
    
    print()
    
    # 运行测试
    result = asyncio.run(main())
    
    # 退出码
    sys.exit(0 if result else 1)