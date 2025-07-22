#!/usr/bin/env python
"""
小红书内容分析运行脚本
展示如何使用CrewAI Flow进行完整的三步骤分析流程
"""

import os
import sys
import asyncio
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.append(str(project_root / "src"))

from xhs_note_analyzer.main import (
    kickoff_content_analysis, 
    plot_content_analysis_flow,
    XHSContentAnalysisFlow
)


def check_environment():
    """检查环境配置"""
    print("🔍 检查环境配置...")
    
    required_env_vars = [
        "OPENROUTER_API_KEY"
    ]
    
    optional_env_vars = [
        "MEDIACRAWLER_API_ENDPOINT",
        "MEDIACRAWLER_API_KEY"
    ]
    
    # 检查必需的环境变量
    missing_vars = []
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ 缺少必需的环境变量: {', '.join(missing_vars)}")
        print("请设置以下环境变量：")
        for var in missing_vars:
            print(f"export {var}='your_value'")
        return False
    
    # 显示可选的环境变量状态
    print("✅ 必需环境变量已配置")
    print("\n📊 可选环境变量状态:")
    for var in optional_env_vars:
        value = os.getenv(var)
        status = "✅ 已配置" if value else "⚠️ 未配置"
        print(f"  {var}: {status}")
    
    return True


def display_analysis_options():
    """显示分析选项"""
    print("\n🎯 可用的分析场景:")
    print("1. 国企央企求职辅导")
    print("2. 考公考编培训")
    print("3. 职业技能培训")
    print("4. 学历提升教育")
    print("5. 自定义分析目标")
    
    choice = input("\n请选择分析场景 (1-5): ").strip()
    
    scenarios = {
        "1": {
            "target": "国企央企求职辅导小程序",
            "context": "专注于国企央企求职培训的教育机构，提供简历优化、面试指导、岗位匹配等服务"
        },
        "2": {
            "target": "考公考编上岸培训课程",
            "context": "专业的公务员和事业编制考试培训机构，提供笔试面试全流程辅导"
        },
        "3": {
            "target": "职业技能提升训练营",
            "context": "面向职场人士的技能培训平台，涵盖数字化办公、沟通技巧、项目管理等"
        },
        "4": {
            "target": "在职学历提升项目",
            "context": "为在职人员提供学历提升服务的教育机构，包括成人高考、自考、专升本等"
        },
        "5": {
            "target": input("请输入推广目标: ").strip(),
            "context": input("请描述业务背景: ").strip()
        }
    }
    
    return scenarios.get(choice, scenarios["1"])


def run_step_by_step_demo():
    """分步骤演示流程"""
    print("\n🎭 分步骤演示模式")
    print("这将演示三个步骤的执行过程，每步完成后暂停")
    
    scenario = display_analysis_options()
    
    # 创建流程实例
    flow = XHSContentAnalysisFlow()
    flow.state.promotion_target = scenario["target"]
    flow.state.business_context = scenario["context"]
    
    print(f"\n🚀 开始分析: {scenario['target']}")
    print(f"📝 业务背景: {scenario['context']}")
    
    try:
        # 步骤1: 初始化
        print("\n" + "="*60)
        print("步骤 0: 初始化分析流程")
        print("="*60)
        flow.initialize_analysis()
        input("按回车键继续到步骤1...")
        
        # 步骤1: 笔记发现
        print("\n" + "="*60)
        print("步骤 1: 查找相关优质笔记")
        print("="*60)
        flow.step1_find_hot_notes()
        print(f"✅ 找到 {len(flow.state.found_notes)} 条相关笔记")
        input("按回车键继续到步骤2...")
        
        # 步骤2: 内容获取
        print("\n" + "="*60)
        print("步骤 2: 获取笔记详细内容")
        print("="*60)
        flow.step2_fetch_note_content()
        print(f"✅ 获取了 {len(flow.state.detailed_notes)} 条详细内容")
        input("按回车键继续到步骤3...")
        
        # 步骤3: 智能分析
        print("\n" + "="*60)
        print("步骤 3: 智能分析并生成建议")
        print("="*60)
        flow.step3_analyze_and_advise()
        print(f"✅ 完成 {len(flow.state.content_analysis)} 条笔记分析")
        input("按回车键查看最终结果...")
        
        # 输出结果
        print("\n" + "="*60)
        print("最终结果输出")
        print("="*60)
        flow.finalize_and_output()
        
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断执行")
    except Exception as e:
        print(f"\n❌ 执行过程中出错: {e}")


def run_full_analysis():
    """运行完整分析流程"""
    print("\n🚀 完整分析模式")
    
    scenario = display_analysis_options()
    
    print(f"\n🎯 分析目标: {scenario['target']}")
    print(f"📝 业务背景: {scenario['context']}")
    
    # 确认执行
    confirm = input("\n是否开始执行？(y/N): ").strip().lower()
    if confirm != 'y':
        print("❌ 用户取消执行")
        return
    
    try:
        # 执行完整流程
        print("\n🔄 开始执行完整分析流程...")
        result = kickoff_content_analysis(
            promotion_target=scenario["target"],
            business_context=scenario["context"]
        )
        
        print("\n🎉 分析流程执行完成！")
        print("📁 请查看 output/ 目录获取详细结果")
        
        # 显示结果摘要
        if hasattr(result, 'final_recommendations') and result.final_recommendations:
            print(f"\n📊 结果摘要:")
            print(f"  - 找到笔记: {len(result.found_notes)} 条")
            print(f"  - 详细内容: {len(result.detailed_notes)} 条")
            print(f"  - 分析建议: {len(result.content_analysis)} 条")
            
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()


def generate_flow_diagram():
    """生成流程图"""
    print("\n📊 生成流程图...")
    try:
        plot_content_analysis_flow()
        print("✅ 流程图已生成")
    except Exception as e:
        print(f"❌ 生成流程图失败: {e}")


def test_components():
    """测试各个组件"""
    print("\n🧪 组件测试模式")
    
    print("1. 测试MediaCrawler客户端")
    print("2. 测试内容分析功能")
    print("3. 测试browser_use代理")
    print("4. 测试所有组件")
    
    choice = input("请选择测试项 (1-4): ").strip()
    
    if choice == "1":
        test_mediacrawler_client()
    elif choice == "2":
        test_content_analysis()
    elif choice == "3":
        test_browser_agent()
    elif choice == "4":
        test_all_components()
    else:
        print("❌ 无效选择")


def test_mediacrawler_client():
    """测试MediaCrawler客户端"""
    print("\n🧪 测试MediaCrawler客户端...")
    try:
        from xhs_note_analyzer.tools.mediacrawler_client import create_mediacrawler_client
        
        client = create_mediacrawler_client()
        
        # 健康检查
        if client.health_check():
            print("✅ MediaCrawler API服务器连接正常")
        else:
            print("❌ MediaCrawler API服务器连接失败")
        
        # 测试笔记爬取
        test_url = "https://xiaohongshu.com/note/example123"
        result = client.crawl_note(test_url)
        print(f"✅ 测试笔记爬取完成: {result.get('success', False)}")
        
    except Exception as e:
        print(f"❌ MediaCrawler客户端测试失败: {e}")


def test_content_analysis():
    """测试内容分析功能"""
    print("\n🧪 测试内容分析功能...")
    try:
        from xhs_note_analyzer.crews.content_advisor_crew.content_advisor_crew import analyze_single_note
        
        test_content = """
        标题：考公上岸攻略分享
        内容：分享我的备考经验，从零基础到成功上岸的全过程...
        图片：[考试资料图片、成绩单图片]
        标签：#考公 #上岸经验 #备考攻略
        """
        
        test_context = "专注于国企央企求职培训的教育机构"
        
        result = analyze_single_note(test_content, test_context)
        print(f"✅ 内容分析测试完成: {bool(result and not result.get('error'))}")
        
    except Exception as e:
        print(f"❌ 内容分析测试失败: {e}")


def test_browser_agent():
    """测试browser_use代理"""
    print("\n🧪 测试browser_use代理...")
    try:
        # 这里可以添加browser_use的简单测试
        # 由于browser_use需要实际的浏览器环境，我们只做基本检查
        print("⚠️ browser_use代理需要在完整环境中测试")
        print("   请运行完整分析流程来测试该组件")
        
    except Exception as e:
        print(f"❌ browser_use代理测试失败: {e}")


def test_all_components():
    """测试所有组件"""
    print("\n🧪 测试所有组件...")
    test_mediacrawler_client()
    test_content_analysis()
    test_browser_agent()
    print("\n✅ 所有组件测试完成")


def main():
    """主函数"""
    print("=" * 80)
    print("🎯 小红书内容分析器 (XHS Note Analyzer)")
    print("    基于CrewAI Flow + browser_use + MediaCrawler")
    print("=" * 80)
    
    # 检查环境
    if not check_environment():
        return
    
    while True:
        print("\n📋 请选择操作:")
        print("1. 运行完整分析流程")
        print("2. 分步骤演示流程")
        print("3. 生成流程图")
        print("4. 测试组件")
        print("5. 退出")
        
        choice = input("\n请输入选项 (1-5): ").strip()
        
        if choice == "1":
            run_full_analysis()
        elif choice == "2":
            run_step_by_step_demo()
        elif choice == "3":
            generate_flow_diagram()
        elif choice == "4":
            test_components()
        elif choice == "5":
            print("👋 再见！")
            break
        else:
            print("❌ 无效选择，请重新输入")


if __name__ == "__main__":
    main() 