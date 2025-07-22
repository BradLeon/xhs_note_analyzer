#!/usr/bin/env python3
"""
小红书指定内容ID数据采集测试

测试流程：
1. 启动数据采集任务（指定note_id）
2. 监控任务进度
3. 验证数据存储
4. 查询采集到的数据
"""

import asyncio
import aiohttp
import time
from typing import Dict, Any, List
import sys
import os

# 添加项目路径到sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from xhs_note_analyzer.tools.mediacrawler_client import (
    MediaCrawlerClient, 
    create_mediacrawler_client,
    fetch_note_content,
    batch_fetch_note_contents,
    get_stored_note,
    create_crawl_task,
    wait_for_task
)

API_BASE = "http://localhost:8000/api/v1"

# 测试用的小红书note_id（你可以替换为实际的note_id）
# 示例格式：note_id通常是24位十六进制字符串，如：676a4d0a000000001f00c58a
# 或者可以是完整的URL：https://www.xiaohongshu.com/explore/676a4d0a000000001f00c58a?xsec_token=xxx&xsec_source=xxx
TEST_NOTE_IDS = [
    # "676a4d0a000000001f00c58a",  # 请替换为真实的note_id
    # "https://www.xiaohongshu.com/explore/676a4d0a000000001f00c58a", # 或使用完整URL
]

PLATFORM = "xhs"

def get_test_note_ids():
    """获取测试用的note_id"""
    if TEST_NOTE_IDS:
        return TEST_NOTE_IDS
    
    print("\n" + "="*50)
    print("⚠️  需要提供真实的小红书note_id进行测试")
    print("="*50)
    print("请提供一个或多个小红书笔记ID，支持以下格式：")
    print("1. note_id: 676a4d0a000000001f00c58a")
    print("2. 完整URL: https://www.xiaohongshu.com/explore/676a4d0a000000001f00c58a")
    print("3. 带token的URL: https://www.xiaohongshu.com/explore/676a4d0a000000001f00c58a?xsec_token=xxx&xsec_source=xxx")
    print("\n输入多个ID时请用逗号分隔，输入空行结束：")
    
    note_ids = []
    while True:
        note_input = input("note_id/URL: ").strip()
        if not note_input:
            break
        
        # 支持逗号分隔的多个ID
        for note_id in note_input.split(','):
            note_id = note_id.strip()
            if note_id:
                note_ids.append(note_id)
    
    if not note_ids:
        print("❌ 未提供任何note_id，将使用示例ID（可能无效）")
        return ["676a4d0a000000001f00c58a"]  # 示例ID
    
    return note_ids

class XhsContentCrawlerTest:
    def __init__(self):
        self.session = None
        self.task_id = f"test_xhs_content_{int(time.time())}"
        self.server_task_id = None  # 服务器返回的实际task_id
        self.test_note_ids = get_test_note_ids()
        self.client = None  # MediaCrawlerClient 实例
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        self.client = create_mediacrawler_client()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_content_crawler(self):
        """测试小红书内容采集功能"""
        print("=" * 60)
        print("🧪 小红书指定内容ID数据采集测试")
        print("=" * 60)
        print(f"测试note_id: {self.test_note_ids}")
        
        try:
            # 步骤1: 创建数据采集任务
            await self._create_crawler_task()
            
            # 步骤2: 监控任务执行
            task_completed = await self._monitor_task_progress()
            
            if task_completed:
                # 步骤3: 验证数据存储
                await self._verify_data_storage()
                
                # 步骤4: 查询采集的数据
                await self._query_collected_data()
            else:
                print("❌ 任务执行失败或超时")
                
        except Exception as e:
            print(f"❌ 测试过程中发生错误: {e}")
            import traceback
            traceback.print_exc()
    
    async def _create_crawler_task(self):
        """创建数据采集任务"""
        print(f"\n📝 步骤1: 创建数据采集任务 (Task ID: {self.task_id})")
        
        payload = {
            "task_id": self.task_id,
            "platform": PLATFORM,
            "task_type": "detail",  # 详情采集模式
            "content_ids": self.test_note_ids,  # 指定note_id列表
            "max_count": len(self.test_note_ids),
            "max_comments": 100,  # 采集评论数量
            "enable_proxy": False,
            "headless": True,
            "save_data_option": "db",  # 保存到数据库
            "config": {
                "login_type": "cookie",  # 使用之前保存的登录状态
                "enable_stealth": True,
                "random_sleep_min": 1.0,
                "random_sleep_max": 3.0,
                "platform_specific": {
                    "enable_get_comments": True,
                    "enable_get_images": False,
                    "max_comments_per_note": 100
                }
            }
        }
        
        async with self.session.post(f"{API_BASE}/tasks", json=payload) as resp:
            resp_text = await resp.text()
            print(f"   服务器响应状态: {resp.status}")
            print(f"   服务器响应内容: {resp_text}")
            
            if resp.status == 200:
                try:
                    data = await resp.json()
                except:
                    data = {"raw": resp_text, "success": False}
                
                if resp.status == 200 and data.get("task_id"):
                    print(f"✅ 任务创建成功")
                    print(f"   任务ID: {data.get('task_id')}")
                    print(f"   消息: {data.get('message', 'N/A')}")
                    print(f"   目标note_id数量: {len(self.test_note_ids)}")
                    print(f"   最大评论数: {payload['max_comments']}")
                    self.server_task_id = data.get('task_id')
                else:
                    raise Exception(f"任务创建失败: {data.get('message', 'Unknown error')}")
            else:
                raise Exception(f"HTTP请求失败: {resp.status}, 响应: {resp_text}")
    
    async def _monitor_task_progress(self) -> bool:
        """监控任务执行进度"""
        print(f"\n📊 步骤2: 监控任务执行进度")
        
        max_wait_time = 600  # 10分钟超时
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            try:
                async with self.session.get(f"{API_BASE}/tasks/{self.server_task_id}/status") as resp:
                    data = await resp.json()
                    
                    status = data.get("status", "unknown")
                    progress = data.get("progress", {})
                    
                    # 显示进度信息
                    stage = progress.get("current_stage", "未知")
                    percent = progress.get("progress_percent", 0)
                    message = data.get("message", "")
                    
                    print(f"   状态: {status} | 阶段: {stage} | 进度: {percent:.1f}% | {message}")
                    
                    # 检查任务状态
                    if status == "completed":
                        print(f"✅ 任务执行完成")
                        return True
                    elif status == "failed":
                        print(f"❌ 任务执行失败: {message}")
                        return False
                    elif status == "running":
                        # 任务正在运行，继续监控
                        pass
                    else:
                        print(f"⚠️  未知状态: {status}")
                
                await asyncio.sleep(5)  # 每5秒检查一次
                
            except Exception as e:
                print(f"⚠️  获取任务状态时出错: {e}")
                await asyncio.sleep(5)
        
        print(f"⏰ 任务监控超时")
        return False
    
    async def _verify_data_storage(self):
        """验证数据存储"""
        print(f"\n💾 步骤3: 验证数据存储")
        
        try:
            # 检查数据访问服务健康状态
            async with self.session.get(f"{API_BASE}/data/health") as resp:
                health_data = await resp.json()
                print(f"   数据访问服务状态: {'✅ 正常' if health_data.get('success') else '❌ 异常'}")
            
            # 获取平台内容数量
            async with self.session.get(f"{API_BASE}/data/content/{PLATFORM}/count", 
                                       params={"task_id": self.server_task_id}) as resp:
                count_data = await resp.json()
                
                if count_data.get("success"):
                    total_count = count_data.get("data", {}).get("count", 0)
                    print(f"   本次任务采集内容数量: {total_count}")
                    
                    if total_count > 0:
                        print(f"✅ 数据已成功存储")
                        return True
                    else:
                        print(f"⚠️  未检测到新的数据")
                        return False
                else:
                    print(f"❌ 获取数据数量失败: {count_data.get('message')}")
                    return False
        
        except Exception as e:
            print(f"❌ 验证数据存储时出错: {e}")
            return False
    
    async def _query_collected_data(self):
        """查询采集到的数据"""
        print(f"\n🔍 步骤4: 查询采集的数据")
        
        try:
            # 查询每个指定的note_id
            for note_id in self.test_note_ids:
                print(f"\n   📋 查询note_id: {note_id}")
                
                # 1. 通过ID查询具体内容
                async with self.session.get(f"{API_BASE}/data/content/{PLATFORM}/{note_id}") as resp:
                    content_data = await resp.json()
                    
                    if content_data.get("success"):
                        content = content_data.get("data")
                        if content:
                            print(f"     ✅ 内容详情已找到")
                            print(f"        标题: {content.get('title', 'N/A')[:50]}...")
                            print(f"        作者: {content.get('user_name', 'N/A')}")
                            print(f"        点赞数: {content.get('liked_count', 'N/A')}")
                            print(f"        评论数: {content.get('comments_count', 'N/A')}")
                            print(f"        发布时间: {content.get('publish_time', 'N/A')}")
                        else:
                            print(f"     ⚠️  内容详情为空")
                    else:
                        print(f"     ❌ 未找到内容: {content_data.get('message')}")
            
            # 2. 查询任务结果汇总
            print(f"\n   📊 任务结果汇总:")
            payload = {
                "task_id": self.server_task_id,
                "limit": 100,
                "offset": 0
            }
            
            async with self.session.post(f"{API_BASE}/data/task/results", json=payload) as resp:
                results_data = await resp.json()
                
                if results_data.get("success"):
                    results = results_data.get("data", [])
                    total = results_data.get("total", 0)
                    
                    print(f"     ✅ 任务结果汇总")
                    print(f"        总计数据量: {total}")
                    print(f"        返回结果数: {len(results)}")
                    
                    if results:
                        # 显示前几条结果的摘要
                        for i, item in enumerate(results[:3]):
                            print(f"        [{i+1}] {item.get('title', 'N/A')[:30]}... | 作者: {item.get('user_name', 'N/A')}")
                    
                else:
                    print(f"     ❌ 获取任务结果失败: {results_data.get('message')}")
        
        except Exception as e:
            print(f"❌ 查询数据时出错: {e}")
    
    async def _cleanup_test_data(self):
        """清理测试数据（可选）"""
        print(f"\n🧹 清理测试数据...")
        # 这里可以添加清理逻辑，比如删除测试任务的数据
        # 但为了验证，我们暂时保留数据
        print(f"   测试数据已保留，可通过API继续查询")
    
    def test_mediacrawler_client(self):
        """测试新的MediaCrawlerClient实现"""
        print("=" * 60)
        print("🧪 测试新的MediaCrawlerClient实现")
        print("=" * 60)
        
        try:
            # 测试1: 健康检查
            print(f"\n📍 测试1: API健康检查")
            is_healthy = self.client.health_check()
            print(f"   API服务器状态: {'✅ 正常' if is_healthy else '❌ 不可用'}")
            
            if not is_healthy:
                print("⚠️ API服务器不可用，跳过后续测试")
                return
            
            # 测试2: 单个笔记内容获取（高层接口）
            print(f"\n📍 测试2: 单个笔记内容获取")
            test_urls = [f"https://xiaohongshu.com/note/{note_id}" for note_id in self.test_note_ids[:1]]
            
            for url in test_urls:
                print(f"   🔍 测试URL: {url}")
                result = self.client.crawl_note(url, fetch_comments=True)
                
                if result.get("success"):
                    data = result.get("data", {})
                    print(f"   ✅ 成功获取内容")
                    print(f"      标题: {data.get('title', 'N/A')[:50]}...")
                    print(f"      作者: {data.get('user_name', 'N/A')}")
                    print(f"      点赞: {data.get('liked_count', 'N/A')}")
                    print(f"      评论: {data.get('comments_count', 'N/A')}")
                else:
                    print(f"   ❌ 获取失败: {result.get('error', 'Unknown error')}")
            
            # 测试3: 批量笔记内容获取
            print(f"\n📍 测试3: 批量笔记内容获取")
            test_urls = [f"https://xiaohongshu.com/note/{note_id}" for note_id in self.test_note_ids[:3]]
            
            print(f"   🔍 批量测试 {len(test_urls)} 个URL")
            results = self.client.batch_crawl_notes(test_urls, fetch_comments=False)
            
            success_count = len([r for r in results if r.get("success")])
            print(f"   📊 批量结果: 成功 {success_count}/{len(results)}")
            
            for i, result in enumerate(results):
                if result.get("success"):
                    data = result.get("data", {})
                    print(f"   [{i+1}] ✅ {data.get('title', 'N/A')[:30]}...")
                else:
                    print(f"   [{i+1}] ❌ {result.get('error', 'Unknown error')}")
            
            # 测试4: 任务管理功能
            print(f"\n📍 测试4: 任务管理功能")
            
            print(f"   🚀 创建测试任务")
            task_result = self.client.create_crawl_task(
                note_ids=self.test_note_ids[:2],
                fetch_comments=True,
                max_comments=50
            )
            
            if task_result.get("task_id"):
                task_id = task_result["task_id"]
                print(f"   ✅ 任务创建成功: {task_id}")
                
                # 监控任务状态
                print(f"   ⏳ 监控任务状态...")
                completed = self.client.wait_for_task_completion(task_id, max_wait_time=300)
                
                if completed:
                    print(f"   ✅ 任务执行完成")
                    
                    # 验证结果
                    print(f"   🔍 验证结果...")
                    for note_id in self.test_note_ids[:2]:
                        result = self.client.get_note_content_by_id(note_id)
                        if result.get("success"):
                            print(f"      ✅ {note_id}: 数据已存储")
                        else:
                            print(f"      ❌ {note_id}: 未找到数据")
                else:
                    print(f"   ⏰ 任务执行超时或失败")
            else:
                print(f"   ❌ 任务创建失败: {task_result.get('message')}")
            
            print(f"\n✅ MediaCrawlerClient测试完成")
            
        except Exception as e:
            print(f"❌ 测试过程中发生错误: {e}")
            import traceback
            traceback.print_exc()


async def main():
    """主函数"""
    async with XhsContentCrawlerTest() as test:
        await test.test_content_crawler()


if __name__ == "__main__":
    print("开始小红书内容采集测试...")
    print("请确保:")
    print("1. API服务器已启动 (http://localhost:8000)")
    print("2. 已完成小红书登录认证")
    print("3. 已有有效的note_id进行测试")
    print()
    
    asyncio.run(main()) 