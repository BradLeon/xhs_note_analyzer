#!/usr/bin/env python
"""
主测试脚本 - 运行所有四个步骤的测试
按序执行：Step1 → Step2 → Step3 → Step4
"""

import asyncio
import subprocess
import sys
import time
from pathlib import Path

def run_test_script(script_name: str, step_name: str) -> bool:
    """运行单个测试脚本"""
    print(f"\n{'='*80}")
    print(f"🚀 开始执行 {step_name}")
    print(f"{'='*80}")
    
    script_path = Path(__file__).parent / script_name
    if not script_path.exists():
        print(f"❌ 测试脚本不存在: {script_path}")
        return False
    
    start_time = time.time()
    
    try:
        # 运行测试脚本
        result = subprocess.run([
            sys.executable, str(script_path)
        ], capture_output=False, text=True)
        
        end_time = time.time()
        duration = end_time - start_time
        
        if result.returncode == 0:
            print(f"\n✅ {step_name} 测试通过 (耗时: {duration:.1f}秒)")
            return True
        else:
            print(f"\n❌ {step_name} 测试失败 (耗时: {duration:.1f}秒)")
            print(f"退出码: {result.returncode}")
            return False
            
    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        print(f"\n❌ {step_name} 测试异常 (耗时: {duration:.1f}秒): {e}")
        return False

def check_environment():
    """检查测试环境"""
    print("🔧 检查测试环境...")
    
    import os
    
    # 检查必需的环境变量
    required_env_vars = [
        "OPENROUTER_API_KEY"
    ]
    
    missing_vars = []
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
        else:
            print(f"✅ {var}: 已设置")
    
    if missing_vars:
        print(f"❌ 缺失环境变量: {missing_vars}")
        print("请设置以下环境变量:")
        for var in missing_vars:
            print(f"  export {var}='your_value'")
        return False
    
    # 检查可选的环境变量
    optional_env_vars = [
        "MEDIACRAWLER_API_ENDPOINT"
    ]
    
    for var in optional_env_vars:
        value = os.getenv(var, "未设置")
        print(f"🔧 {var}: {value}")
    
    # 检查输出目录
    output_dir = Path("tests/output")
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 输出目录: {output_dir.absolute()}")
    
    return True

def cleanup_test_outputs():
    """清理之前的测试输出（可选）"""
    print("\n🧹 清理测试输出...")
    
    output_dir = Path("tests/output")
    if output_dir.exists():
        import shutil
        try:
            shutil.rmtree(output_dir)
            print("✅ 旧测试输出已清理")
        except Exception as e:
            print(f"⚠️ 清理失败（可忽略）: {e}")
    
    output_dir.mkdir(parents=True, exist_ok=True)

def generate_test_summary(results: dict):
    """生成测试摘要报告"""
    print(f"\n{'='*80}")
    print("📊 测试摘要报告")
    print(f"{'='*80}")
    
    total_tests = len(results)
    passed_tests = sum(1 for success in results.values() if success)
    
    print(f"总测试数: {total_tests}")
    print(f"通过测试: {passed_tests}")
    print(f"失败测试: {total_tests - passed_tests}")
    print(f"成功率: {passed_tests/total_tests*100:.1f}%")
    
    print(f"\n详细结果:")
    for step_name, success in results.items():
        status = "✅ 通过" if success else "❌ 失败"
        print(f"  {step_name}: {status}")
    
    # 保存摘要到文件
    summary_file = Path("tests/output/test_summary.txt")
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("XHS Note Analyzer 测试摘要报告\\n")
        f.write("=" * 50 + "\\n\\n")
        f.write(f"执行时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\\n")
        f.write(f"总测试数: {total_tests}\\n")
        f.write(f"通过测试: {passed_tests}\\n")
        f.write(f"失败测试: {total_tests - passed_tests}\\n")
        f.write(f"成功率: {passed_tests/total_tests*100:.1f}%\\n\\n")
        
        f.write("详细结果:\\n")
        f.write("-" * 30 + "\\n")
        for step_name, success in results.items():
            status = "PASS" if success else "FAIL"
            f.write(f"{step_name}: {status}\\n")
        
        if passed_tests == total_tests:
            f.write("\\n🎉 所有测试通过！系统功能正常。\\n")
        else:
            f.write("\\n⚠️ 部分测试失败，请检查具体错误信息。\\n")
    
    print(f"\\n💾 摘要报告已保存: {summary_file}")
    
    return passed_tests == total_tests

def main():
    """主测试函数"""
    print("🧪 XHS Note Analyzer - 完整测试套件")
    print("=" * 80)
    print("测试流程: Step1(查找笔记) → Step2(采集内容) → Step3(内容分析) → Step4(策略制定)")
    print("=" * 80)
    
    # 检查环境
    if not check_environment():
        print("❌ 环境检查失败，无法继续测试")
        return False
    
    # 询问是否清理旧输出
    try:
        cleanup = input("\\n🤔 是否清理旧的测试输出? (y/N): ").lower().strip()
        if cleanup == 'y':
            cleanup_test_outputs()
    except KeyboardInterrupt:
        print("\\n用户取消测试")
        return False
    
    # 定义测试步骤
    test_steps = [
        ("test_step1_find_hot_notes.py", "Step1: 查找相关优质笔记"),
        ("test_step2_fetch_note_content.py", "Step2: 采集笔记详细内容"), 
        ("test_step3_multi_dimensional_analysis.py", "Step3: 多维度内容分析"),
        ("test_step4_strategy_making.py", "Step4: 实战策略制定")
    ]
    
    results = {}
    overall_start_time = time.time()
    
    # 按序执行测试
    for script_name, step_name in test_steps:
        success = run_test_script(script_name, step_name)
        results[step_name] = success
        
        # 如果某步失败，询问是否继续
        if not success:
            try:
                continue_test = input(f"\\n❓ {step_name} 失败，是否继续下一步测试? (y/N): ").lower().strip()
                if continue_test != 'y':
                    print("用户选择停止测试")
                    break
            except KeyboardInterrupt:
                print("\\n用户中断测试")
                break
    
    overall_end_time = time.time()
    total_duration = overall_end_time - overall_start_time
    
    # 生成测试摘要
    print(f"\\n⏱️ 总测试耗时: {total_duration:.1f}秒")
    all_passed = generate_test_summary(results)
    
    if all_passed:
        print("\\n🎉 恭喜！所有测试都通过了！")
        print("✨ XHS Note Analyzer 系统功能完整且正常")
        print("💡 你现在可以运行完整的分析流程了")
    else:
        print("\\n⚠️ 部分测试失败，请检查上面的错误信息")
        print("🔧 常见解决方案:")
        print("  1. 检查环境变量是否正确设置")
        print("  2. 确认网络连接正常")
        print("  3. 检查依赖包是否正确安装")
        print("  4. 查看具体的错误日志文件")
    
    return all_passed

if __name__ == "__main__":
    # 检查Python版本
    if sys.version_info < (3, 8):
        print("❌ 错误: 需要Python 3.8或更高版本")
        sys.exit(1)
    
    # 检查当前目录
    if not Path("tests").exists():
        print("❌ 错误: 请在项目根目录下运行此脚本")
        print("当前目录应包含 'tests' 文件夹")
        sys.exit(1)
    
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\\n\\n⏹️ 用户中断测试")
        sys.exit(1)
    except Exception as e:
        print(f"\\n❌ 测试运行异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)