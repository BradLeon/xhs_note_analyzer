"""
MediaCrawler API 客户端工具
用于与MediaCrawler服务器通信，获取小红书笔记详细内容
参考: https://github.com/BradLeon/MediaCrawler-API-Server
"""

import os
import json
import requests
# Removed unused imports: asyncio, aiohttp
import time
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


class MediaCrawlerClient:
    """MediaCrawler API 客户端"""
    
    def __init__(self, api_endpoint: str = None, api_key: str = None, debug_requests: bool = True):
        """
        初始化客户端
        
        Args:
            api_endpoint: API服务器地址，默认从环境变量MEDIACRAWLER_API_ENDPOINT获取
            api_key: API密钥，默认从环境变量MEDIACRAWLER_API_KEY获取
            debug_requests: 是否开启HTTP请求调试，默认True
        """
        self.api_endpoint = api_endpoint or os.getenv("MEDIACRAWLER_API_ENDPOINT", "http://localhost:8000")
        self.api_key = api_key or os.getenv("MEDIACRAWLER_API_KEY", "")
        self.debug_requests = debug_requests
        self.session = requests.Session()
        
        # 设置认证头
        if self.api_key:
            self.session.headers.update({"Authorization": f"Bearer {self.api_key}"})
            
        # 设置默认头部
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "MediaCrawler-Client/1.0"
        })
        
        logger.info(f"🔧 MediaCrawler客户端初始化完成")
        logger.info(f"🔗 API端点: {self.api_endpoint}")
        logger.info(f"🔑 API密钥: {'已设置' if self.api_key else '未设置'}")
        logger.info(f"🐛 调试模式: {'开启' if self.debug_requests else '关闭'}")
    
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
    
    def create_crawl_task(self, note_urls: List[str], fetch_comments: bool = False, 
                         max_comments: int = 100) -> Dict[str, Any]:
        """
        创建小红书内容采集任务
        
        Args:
            note_urls: 笔记URL列表（必须包含xsec_token和xsec_source参数）
            fetch_comments: 是否获取评论
            max_comments: 最大评论数量
            
        Returns:
            任务创建结果
        """
        try:
            # 从URL提取note_ids用于content_ids字段
            note_ids = []
            for url in note_urls:
                note_id = self.extract_note_id_from_url(url)
                if note_id:
                    note_ids.append(note_id)
                else:
                    logger.warning(f"⚠️ 无法从URL提取note_id: {url}")
            
            # 构建符合新API格式的payload
            payload = {
                "platform": "xhs",
                "task_type": "detail",
                "content_ids": note_ids,                    # 提取的note_id列表
                "xhs_note_urls": note_urls,                 # 必需：包含token的完整URL
                "max_count": len(note_urls),
                "max_comments": max_comments if fetch_comments else 0,
                "start_page": 1,
                "enable_proxy": False,
                "headless": False,
                "enable_comments": fetch_comments,
                "enable_sub_comments": fetch_comments,
                "save_data_option": "db",
                "clear_cookies": False
            }
            
            logger.info(f"🔄 创建采集任务，目标数量: {len(note_urls)}")
            logger.info(f"📋 URL格式: {len([url for url in note_urls if 'xsec_token' in url])}/{len(note_urls)} 包含token")
            
            # 调试: 打印完整请求信息
            if self.debug_requests:
                logger.info(f"📡 POST请求: {self.api_endpoint}/api/v1/tasks")
                logger.info(f"📦 请求头: {dict(self.session.headers)}")
                logger.info(f"📄 请求体: {json.dumps(payload, ensure_ascii=False, indent=2)}")
            
            response = self.session.post(
                f"{self.api_endpoint}/api/v1/tasks",
                json=payload,
                timeout=30
            )
            
            # 调试: 打印响应信息
            if self.debug_requests:
                logger.info(f"📨 响应状态: {response.status_code} {response.reason}")
                logger.info(f"📋 响应头: {dict(response.headers)}")
                logger.info(f"📝 响应体: {response.text[:1000]}...")
            
            response.raise_for_status()
            
            result = response.json()
            # 适配新的CrawlerTaskResponse格式
            if result.get("task_id"):
                logger.info(f"✅ 任务创建成功: {result.get('task_id')}")
                logger.info(f"📝 服务器消息: {result.get('message', 'N/A')}")
                # 为了兼容性，确保返回success标志
                result["success"] = True
            else:
                logger.warning(f"⚠️ 任务创建响应异常: {result}")
                result["success"] = False
                
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ 创建任务失败, 错误: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"❌ 响应状态: {e.response.status_code}")
                logger.error(f"❌ 响应内容: {e.response.text[:500]}")
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
            url = f"{self.api_endpoint}/api/v1/tasks/{task_id}/status"
            
            # 调试: 打印请求信息
            if self.debug_requests:
                logger.info(f"📡 GET请求: {url}")
                logger.info(f"📦 请求头: {dict(self.session.headers)}")
            
            response = self.session.get(url, timeout=10)
            
            # 调试: 打印响应信息
            if self.debug_requests:
                logger.info(f"📨 响应状态: {response.status_code} {response.reason}")
                logger.info(f"📝 响应体: {response.text[:500]}...")
            
            response.raise_for_status()
            
            result = response.json()
            status = result.get("status", "unknown")
            logger.info(f"📊 任务 {task_id} 状态: {status}")
            
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ 获取任务状态失败: {task_id}, 错误: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"❌ 响应状态: {e.response.status_code}")
                logger.error(f"❌ 响应内容: {e.response.text[:500]}")
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"❌ 处理失败: {task_id}, 错误: {e}")
            return {"success": False, "error": str(e)}
    
    def get_task_result(self, task_id: str) -> Dict[str, Any]:
        """
        获取任务执行结果
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务结果信息
        """
        try:
            url = f"{self.api_endpoint}/api/v1/tasks/{task_id}/result"
            
            if self.debug_requests:
                logger.info(f"📡 GET请求: {url}")
            
            response = self.session.get(url, timeout=10)
            
            if self.debug_requests:
                logger.info(f"📨 响应状态: {response.status_code} {response.reason}")
                logger.info(f"📝 响应体: {response.text[:1000]}...")
            
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"📊 任务 {task_id} 结果: 成功={result.get('success')}, 数据条数={result.get('data_count', 0)}")
            
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ 获取任务结果失败: {task_id}, 错误: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"❌ 响应状态: {e.response.status_code}")
                logger.error(f"❌ 响应内容: {e.response.text[:500]}")
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"❌ 处理失败: {task_id}, 错误: {e}")
            return {"success": False, "error": str(e)}
    
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
            
            url = f"{self.api_endpoint}/api/v1/data/content/xhs/{note_id}"
            
            # 调试: 打印请求信息
            if self.debug_requests:
                logger.info(f"📡 GET请求: {url}")
                logger.info(f"📦 请求头: {dict(self.session.headers)}")
            
            response = self.session.get(url, timeout=10)
            
            # 调试: 打印响应信息
            if self.debug_requests:
                logger.info(f"📨 响应状态: {response.status_code} {response.reason}")
                logger.info(f"📝 响应体: {response.text[:1000]}...")
            
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("data"):
                logger.info(f"✅ 成功获取笔记内容: {note_id}")
                # 为了兼容性，添加success字段
                result["success"] = True
            else:
                logger.warning(f"⚠️ 未找到笔记内容: {note_id}")
                result["success"] = False
            
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ 查询笔记失败: {note_id}, 错误: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"❌ 响应状态: {e.response.status_code}")
                logger.error(f"❌ 响应内容: {e.response.text[:500]}")
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"❌ 处理失败: {note_id}, 错误: {e}")
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
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            status_result = self.get_task_status(task_id)
            
            if not status_result.get("success", True):
                # 如果获取状态失败，等一会再试
                time.sleep(check_interval)
                continue
                
            status = status_result.get("status", "unknown")
            done = status_result.get("done", False)
            success = status_result.get("success")
            
            if done:
                if success is True:
                    logger.info(f"✅ 任务 {task_id} 执行完成")
                    return True
                else:
                    logger.error(f"❌ 任务 {task_id} 执行失败")
                    return False
            elif status == "failed":
                logger.error(f"❌ 任务 {task_id} 执行失败")
                return False
            elif status in ["running", "pending"]:
                # 任务正在运行，继续等待
                progress = status_result.get("progress", {})
                if progress:
                    percent = progress.get("progress_percent", 0)
                    stage = progress.get("current_stage", "未知")
                    logger.info(f"⏳ 任务 {task_id} 进行中: {stage} ({percent:.1f}%)")
                else:
                    logger.info(f"⏳ 任务 {task_id} 状态: {status}")
                time.sleep(check_interval)
            else:
                logger.warning(f"⚠️ 任务 {task_id} 状态未知: {status}")
                time.sleep(check_interval)
        
        logger.error(f"⏰ 任务 {task_id} 等待超时")
        return False

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
                note_urls=[note_url],
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
            # 构建URL到note_id的映射，同时收集有效的URL和note_id
            valid_urls = []
            url_to_id_map = {}  # URL -> note_id
            
            for url in note_urls:
                note_id = self.extract_note_id_from_url(url)
                if note_id:
                    valid_urls.append(url)
                    url_to_id_map[url] = note_id
                else:
                    logger.warning(f"⚠️ 无法从URL提取note_id: {url}")
            
            if not valid_urls:
                logger.error("❌ 没有有效的URL")
                return [{"success": False, "error": "没有有效的note_id"}] * len(note_urls)
            
            logger.info(f"🔄 开始批量爬取 {len(valid_urls)} 个笔记")
            
            # 检查哪些数据已存在，哪些需要新采集
            existing_data = {}
            new_urls = []
            
            for url in valid_urls:
                note_id = url_to_id_map[url]
                existing_result = self.get_note_content_by_id(note_id)
                if existing_result.get("success") and existing_result.get("data"):
                    existing_data[note_id] = existing_result
                    logger.info(f"✅ 从数据库获取到现有数据: {note_id}")
                else:
                    new_urls.append(url)
            
            # 对于需要新采集的URL，创建批量采集任务
            if new_urls:
                logger.info(f"🚀 创建批量采集任务，目标: {len(new_urls)} 个新笔记")
                
                task_result = self.create_crawl_task(
                    note_urls=new_urls,
                    fetch_comments=fetch_comments
                )
                
                if task_result.get("task_id"):
                    task_id = task_result["task_id"]
                    
                    # 等待任务完成
                    if self.wait_for_task_completion(task_id, max_wait_time=600):
                        logger.info(f"✅ 批量采集任务完成: {task_id}")
                        
                        # 获取新采集的数据
                        for url in new_urls:
                            note_id = url_to_id_map[url]
                            result = self.get_note_content_by_id(note_id)
                            if result.get("success"):
                                existing_data[note_id] = result
                            else:
                                existing_data[note_id] = {"success": False, "error": f"无法获取数据: {note_id}"}
                    else:
                        logger.error(f"❌ 批量采集任务失败或超时: {task_id}")
                        # 为失败的URL创建错误结果
                        for url in new_urls:
                            note_id = url_to_id_map[url]
                            existing_data[note_id] = {"success": False, "error": f"采集任务失败: {task_id}"}
                else:
                    logger.error(f"❌ 创建批量任务失败: {task_result.get('message')}")
                    # 为所有新URL创建错误结果
                    for url in new_urls:
                        note_id = url_to_id_map[url]
                        existing_data[note_id] = {"success": False, "error": "创建采集任务失败"}
            
            # 按原始URL顺序组织结果
            results = []
            for url in note_urls:
                if url in url_to_id_map:
                    note_id = url_to_id_map[url]
                    results.append(existing_data.get(note_id, {"success": False, "error": f"未处理的笔记: {note_id}"}))
                else:
                    results.append({"success": False, "error": f"无法处理URL: {url}"})
            
            success_count = len([r for r in results if r.get("success", False)])
            logger.info(f"🎯 批量爬取完成: 成功 {success_count}/{len(note_urls)}")
            logger.info(f"📊 数据来源: 缓存 {len(existing_data) - len(new_urls if 'new_urls' in locals() else [])}, 新采集 {len(new_urls if 'new_urls' in locals() else [])}")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ 批量爬取失败: {e}")
            return [{"success": False, "error": str(e)}] * len(note_urls)
    
    def health_check(self) -> bool:
        """检查API服务器健康状态"""
        try:
            url = f"{self.api_endpoint}/api/v1/data/health"
            
            # 调试: 打印请求信息
            if self.debug_requests:
                logger.info(f"📡 GET请求: {url}")
                logger.info(f"📦 请求头: {dict(self.session.headers)}")
            
            response = self.session.get(url, timeout=5)
            
            # 调试: 打印响应信息
            if self.debug_requests:
                logger.info(f"📨 响应状态: {response.status_code} {response.reason}")
                logger.info(f"📝 响应体: {response.text[:200]}...")
            
            is_healthy = response.status_code == 200
            logger.info(f"🩺 健康检查结果: {'✅ 健康' if is_healthy else '❌ 不健康'}")
            
            return is_healthy
            
        except Exception as e:
            logger.error(f"❌ 健康检查异常: {e}")
            return False


def create_mediacrawler_client(debug_requests: bool = True) -> MediaCrawlerClient:
    """创建MediaCrawler客户端实例"""
    return MediaCrawlerClient(debug_requests=debug_requests)


# 便捷函数
def fetch_note_content(note_url: str, fetch_comments: bool = False) -> Dict[str, Any]:
    """获取单个笔记内容的便捷函数"""
    client = create_mediacrawler_client()
    return client.crawl_note(note_url, fetch_comments)


def batch_fetch_note_contents(note_urls: List[str], fetch_comments: bool = False) -> List[Dict[str, Any]]:
    """批量获取笔记内容的便捷函数"""
    client = create_mediacrawler_client()
    return client.batch_crawl_notes(note_urls, fetch_comments)


if __name__ == "__main__":
    # 测试代码
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # 测试API连接
    client = create_mediacrawler_client()
    
    print("🧪 测试MediaCrawler API连接...")
    if client.health_check():
        print("✅ API服务器连接正常")
        
        # 如果API可用，测试笔记爬取
        test_urls = [
            "https://www.xiaohongshu.com/explore/65728c2a000000003403fc88?xsec_token=ZBBMPkZKZC66wNYHvcBT26aYWhVGGRQZBgbpYzClweEPc=&xsec_source=pc_ad"
        ]
        print(f"\n🧪 测试笔记爬取: {test_urls[0][:80]}...")
        result = client.crawl_note(test_urls[0])
        print(f"结果: {json.dumps(result, ensure_ascii=False, indent=2)[:500]}...")
    else:
        print("❌ API服务器连接失败，跳过爬取测试")