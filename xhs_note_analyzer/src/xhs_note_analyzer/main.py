#!/usr/bin/env python
import asyncio
import json
import logging
from typing import List, Dict, Any
from pathlib import Path
from pydantic import BaseModel

from crewai.flow import Flow, listen, start

# 配置调试日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 导入现有组件
from xhs_note_analyzer.tools.hot_note_finder_tool import find_hot_notes
from xhs_note_analyzer.crews.content_analyzer_crew import create_content_analyzer, ContentAnalysisReport
from xhs_note_analyzer.crews.strategy_maker_crew import create_strategy_maker, StrategyReport
from xhs_note_analyzer.tools.mediacrawler_client import MediaCrawlerClient


class NoteData(BaseModel):
    """笔记基础数据模型"""
    note_id: str = ""    # 笔记ID
    note_title: str
    note_url: str
    impression: int = 0  # 总曝光量
    click: int = 0       # 总阅读量
    like: int = 0        # 总点赞量
    collect: int = 0     # 总收藏量
    comment: int = 0     # 总评论量
    engage: int = 0      # 总互动量


class NoteContentData(BaseModel):
    """笔记详细内容数据模型"""
    note_id: str = ""        # 笔记ID（用于关联）
    title: str = ""          # 笔记标题
    basic_info: NoteData
    content: str = ""        # 笔记文字内容
    images: List[str] = []   # 图片URL列表
    video_url: str = ""      # 视频URL
    author_info: Dict[str, Any] = {}  # 作者信息
    tags: List[str] = []     # 标签列表
    create_time: str = ""    # 创建时间


class ContentAdvice(BaseModel):
    """内容制作建议模型"""
    topic_suggestions: List[str] = []      # 选题建议
    copywriting_advice: List[str] = []     # 文案建议
    creative_ideas: List[str] = []         # 创意建议
    video_script: str = ""                 # 视频脚本
    image_suggestions: List[str] = []      # 配图建议
    target_audience: str = ""              # 目标受众
    content_strategy: str = ""             # 内容策略


class XHSContentAnalysisState(BaseModel):
    """流程状态管理"""
    # 输入参数
    promotion_target: str = "国企央企求职辅导小程序"
    business_context: str = ""
    business_goals: Dict[str, Any] = {}  # 新增：业务目标和约束条件
    
    # 第一步：笔记查找结果
    found_notes: List[NoteData] = []
    notes_search_completed: bool = False
    
    # 第二步：内容获取结果
    detailed_notes: List[NoteContentData] = []
    content_fetch_completed: bool = False
    
    # 第三步：内容分析结果
    content_analysis: List[ContentAdvice] = []
    content_analysis_report: ContentAnalysisReport = None
    analysis_completed: bool = False
    
    # 第四步：策略制定结果
    strategy_report: StrategyReport = None
    strategy_completed: bool = False
    
    # 最终输出
    final_recommendations: Dict[str, Any] = {}


class XHSContentAnalysisFlow(Flow[XHSContentAnalysisState]):
    """小红书内容分析流程
    
    串行执行四个步骤：
    1. 笔记查找 - 使用browser_use agent查找相关优质笔记
    2. 内容获取 - 通过MediaCrawler API获取详细内容
    3. 内容分析 - 使用LLM分析并给出制作建议
    4. 策略制定 - 基于分析结果制定实战策略（选题、TA、创作指导）
    """

    @start()
    def initialize_analysis(self):
        """初始化分析流程"""
        print(f"🚀 开始小红书内容分析流程")
        print(f"📌 推广目标: {self.state.promotion_target}")
        
        # 设置默认业务上下文
        if not self.state.business_context:
            self.state.business_context = f"""
            我们是一家专注于{self.state.promotion_target}的教育服务机构。
            主要提供求职指导、面试培训、简历优化等服务。
            目标用户是准备进入国企央企工作的求职者。
            """
        
        print("✅ 流程初始化完成")

    @listen(initialize_analysis)
    async def step1_find_hot_notes(self):
        """第一步：查找相关优质笔记"""
        print("\n📍 === 第一步：查找相关优质笔记 ===")
        logger.info(f"🔍 DEBUG: 开始Step1，目标：{self.state.promotion_target}")
        
        try:
            # 使用新的find_hot_notes工具函数
            print("🔍 启动find_hot_notes工具查找优质笔记...")
            print(f"🎯 查找目标: {self.state.promotion_target}")
            
            # 调用find_hot_notes函数
            result = await find_hot_notes(
                promotion_target=self.state.promotion_target, 
                max_pages=5,
                output_dir="output"
            )
            
            if result.success and result.data.note_data_list:
                logger.info(f"🔍 DEBUG: find_hot_notes返回成功，笔记数：{len(result.data.note_data_list)}")
                # 转换结果为NoteData对象
                found_notes = []
                for note_data in result.data.note_data_list:
                    # 从URL提取note_id
                    client = MediaCrawlerClient()
                    note_id = client.extract_note_id_from_url(note_data.note_url) or ""
                    
                    note = NoteData(
                        note_id=note_id,
                        note_title=note_data.note_title,
                        note_url=note_data.note_url,
                        impression=note_data.impression,
                        click=note_data.click,
                        like=note_data.like,
                        collect=note_data.collect,
                        comment=note_data.comment,
                        engage=note_data.engage
                    )
                    found_notes.append(note)
                
                self.state.found_notes = found_notes
                self.state.notes_search_completed = True
                
                print(f"✅ find_hot_notes成功找到 {len(self.state.found_notes)} 条相关笔记")
                for i, note in enumerate(self.state.found_notes, 1):
                    print(f"   {i}. {note.note_title} (点赞: {note.like:,}, 收藏: {note.collect:,})")
                
                print(f"📄 {result.message}")
                
            else:
                # 如果工具执行失败，回退到模拟数据
                print(f"⚠️ find_hot_notes执行失败: {result.message}")
                print("🔄 回退到模拟数据...")
                self.state.found_notes = self._mock_find_notes()
                self.state.notes_search_completed = True
                
                print(f"✅ 使用模拟数据，找到 {len(self.state.found_notes)} 条笔记")
                for i, note in enumerate(self.state.found_notes, 1):
                    print(f"   {i}. {note.note_title} (点赞: {note.like:,})")
                
        except Exception as e:
            print(f"❌ 笔记查找失败: {e}")
            print("🔄 回退到模拟数据...")
            # 即使出错也提供模拟数据，确保流程能继续
            self.state.found_notes = self._mock_find_notes()
            self.state.notes_search_completed = True

    @listen(step1_find_hot_notes)
    def step2_fetch_note_content(self):
        """第二步：获取笔记详细内容"""
        print("\n📍 === 第二步：获取笔记详细内容 ===")
        logger.info(f"🔍 DEBUG: 开始Step2，待处理笔记数：{len(self.state.found_notes) if self.state.found_notes else 0}")
        
        if not self.state.notes_search_completed or not self.state.found_notes:
            logger.warning("🔍 DEBUG: Step2跳过，原因：无笔记数据")
            print("⚠️ 跳过内容获取：未找到笔记数据")
            return
        
        try:
            print("🔄 通过MediaCrawler API获取笔记详细内容...")
            print(f"📊 待处理笔记数量: {len(self.state.found_notes)}")
            
            # 创建MediaCrawler客户端并检查服务状态
            client = MediaCrawlerClient()
            
            # 检查API服务器健康状态
            if client.health_check():
                print("✅ MediaCrawler API服务器连接正常")
                
                # 尝试批量获取内容（更高效）
                note_urls = [note.note_url for note in self.state.found_notes]
                print(f"🚀 开始批量获取 {len(note_urls)} 条笔记内容...")
                
                batch_results = client.batch_crawl_notes(note_urls, fetch_comments=False)
                
                # 处理批量结果
                for i, (note, api_result) in enumerate(zip(self.state.found_notes, batch_results)):
                    print(f"📥 处理笔记 {i+1}/{len(self.state.found_notes)}: {note.note_title}")
                    
                    if api_result.get("success", False):
                        # 使用API返回的真实数据
                        detailed_content = self._convert_api_result_to_note_content(note, api_result)
                    else:
                        # API失败，使用模拟数据
                        print(f"  ⚠️ API获取失败，使用模拟数据: {api_result.get('error', 'Unknown error')}")
                        detailed_content = self._create_mock_note_content(note)
                    
                    self.state.detailed_notes.append(detailed_content)
                
            else:
                print("⚠️ MediaCrawler API服务器不可用，使用模拟数据")
                # 服务器不可用，为所有笔记创建模拟数据
                for note in self.state.found_notes:
                    print(f"📥 创建模拟数据: {note.note_title}")
                    detailed_content = self._create_mock_note_content(note)
                    self.state.detailed_notes.append(detailed_content)
            
            self.state.content_fetch_completed = True
            success_count = len([n for n in self.state.detailed_notes if n.content])
            print(f"✅ 内容获取完成: 成功 {success_count}/{len(self.state.detailed_notes)} 条")
            
        except Exception as e:
            print(f"❌ 内容获取失败: {e}")
            # 即使出错也创建模拟数据，确保流程能继续
            print("🔄 创建模拟数据以确保流程继续...")
            for note in self.state.found_notes:
                if not any(d.basic_info.note_url == note.note_url for d in self.state.detailed_notes):
                    detailed_content = self._create_mock_note_content(note)
                    self.state.detailed_notes.append(detailed_content)
            
            self.state.content_fetch_completed = True

    @listen(step2_fetch_note_content)
    def step3_multi_dimensional_analysis(self):
        """第三步：多维度内容分析"""
        print("\n📍 === 第三步：多维度内容分析 ===")
        logger.info(f"🔍 DEBUG: 开始Step3，待分析笔记数：{len(self.state.detailed_notes) if self.state.detailed_notes else 0}")
        
        if not self.state.content_fetch_completed or not self.state.detailed_notes:
            logger.warning("🔍 DEBUG: Step3跳过，原因：无详细内容")
            print("⚠️ 跳过内容分析：未获取到详细内容")
            return
        
        try:
            print("🧠 启动三维度深度内容分析...")
            print(f"📊 待分析笔记数量: {len(self.state.detailed_notes)}")
            
            # 创建内容分析器
            content_analyzer = create_content_analyzer()
            
            # 执行多维度分析
            print("🔍 执行分析维度:")
            print("   1️⃣ 内容结构分析 (标题-开头-正文-结尾)")
            print("   2️⃣ 情感价值分析 (痛点挖掘-价值主张)")  
            print("   3️⃣ 视觉元素分析 (配图风格-排版特点)")
            
            # 批量分析所有笔记
            analysis_report = content_analyzer.analyze_multiple_notes(self.state.detailed_notes)
            
            # 保存分析结果
            self.state.content_analysis_report = analysis_report
            self.state.analysis_completed = True
            
            # 保存到文件
            content_analyzer.save_analysis_results(analysis_report, "output")
            
            # 显示分析摘要
            print(f"✅ 多维度分析完成!")
            print(f"📈 分析结果摘要:")
            print(f"   • 分析笔记数: {analysis_report.total_notes}")
            print(f"   • 平均评分: {analysis_report.average_score:.1f}/100")
            print(f"   • 识别成功公式: {len(analysis_report.success_formulas)}")
            print(f"   • 提取共同模式: {len(analysis_report.common_patterns)}")
            
            # 清空旧的兼容性数据，使用新的报告格式
            self.state.content_analysis = []
            
            # 生成最终建议
            self.state.final_recommendations = self._generate_final_recommendations_from_analysis()
            
        except Exception as e:
            print(f"❌ 多维度分析失败: {e}")
            import traceback
            traceback.print_exc()
            
            # 回退到简单分析
            print("🔄 回退到基础分析模式...")
            self._fallback_basic_analysis()
            self.state.analysis_completed = True

    @listen(step3_multi_dimensional_analysis)
    def step4_strategy_making(self):
        """第四步：实战策略制定"""
        print("\n📍 === 第四步：实战策略制定 ===")
        logger.info(f"🔍 DEBUG: 开始Step4，分析报告状态：{self.state.analysis_completed}")
        
        if not self.state.analysis_completed or not self.state.content_analysis_report:
            logger.warning("🔍 DEBUG: Step4跳过，原因：内容分析未完成")
            print("⚠️ 跳过策略制定：内容分析未完成")
            return
        
        try:
            print("🧠 基于分析结果制定实战策略...")
            print("🎯 策略制定维度:")
            print("   1️⃣ 选题策略 - 热门选题挖掘、关键词集群、竞争分析")
            print("   2️⃣ TA策略 - 用户画像、需求分析、触达策略")  
            print("   3️⃣ 内容创作指导 - 文案指南、配图指南、视频脚本")
            
            # 创建策略制定器
            strategy_maker = create_strategy_maker()
            
            # 执行策略制定
            strategy_report = strategy_maker.make_strategy(
                business_context=self.state.business_context,
                target_product=self.state.promotion_target,
                content_analysis_report=self.state.content_analysis_report,
                business_goals=self.state.business_goals
            )
            
            # 保存策略结果
            self.state.strategy_report = strategy_report
            self.state.strategy_completed = True
            
            # 保存到文件
            strategy_maker.save_strategy_results(strategy_report, "output")
            
            # 显示策略摘要
            print(f"✅ 实战策略制定完成!")
            print(f"📈 策略摘要:")
            print(f"   • 选题建议: {len(strategy_report.topic_strategy.trending_topics)}个")
            print(f"   • 核心建议: {len(strategy_report.key_recommendations)}条")
            print(f"   • 成功要素: {len(strategy_report.success_factors)}个关键要素")
            print(f"   • 差异化要点: {len(strategy_report.differentiation_points)}个")
            
            # 更新最终建议
            self.state.final_recommendations.update({
                "strategy_summary": strategy_report.report_summary,
                "key_strategies": strategy_report.key_recommendations,
                "success_factors": strategy_report.success_factors,
                "differentiation_points": strategy_report.differentiation_points
            })
            
        except Exception as e:
            print(f"❌ 策略制定失败: {e}")
            import traceback
            traceback.print_exc()
            
            # 设置基础策略结果
            self.state.strategy_completed = False
            print("🔄 将使用基础分析结果继续流程...")

    @listen(step4_strategy_making)
    def finalize_and_output(self):
        """输出最终结果"""
        print("\n📍 === 输出最终结果 ===")
        
        if not self.state.analysis_completed:
            print("⚠️ 分析未完成，输出部分结果")
        
        if not self.state.strategy_completed:
            print("⚠️ 策略制定未完成，仅输出分析结果")
        
        # 保存结果到文件
        self._save_analysis_results()
        
        # 显示摘要
        self._display_analysis_summary()
        
        print("🎉 小红书内容分析与策略制定流程完成！")

    def _mock_find_notes(self) -> List[NoteData]:
        """模拟笔记查找结果（占位符函数）"""
        # TODO: 替换为真实的browser_use调用
        return [
            NoteData(
                note_id="676a4d0a000000001f00c58a",
                note_title="考公上岸攻略分享",
                note_url="https://xiaohongshu.com/note/676a4d0a000000001f00c58a",
                impression=50000, click=8000, like=1200, collect=800, comment=150, engage=2150
            ),
            NoteData(
                note_id="676a4d0a000000001f00c58b",
                note_title="国企面试技巧大全",
                note_url="https://xiaohongshu.com/note/676a4d0a000000001f00c58b", 
                impression=30000, click=5000, like=800, collect=500, comment=100, engage=1400
            ),
            NoteData(
                note_id="676a4d0a000000001f00c58c",
                note_title="央企求职简历模板",
                note_url="https://xiaohongshu.com/note/676a4d0a000000001f00c58c",
                impression=40000, click=6500, like=1000, collect=600, comment=120, engage=1720
            )
        ]

    
    def _convert_api_result_to_note_content(self, note: NoteData, api_result: Dict[str, Any]) -> NoteContentData:
        """将API返回结果转换为NoteContentData格式"""
        raw_data = api_result.get("data", {})
        
        # 处理图片URL列表
        images = []
        if raw_data.get("images"):
            images = raw_data["images"] if isinstance(raw_data["images"], list) else [raw_data["images"]]
        
        # 处理作者信息
        author_info = {}
        if raw_data.get("user_name"):
            author_info["name"] = raw_data["user_name"]
        if raw_data.get("user_id"):
            author_info["user_id"] = raw_data["user_id"]
        if raw_data.get("followers_count"):
            author_info["followers"] = raw_data["followers_count"]
        
        # 处理标签
        tags = []
        if raw_data.get("tags"):
            tags = raw_data["tags"] if isinstance(raw_data["tags"], list) else [raw_data["tags"]]
        elif raw_data.get("tag_list"):
            tags = raw_data["tag_list"]
        
        # 更新基础数据统计
        note.like = raw_data.get("liked_count", note.like)
        note.collect = raw_data.get("collected_count", note.collect)
        note.comment = raw_data.get("comments_count", note.comment)
        note.click = raw_data.get("view_count", note.click)
        
        return NoteContentData(
            note_id=note.note_id,
            title=raw_data.get("title", note.note_title),
            basic_info=note,
            content=raw_data.get("desc", raw_data.get("content", f"这是{note.note_title}的详细内容...")),
            images=images,
            video_url=raw_data.get("video_url", ""),
            author_info=author_info,
            tags=tags,
            create_time=raw_data.get("publish_time", raw_data.get("create_time", ""))
        )

    def _create_mock_note_content(self, note: NoteData) -> NoteContentData:
        """创建模拟笔记内容数据"""
        return NoteContentData(
            note_id=note.note_id,
            title=note.note_title,
            basic_info=note,
            content=f"这是{note.note_title}的详细内容，包含求职指导、面试技巧和职场建议等相关信息。",
            images=["https://example.com/image1.jpg", "https://example.com/image2.jpg"],
            author_info={"name": "求职导师", "followers": 10000, "user_id": "mock_user"},
            tags=["求职", "国企", "面试", "职场", "指导"],
            create_time="2024-01-01 12:00:00"
        )


    def _generate_final_recommendations_from_analysis(self) -> Dict[str, Any]:
        """基于多维度分析生成最终建议"""
        if not self.state.content_analysis_report:
            return self._generate_final_recommendations()
        
        report = self.state.content_analysis_report
        
        return {
            "analysis_summary": f"完成对{report.total_notes}篇优质笔记的三维度深度分析",
            "average_score": f"{report.average_score:.1f}/100",
            "success_formulas": report.success_formulas,
            "common_patterns": report.common_patterns,
            "top_recommendations": [
                "复制高分笔记的成功要素",
                "关注共同模式中的关键元素", 
                "重点优化评分较低的维度",
                "建立标准化的内容创作流程"
            ],
            "implementation_plan": {
                "短期目标": "应用识别出的成功公式",
                "中期目标": "建立个人内容创作体系",
                "长期目标": "形成可复制的爆款内容模板"
            }
        }

    def _generate_final_recommendations(self) -> Dict[str, Any]:
        """生成最终综合建议（兼容性函数）"""
        return {
            "summary": f"基于{len(self.state.detailed_notes)}条优质笔记的分析",
            "top_topics": ["热门选题1", "热门选题2", "热门选题3"],
            "content_strategy": "内容策略建议...",
            "implementation_plan": "实施计划..."
        }

    def _fallback_basic_analysis(self):
        """回退基础分析模式"""
        print("📝 执行基础内容分析...")
        
        for detailed_note in self.state.detailed_notes:
            print(f"🔍 基础分析: {detailed_note.basic_info.note_title}")
            
            # 简单的内容分析
            advice = ContentAdvice(
                topic_suggestions=[f"基于{detailed_note.basic_info.note_title}的选题建议"],
                copywriting_advice=["标题优化", "开头改进", "结尾强化"],
                creative_ideas=["视觉优化", "互动设计"],
                content_strategy=f"基础分析 - 点赞数: {detailed_note.basic_info.like}"
            )
            self.state.content_analysis.append(advice)
        
        # 生成基础建议
        self.state.final_recommendations = self._generate_final_recommendations()
        
        print(f"✅ 基础分析完成: {len(self.state.content_analysis)} 条")

    def _save_analysis_results(self):
        """保存分析结果到文件"""
        try:
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)
            
            # 保存完整结果
            result_file = output_dir / "xhs_content_analysis_result.json"
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(self.state.model_dump(), f, ensure_ascii=False, indent=2)
            
            print(f"💾 完整结果已保存: {result_file}")
            
            # 保存可读格式的摘要
            summary_file = output_dir / "analysis_summary.txt"
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write("小红书内容分析报告\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"推广目标: {self.state.promotion_target}\n")
                f.write(f"分析笔记数: {len(self.state.found_notes)}\n")
                f.write(f"详细内容数: {len(self.state.detailed_notes)}\n")
                analysis_count = len(self.state.content_analysis_report.analysis_results) if self.state.content_analysis_report else len(self.state.content_analysis)
                f.write(f"分析建议数: {analysis_count}\n\n")
                
                if self.state.final_recommendations:
                    f.write("综合建议:\n")
                    f.write(json.dumps(self.state.final_recommendations, ensure_ascii=False, indent=2))
            
            print(f"📋 分析摘要已保存: {summary_file}")
            
        except Exception as e:
            print(f"❌ 保存结果失败: {e}")

    def _display_analysis_summary(self):
        """显示分析摘要"""
        print("\n" + "="*70)
        print("📊 完整分析与策略摘要")
        print("="*70)
        print(f"🎯 推广目标: {self.state.promotion_target}")
        print(f"📈 找到笔记: {len(self.state.found_notes)} 条")
        print(f"📄 详细内容: {len(self.state.detailed_notes)} 条")
        analysis_count = len(self.state.content_analysis_report.analysis_results) if self.state.content_analysis_report else len(self.state.content_analysis)
        print(f"💡 分析建议: {analysis_count} 条")
        
        # 内容分析结果
        if self.state.content_analysis_report:
            print(f"📋 分析报告: 平均评分 {self.state.content_analysis_report.average_score:.1f}/100")
        
        # 策略制定结果
        if self.state.strategy_completed and self.state.strategy_report:
            print(f"🚀 策略制定: 已完成")
            print(f"   • 选题建议: {len(self.state.strategy_report.topic_strategy.trending_topics)}个")
            print(f"   • 核心建议: {len(self.state.strategy_report.key_recommendations)}条")
            print(f"   • 成功要素: {len(self.state.strategy_report.success_factors)}个")
        else:
            print(f"🚀 策略制定: 未完成")
        
        # 核心建议展示
        if self.state.final_recommendations:
            print(f"\n🎯 核心建议总结:")
            for key, value in self.state.final_recommendations.items():
                if isinstance(value, list):
                    print(f"   {key}: {len(value)}项建议")
                else:
                    print(f"   {key}: {value}")
        
        print("="*70)


async def kickoff_content_analysis(promotion_target: str = "国企央企求职辅导小程序", 
                                  business_context: str = "",
                                  business_goals: Dict[str, Any] = None):
    """启动内容分析与策略制定流程"""
    print("🚀 启动小红书内容分析与策略制定流程...")
    
    # 创建流程实例
    flow = XHSContentAnalysisFlow()
    
    # 设置初始状态
    flow.state.promotion_target = promotion_target
    if business_context:
        flow.state.business_context = business_context
    if business_goals:
        flow.state.business_goals = business_goals
    
    # 执行流程
    await flow.kickoff()
    
    return flow.state


def plot_content_analysis_flow():
    """绘制流程图"""
    flow = XHSContentAnalysisFlow()
    flow.plot()


if __name__ == "__main__":
    # 执行内容分析与策略制定流程
    business_goals = {
        "target_audience": "25-35岁准备进入国企央企的求职者",
        "content_volume": "每周发布3-5篇内容",
        "conversion_goal": "小程序注册用户数提升50%",
        "time_frame": "3个月内完成策略实施",
        "budget_constraint": "中等预算，注重ROI"
    }
    
    result = asyncio.run(kickoff_content_analysis(
        promotion_target="国企央企求职辅导小程序",
        business_context="专注于国企央企求职培训的教育机构",
        business_goals=business_goals
    ))
    
    print("\n🎉 流程执行完成！")
