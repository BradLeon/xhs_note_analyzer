import asyncio
import json
import os
import logging
import pyperclip
import psutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from browser_use import Agent, Controller, ActionResult
from browser_use.browser import BrowserSession, BrowserProfile
from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import PromptTemplate
from playwright.async_api import Page
from crewai.tools import BaseTool
import re


# 配置详细日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('hot_note_finder_tool.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# 尝试导入EventBus用于内存监测
try:
    from bubus.service import EventBus
    EVENTBUS_AVAILABLE = True
except ImportError:
    EVENTBUS_AVAILABLE = False
    logger.warning("⚠️ 无法导入EventBus，内存监测功能将受限")


async def monitor_eventbus_memory(interval: int = 30) -> None:
    """
    定时监测EventBus内存使用情况
    
    Args:
        interval: 监测间隔，单位秒，默认30秒
    """
    if not EVENTBUS_AVAILABLE:
        logger.warning("⚠️ EventBus不可用，跳过内存监测")
        return
        
    monitor_count = 0
    try:
        logger.info(f"📊 开始内存监测，间隔{interval}秒")
        
        while True:
            try:
                monitor_count += 1
                
                # 获取当前进程内存使用情况
                current_process = psutil.Process()
                process_memory_mb = current_process.memory_info().rss / 1024 / 1024
                
                # 尝试获取EventBus的内存使用情况
                eventbus_memory_mb = 0
                active_instances = 0
                
                if hasattr(EventBus, '_instances') and EventBus._instances:
                    active_instances = len([ref for ref in EventBus._instances if ref() is not None])
                    # 简单估算EventBus内存使用
                    eventbus_memory_mb = active_instances * 10  # 粗略估算每个实例10MB
                
                logger.info(f"📊 内存监测#{monitor_count} - 进程总内存: {process_memory_mb:.1f}MB, EventBus实例: {active_instances}, 估算EventBus内存: {eventbus_memory_mb:.1f}MB")
                
                # 内存警告阈值
                if process_memory_mb > 500:  # 进程内存超过500MB
                    logger.warning(f"⚠️ 进程内存使用过高: {process_memory_mb:.1f}MB")
                    
                if eventbus_memory_mb > 50:  # EventBus内存超过50MB
                    logger.warning(f"⚠️ EventBus内存使用过高: {eventbus_memory_mb:.1f}MB，建议清理")
                    
            except Exception as e:
                logger.error(f"❌ 内存监测失败: {e}")
                
            await asyncio.sleep(interval)
            
    except asyncio.CancelledError:
        logger.info("🛑 内存监测任务已取消")
        raise
    except Exception as e:
        logger.error(f"❌ 内存监测异常退出: {e}")

async def cleanup_eventbus(agent: Agent = None) -> None:
    """
    清理EventBus内存
    
    Args:
        agent: 需要清理的Agent实例
    """
    try:
        logger.info("🧹 开始清理EventBus内存...")
        
        # 清理Agent相关的EventBus
        if agent and hasattr(agent, '_eventbus'):
            if hasattr(agent._eventbus, 'stop'):
                await agent._eventbus.stop(clear=True)
                logger.info("✅ Agent EventBus已清理")
        
        # 尝试清理全局EventBus实例
        if EVENTBUS_AVAILABLE and hasattr(EventBus, '_instances'):
            cleaned_count = 0
            for ref in list(EventBus._instances):
                instance = ref()
                if instance is not None:
                    try:
                        if hasattr(instance, 'stop'):
                            await instance.stop(clear=True)
                        elif hasattr(instance, 'clear'):
                            instance.clear()
                        cleaned_count += 1
                    except Exception as e:
                        logger.warning(f"⚠️ 清理EventBus实例失败: {e}")
            
            if cleaned_count > 0:
                logger.info(f"✅ 已清理 {cleaned_count} 个EventBus实例")
        
        logger.info("🧹 EventBus内存清理完成")
        
    except Exception as e:
        logger.error(f"❌ EventBus清理失败: {e}")

class NoteData(BaseModel):
    """笔记数据模型"""
    note_id: str = Field(default="", description="笔记ID")
    note_title: str = Field(description="笔记标题")
    note_url: str = Field(description="笔记URL")
    impression: int = Field(default=0, description="总曝光量")
    click: int = Field(default=0, description="总阅读量")
    like: int = Field(default=0, description="总点赞量")
    collect: int = Field(default=0, description="总收藏量")
    comment: int = Field(default=0, description="总评论量")
    engage: int = Field(default=0, description="总互动量")

class NoteDataList(BaseModel):
    """笔记数据列表模型"""
    note_data_list: List[NoteData] = Field(default_factory=list, description="笔记数据列表")
    total_count: int = Field(default=0, description="总笔记数量")
    collection_method: str = Field(default="browser_automation", description="采集方法")

class ToolExecutionResult(BaseModel):
    """工具执行结果模型"""
    success: bool = Field(description="执行是否成功")
    data: NoteDataList = Field(description="采集到的笔记数据")
    message: str = Field(description="执行结果消息")
    debug_info: Dict[str, Any] = Field(default_factory=dict, description="调试信息")

class ActionStateManager:
    """Action之间的状态管理器，解决参数传递问题 - 单例模式"""
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not ActionStateManager._initialized:
            self.state = {}
            self.execution_log = []
            self.note_detail_parsed = {}
            ActionStateManager._initialized = True
    
    def set_data(self, key: str, value: Any, description: str = ""):
        """设置状态数据"""
        self.state[key] = value
        self.execution_log.append({
            "action": "set",
            "key": key,
            "description": description,
            "timestamp": asyncio.get_event_loop().time()
        })
        logger.info(f"🐛 DEBUG: 设置状态 {key} = '{value}', 实例ID: {id(self)}, 描述: {description}")
    
    def get_data(self, key: str, default=None):
        """获取状态数据"""
        value = self.state.get(key, default)
        logger.info(f"🐛 DEBUG: 获取状态 {key} = '{value}', 实例ID: {id(self)}, 当前状态keys: {list(self.state.keys())}")
        return value
    
    def set_note_detail_parsed(self, key: str, value: bool):
        """设置状态数据"""
        self.note_detail_parsed[key] = value
        logger.info(f"🗄️ 笔记详情页解析状态设置: {key} = {type(value)} ({value})")
    
    def get_note_detail_parsed(self, key: str, default=False):
        """获取状态数据"""
        value = self.note_detail_parsed.get(key, default)
        logger.info(f"🔍 笔记详情页解析状态获取: {key} = {type(value)}")
        return value

    def clear_data(self, key: str = None):
        """清除状态数据"""
        if key:
            self.state.pop(key, None)
            logger.info(f"🗑️ 清除状态: {key}")
        else:
            self.state.clear()
            logger.info("🗑️ 清除所有状态")
    
    def get_execution_summary(self):
        """获取执行摘要"""
        return {
            "total_actions": len(self.execution_log),
            "current_state_keys": list(self.state.keys()),
            "execution_log": self.execution_log[-5:]  # 最近5条记录
        }

# 创建全局状态管理器（向后兼容）
action_state = ActionStateManager()

def ensure_auth_file_exists(auth_file_path: Path) -> bool:
    """
    确保认证文件存在且格式正确
    
    Args:
        auth_file_path: 认证文件路径
    
    Returns:
        bool: 文件是否存在且有效
    """
    try:
        if not auth_file_path.exists():
            logger.info(f"认证文件不存在: {auth_file_path}")
            return False
        
        # 检查文件大小
        file_size = auth_file_path.stat().st_size
        if file_size == 0:
            logger.warning(f"认证文件为空: {auth_file_path}")
            return False
        
        # 尝试解析JSON
        with open(auth_file_path, 'r', encoding='utf-8') as f:
            auth_data = json.load(f)
        
        # 检查基本结构
        if not isinstance(auth_data, dict):
            logger.warning(f"认证文件格式错误，不是字典类型: {type(auth_data)}")
            return False
        
        # 检查cookies字段
        cookies = auth_data.get('cookies', [])
        if not isinstance(cookies, list):
            logger.warning(f"cookies字段格式错误: {type(cookies)}")
            return False
        
        logger.info(f"认证文件验证通过: {auth_file_path} (包含 {len(cookies)} 个cookies)")
        return True
        
    except json.JSONDecodeError as e:
        logger.error(f"认证文件JSON格式错误: {e}")
        return False
    except Exception as e:
        logger.error(f"验证认证文件时出错: {e}")
        return False

def create_precision_controller() -> Controller:
    """创建精确控制器，包含自定义action"""
    controller = Controller()
    logger.info("🎯 开始注册精确控制器的自定义action")
    
    @controller.action('navigate and login xiaohongshu ad platform', domains=['ad.xiaohongshu.com'])
    async def navigate_and_login_xiaohongshu_ad_platform(xhs_ad_email: str, xhs_ad_password: str, browser_session: BrowserSession) -> ActionResult:
        """导航到小红书广告平台并检测登录状态，必要时进行登录"""
        logger.info("🎯 开始导航到小红书广告平台并检测登录状态")
        
        try:
            page = await browser_session.get_current_page()
            
            # 步骤1: 导航到小红书广告平台
            logger.info("📍 正在导航到小红书广告平台...")
            await page.goto("https://ad.xiaohongshu.com/")
            await page.wait_for_load_state('networkidle')
            logger.info("✅ 成功导航到小红书广告平台")
            
            # 步骤2: 检测登录状态
            logger.info("🔍 检测当前登录状态...")
            
            # 检查是否存在"账号登录"按钮，如果存在说明未登录
            login_button_exists = await page.locator("div").filter(has_text=re.compile(r"^账号登录$")).count() > 0
            
            if not login_button_exists:
                # 如果没有"账号登录"按钮，说明已经登录
                logger.info("✅ 检测到已登录状态（通过cookies），跳过登录步骤")
                return ActionResult(extracted_content="Already logged in to XiaoHongShu Ad Platform via cookies")
            
            # 步骤3: 执行登录流程
            logger.info("🔐 检测到未登录状态，开始执行登录流程...")
            
            # 使用原代码中的精准定位器执行登录
            await page.locator("div").filter(has_text=re.compile(r"^账号登录$")).first.click()
            await page.get_by_role("textbox", name="邮箱").fill(xhs_ad_email)
            await page.get_by_role("textbox", name="密码").fill(xhs_ad_password)
            await page.locator(".d-checkbox-indicator").first.click()
            await page.get_by_role("button", name="登 录").click()
            
            # 等待登录完成
            await asyncio.sleep(3)
            
            # 手动保存cookies状态
            try:
                auth_file = Path.cwd().absolute() / 'xiaohongshu_auth.json'
                logger.info(f"💾 保存认证状态到: {auth_file}")
                await browser_session.save_storage_state(str(auth_file))
                logger.info("✅ 认证状态保存成功")
            except Exception as save_error:
                logger.warning(f"⚠️ 保存认证状态失败: {save_error}")
            
            logger.info("✅ 成功完成登录操作")
            return ActionResult(extracted_content="Successfully navigated and logged in to XiaoHongShu Ad Platform")
            
        except Exception as e:
            logger.error(f"❌ 导航和登录过程失败: {str(e)}")
            return ActionResult(extracted_content=f"Failed to navigate and login: {str(e)}")

    @controller.action('navigate to content inspiration page', domains=['ad.xiaohongshu.com'])
    async def navigate_to_content_inspiration(browser_session: BrowserSession) -> ActionResult:
        """导航到内容灵感页面"""
        logger.info("🎯 开始导航到内容灵感页面")
        try:
            page = await browser_session.get_current_page()
            await page.goto("https://ad.xiaohongshu.com/microapp/traffic-guide/contentInspiration/")
            # 下划页面到指定模块
            await page.get_by_role("heading", name="核心笔记").scroll_into_view_if_needed()
            await page.get_by_role("heading", name="核心笔记").click()
            return ActionResult(extracted_content="Successfully navigated to content inspiration page")
        except Exception as e:
            logger.error(f"❌ 导航到内容灵感页面失败: {str(e)}")
            return ActionResult(extracted_content=f"Failed to navigate to content inspiration page: {str(e)}")
    
    @controller.action('get_core_note_titles', domains=['ad.xiaohongshu.com'])
    async def get_core_note_titles(browser_session: BrowserSession) -> ActionResult:
        """获取核心笔记的title列表"""
        logger.info("🎯 开始获取核心笔记的title列表")
        try:
            # 等待核心笔记区域加载
            page = await browser_session.get_current_page()
            logger.info(f"🔍 DEBUG: 当前页面URL: {page.url}")

            # 等待列表加载
            await page.wait_for_selector('.grid-card')
            
            # 获取所有项目
            items = await page.locator('[class*="d-grid-item"][style*="grid-area: span 1 / span 4"]').all()
            
            titles = []
            for item in items:
                # 在每个 d-grid-item 中查找 title
                title_text = await item.locator('.title').text_content()
                if title_text:
                    titles.append(title_text.strip())
                    print(f"获取到笔记标题: {title_text}")
            
            logger.info(f"✅ 成功获取到 {len(titles)} 个标题")
            
            # ⭐ 关键改进：将结果保存到状态管理器
            state_manager = ActionStateManager()
            current_page = state_manager.get_data('current_page', 1)
            state_manager.set_data("all_titles", titles, f"第{current_page}页的所有笔记标题")
            state_manager.set_data("titles_count", len(titles), "当前页标题数量")
            
            logger.info(f"🔍 DEBUG: 状态管理器已保存 {len(titles)} 个标题到第{current_page}页")
            
            return ActionResult(extracted_content=json.dumps(titles, ensure_ascii=False))
        except Exception as e:
            logger.error(f"❌ 获取核心笔记的title列表失败: {str(e)}")
            import traceback
            logger.error(f"❌ DEBUG: 详细错误堆栈: {traceback.format_exc()}")
            return ActionResult(extracted_content=f"Failed to get core note titles: {str(e)}")

    @controller.action('click next page', domains=['ad.xiaohongshu.com'])
    async def click_next_page(browser_session: BrowserSession) -> ActionResult:
        """点击下一页"""
        logger.info("🎯 开始点击下一页")
        try:
            page = await browser_session.get_current_page()
            logger.info(f"🔍 DEBUG: 点击下一页前，当前URL: {page.url}")
            
            # 更新页码状态
            state_manager = ActionStateManager()
            current_page = state_manager.get_data("current_page", 1)
            max_pages = state_manager.get_data("max_pages", 3)  # 获取最大页数限制
            next_page = current_page + 1
            
            # ⭐ 关键修复：检查页面数量限制
            if current_page >= max_pages:
                logger.info(f"🛑 已达到最大页数限制: {current_page}/{max_pages}")
                return ActionResult(extracted_content=f"Reached maximum pages limit: {current_page}/{max_pages}")
            
            logger.info(f"🔍 DEBUG: 准备从第{current_page}页跳转到第{next_page}页 (最大页数: {max_pages})")
            
            # 使用原有XPath作为备用
            try:
                logger.info("🔍 尝试策略1b: 使用原有XPath定位")
                xpath_button = page.locator('//*[@id="content-core-notes"]/div[3]/div[2]/div[2]/div[1]/div[9]')
                if await xpath_button.count() > 0:
                    await xpath_button.click()
                    logger.info("✅ 策略1成功: XPath点击成功")
                    
                    # 更新页码状态
                    state_manager.set_data("current_page", next_page, f"已跳转到第{next_page}页")
                    logger.info(f"🔍 DEBUG: 页码状态已更新为第{next_page}页")
                    
                    return ActionResult(extracted_content="Successfully clicked next page using XPath")
            except Exception as e:
                logger.warning(f"⚠️ 策略1b失败: {e}")
            
            # 所有策略都失败
            logger.error("❌ 所有下一页点击策略都失败")
            return ActionResult(extracted_content="Failed to click next page: All strategies failed")
            
        except Exception as e:
            logger.error(f"❌ 点击下一页失败: {str(e)}")
            return ActionResult(extracted_content=f"Failed to click next page: {str(e)}")

    @controller.action('extract_related_titles', domains=['ad.xiaohongshu.com'])
    async def extract_related_titles() -> ActionResult:
        """提取相关标题 - 基于语义和行业相关性而非字面量匹配"""
        logger.info(f"🎯 开始提取相关标题")
        
        # ⭐ 单例模式：直接获取状态管理器实例
        state_manager = ActionStateManager()
        logger.info(f"🐛 DEBUG: extract_related_titles中获取状态管理器")
        logger.info(f"🐛 DEBUG: extract_related_titles中ActionStateManager实例ID: {id(state_manager)}")
        logger.info(f"🐛 DEBUG: extract_related_titles中当前完整状态: {dict(state_manager.state)}")
        
        # 从状态管理器获取标题列表
        title_list = state_manager.get_data("all_titles", [])
        logger.info(f"🔍 DEBUG: 从状态管理器获取标题列表，类型: {type(title_list)}, 长度: {len(title_list) if title_list else 'None'}")
        
        if not title_list:
            logger.warning("⚠️ 未找到标题列表，可能需要先执行 get_core_note_titles")
            return ActionResult(extracted_content='{"related_titles": [], "error": "未找到标题数据"}')
        
        promotion_target = state_manager.get_data("promotion_target", "")
        logger.info(f"🔍 DEBUG: 从状态管理器获取推广标的: '{promotion_target}' (类型: {type(promotion_target)})")
        logger.info(f"🐛 DEBUG: 推广标的获取后的完整状态检查: {dict(state_manager.state)}")
        
        if not promotion_target:
            logger.warning("⚠️ 未找到推广标的，可能需要先执行 set_promotion_target")
            return ActionResult(extracted_content='{"related_titles": [], "error": "未找到推广标的"}')
        
        logger.info(f"🎯 提取相关标题, 推广标的: {promotion_target}, 标题列表长度: {len(title_list)}")
        logger.info(f"🔍 DEBUG: 标题列表内容: {title_list[:5] if len(title_list) > 5 else title_list}")  # 只显示前5个
      
        try:
            extraction_llm = ChatOpenAI(
                base_url='https://openrouter.ai/api/v1',
                model='qwen/qwen3-235b-a22b-2507',
                api_key=os.environ['OPENROUTER_API_KEY'],
                temperature=0.1
            )

            logger.info("✅ DEBUG: LLM实例创建成功")
        except Exception as llm_error:
            logger.error(f"❌ DEBUG: LLM实例创建失败: {llm_error}")
            return ActionResult(extracted_content='{"related_titles": [], "error": "LLM实例创建失败"}')

        # 改进的 prompt - 强调语义和行业相关性
        prompt = '''您是一个专业的内容分析师。请从给定的标题列表中找出与推广目标在语义、行业或目标用户群体上相关的标题。

推广目标: {promotion_target}

判断相关性的标准：
1. 行业相关性：属于同一个行业领域（如教育培训、求职就业、考试备考等）
2. 目标用户群体相关：面向相似的用户群体（如求职者、备考人员、职场新人等）
3. 功能相关性：提供类似的服务或解决相似的问题（如技能提升、职业规划、考试指导等）

例如：
- "国企央企求职辅导" 与 "公务员考试备考"、"简历优化指导"、"面试技巧分享"、"职场技能提升" 等都是相关的
- "考公上岸经验"、"事业编制备考"、"Dream Offer获取" 等也都属于求职就业领域

标题列表: {title_list}

请返回相关的标题列表，格式为简单的JSON数组，不需要其他解释：
["相关标题1", "相关标题2", ...]

如果没有找到相关标题，返回空数组：[]'''

        template = PromptTemplate(input_variables=['title_list', 'promotion_target'], template=prompt)

        try:
                logger.info("🔍 DEBUG: 开始调用LLM进行标题提取...")
                output = await extraction_llm.ainvoke(template.format(title_list=title_list, promotion_target=promotion_target))
                logger.info(f"🔍 DEBUG: LLM调用成功，输出类型: {type(output)}")
                
                # 尝试解析为JSON
                import json
                try:
                    # 提取JSON内容
                    response_content = output.content.strip()
                    logger.info(f"🔍 DEBUG: LLM原始响应内容: {response_content[:200]}...")  # 只显示前200字符
                    
                    # 如果包含代码块，提取JSON部分
                    if '```' in response_content:
                        start_idx = response_content.find('[')
                        end_idx = response_content.rfind(']') + 1
                        if start_idx != -1 and end_idx != 0:
                            response_content = response_content[start_idx:end_idx]
                            logger.info(f"🔍 DEBUG: 提取JSON部分: {response_content}")
                    
                    related_titles = json.loads(response_content)
                    logger.info(f"🔍 DEBUG: JSON解析成功，相关标题类型: {type(related_titles)}, 长度: {len(related_titles)}")
                    
                    logger.info(f"✅ 成功提取到 {len(related_titles)} 个相关标题")
                    logger.info(f"📋 相关标题: {related_titles}")
                    
                    # ⭐ 关键改进：将相关标题保存到状态管理器
                    state_manager.set_data("related_titles", related_titles, f"与{promotion_target}相关的标题")
                    state_manager.set_data("related_count", len(related_titles), "相关标题数量")
                    state_manager.set_data("processed_note_index", 0, "当前处理的笔记索引")
                    
                    logger.info(f"🔍 DEBUG: 状态管理器已保存相关标题数据")
                    
                    # 返回JSON格式的结果
                    result = {
                        "related_titles": related_titles,
                        "total_count": len(related_titles),
                        "original_count": len(title_list)
                    }
                    
                    return ActionResult(extracted_content=json.dumps(result, ensure_ascii=False), include_in_memory=True)
                    
                except json.JSONDecodeError as je:
                    logger.warning(f"⚠️ DEBUG: JSON解析失败: {je}")
                    logger.warning(f"⚠️ DEBUG: 原始内容: {response_content}")
                    # 如果JSON解析失败，尝试手动提取
                    response_content = output.content.strip()
                    return ActionResult(extracted_content=response_content, include_in_memory=True)
                    
        except Exception as e:
            logger.error(f'❌ 提取相关标题时出错: {e}')
            import traceback
            logger.error(f"❌ DEBUG: 详细错误堆栈: {traceback.format_exc()}")
            return ActionResult(extracted_content='{"related_titles": [], "error": "提取失败"}', include_in_memory=False)

    @controller.action('process_all_related_notes', domains=['ad.xiaohongshu.com'])
    async def process_all_related_notes(browser_session: BrowserSession) -> ActionResult:
        """循环处理所有相关标题：打开详情页 -> 提取数据 -> 关闭详情页"""
        logger.info("🔄 开始循环处理所有相关标题的笔记详情")
        
        try:
            # 从状态管理器获取相关标题列表
            state_manager = ActionStateManager()
            related_titles = state_manager.get_data("related_titles", [])
            logger.info(f"🔍 DEBUG: 获取相关标题列表，类型: {type(related_titles)}, 内容: {related_titles}")
            
            if not related_titles:
                logger.warning("⚠️ 未找到相关标题列表")
                return ActionResult(extracted_content='{"success": false, "error": "未找到相关标题列表，请先执行extract_related_titles"}')
            
            # 确保related_titles是列表类型
            if not isinstance(related_titles, list):
                logger.error(f"❌ DEBUG: related_titles不是列表类型: {type(related_titles)}")
                return ActionResult(extracted_content='{"success": false, "error": "相关标题数据格式错误"}')
            
            logger.info(f"📋 开始处理 {len(related_titles)} 个相关标题")
            
            page = await browser_session.get_current_page()
            processed_count = 0
            failed_count = 0
            processing_results = []
            
            for i, note_title in enumerate(related_titles):
                try:
                    logger.info(f"🔄 处理第 {i+1}/{len(related_titles)} 个标题: {note_title}")
                    logger.info(f"🔍 DEBUG: 当前标题类型: {type(note_title)}, 内容: {note_title}")
                    
                    # 确保note_title是字符串
                    if not isinstance(note_title, str):
                        logger.error(f"❌ DEBUG: 标题不是字符串类型: {type(note_title)}")
                        processing_results.append({
                            "title": str(note_title),
                            "status": "failed",
                            "error": "标题类型错误"
                        })
                        continue
                    
                    # 检查是否已经解析过该笔记
                    is_parsed = state_manager.get_note_detail_parsed(note_title, False)
                    if is_parsed:
                        logger.info(f"⏭️ 跳过已解析的笔记: {note_title}")
                        processing_results.append({
                            "title": note_title,
                            "status": "skipped",
                            "reason": "already_parsed"
                        })
                        continue
                    
                    # 步骤a: 打开笔记详情页
                    logger.info(f"📖 打开笔记详情页: {note_title}")
                    await page.get_by_role("heading", name="核心笔记").click()
                    await asyncio.sleep(0.5)  # 等待页面稳定
                    
                    # 尝试点击标题
                    title_locator = page.locator("#content-core-notes").get_by_text(note_title)
                    await title_locator.click()
                    await asyncio.sleep(2)  # 等待弹窗加载
                    
                    # 步骤b: 提取笔记数据
                    logger.info(f"📊 提取笔记数据: {note_title}")
                    
                    # 检查弹窗是否成功打开
                    modal_title = await page.locator(".interaction-title").text_content()
                    if not modal_title or modal_title.strip() != note_title:
                        logger.warning(f"⚠️ 弹窗标题不匹配: 期望'{note_title}', 实际'{modal_title}'")
                    
                    # 复制笔记链接
                    await page.get_by_text("复制小红书笔记链接").click()
                    await asyncio.sleep(0.5)
                    note_url = pyperclip.paste()
                    logger.info(f"📎 获取笔记链接: {note_url}")
                    
                    # 提取数据统计
                    items = await page.locator('.interaction-card-item').all()
                    stats = {}
                    
                    for item in items:
                        label_text = await item.locator('.interaction-card-item-label text').text_content()
                        value_text = await item.locator('.interaction-card-item-value').text_content()
                        
                        # 格式化数据 - 使用与extract_note_data_from_modal相同的逻辑
                        if value_text:
                            value_text = value_text.strip()
                            try:
                                if "万" in value_text:
                                    # 处理 "36.3万" 或 "3万" 格式
                                    numeric_part = value_text.replace("万", "").strip()
                                    if numeric_part:
                                        value = int(float(numeric_part) * 10000)
                                    else:
                                        value = 0
                                elif "千" in value_text:
                                    # 处理 "3.5千" 格式
                                    numeric_part = value_text.replace("千", "").strip()
                                    if numeric_part:
                                        value = int(float(numeric_part) * 1000)
                                    else:
                                        value = 0
                                elif value_text.replace(".", "").replace(",", "").isdigit():
                                    # 处理纯数字格式 "1000" 或 "1,000"
                                    clean_text = value_text.replace(",", "")
                                    if "." in clean_text:
                                        value = int(float(clean_text))
                                    else:
                                        value = int(clean_text)
                                else:
                                    # 其他格式设为0
                                    value = 0
                            except (ValueError, TypeError) as e:
                                logger.warning(f"⚠️ 数据格式转换失败: '{value_text}' -> {e}")
                                value = 0
                        else:
                            value = 0
                        
                        label = label_text.strip() if label_text else ''
                        match label:
                            case "总曝光量":
                                stats["impression"] = value
                            case "总阅读量":
                                stats["click"] = value
                            case "总点赞量":
                                stats["like"] = value
                            case "总收藏量":
                                stats["collect"] = value
                            case "总评论量":
                                stats["comment"] = value
                            case "总互动量":
                                stats["engage"] = value
                        
                        logger.info(f"📊 数据解析: {label} = '{value_text}' -> {value}")
                    
                    # 构造笔记数据
                    note_data = {
                        "note_title": note_title,
                        "note_url": note_url or f"https://xiaohongshu.com/note/unknown_{i}",
                        "impression": stats.get("impression", 0),
                        "click": stats.get("click", 0),
                        "like": stats.get("like", 0),
                        "collect": stats.get("collect", 0),
                        "comment": stats.get("comment", 0),
                        "engage": stats.get("engage", 0)
                    }
                    
                    # 保存到状态管理器
                    collected_notes = state_manager.get_data("collected_notes", [])
                    collected_notes.append(note_data)
                    state_manager.set_data("collected_notes", collected_notes, f"已采集{len(collected_notes)}条笔记数据")
                    state_manager.set_note_detail_parsed(note_title, True)
                    
                    # 步骤c: 关闭笔记详情页
                    logger.info(f"❌ 关闭笔记详情页: {note_title}")
                    close_button = page.locator("div").filter(has_text=re.compile(r"^笔记详情$")).get_by_role("img")
                    await close_button.click()
                    await asyncio.sleep(1)  # 等待弹窗关闭
                    
                    processed_count += 1
                    processing_results.append({
                        "title": note_title,
                        "status": "success",
                        "data": note_data
                    })
                    
                    logger.info(f"✅ 成功处理: {note_title} ({i+1}/{len(related_titles)})")
                    
                except Exception as e:
                    failed_count += 1
                    error_msg = str(e)
                    logger.error(f"❌ 处理失败: {note_title} - {error_msg}")
                    
                    # 尝试关闭打开的弹窗
                    try:
                        close_button = page.locator("div").filter(has_text=re.compile(r"^笔记详情$")).get_by_role("img")
                        if await close_button.is_visible():
                            await close_button.click()
                            await asyncio.sleep(0.5)
                    except:
                        pass
                    
                    processing_results.append({
                        "title": note_title,
                        "status": "failed",
                        "error": error_msg
                    })
                    
                    # 如果连续失败太多，提前结束
                    if failed_count >= 3:
                        logger.warning("⚠️ 连续失败过多，提前结束处理")
                        break
            
            # 汇总结果
            total_collected = len(state_manager.get_data("collected_notes", []))
            result = {
                "success": True,
                "summary": {
                    "total_related_titles": len(related_titles),
                    "processed_count": processed_count,
                    "failed_count": failed_count,
                    "skipped_count": len([r for r in processing_results if r["status"] == "skipped"]),
                    "total_collected_notes": total_collected
                },
                "processing_results": processing_results,
                "message": f"循环处理完成: 成功{processed_count}个, 失败{failed_count}个, 总采集{total_collected}条笔记"
            }
            
            logger.info(f"🎉 循环处理完成: {result['summary']}")
            return ActionResult(extracted_content=json.dumps(result, ensure_ascii=False))
            
        except Exception as e:
            logger.error(f"❌ 循环处理过程中出错: {str(e)}")
            return ActionResult(extracted_content=f"循环处理失败: {str(e)}")

    @controller.action('get_collection_status')
    async def get_collection_status() -> ActionResult:
        """获取当前采集进度和状态"""
        logger.info("🎯 获取当前采集进度")
        
        state_manager = ActionStateManager()
        status = {
            "execution_summary": state_manager.get_execution_summary(),
            "data_summary": {
                "all_titles_count": len(state_manager.get_data("all_titles", [])),
                "related_titles_count": state_manager.get_data("related_count", 0),
                "processed_index": state_manager.get_data("processed_note_index", 0),
                "collected_notes_count": len(state_manager.get_data("collected_notes", [])),
                "current_page": state_manager.get_data("current_page", 1),
                "parsed_notes_count": len(state_manager.note_detail_parsed)
            },
            "current_state": dict(state_manager.state)
        }
        
        logger.info(f"📊 当前进度: {status['data_summary']}")
        return ActionResult(extracted_content=json.dumps(status, ensure_ascii=False))

    logger.info(f"✅ 控制器创建完成")
    return controller

def create_hot_note_finder_agent(promotion_target: str = '国企央企求职辅导小程序', max_pages: int = 3) -> Agent:
    """创建使用Controller Action的代理"""
    
    # 配置LLM
    llm = ChatOpenAI(
        base_url='https://openrouter.ai/api/v1',
        model='google/gemini-2.5-flash-lite-preview-06-17',
        api_key=os.environ['OPENROUTER_API_KEY'],
        temperature=0.1
    )

    planner_llm = ChatOpenAI(
        base_url='https://openrouter.ai/api/v1',
        model='google/gemini-2.5-flash-lite-preview-06-17',
        api_key=os.environ['OPENROUTER_API_KEY'],
        temperature=0.1
    )

    # 使用绝对路径配置认证文件
    auth_file = Path.cwd().absolute() / 'xiaohongshu_auth.json'
    browser_data_dir = Path.cwd().absolute() / 'browser_data' / 'xiaohongshu'
    
    # 确保浏览器数据目录存在
    browser_data_dir.mkdir(parents=True, exist_ok=True)
    
    # 验证认证文件
    auth_file_valid = ensure_auth_file_exists(auth_file)
    logger.info(f"🔍 认证文件状态: {auth_file} -> {'有效' if auth_file_valid else '无效或不存在'}")
    
    # 创建浏览器会话，使用绝对路径
    browser_profile = BrowserProfile(
        executable_path=Path('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'),
        user_data_dir=str(browser_data_dir),  # 使用持久化数据目录
    )

    browser_session = BrowserSession(
        allowed_domains=['https://*.xiaohongshu.com'],
        storage_state=str(auth_file) if auth_file_valid else None,  # 使用绝对路径
        save_storage_state=str(auth_file),  # 设置保存路径
        browser_profile=browser_profile,
        headless=False,
    )

     # 敏感数据配置
    sensitive_data = {
        'https://ad.xiaohongshu.com/': {
            'xhs_ad_email': '1696249664@qq.com',
            'xhs_ad_password': 'Abcd1234',
        }
    }
    
    # 创建精确控制器
    controller = create_precision_controller()
  # 使用Controller Action的任务描述，集成精确选择器

    task = f"""
你是一个专业的小红书数据采集助手，具备精确的元素定位能力。你的任务是采集与"{promotion_target}"相关的优质热门笔记数据。

**重要提示：相关性判断标准**
不要只进行字面量匹配！要根据以下标准判断相关性：
1. 行业相关性：属于同一个行业领域（教育培训、求职就业、考试备考等）
2. 目标用户群体：面向相似的用户群体（求职者、备考人员、职场新人等）  
3. 功能相关性：提供类似的服务或解决相似的问题（技能提升、职业规划、考试指导等）

**🎯 任务目标：**
采集与"{promotion_target}"相关的优质热门笔记数据。

**📋 相关性判断标准：**
不要只进行字面量匹配！要根据语义相关性判断：
- 行业相关：教育培训、求职就业、考试备考等
- 用户群体：求职者、备考人员、职场新人等  
- 功能相关：技能提升、职业规划、考试指导等

**🔍 执行步骤：**
1. Go to https://ad.xiaohongshu.com/
2. 导航到: 数据 -> 笔记 -> 内容灵感页面, 使用 navigate_to_content_inspiration tool
3. 获取当前页面核心笔记的所有标题，使用 get_core_note_titles tool
4. 从当前页面所有核心笔记的标题中提取有相关性的标题，使用 extract_related_titles tool
5. 使用 process_all_related_notes tool 批量处理所有相关标题的笔记详情，每个笔记执行：打开详情页 -> 提取数据 -> 关闭详情页的操作
6. 使用 get_collection_status tool 查看当前采集进度和状态
7. 点击下一页，使用 click_next_page tool，重复步骤3-6，最多处理{max_pages}页
8. **重要**：如果 click_next_page 返回 "Reached maximum pages limit"，立即停止处理并使用 get_collection_status 获取最终结果
9. 最终使用 get_collection_status tool 获取完整的采集结果

**⚠️ 重要约束：**
- 严格遵守 {max_pages} 页的处理限制，不得超过此数量
- 如果 click_next_page 提示达到页面限制，必须立即停止并输出结果
- 如果某个action连续失败，请立即使用 get_collection_status 获取已采集的数据并输出结果
- 不要无限重试失败的操作，优先保证已采集数据的完整性
- 如果出现技术问题，请立即使用 get_collection_status 输出当前已采集的数据

**最终输出格式：**
请以结构化的JSON格式输出结果:

{{
  "note_data_list": [
    {{
      "note_title": 笔记标题,
      "note_url": 完整URL, 
      "impression": 曝光量数字,
      "click": 阅读量数字,
      "like": 点赞量数字,
      "collect": 收藏量数字,
      "comment": 评论量数字,
      "engage": 互动量数字
    }}
  ]
}}
"""
    
    # 官方调试功能
    debug_dir = Path("output/debug")
    debug_dir.mkdir(parents=True, exist_ok=True)
    
    # ⭐ 关键修复：确保推广标的被设置到状态管理器
    logger.info(f"🐛 DEBUG: 在create_hot_note_finder_agent中准备设置推广标的: '{promotion_target}'")
    logger.info(f"🐛 DEBUG: create_hot_note_finder_agent中action_state实例ID: {id(action_state)}")
    action_state.set_data("promotion_target", promotion_target, f"推广标的: {promotion_target}")
    logger.info(f"🎯 推广标的已设置到状态管理器: {promotion_target}")
    logger.info(f"🐛 DEBUG: 设置后的完整状态: {dict(action_state.state)}")
    
    # 创建代理
    agent = Agent(
        task=task,
        llm=llm,
        planner_llm=planner_llm,
        use_vision=True,  # 结合视觉识别和精确控制
        sensitive_data=sensitive_data,
        controller=controller,
        browser_session=browser_session,
        # 官方调试选项
        save_conversation_path=str(debug_dir / "conversation"),  # 保存完整对话历史
        generate_gif=str(debug_dir / "debug_execution.gif"),  # 生成执行过程GIF
    )

    return agent

async def save_results_for_crewai_flows(note_data_list: List[NoteData], output_dir: str = "output") -> Dict[str, str]:
    """
    优化的保存函数，便于CrewAI flows中其他agent读取信息
    
    Args:
        note_data_list: 笔记数据列表
        output_dir: 输出目录
    
    Returns:
        包含各种文件路径的字典，便于其他agent引用
    """
    try:
        # 确保输出目录存在
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # 生成时间戳
        import time
        timestamp = int(time.time())
        
        # 文件路径
        json_file = output_path / f"hot_notes_data_{timestamp}.json"
        summary_file = output_path / f"hot_notes_summary_{timestamp}.txt"
        csv_file = output_path / f"hot_notes_data_{timestamp}.csv"
        
        # 1. 保存结构化JSON数据（供其他agent程序化读取）
        structured_data = {
            "metadata": {
                "collection_time": timestamp,
                "total_notes": len(note_data_list),
                "collection_method": "browser_automation_tool",
                "data_version": "1.0"
            },
            "notes": [note.model_dump() for note in note_data_list],
            "statistics": {
                "total_impression": sum(note.impression for note in note_data_list),
                "total_click": sum(note.click for note in note_data_list),
                "total_like": sum(note.like for note in note_data_list),
                "total_collect": sum(note.collect for note in note_data_list),
                "total_comment": sum(note.comment for note in note_data_list),
                "total_engage": sum(note.engage for note in note_data_list),
                "avg_engagement_rate": sum(note.engage / max(note.impression, 1) for note in note_data_list) / len(note_data_list) if note_data_list else 0
            }
        }
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(structured_data, f, ensure_ascii=False, indent=2)
        
        # 2. 保存人类可读的摘要（供human review和其他agent理解）
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(f"小红书热门笔记采集结果摘要\n")
            f.write(f"采集时间: {timestamp}\n")
            f.write(f"采集方法: browser_automation_tool\n")
            f.write(f"总计笔记数: {len(note_data_list)}\n")
            f.write("=" * 80 + "\n\n")
            
            # 统计信息
            f.write("📊 数据统计:\n")
            f.write(f"- 总曝光量: {structured_data['statistics']['total_impression']:,}\n")
            f.write(f"- 总阅读量: {structured_data['statistics']['total_click']:,}\n")
            f.write(f"- 总点赞量: {structured_data['statistics']['total_like']:,}\n")
            f.write(f"- 总收藏量: {structured_data['statistics']['total_collect']:,}\n")
            f.write(f"- 总评论量: {structured_data['statistics']['total_comment']:,}\n")
            f.write(f"- 总互动量: {structured_data['statistics']['total_engage']:,}\n")
            f.write(f"- 平均互动率: {structured_data['statistics']['avg_engagement_rate']:.2%}\n\n")
            
            # 笔记详情
            f.write("📝 笔记详情:\n")
            f.write("-" * 80 + "\n")
            
            for i, note in enumerate(note_data_list, 1):
                f.write(f"\n{i}. {note.note_title}\n")
                f.write(f"   链接: {note.note_url}\n")
                f.write(f"   数据: 曝光{note.impression:,} | 阅读{note.click:,} | 点赞{note.like:,} | 收藏{note.collect:,} | 评论{note.comment:,} | 互动{note.engage:,}\n")
                if note.impression > 0:
                    engagement_rate = note.engage / note.impression
                    f.write(f"   互动率: {engagement_rate:.2%}\n")
        
        # 3. 保存CSV格式数据（供数据分析工具使用）
        import csv
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['note_title', 'note_url', 'impression', 'click', 'like', 'collect', 'comment', 'engage', 'engagement_rate']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for note in note_data_list:
                engagement_rate = note.engage / note.impression if note.impression > 0 else 0
                writer.writerow({
                    'note_title': note.note_title,
                    'note_url': note.note_url,
                    'impression': note.impression,
                    'click': note.click,
                    'like': note.like,
                    'collect': note.collect,
                    'comment': note.comment,
                    'engage': note.engage,
                    'engagement_rate': f"{engagement_rate:.4f}"
                })
        
        # 4. 创建最新数据的符号链接（便于其他agent总是读取最新数据）
        latest_json = output_path / "latest_hot_notes.json"
        latest_summary = output_path / "latest_hot_notes_summary.txt"
        latest_csv = output_path / "latest_hot_notes.csv"
        
        # 删除旧的符号链接（如果存在）
        for latest_file in [latest_json, latest_summary, latest_csv]:
            if latest_file.exists():
                latest_file.unlink()
        
        # 创建新的符号链接
        latest_json.symlink_to(json_file.name)
        latest_summary.symlink_to(summary_file.name)
        latest_csv.symlink_to(csv_file.name)
        
        logger.info(f"✅ 数据已保存到多种格式文件，便于CrewAI flows读取")
        
        return {
            "json_file": str(json_file),
            "summary_file": str(summary_file),
            "csv_file": str(csv_file),
            "latest_json": str(latest_json),
            "latest_summary": str(latest_summary),
            "latest_csv": str(latest_csv),
            "total_notes": len(note_data_list)
        }
        
    except Exception as e:
        logger.error(f"❌ 保存文件时出错: {e}")
        return {"error": str(e)}

class HotNoteFinder:
    """
    小红书热门笔记查找工具 - 基于browser_use的CrewAI工具
    """
    
    name: str = "hot_note_finder"
    description: str = """
    查找小红书平台上与指定推广目标相关的热门笔记数据。
    该工具使用browser_use自动化浏览器操作，登录小红书广告平台，
    采集与目标相关的优质笔记的详细数据（包括曝光量、阅读量、点赞量等）。
    
    输入参数：
    - promotion_target: 推广目标（例如：'国企央企求职辅导小程序'）
    - max_pages: 最大处理页数（默认3页）
    - output_dir: 输出目录（默认'output'）
    
    输出：包含笔记数据的结构化结果，保存为多种格式便于后续处理。
    """
    
    def _run(self, promotion_target: str, max_pages: int = 3, output_dir: str = "output") -> str:
        """
        同步运行工具（CrewAI要求）
        """
        try:
            # 由于browser_use是异步的，我们需要在这里运行异步代码
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self._async_run(promotion_target, max_pages, output_dir))
            loop.close()
            return result
        except Exception as e:
            logger.error(f"❌ 工具执行失败: {e}")
            return json.dumps({
                "success": False,
                "error": str(e),
                "message": "热门笔记查找工具执行失败"
            }, ensure_ascii=False)
    
    async def _async_run(self, promotion_target: str, max_pages: int = 3, output_dir: str = "output") -> str:
        """
        异步执行核心逻辑
        """
        logger.info(f"🚀 开始执行热门笔记查找任务")
        logger.info(f"🎯 推广目标: {promotion_target}")
        logger.info(f"📄 最大页数: {max_pages}")
        
        # 启动内存监测任务
        memory_monitor_task = None
        agent = None
        
        try:
            # 先执行初始EventBus清理
            await cleanup_eventbus()
            logger.info("🧹 初始EventBus清理完成")
            
            # 启动内存监测（缩短间隔到10秒进行测试）
            memory_monitor_task = asyncio.create_task(monitor_eventbus_memory(10))
            logger.info("📊 内存监测任务已启动")
            
            # 创建状态管理器
            action_state = ActionStateManager()
            
            # 创建代理
            agent = create_hot_note_finder_agent(promotion_target=promotion_target, max_pages=max_pages)
            logger.info("✅ 代理创建成功")
            
            # 清理之前的状态
            logger.info(f"🐛 DEBUG: HotNoteFinder._async_run中清理前的状态: {dict(action_state.state)}")
            logger.info(f"🐛 DEBUG: HotNoteFinder._async_run中action_state实例ID: {id(action_state)}")
            action_state.clear_data()
            logger.info(f"🐛 DEBUG: HotNoteFinder._async_run中清理后的状态: {dict(action_state.state)}")
            
            action_state.set_data("promotion_target", promotion_target, f"推广标的: {promotion_target}")
            action_state.set_data("max_pages", max_pages, f"最大页数: {max_pages}")
            logger.info(f"🎯 工具执行: 最大页数已设置 = {max_pages}")
            
            try: 
                # 运行任务
                logger.info("🔄 开始执行采集任务...")
                history = await agent.run()
                
                logger.info(f"📊 任务执行完成，状态: {history.is_done()}")
                
                # 详细调试agent执行状态
                logger.info(f"🔍 DEBUG: Agent执行历史分析:")
                logger.info(f"  - 是否完成: {history.is_done()}")
                logger.info(f"  - 是否有错误: {history.has_errors()}")
                logger.info(f"  - 执行步数: {len(history.messages) if hasattr(history, 'messages') else 'N/A'}")
                if hasattr(history, 'errors') and history.errors():
                    logger.error(f"  - 错误列表: {history.errors()}")
                
                # 尝试多种方式获取结果数据
                collected_notes_data = []
                data_source = "none"
                
                # 策略1: 从final_result获取
                if history.is_done() and not history.has_errors():
                    final_result = history.final_result()
                    logger.info(f"🔍 DEBUG: final_result类型: {type(final_result)}")
                    logger.info(f"🔍 DEBUG: final_result内容: {repr(final_result)[:200]}...")
                    
                    if final_result:
                        try:
                            # 尝试解析agent的结果
                            if isinstance(final_result, str):
                                if final_result.strip():  # 确保不是空字符串
                                    result_data = json.loads(final_result)
                                    if "note_data_list" in result_data:
                                        collected_notes_data = result_data["note_data_list"]
                                        data_source = "final_result"
                                        logger.info(f"✅ 从final_result成功获取 {len(collected_notes_data)} 条数据")
                                else:
                                    logger.warning("⚠️ final_result是空字符串")
                            else:
                                result_data = final_result
                                if hasattr(result_data, 'get') and "note_data_list" in result_data:
                                    collected_notes_data = result_data["note_data_list"]
                                    data_source = "final_result_object"
                        except Exception as parse_error:
                            logger.warning(f"⚠️ 解析final_result失败: {parse_error}")
                
                # 策略2: 从状态管理器获取已收集的数据
                if not collected_notes_data:
                    logger.info("🔍 DEBUG: 尝试从ActionStateManager获取数据")
                    try:
                        state_collected_notes = action_state.get_data("collected_notes", [])
                        if state_collected_notes:
                            collected_notes_data = state_collected_notes
                            data_source = "state_manager"
                            logger.info(f"✅ 从状态管理器获取 {len(collected_notes_data)} 条数据")
                    except Exception as state_error:
                        logger.warning(f"⚠️ 从状态管理器获取数据失败: {state_error}")
                
                # 策略3: 从执行历史中提取数据 
                if not collected_notes_data and hasattr(history, 'messages'):
                    logger.info("🔍 DEBUG: 尝试从执行历史中提取数据")
                    try:
                        for message in reversed(history.messages):  # 从最新的消息开始查找
                            if hasattr(message, 'content') and message.content:
                                content = str(message.content)
                                if '"note_data_list"' in content or '"success": true' in content:
                                    try:
                                        # 尝试从消息内容中提取JSON
                                        import re
                                        json_match = re.search(r'\{.*"note_data_list".*\}', content, re.DOTALL)
                                        if json_match:
                                            result_data = json.loads(json_match.group())
                                            if "note_data_list" in result_data:
                                                collected_notes_data = result_data["note_data_list"]
                                                data_source = "history_extraction"
                                                logger.info(f"✅ 从执行历史提取 {len(collected_notes_data)} 条数据")
                                                break
                                    except:
                                        continue
                    except Exception as history_error:
                        logger.warning(f"⚠️ 从执行历史提取数据失败: {history_error}")
                
                logger.info(f"📊 数据获取结果: 来源={data_source}, 数量={len(collected_notes_data)}")
                
                # 数据验证和转换
                note_list = []
                if collected_notes_data:
                    logger.info(f"🔍 DEBUG: 开始验证和转换 {len(collected_notes_data)} 条笔记数据")
                    
                    for i, note_data in enumerate(collected_notes_data):
                        try:
                            # 验证数据结构
                            if not isinstance(note_data, dict):
                                logger.warning(f"⚠️ 笔记 {i+1} 数据格式错误: {type(note_data)}")
                                continue
                                
                            # 确保必要字段存在
                            required_fields = ['note_title', 'note_url']
                            missing_fields = [field for field in required_fields if field not in note_data]
                            if missing_fields:
                                logger.warning(f"⚠️ 笔记 {i+1} 缺少必要字段: {missing_fields}")
                                continue
                                
                            # 记录数据详情用于调试
                            logger.debug(f"📝 笔记 {i+1}: {note_data.get('note_title', 'N/A')[:50]}...")
                            
                            # 从URL提取note_id
                            note_url = note_data.get("note_url", "")
                            note_id = ""
                            if note_url:
                                # 简单的note_id提取逻辑
                                if "/note/" in note_url:
                                    note_id = note_url.split("/note/")[-1].split("?")[0]
                                elif "/explore/" in note_url:
                                    note_id = note_url.split("/explore/")[-1].split("?")[0]
                            
                            note = NoteData(
                                note_id=note_id,
                                note_title=note_data.get("note_title", ""),
                                note_url=note_url,
                                impression=note_data.get("impression", 0),
                                click=note_data.get("click", 0),
                                like=note_data.get("like", 0),
                                collect=note_data.get("collect", 0),
                                comment=note_data.get("comment", 0),
                                engage=note_data.get("engage", 0)
                            )
                            note_list.append(note)
                            
                        except Exception as e:
                            logger.warning(f"⚠️ 跳过无效笔记数据 {i+1}: {e}")
                            continue
                    
                    logger.info(f"✅ 数据验证完成，有效笔记: {len(note_list)}/{len(collected_notes_data)}")
                else:
                    logger.warning("⚠️ 未获取到任何笔记数据")
                
                if note_list:
                    # 保存结果
                    file_paths = await save_results_for_crewai_flows(note_list, output_dir)
                    
                    # 构建成功结果
                    result = ToolExecutionResult(
                        success=True,
                        data=NoteDataList(
                            note_data_list=note_list,
                            total_count=len(note_list),
                            collection_method="browser_automation_tool"
                        ),
                        message=f"成功采集到 {len(note_list)} 条热门笔记数据",
                        debug_info={
                            "promotion_target": promotion_target,
                            "processed_pages": min(max_pages, 10),  # 实际处理的页数
                            "file_paths": file_paths,
                            "execution_summary": action_state.get_execution_summary()
                        }
                    )
                    
                    logger.info(f"✅ 工具执行成功，采集到 {len(note_list)} 条笔记")
                    return json.dumps(result.model_dump(), ensure_ascii=False, indent=2)
                
                else:
                    # 没有采集到数据
                    result = ToolExecutionResult(
                        success=False,
                        data=NoteDataList(note_data_list=[], total_count=0),
                        message="未采集到相关笔记数据，可能是目标关键词过于具体或网络问题",
                        debug_info={
                            "promotion_target": promotion_target,
                            "agent_errors": history.errors() if history else [],
                            "execution_summary": action_state.get_execution_summary()
                        }
                    )
                    
                    logger.warning("⚠️ 未采集到笔记数据")
                    return json.dumps(result.model_dump(), ensure_ascii=False, indent=2)
                    
            except Exception as e:
                logger.error(f"⚠️ Agent执行中断: {e}")
                
                # 即使agent执行失败，也尝试返回部分结果
                result = ToolExecutionResult(
                    success=False,
                    data=NoteDataList(note_data_list=[], total_count=0),
                    message=f"采集过程中断: {str(e)}",
                    debug_info={
                        "promotion_target": promotion_target,
                        "error": str(e),
                        "execution_summary": action_state.get_execution_summary()
                    }
                )
                
                return json.dumps(result.model_dump(), ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"❌ 工具执行过程中出错: {e}")
            import traceback
            traceback.print_exc()
            
            # 返回错误结果
            result = ToolExecutionResult(
                success=False,
                data=NoteDataList(note_data_list=[], total_count=0),
                message=f"工具执行失败: {str(e)}",
                debug_info={"error": str(e)}
            )
            
            return json.dumps(result.model_dump(), ensure_ascii=False, indent=2)
        
        finally:
            # 检查并停止内存监测任务
            if memory_monitor_task:
                logger.info(f"🔍 DEBUG: 内存监测任务状态 - done: {memory_monitor_task.done()}, cancelled: {memory_monitor_task.cancelled()}")
                if not memory_monitor_task.done():
                    logger.info("🛑 正在取消内存监测任务...")
                    memory_monitor_task.cancel()
                    try:
                        await memory_monitor_task
                    except asyncio.CancelledError:
                        logger.info("✅ 内存监测任务已取消")
                    except Exception as cancel_error:
                        logger.warning(f"⚠️ 取消内存监测任务时出错: {cancel_error}")
                else:
                    logger.info("📊 内存监测任务已自然结束")
            
            # 执行最终EventBus清理
            if agent:
                try:
                    await cleanup_eventbus(agent)
                    logger.info("✅ 最终EventBus清理完成")
                except Exception as cleanup_error:
                    logger.error(f"⚠️ 最终EventBus清理失败: {cleanup_error}")
            else:
                logger.info("🧹 执行全局EventBus清理")
                try:
                    await cleanup_eventbus()
                    logger.info("✅ 全局EventBus清理完成")
                except Exception as cleanup_error:
                    logger.error(f"⚠️ 全局EventBus清理失败: {cleanup_error}")
            
            logger.info("🔄 资源清理完成")

async def find_hot_notes(promotion_target: str, max_pages: int = 3, output_dir: str = "output") -> ToolExecutionResult:
    """
    可被外部调用的核心函数 - 替代原来的main()函数
    
    Args:
        promotion_target: 推广目标
        max_pages: 最大处理页数
        output_dir: 输出目录
    
    Returns:
        ToolExecutionResult: 执行结果
    """
    logger.info(f"🚀 开始执行热门笔记查找")
    logger.info(f"🎯 推广目标: {promotion_target}")
    
    try:
        # 创建工具实例
        tool = HotNoteFinder()
        
        # 执行工具
        result_str = await tool._async_run(promotion_target, max_pages, output_dir)
        
        # 解析结果
        result_data = json.loads(result_str)
        result = ToolExecutionResult(**result_data)
        
        return result
        
    except Exception as e:
        logger.error(f"❌ find_hot_notes执行失败: {e}")
        return ToolExecutionResult(
            success=False,
            data=NoteDataList(note_data_list=[], total_count=0),
            message=f"执行失败: {str(e)}",
            debug_info={"error": str(e)}
        )

# 便于直接调用的简化函数
async def main(promotion_target: str = '国企央企求职辅导小程序', max_pages: int = 3):
    """
    主函数 - 可被外部调用，替代原来的main()
    """
    result = await find_hot_notes(promotion_target, max_pages)
    
    if result.success:
        print(f"✅ 采集成功！共获得 {result.data.total_count} 条笔记数据")
        print(f"📄 详细信息: {result.message}")
        
        # 显示前几条数据作为示例
        for i, note in enumerate(result.data.note_data_list[:3], 1):
            print(f"\n{i}. {note.note_title}")
            print(f"   曝光: {note.impression:,} | 阅读: {note.click:,} | 点赞: {note.like:,}")
            print(f"   链接: {note.note_url}")
    else:
        print(f"❌ 采集失败: {result.message}")
    
    return result

if __name__ == "__main__":
    # 支持直接运行
    import sys
    
    promotion_target = sys.argv[1] if len(sys.argv) > 1 else '国企央企求职辅导小程序'
    max_pages = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    
    asyncio.run(main(promotion_target, max_pages))