import asyncio
import json
import os
import logging
import pyperclip
from pathlib import Path
from typing import List, Dict, Any
from pydantic import BaseModel
from browser_use import Agent, Controller, ActionResult
from browser_use.browser import BrowserSession, BrowserProfile
from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import PromptTemplate
from playwright.async_api import Page
import re

# 配置详细日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('controller_action_debug.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class NoteData(BaseModel):
    note_title: str
    note_url: str
    impression: int  # 总曝光量
    click: int       # 总阅读量
    like: int        # 总点赞量
    collect: int     # 总收藏量
    comment: int     # 总评论量
    engage: int      # 总互动量


class NoteDataList(BaseModel):
    note_data_list: List[NoteData]

# 添加状态管理类
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
        #logger.info(f"🗄️ 状态设置: {key} = {value} ({description})")
    
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

# 创建全局状态管理器
action_state = ActionStateManager()

def create_precision_controller() -> Controller:
    """创建精确控制器，包含自定义action"""
    controller = Controller()
    logger.info("🎯 开始注册精确控制器的自定义action")
    
    @controller.action('navigate and login xiaohongshu ad platform', domains=['ad.xiaohongshu.com'])
    async def navigate_and_login_xiaohongshu_ad_platform(xhs_ad_email: str, xhs_ad_password: str, browser_session: BrowserSession) -> ActionResult:
        """导航到小红书广告平台并检测登录状态，必要时进行登录"""
        logger.info("🎯 开始导航到小红书广告平台并检测登录状态")
        logger.info(f"🎯 邮箱: {xhs_ad_email}, 密码: {xhs_ad_password}")
        
        try:
            page = await browser_session.get_current_page()
            
            # 步骤1: 导航到小红书广告平台 (使用原代码的导航逻辑)
            logger.info("📍 正在导航到小红书广告平台...")
            await page.goto("https://ad.xiaohongshu.com/")
            await page.wait_for_load_state('networkidle')
            logger.info("✅ 成功导航到小红书广告平台")
            
            # 步骤2: 检测登录状态 (使用原代码中的登录相关元素作为检测依据)
            logger.info("🔍 检测当前登录状态...")
            
            # 检查是否存在"账号登录"按钮，如果存在说明未登录
            login_button_exists = await page.locator("div").filter(has_text=re.compile(r"^账号登录$")).count() > 0
            
            if not login_button_exists:
                # 如果没有"账号登录"按钮，说明已经登录
                logger.info("✅ 检测到已登录状态（通过cookies），跳过登录步骤")
                return ActionResult(extracted_content="Already logged in to XiaoHongShu Ad Platform via cookies")
            
            # 步骤3: 执行登录流程 (完全使用原代码的登录逻辑)
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
            
            # ⭐ 关键改进：将结果保存到状态管理器
            current_page = action_state.get_data('current_page', 1)
            action_state.set_data("all_titles", titles, f"第{current_page}页的所有笔记标题")
            action_state.set_data("titles_count", len(titles), "当前页标题数量")
            
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
            current_page = action_state.get_data("current_page", 1)
            next_page = current_page + 1
            logger.info(f"🔍 DEBUG: 准备从第{current_page}页跳转到第{next_page}页")
            
            
            # 策略1: 使用原有XPath作为备用
            try:
                logger.info("🔍 尝试策略1b: 使用原有XPath定位")
                xpath_button = page.locator('//*[@id="content-core-notes"]/div[3]/div[2]/div[2]/div[1]/div[9]')
                if await xpath_button.count() > 0:
                    await xpath_button.click()
                    logger.info("✅ 策略1成功: XPath点击成功")
                    
                    # 更新页码状态
                    action_state.set_data("current_page", next_page, f"已跳转到第{next_page}页")
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
        
        # ⭐ 关键改进：从状态管理器获取标题列表，确保数据流正确
        title_list = action_state.get_data("all_titles", [])
        logger.info(f"🔍 DEBUG: 从状态管理器获取标题列表，类型: {type(title_list)}, 长度: {len(title_list) if title_list else 'None'}")
        
        if not title_list:
            logger.warning("⚠️ 未找到标题列表，可能需要先执行 get_core_note_titles")
            return ActionResult(extracted_content='{"related_titles": [], "error": "未找到标题数据"}')
        
        promotion_target = action_state.get_data("promotion_target", "")
        logger.info(f"🔍 DEBUG: 从状态管理器获取推广标的: {promotion_target}")
        
        if not promotion_target:
            logger.warning("⚠️ 未找到推广标的，可能需要先执行 set_promotion_target")
            return ActionResult(extracted_content='{"related_titles": [], "error": "未找到推广标的"}')
        
        logger.info(f"🎯 提取相关标题, 推广标的: {promotion_target}, 标题列表长度: {len(title_list)}")
        logger.info(f"🔍 DEBUG: 标题列表内容: {title_list[:5] if len(title_list) > 5 else title_list}")  # 只显示前5个
      
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
                    action_state.set_data("related_titles", related_titles, f"与{promotion_target}相关的标题")
                    action_state.set_data("related_count", len(related_titles), "相关标题数量")
                    action_state.set_data("processed_note_index", 0, "当前处理的笔记索引")
                    
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
            related_titles = action_state.get_data("related_titles", [])
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
                    is_parsed = action_state.get_note_detail_parsed(note_title, False)
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
                    collected_notes = action_state.get_data("collected_notes", [])
                    collected_notes.append(note_data)
                    action_state.set_data("collected_notes", collected_notes, f"已采集{len(collected_notes)}条笔记数据")
                    action_state.set_note_detail_parsed(note_title, True)
                    
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
            total_collected = len(action_state.get_data("collected_notes", []))
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
        
        status = {
            "execution_summary": action_state.get_execution_summary(),
            "data_summary": {
                "all_titles_count": len(action_state.get_data("all_titles", [])),
                "related_titles_count": action_state.get_data("related_count", 0),
                "processed_index": action_state.get_data("processed_note_index", 0),
                "collected_notes_count": len(action_state.get_data("collected_notes", [])),
                "current_page": action_state.get_data("current_page", 1),
                "parsed_notes_count": len(action_state.note_detail_parsed)
            },
            "current_state": dict(action_state.state)
        }
        
        logger.info(f"📊 当前进度: {status['data_summary']}")
        return ActionResult(extracted_content=json.dumps(status, ensure_ascii=False))

    # 验证所有action是否成功注册
    logger.info("🔍 验证已注册的action:")
    expected_actions = [
        'navigate and login xiaohongshu ad platform',
        'navigate to content inspiration page', 
        'get_core_note_titles',
        'extract_related_titles',  # 确保这个action名称正确
        'process_all_related_notes',
        'open note detail card',
        'close note detail card',
        'click next page', 
        'extract note data from modal',
        'get_collection_status'
    ]
    

    actions_keys = controller.registry.registry.actions.keys()
    actions_values = controller.registry.registry.actions.values()
    for action_key, action_value in zip(actions_keys, actions_values):
        logger.info(f"已注册的 action_key: {action_key}")
        logger.info(f"已注册的 action_value: {action_value}")


    # 检查controller的action注册情况
    logger.info(f"✅ 控制器创建完成，共注册 {len(actions_keys)} 个action")
    return controller



def create_hot_note_finder_agent(promotion_target = '国企央企求职辅导小程序') -> Agent:
    """创建使用Controller Action的代理"""
    
    # 配置LLM
    llm = ChatOpenAI(
        base_url='https://openrouter.ai/api/v1',
        #model='anthropic/claude-3.5-sonnet',  # Claude对工具调用识别很准确
        #model='qwen/qwen2.5-vl-72b-instruct',
        #model='google/gemini-2.5-flash',
        model='google/gemini-2.5-flash-lite-preview-06-17',
        api_key=os.environ['OPENROUTER_API_KEY'],
        temperature=0.1
    )

    planner_llm = ChatOpenAI(
        base_url='https://openrouter.ai/api/v1',
        #model='google/gemini-2.5-flash',
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
6. 使用 get_collection_status tool 查看当前采集进度和状态
7. 点击下一页，使用 click_next_page tool，重复步骤3-6，最多处理10页
8. 最终使用 get_collection_status tool 获取完整的采集结果

**⚠️ 重要约束：**
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
    
    # ⭐ 添加官方调试功能
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
        # ⭐ 官方调试选项
        save_conversation_path=str(debug_dir / "conversation"),  # 保存完整对话历史
        generate_gif=str(debug_dir / "debug_execution.gif"),  # 生成执行过程GIF
    )

    return agent


async def save_results_to_file(note_data_list: List[NoteData], filename: str = "xiaohongshu_notes_controller_action.json"):
    """保存结果到文件"""
    try:
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        output_file = output_dir / filename
        data = {
            "collection_time": asyncio.get_event_loop().time(),
            "total_notes": len(note_data_list),
            "method": "controller_action_precision",
            "notes": [note.model_dump() for note in note_data_list]
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Controller Action版数据已保存到: {output_file}")
        
        # 保存易读格式
        txt_file = output_dir / filename.replace('.json', '.txt')
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(f"小红书优质笔记采集结果（Controller Action精确版）\n")
            f.write(f"采集方法: browser_use + @controller.action精确控制\n")
            f.write(f"总计笔记数: {len(note_data_list)}\n")
            f.write("=" * 80 + "\n\n")
            
            for i, note in enumerate(note_data_list, 1):
                f.write(f"笔记 {i}:\n")
                f.write(f"标题: {note.note_title}\n")
                f.write(f"链接: {note.note_url}\n")
                f.write(f"曝光量: {note.impression:,}\n")
                f.write(f"阅读量: {note.click:,}\n")
                f.write(f"点赞量: {note.like:,}\n")
                f.write(f"收藏量: {note.collect:,}\n")
                f.write(f"评论量: {note.comment:,}\n")
                f.write(f"互动量: {note.engage:,}\n")
                f.write("-" * 60 + "\n\n")
        
        print(f"✅ 易读格式已保存到: {txt_file}")
        
    except Exception as e:
        print(f"❌ 保存文件时出错: {e}")


async def main():
    """主函数 - 使用状态管理器保存中间结果"""
    print("🚀 开始启动Controller Action精确控制笔记采集...")
    print("🎯 方案: browser_use + @controller.action + ActionStateManager状态管理 + 官方调试功能")
    
    try:
        promotion_target = '国企央企求职辅导小程序'

        # 创建代理
        agent = create_hot_note_finder_agent(promotion_target=promotion_target)
        print("✅ Controller Action代理创建成功")
        
        # 清理之前的状态
        action_state.clear_data()
        print("🗑️ 清理之前的状态数据")

        # 设置推广目标
        action_state.set_data("promotion_target", promotion_target)
        
        try:
            # 运行任务
            print("🔄 开始执行Controller Action精确采集任务...")
            history = await agent.run()
            
            # ⭐ 官方调试信息分析
            print("\n🔍 ===== 官方AgentHistory调试信息 =====")
            print(f"📊 任务是否完成: {history.is_done()}")
            print(f"❌ 是否有错误: {history.has_errors()}")
            print(f"📈 总执行步数: {len(history.model_actions())}")
            print(f"🌐 访问的URL数量: {len(history.urls())}")
            print(f"📸 截图数量: {len(history.screenshots())}")
            
            # 显示访问的URL
            urls = history.urls()
            if urls:
                print(f"\n🌐 访问的URL列表:")
                for i, url in enumerate(urls, 1):
                    print(f"  {i}. {url}")
            
            # 显示执行的action
            actions = history.action_names()
            if actions:
                print(f"\n🔧 执行的Action列表:")
                for i, action in enumerate(actions, 1):
                    print(f"  {i}. {action}")
            
            # 显示错误信息
            errors = history.errors()
            if errors:
                print(f"\n❌ 错误列表:")
                for i, error in enumerate(errors, 1):
                    print(f"  {i}. {error}")
            
            # 显示Agent的推理过程
            thoughts = history.model_thoughts()
            if thoughts:
                print(f"\n🧠 Agent推理过程 (最后3条):")
                for i, thought in enumerate(thoughts[-3:], 1):
                    print(f"  {i}. {thought[:200]}...")  # 只显示前200字符
            
            # 获取最终结果
            final_result = history.final_result()
            print(f"\n📋 Agent最终结果类型: {type(final_result)}")
            if final_result:
                print(f"📋 Agent最终结果长度: {len(str(final_result))}")
            
            # 保存完整的调试信息
            await save_agent_history_debug(history)
            
            print(f"\n📊 Agent任务执行完成")
            
        except Exception as e:
            print(f"⚠️ Agent执行中断: {e}")
            print("🔄 继续尝试从状态管理器获取中间结果...")
        
        # ⭐ 关键改进：优先从状态管理器获取结果
        print("\n🔍 从状态管理器获取采集结果...")
        collected_notes_data = action_state.get_data("collected_notes", [])
        
        if collected_notes_data:
            print(f"✅ 从状态管理器成功获取到 {len(collected_notes_data)} 条笔记数据")
            
            # 转换为NoteData对象列表
            note_list = []
            for note_data in collected_notes_data:
                try:
                    note = NoteData(
                        note_title=note_data.get("note_title", ""),
                        note_url=note_data.get("note_url", ""),
                        impression=note_data.get("impression", 0),
                        click=note_data.get("click", 0),
                        like=note_data.get("like", 0),
                        collect=note_data.get("collect", 0),
                        comment=note_data.get("comment", 0),
                        engage=note_data.get("engage", 0)
                    )
                    note_list.append(note)
                except Exception as e:
                    print(f"⚠️ 跳过无效笔记数据: {e}")
                    continue
            
            if note_list:
                # 显示结果摘要
                print(f"\n📈 采集结果摘要 (来源: ActionStateManager):")
                print("=" * 80)
                
                for i, note in enumerate(note_list, 1):
                    print(f"{i}. {note.note_title}")
                    print(f"   曝光: {note.impression:,} | 阅读: {note.click:,} | 点赞: {note.like:,}")
                    print(f"   收藏: {note.collect:,} | 评论: {note.comment:,} | 互动: {note.engage:,}")
                    print(f"   链接: {note.note_url}")
                    print("-" * 60)
                
                # 保存状态管理器中的结果
                await save_results_to_file(note_list, "xiaohongshu_notes_state_manager.json")
                
                # 显示状态管理器的统计信息
                print(f"\n📊 状态管理器统计:")
                print(f"   - 总标题数: {len(action_state.get_data('all_titles', []))}")
                print(f"   - 相关标题数: {action_state.get_data('related_count', 0)}")
                print(f"   - 已采集笔记数: {len(collected_notes_data)}")
                print(f"   - 已解析笔记数: {len(action_state.note_detail_parsed)}")
                print(f"   - 执行步骤数: {len(action_state.execution_log)}")
                
            else:
                print("⚠️ 状态管理器中的笔记数据格式异常")
        
        else:
            print("⚠️ 状态管理器中未找到采集数据")
            
            # 如果状态管理器没有数据，尝试解析agent结果
            if 'history' in locals() and history:
                print("🔄 尝试解析AgentHistory的原始结果...")
                try:
                    final_result = history.final_result()
                    if final_result:
                        # 如果结果是字符串，尝试解析为JSON
                        if isinstance(final_result, str):
                            parsed_data = NoteDataList.model_validate_json(final_result)
                        else:
                            # 如果是字典类型，直接解析
                            parsed_data = NoteDataList.model_validate(final_result)
                        
                        note_list = parsed_data.note_data_list
                        
                        if note_list:
                            print(f"✅ 从AgentHistory结果成功解析到 {len(note_list)} 条笔记数据")
                            await save_results_to_file(note_list, "xiaohongshu_notes_agent_result.json")
                        else:
                            print("⚠️ AgentHistory结果中未找到笔记数据")
                            
                except Exception as e:
                    print(f"❌ 解析AgentHistory结果时出错: {e}")
                    print(f"原始结果: {final_result}")
            else:
                print("❌ 没有可用的采集结果")
        
        # 保存状态管理器的完整状态（用于调试）
        await save_state_manager_debug_info()
                    
    except Exception as e:
        print(f"❌ 主函数执行过程中出错: {e}")
        import traceback
        traceback.print_exc()
        
        # 即使出错，也尝试保存状态管理器中的数据
        print("\n🚨 尝试保存状态管理器中的紧急备份数据...")
        try:
            emergency_notes = action_state.get_data("collected_notes", [])
            if emergency_notes:
                await save_emergency_backup(emergency_notes)
                print(f"✅ 紧急备份已保存: {len(emergency_notes)} 条笔记")
            else:
                print("⚠️ 状态管理器中无数据可备份")
        except Exception as backup_error:
            print(f"❌ 紧急备份失败: {backup_error}")


async def save_state_manager_debug_info():
    """保存状态管理器的调试信息"""
    try:
        debug_info = {
            "state_data": dict(action_state.state),
            "execution_log": action_state.execution_log,
            "note_detail_parsed": dict(action_state.note_detail_parsed),
            "execution_summary": action_state.get_execution_summary()
        }
        
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        debug_file = output_dir / "state_manager_debug.json"
        
        with open(debug_file, 'w', encoding='utf-8') as f:
            json.dump(debug_info, f, ensure_ascii=False, indent=2)
        
        print(f"🐛 状态管理器调试信息已保存: {debug_file}")
        
    except Exception as e:
        print(f"❌ 保存调试信息失败: {e}")


async def save_emergency_backup(notes_data):
    """保存紧急备份数据"""
    try:
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        backup_file = output_dir / "emergency_backup.json"
        backup_data = {
            "backup_time": asyncio.get_event_loop().time(),
            "total_notes": len(notes_data),
            "notes": notes_data,
            "source": "ActionStateManager_emergency_backup"
        }
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        
        print(f"🚨 紧急备份已保存: {backup_file}")
        
    except Exception as e:
        print(f"❌ 紧急备份保存失败: {e}")


async def save_agent_history_debug(history) -> None:
    """保存AgentHistory的详细调试信息"""
    try:
        debug_info = {
            "execution_summary": {
                "is_done": history.is_done(),
                "has_errors": history.has_errors(),
                "total_steps": len(history.model_actions()),
                "urls_count": len(history.urls()),
                "screenshots_count": len(history.screenshots()),
            },
            "urls": history.urls(),
            "action_names": history.action_names(),
            "errors": history.errors(),
            "model_thoughts": history.model_thoughts(),
            "final_result": history.final_result(),
            "extracted_content": history.extracted_content(),
            "action_results": [str(result) for result in history.action_results()],  # 转换为字符串避免序列化问题
        }
        
        output_dir = Path("output/debug")
        output_dir.mkdir(parents=True, exist_ok=True)
        debug_file = output_dir / "agent_history_debug.json"
        
        with open(debug_file, 'w', encoding='utf-8') as f:
            json.dump(debug_info, f, ensure_ascii=False, indent=2)
        
        print(f"🐛 AgentHistory调试信息已保存: {debug_file}")
        
    except Exception as e:
        print(f"❌ 保存AgentHistory调试信息失败: {e}")


if __name__ == "__main__":
    asyncio.run(main()) 