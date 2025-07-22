import asyncio
import json
import os
import logging
import pyperclip
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from browser_use import Agent, Controller, ActionResult
from browser_use.browser import BrowserSession, BrowserProfile
from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import PromptTemplate
from playwright.async_api import Page
from crewai_tools import BaseTool
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
    """Action之间的状态管理器，解决参数传递问题"""
    def __init__(self):
        self.state = {}
        self.execution_log = []
        self.note_detail_parsed = {}
    
    def set_data(self, key: str, value: Any, description: str = ""):
        """设置状态数据"""
        self.state[key] = value
        self.execution_log.append({
            "action": "set",
            "key": key,
            "description": description,
            "timestamp": asyncio.get_event_loop().time()
        })
    
    def get_data(self, key: str, default=None):
        """获取状态数据"""
        value = self.state.get(key, default)
        logger.info(f"🔍 状态获取: {key} = {type(value)}")
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
            
            # 使用原有XPath作为备用
            try:
                logger.info("🔍 尝试策略1b: 使用原有XPath定位")
                xpath_button = page.locator('//*[@id="content-core-notes"]/div[3]/div[2]/div[2]/div[1]/div[9]')
                if await xpath_button.count() > 0:
                    await xpath_button.click()
                    logger.info("✅ 策略1成功: XPath点击成功")
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
        
        try:
            extraction_llm = ChatOpenAI(
                base_url='https://openrouter.ai/api/v1',
                model='deepseek/deepseek-chat:free',
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

        # 这里需要从外部获取数据，暂时返回空结果
        return ActionResult(extracted_content='{"related_titles": [], "error": "需要外部提供标题列表"}')

    @controller.action('process_all_related_notes', domains=['ad.xiaohongshu.com'])
    async def process_all_related_notes(browser_session: BrowserSession) -> ActionResult:
        """循环处理所有相关标题：打开详情页 -> 提取数据 -> 关闭详情页"""
        logger.info("🔄 开始循环处理所有相关标题的笔记详情")
        
        try:
            page = await browser_session.get_current_page()
            processing_results = []
            
            # 这里需要从外部获取相关标题列表，暂时返回空结果
            result = {
                "success": True,
                "summary": {
                    "total_related_titles": 0,
                    "processed_count": 0,
                    "failed_count": 0,
                    "skipped_count": 0,
                    "total_collected_notes": 0
                },
                "processing_results": processing_results,
                "message": "循环处理完成: 需要外部提供相关标题列表"
            }
            
            return ActionResult(extracted_content=json.dumps(result, ensure_ascii=False))
            
        except Exception as e:
            logger.error(f"❌ 循环处理过程中出错: {str(e)}")
            return ActionResult(extracted_content=f"循环处理失败: {str(e)}")

    logger.info(f"✅ 控制器创建完成")
    return controller

def create_hot_note_finder_agent(promotion_target: str = '国企央企求职辅导小程序') -> Agent:
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

    # 检查认证状态文件
    auth_file = Path('./xiaohongshu_auth.json')
    
    # 创建浏览器会话
    browser_profile = BrowserProfile(
        executable_path=Path('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'),
        user_data_dir=None,
    )

    browser_session = BrowserSession(
        allowed_domains=['https://*.xiaohongshu.com'],
        storage_state='./xiaohongshu_auth.json' if auth_file.exists() else None,
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
6. 点击下一页，使用 click_next_page tool，重复步骤3-6，最多处理10页
7. 最终输出采集结果

**⚠️ 重要约束：**
- 如果某个action连续失败，请立即输出已采集的数据并结束
- 不要无限重试失败的操作，优先保证已采集数据的完整性
- 如果出现技术问题，请立即输出当前已采集的数据

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

class HotNoteFinder(BaseTool):
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
        
        try:
            # 创建状态管理器
            action_state = ActionStateManager()
            
            # 创建代理
            agent = create_hot_note_finder_agent(promotion_target=promotion_target)
            logger.info("✅ 代理创建成功")
            
            # 清理之前的状态
            action_state.clear_data()
            action_state.set_data("promotion_target", promotion_target)
            action_state.set_data("max_pages", max_pages)
            
            try: 
                # 运行任务
                logger.info("🔄 开始执行采集任务...")
                history = await agent.run()
                
                logger.info(f"📊 任务执行完成，状态: {history.is_done()}")
                
                # 模拟从状态管理器获取结果（实际应该从agent执行结果中获取）
                # 这里简化处理，返回示例数据结构
                collected_notes_data = []
                
                # 如果agent执行成功，尝试解析结果
                if history.is_done() and not history.has_errors():
                    final_result = history.final_result()
                    if final_result:
                        try:
                            # 尝试解析agent的结果
                            if isinstance(final_result, str):
                                result_data = json.loads(final_result)
                            else:
                                result_data = final_result
                            
                            if "note_data_list" in result_data:
                                collected_notes_data = result_data["note_data_list"]
                        except Exception as parse_error:
                            logger.warning(f"⚠️ 解析agent结果失败: {parse_error}")
                
                # 转换为NoteData对象列表
                note_list = []
                for note_data in collected_notes_data:
                    try:
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
                        logger.warning(f"⚠️ 跳过无效笔记数据: {e}")
                        continue
                
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