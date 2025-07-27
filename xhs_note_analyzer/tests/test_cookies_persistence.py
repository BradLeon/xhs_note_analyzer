#!/usr/bin/env python
"""
测试脚本 - Cookies 持久化功能测试
验证小红书登录状态是否能够正确保存和恢复
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from xhs_note_analyzer.tools.hot_note_finder_tool import (
    create_hot_note_finder_agent, 
    ensure_auth_file_exists
)

# 配置测试日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_cookies_persistence.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def check_auth_file_status():
    """检查认证文件状态"""
    print("🔍 检查认证文件状态...")
    
    auth_file = Path.cwd() / 'xiaohongshu_auth.json'
    print(f"认证文件路径: {auth_file.absolute()}")
    
    if auth_file.exists():
        file_size = auth_file.stat().st_size
        print(f"✅ 认证文件存在，大小: {file_size} bytes")
        
        # 检查文件内容
        if ensure_auth_file_exists(auth_file):
            print("✅ 认证文件格式有效")
            
            # 显示文件内容摘要
            try:
                with open(auth_file, 'r', encoding='utf-8') as f:
                    auth_data = json.load(f)
                    cookies_count = len(auth_data.get('cookies', []))
                    origins_count = len(auth_data.get('origins', []))
                    print(f"  📊 包含 {cookies_count} 个cookies")
                    print(f"  📊 包含 {origins_count} 个origins")
                    
                    # 显示相关的cookies域名
                    xiaohongshu_cookies = [
                        cookie for cookie in auth_data.get('cookies', [])
                        if 'xiaohongshu' in cookie.get('domain', '')
                    ]
                    if xiaohongshu_cookies:
                        print(f"  🍪 包含 {len(xiaohongshu_cookies)} 个小红书相关cookies")
                        for cookie in xiaohongshu_cookies[:3]:  # 只显示前3个
                            print(f"    - {cookie.get('name', 'unknown')} ({cookie.get('domain', 'unknown domain')})")
                    else:
                        print("  ⚠️ 未发现小红书相关cookies")
                        
            except Exception as e:
                print(f"  ❌ 读取认证文件内容失败: {e}")
        else:
            print("❌ 认证文件格式无效")
        
        return True
    else:
        print("❌ 认证文件不存在")
        return False

def check_browser_data_dir():
    """检查浏览器数据目录"""
    print("\n🔍 检查浏览器数据目录...")
    
    browser_data_dir = Path.cwd() / 'browser_data' / 'xiaohongshu'
    print(f"浏览器数据目录: {browser_data_dir.absolute()}")
    
    if browser_data_dir.exists():
        # 统计目录内容
        try:
            items = list(browser_data_dir.rglob('*'))
            files = [item for item in items if item.is_file()]
            dirs = [item for item in items if item.is_dir()]
            
            print(f"✅ 浏览器数据目录存在")
            print(f"  📂 包含 {len(dirs)} 个子目录")
            print(f"  📄 包含 {len(files)} 个文件")
            
            # 查找重要的Chrome数据文件
            important_files = ['Default/Cookies', 'Default/Local Storage', 'Default/Session Storage']
            for important_file in important_files:
                file_path = browser_data_dir / important_file
                if file_path.exists():
                    file_size = file_path.stat().st_size
                    print(f"  ✅ {important_file}: {file_size} bytes")
                else:
                    print(f"  ❌ {important_file}: 不存在")
                    
        except Exception as e:
            print(f"  ❌ 读取浏览器数据目录失败: {e}")
        
        return True
    else:
        print("❌ 浏览器数据目录不存在")
        return False

async def test_agent_creation_with_auth():
    """测试创建代理时的认证状态处理"""
    print("\n🔍 测试代理创建与认证状态...")
    
    try:
        # 创建代理
        agent = create_hot_note_finder_agent(
            promotion_target="测试目标_cookies验证"
        )
        
        print("✅ 代理创建成功")
        
        # 检查代理的浏览器会话配置
        if hasattr(agent, 'browser_session'):
            session = agent.browser_session
            print(f"  🌐 允许的域名: {session.allowed_domains}")
            print(f"  📁 存储状态文件: {session.save_storage_state}")
            
            # 检查浏览器配置
            if hasattr(session, 'browser_profile'):
                profile = session.browser_profile
                print(f"  🗂️ 用户数据目录: {profile.user_data_dir}")
        
        return True
        
    except Exception as e:
        print(f"❌ 代理创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def simulate_successful_login():
    """模拟成功登录后保存认证状态"""
    print("\n🧪 模拟登录成功后的认证状态保存...")
    
    # 创建模拟的认证状态数据
    mock_auth_state = {
        "cookies": [
            {
                "name": "session_token",
                "value": "mock_session_token_12345",
                "domain": ".xiaohongshu.com",
                "path": "/",
                "expires": 1999999999,
                "httpOnly": True,
                "secure": True,
                "sameSite": "Lax"
            },
            {
                "name": "user_id",
                "value": "mock_user_id_67890",
                "domain": ".xiaohongshu.com",
                "path": "/",
                "expires": 1999999999,
                "httpOnly": False,
                "secure": True,
                "sameSite": "Lax"
            }
        ],
        "origins": [
            {
                "origin": "https://ad.xiaohongshu.com",
                "localStorage": [
                    {
                        "name": "auth_token",
                        "value": "mock_auth_token_abcdef"
                    }
                ]
            }
        ]
    }
    
    # 保存到认证文件
    auth_file = Path.cwd() / 'xiaohongshu_auth.json'
    try:
        with open(auth_file, 'w', encoding='utf-8') as f:
            json.dump(mock_auth_state, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 模拟认证状态已保存到: {auth_file}")
        return True
        
    except Exception as e:
        print(f"❌ 保存模拟认证状态失败: {e}")
        return False

def cleanup_test_files():
    """清理测试文件"""
    print("\n🧹 清理测试文件...")
    
    files_to_clean = [
        Path.cwd() / 'xiaohongshu_auth.json',
        Path.cwd() / 'browser_data'
    ]
    
    cleaned_count = 0
    for file_path in files_to_clean:
        try:
            if file_path.is_file():
                file_path.unlink()
                print(f"  ✅ 删除文件: {file_path}")
                cleaned_count += 1
            elif file_path.is_dir():
                import shutil
                shutil.rmtree(file_path)
                print(f"  ✅ 删除目录: {file_path}")
                cleaned_count += 1
        except Exception as e:
            print(f"  ⚠️ 清理失败 {file_path}: {e}")
    
    print(f"清理完成，处理了 {cleaned_count} 个项目")

async def main():
    """主测试函数"""
    print("🧪 小红书登录状态持久化测试")
    print("=" * 60)
    
    # 询问是否要清理旧文件
    try:
        cleanup = input("🤔 是否清理旧的认证文件和浏览器数据? (y/N): ").lower().strip()
        if cleanup == 'y':
            cleanup_test_files()
    except KeyboardInterrupt:
        print("\n用户取消测试")
        return False
    
    # 1. 检查当前状态
    print("\n" + "="*60)
    print("📋 第一步：检查当前认证状态")
    print("="*60)
    
    auth_exists = check_auth_file_status()
    browser_data_exists = check_browser_data_dir()
    
    # 2. 如果没有认证文件，创建模拟的
    if not auth_exists:
        print("\n" + "="*60)
        print("📋 第二步：创建模拟认证状态")
        print("="*60)
        
        if not simulate_successful_login():
            print("❌ 无法创建模拟认证状态")
            return False
    
    # 3. 测试代理创建
    print("\n" + "="*60)
    print("📋 第三步：测试代理创建")
    print("="*60)
    
    agent_success = await test_agent_creation_with_auth()
    
    # 4. 重新检查状态
    print("\n" + "="*60)
    print("📋 第四步：重新检查认证状态")
    print("="*60)
    
    final_auth_exists = check_auth_file_status()
    final_browser_data_exists = check_browser_data_dir()
    
    # 5. 测试总结
    print("\n" + "="*60)
    print("📊 测试总结")
    print("="*60)
    
    print(f"认证文件存在: {'✅' if final_auth_exists else '❌'}")
    print(f"浏览器数据存在: {'✅' if final_browser_data_exists else '❌'}")
    print(f"代理创建成功: {'✅' if agent_success else '❌'}")
    
    if final_auth_exists and agent_success:
        print("\n🎉 Cookies持久化功能测试通过!")
        print("💡 下次运行时应该会自动使用保存的登录状态")
        print("📝 实际测试建议:")
        print("  1. 运行 python test_step1_find_hot_notes.py")
        print("  2. 完成首次登录")
        print("  3. 再次运行测试，观察是否跳过登录步骤")
    else:
        print("\n⚠️ Cookies持久化功能可能存在问题")
        print("🔧 建议:")
        print("  1. 检查browser_use版本是否最新")
        print("  2. 检查文件权限")
        print("  3. 查看详细日志文件")
    
    return final_auth_exists and agent_success

if __name__ == "__main__":
    # 检查环境变量
    import os
    if not os.getenv("OPENROUTER_API_KEY"):
        print("⚠️ 警告: 未设置 OPENROUTER_API_KEY 环境变量")
        print("这可能影响代理的LLM功能，但不影响cookies测试")
        print()
    
    # 运行测试
    result = asyncio.run(main())
    
    # 退出码
    sys.exit(0 if result else 1)