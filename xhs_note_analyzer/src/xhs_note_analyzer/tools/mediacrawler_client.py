"""
MediaCrawler API 客户端工具
用于与MediaCrawler服务器通信，获取小红书笔记详细内容
参考: https://github.com/BradLeon/MediaCrawler-API-Server
"""

import os
import json
import requests
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


class MediaCrawlerClient:
    """MediaCrawler API 客户端"""
    
    def __init__(self, api_endpoint: str = None, api_key: str = None):
        """
        初始化客户端
        
        Args:
            api_endpoint: API服务器地址，默认从环境变量MEDIACRAWLER_API_ENDPOINT获取
            api_key: API密钥，默认从环境变量MEDIACRAWLER_API_KEY获取
        """
        self.api_endpoint = api_endpoint or os.getenv("MEDIACRAWLER_API_ENDPOINT", "http://localhost:8000")
        self.api_key = api_key or os.getenv("MEDIACRAWLER_API_KEY", "")
        self.session = requests.Session()
        
        # 设置认证头
        if self.api_key:
            self.session.headers.update({"Authorization": f"Bearer {self.api_key}"})
    
    def extract_note_id_from_url(self, note_url: str) -> Optional[str]:
        """从小红书笔记URL提取note_id"""
        try:
            # 如果输入本身就是note_id（24位十六进制字符串），直接返回
            if len(note_url) == 24 and all(c in '0123456789abcdef' for c in note_url.lower()):
                return note_url
            
            # 小红书笔记URL格式支持：
            # 1. https://xiaohongshu.com/note/[note_id]
            # 2. https://www.xiaohongshu.com/note/[note_id]  
            # 3. https://www.xiaohongshu.com/explore/[note_id]?xsec_token=xxx&xsec_source=xxx
            # 4. https://xhslink.com/xxx (短链接，暂不支持)
            
            parsed = urlparse(note_url)
            
            if 'xiaohongshu.com' in parsed.netloc:
                path = parsed.path
                
                # 处理 /note/ 路径
                if '/note/' in path:
                    note_id = path.split('/note/')[-1].split('?')[0].split('#')[0]
                    if note_id and len(note_id) >= 20:  # note_id通常是24位，但至少20位
                        return note_id
                
                # 处理 /explore/ 路径 (新格式)
                elif '/explore/' in path:
                    note_id = path.split('/explore/')[-1].split('?')[0].split('#')[0]
                    if note_id and len(note_id) >= 20:  # note_id通常是24位，但至少20位
                        return note_id
                        
                # 处理 /discovery/item/ 路径 (另一种可能格式)
                elif '/discovery/item/' in path:
                    note_id = path.split('/discovery/item/')[-1].split('?')[0].split('#')[0]
                    if note_id and len(note_id) >= 20:
                        return note_id
            
            # 如果都不匹配，尝试用正则表达式匹配24位十六进制字符串
            import re
            note_id_pattern = r'[0-9a-f]{24}'
            match = re.search(note_id_pattern, note_url.lower())
            if match:
                return match.group(0)
            
            logger.warning(f"无法从URL提取note_id: {note_url}")
            return None
            
        except Exception as e:
            logger.error(f"解析URL失败: {note_url}, 错误: {e}")
            return None
    
    def create_crawl_task(self, note_ids: List[str], task_id: str = None, fetch_comments: bool = False, 
                         max_comments: int = 100) -> Dict[str, Any]:
        """
        创建小红书内容采集任务
        
        Args:
            note_ids: 笔记ID列表
            task_id: 任务ID，如果不提供会自动生成
            fetch_comments: 是否获取评论
            max_comments: 最大评论数量
            
        Returns:
            任务创建结果
        """
        try:
            import time
            if not task_id:
                task_id = f"crawl_task_{int(time.time())}"
            
            payload = {
                "task_id": task_id,
                "platform": "xhs",
                "task_type": "detail",
                "content_ids": note_ids,
                "max_count": len(note_ids),
                "max_comments": max_comments if fetch_comments else 0,
                "enable_proxy": False,
                "headless": True,
                "save_data_option": "db",
                "config": {
                    "login_type": "cookie",
                    "enable_stealth": True,
                    "random_sleep_min": 1.0,
                    "random_sleep_max": 3.0,
                    "platform_specific": {
                        "enable_get_comments": fetch_comments,
                        "enable_get_images": True,
                        "max_comments_per_note": max_comments
                    }
                }
            }
            
            logger.info(f"🔄 创建采集任务: {task_id}, 目标数量: {len(note_ids)}")
            
            response = self.session.post(
                f"{self.api_endpoint}/api/v1/tasks",
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            if result.get("task_id"):
                logger.info(f"✅ 任务创建成功: {result.get('task_id')}")
            else:
                logger.warning(f"⚠️ 任务创建响应异常: {result}")
                
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ 创建任务失败, 错误: {e}")
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"❌ 处理失败, 错误: {e}")
            return {"success": False, "error": str(e)}
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        获取任务执行状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务状态信息
        """
        try:
            response = self.session.get(
                f"{self.api_endpoint}/api/v1/tasks/{task_id}/status",
                timeout=10
            )
            response.raise_for_status()
            
            result = response.json()
            status = result.get("status", "unknown")
            logger.info(f"📊 任务 {task_id} 状态: {status}")
            
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ 获取任务状态失败: {task_id}, 错误: {e}")
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"❌ 处理失败: {task_id}, 错误: {e}")
            return {"success": False, "error": str(e)}
    
    def wait_for_task_completion(self, task_id: str, max_wait_time: int = 600, 
                                check_interval: int = 5) -> bool:
        """
        等待任务完成
        
        Args:
            task_id: 任务ID
            max_wait_time: 最大等待时间（秒）
            check_interval: 检查间隔（秒）
            
        Returns:
            任务是否成功完成
        """
        import time
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            status_result = self.get_task_status(task_id)
            
            if not status_result.get("success", True):
                # 如果获取状态失败，等一会再试
                time.sleep(check_interval)
                continue
                
            status = status_result.get("status", "unknown")
            
            if status == "completed":
                logger.info(f"✅ 任务 {task_id} 执行完成")
                return True
            elif status == "failed":
                logger.error(f"❌ 任务 {task_id} 执行失败")
                return False
            elif status in ["running", "pending"]:
                # 任务正在运行，继续等待
                progress = status_result.get("progress", {})
                percent = progress.get("progress_percent", 0)
                stage = progress.get("current_stage", "未知")
                logger.info(f"⏳ 任务 {task_id} 进行中: {stage} ({percent:.1f}%)")
                time.sleep(check_interval)
            else:
                logger.warning(f"⚠️ 任务 {task_id} 状态未知: {status}")
                time.sleep(check_interval)
        
        logger.error(f"⏰ 任务 {task_id} 等待超时")
        return False

    def get_note_content_by_id(self, note_id: str) -> Dict[str, Any]:
        """
        根据note_id获取笔记内容
        
        Args:
            note_id: 笔记ID
            
        Returns:
            笔记详细内容
        """
        try:
            logger.info(f"🔍 查询笔记内容: {note_id}")
            
            response = self.session.get(
                f"{self.api_endpoint}/api/v1/data/content/xhs/{note_id}",
                timeout=10
            )
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("success") and result.get("data"):
                logger.info(f"✅ 成功获取笔记内容: {note_id}")
            else:
                logger.warning(f"⚠️ 未找到笔记内容: {note_id}")
            
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ 查询笔记失败: {note_id}, 错误: {e}")
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"❌ 处理失败: {note_id}, 错误: {e}")
            return {"success": False, "error": str(e)}

    def crawl_note(self, note_url: str, fetch_comments: bool = False) -> Dict[str, Any]:
        """
        爬取单个笔记内容（高层次接口，自动处理任务创建和等待）
        
        Args:
            note_url: 笔记URL
            fetch_comments: 是否获取评论
            
        Returns:
            笔记详细内容数据
        """
        try:
            # 从URL提取note_id
            note_id = self.extract_note_id_from_url(note_url)
            if not note_id:
                raise ValueError(f"无法从URL提取note_id: {note_url}")
            
            logger.info(f"🔄 开始爬取笔记: {note_url} (ID: {note_id})")
            
            # 先尝试从数据库获取
            existing_data = self.get_note_content_by_id(note_id)
            if existing_data.get("success") and existing_data.get("data"):
                logger.info(f"✅ 从数据库获取到现有数据: {note_id}")
                return existing_data
            
            # 如果数据库中没有，创建采集任务
            task_result = self.create_crawl_task(
                note_ids=[note_id],
                fetch_comments=fetch_comments
            )
            
            if not task_result.get("task_id"):
                raise Exception(f"任务创建失败: {task_result.get('message', 'Unknown error')}")
            
            task_id = task_result["task_id"]
            
            # 等待任务完成
            if self.wait_for_task_completion(task_id, max_wait_time=300):
                # 任务完成，获取结果
                result = self.get_note_content_by_id(note_id)
                if result.get("success"):
                    logger.info(f"✅ 成功爬取笔记内容: {note_url}")
                    return result
                else:
                    raise Exception(f"任务完成但无法获取数据: {result.get('message')}")
            else:
                raise Exception(f"任务执行失败或超时: {task_id}")
            
        except Exception as e:
            logger.error(f"❌ 爬取笔记失败: {note_url}, 错误: {e}")
            return {"success": False, "error": str(e)}
    
    def batch_crawl_notes(self, note_urls: List[str], fetch_comments: bool = False) -> List[Dict[str, Any]]:
        """
        批量爬取笔记内容（优化版本，使用单个任务处理多个笔记）
        
        Args:
            note_urls: 笔记URL列表
            fetch_comments: 是否获取评论
            
        Returns:
            笔记详细内容列表
        """
        if not note_urls:
            return []
        
        try:
            # 提取所有note_id
            note_ids = []
            url_to_id_map = {}
            
            for url in note_urls:
                note_id = self.extract_note_id_from_url(url)
                if note_id:
                    note_ids.append(note_id)
                    url_to_id_map[note_id] = url
                else:
                    logger.warning(f"⚠️ 无法从URL提取note_id: {url}")
            
            if not note_ids:
                logger.error("❌ 没有有效的note_id")
                return [{"success": False, "error": "没有有效的note_id"}] * len(note_urls)
            
            logger.info(f"🔄 开始批量爬取 {len(note_ids)} 个笔记")
            
            # 先检查哪些数据已经存在
            existing_data = {}
            new_note_ids = []
            
            for note_id in note_ids:
                existing_result = self.get_note_content_by_id(note_id)
                if existing_result.get("success") and existing_result.get("data"):
                    existing_data[note_id] = existing_result
                    logger.info(f"✅ 从数据库获取到现有数据: {note_id}")
                else:
                    new_note_ids.append(note_id)
            
            # 对于没有的数据，创建批量采集任务
            if new_note_ids:
                logger.info(f"🚀 创建批量采集任务，目标: {len(new_note_ids)} 个新笔记")
                
                task_result = self.create_crawl_task(
                    note_ids=new_note_ids,
                    fetch_comments=fetch_comments
                )
                
                if task_result.get("task_id"):
                    task_id = task_result["task_id"]
                    
                    # 等待任务完成
                    if self.wait_for_task_completion(task_id, max_wait_time=600):
                        logger.info(f"✅ 批量采集任务完成: {task_id}")
                        
                        # 获取新采集的数据
                        for note_id in new_note_ids:
                            result = self.get_note_content_by_id(note_id)
                            if result.get("success"):
                                existing_data[note_id] = result
                            else:
                                existing_data[note_id] = {"success": False, "error": f"无法获取数据: {note_id}"}
                    else:
                        logger.error(f"❌ 批量采集任务失败或超时: {task_id}")
                        # 为失败的note_id创建错误结果
                        for note_id in new_note_ids:
                            existing_data[note_id] = {"success": False, "error": f"采集任务失败: {task_id}"}
                else:
                    logger.error(f"❌ 创建批量任务失败: {task_result.get('message')}")
                    # 为所有新note_id创建错误结果
                    for note_id in new_note_ids:
                        existing_data[note_id] = {"success": False, "error": "创建采集任务失败"}
            
            # 按原始URL顺序组织结果
            results = []
            for url in note_urls:
                note_id = self.extract_note_id_from_url(url)
                if note_id and note_id in existing_data:
                    results.append(existing_data[note_id])
                else:
                    results.append({"success": False, "error": f"无法处理URL: {url}"})
            
            success_count = len([r for r in results if r.get("success", False)])
            logger.info(f"🎯 批量爬取完成: 成功 {success_count}/{len(note_urls)}")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ 批量爬取失败: {e}")
            return [{"success": False, "error": str(e)}] * len(note_urls)
    
    def health_check(self) -> bool:
        """检查API服务器健康状态"""
        try:
            response = self.session.get(f"{self.api_endpoint}/health", timeout=5)
            return response.status_code == 200
        except:
            return False


def create_mediacrawler_client() -> MediaCrawlerClient:
    """创建MediaCrawler客户端实例"""
    return MediaCrawlerClient()


# 便捷函数
def fetch_note_content(note_url: str, fetch_comments: bool = False) -> Dict[str, Any]:
    """获取单个笔记内容的便捷函数"""
    client = create_mediacrawler_client()
    return client.crawl_note(note_url, fetch_comments)


def batch_fetch_note_contents(note_urls: List[str], fetch_comments: bool = False) -> List[Dict[str, Any]]:
    """批量获取笔记内容的便捷函数"""
    client = create_mediacrawler_client()
    return client.batch_crawl_notes(note_urls, fetch_comments)


def test_url_extraction():
    """测试URL解析功能"""
    print("🧪 测试URL解析功能...")
    client = create_mediacrawler_client()
    
    test_cases = [
        # 测试用例: (输入URL, 期望的note_id)
        ("68622a8b0000000015020c92", "68622a8b0000000015020c92"),  # 纯note_id
        ("https://www.xiaohongshu.com/explore/68622a8b0000000015020c92?xsec_token=ZBuyva3FFEKzv_CBjmw6dEClLM879Okee6liwo_ZdFl4M=&xsec_source=pc_ad", "68622a8b0000000015020c92"),  # 新格式
        ("https://www.xiaohongshu.com/note/676a4d0a000000001f00c58a", "676a4d0a000000001f00c58a"),  # 旧格式
        ("https://xiaohongshu.com/note/676a4d0a000000001f00c58a", "676a4d0a000000001f00c58a"),  # 无www
        ("https://www.xiaohongshu.com/explore/676a4d0a000000001f00c58a", "676a4d0a000000001f00c58a"),  # explore格式
        ("invalid_url", None),  # 无效URL
    ]
    
    for test_url, expected in test_cases:
        result = client.extract_note_id_from_url(test_url)
        status = "✅" if result == expected else "❌"
        print(f"{status} {test_url[:50]}... -> {result} (期望: {expected})")
    
    print()


if __name__ == "__main__":
    # 测试代码
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # 测试URL解析
    test_url_extraction()
    
    # 测试API连接
    client = create_mediacrawler_client()
    
    print("🧪 测试MediaCrawler API连接...")
    if client.health_check():
        print("✅ API服务器连接正常")
        
        # 如果API可用，测试笔记爬取
        test_url = "https://www.xiaohongshu.com/explore/68622a8b0000000015020c92"
        print(f"\n🧪 测试笔记爬取: {test_url}")
        result = client.crawl_note(test_url)
        print(f"结果: {json.dumps(result, ensure_ascii=False, indent=2)[:500]}...")
    else:
        print("❌ API服务器连接失败，跳过爬取测试") 