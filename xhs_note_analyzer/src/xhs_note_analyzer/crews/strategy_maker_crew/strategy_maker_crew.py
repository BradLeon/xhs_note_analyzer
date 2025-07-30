#!/usr/bin/env python

"""
Strategy Maker Crew
小红书实战策略制定Crew - Step4实现

负责基于内容分析结果制定实战策略：
1. 选题策略制定 - 热门选题挖掘、关键词策略、竞争分析
2. TA策略分析 - 用户画像、需求分析、触达策略
3. 内容创作指导 - 文案指南、配图指南、视频脚本
4. 策略整合协调 - 实施计划、风险管控、成效评估
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from crewai import Agent, Crew, Task, Process
from crewai.project import CrewBase, agent, crew, task
from langchain_openai import ChatOpenAI

from .models import (
    RecommendedTopic,
    TopicStrategy,
    TargetAudienceStrategy,
    ContentCreationGuide,
    CompleteCopywriting,
    VideoScript,
    ImageDescription,
    TopicContentPackage,
    OverallExecutionTips,
    StrategyReport
)

# 从公共模型导入
from xhs_note_analyzer.models import ContentAnalysisReport

logger = logging.getLogger(__name__)

@CrewBase
class StrategyMakerCrew():
    """实战策略制定Crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    def __init__(self):
        self.llm = ChatOpenAI(
        base_url='https://openrouter.ai/api/v1',
        model='openrouter/google/gemini-2.5-pro',
        api_key=os.environ['OPENROUTER_API_KEY'],
        temperature=0.1
        )


    @agent
    def topic_strategy_expert(self) -> Agent:
        """选题策略专家"""
        return Agent(
            config=self.agents_config['topic_strategy_expert'],
            llm=self.llm,
            verbose=True
        )

    @agent 
    def target_audience_analyst(self) -> Agent:
        """目标用户分析师"""
        return Agent(
            config=self.agents_config['target_audience_analyst'],
            llm=self.llm,
            verbose=True
        )

    @agent
    def content_creation_guide(self) -> Agent:
        """内容创作指导师"""
        return Agent(
            config=self.agents_config['content_creation_guide'],
            llm=self.llm,
            verbose=True
        )



    @task
    def analyze_target_audience_task(self) -> Task:
        """分析目标用户任务 - 第一步"""
        return Task(
            config=self.tasks_config['analyze_target_audience'],
            agent=self.target_audience_analyst(),
            output_pydantic=TargetAudienceStrategy
        )

    @task
    def develop_topic_strategy_task(self) -> Task:
        """制定选题策略任务 - 第二步，基于TA分析"""
        return Task(
            config=self.tasks_config['develop_topic_strategy'],
            agent=self.topic_strategy_expert(),
            context=[self.analyze_target_audience_task()],
            output_pydantic=TopicStrategy
        )

    @task
    def create_content_creation_guide_task(self) -> Task:
        """制定内容创作指导任务 - 第三步，基于TA分析和选题策略"""
        return Task(
            config=self.tasks_config['create_content_creation_guide'],
            agent=self.content_creation_guide(),
            context=[
                self.analyze_target_audience_task(),
                self.develop_topic_strategy_task()
            ],
            output_pydantic=ContentCreationGuide
        )



    @crew
    def crew(self) -> Crew:
        """创建策略制定Crew"""
        return Crew(
            agents=[
                self.target_audience_analyst(),
                self.topic_strategy_expert(),
                self.content_creation_guide()
            ],
            tasks=[
                self.analyze_target_audience_task(),
                self.develop_topic_strategy_task(),
                self.create_content_creation_guide_task()
            ],
            process=Process.sequential,
            verbose=True
        )

    def make_strategy(self, 
                     business_context: str,
                     target_product: str,
                     content_analysis_report: 'ContentAnalysisReport',
                     business_goals: Optional[Dict[str, Any]] = None) -> StrategyReport:
        """
        制定完整的实战策略
        
        Args:
            business_context: 业务背景描述
            target_product: 目标产品/服务
            content_analysis_report: Step3的内容分析报告
            business_goals: 业务目标和约束条件
            
        Returns:
            StrategyReport: 完整的实战策略报告
        """
        try:
            logger.info(f"🚀 开始制定实战策略: {target_product}")
            
            # 准备策略制定输入数据
            strategy_input = self._prepare_strategy_input(
                business_context, 
                target_product, 
                content_analysis_report,
                business_goals
            )
            
            # 执行策略制定 - 现在是三个独立任务
            crew_results = self.crew().kickoff(inputs=strategy_input)
            
            # 解析并整合三个任务的结果
            strategy_report = self._integrate_strategy_results(crew_results, strategy_input)
            
            logger.info(f"✅ 实战策略制定完成: {target_product}")
            return strategy_report
            
        except Exception as e:
            logger.error(f"❌ 策略制定失败: {target_product}, 错误: {e}")
            # 返回基础策略结果
            return self._create_fallback_strategy(business_context, target_product)

    def _prepare_strategy_input(self, 
                               business_context: str,
                               target_product: str,
                               content_analysis_report: 'ContentAnalysisReport',
                               business_goals: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """准备策略制定的输入数据"""
        
        # 构建策略输入
        strategy_input = {
            "business_context": business_context,
            "target_product": target_product,
            "business_goals": business_goals,
            "analysis_report": content_analysis_report.model_dump() if content_analysis_report else {},
            "success_factors": content_analysis_report.success_formulas if content_analysis_report else [],
        }
        
        return strategy_input


    def _integrate_strategy_results(self, crew_results, strategy_input: Dict[str, Any]) -> StrategyReport:
        """直接汇总三个任务的结果为结构化策略报告"""
        try:
            logger.info("🔄 开始汇总三个任务结果")
            
            # 从crew_results中提取三个任务的输出
            if hasattr(crew_results, 'tasks_output') and crew_results.tasks_output:
                # 按顺序获取三个任务的结果
                task_outputs = crew_results.tasks_output
                logger.info(f"📋 获取到 {len(task_outputs)} 个任务输出")
                
                # 初始化任务结果
                target_audience_result = None
                topic_strategy_result = None
                content_creation_result = None
                
                # 解析各任务结果
                for i, task_output in enumerate(task_outputs):
                    if hasattr(task_output, 'pydantic') and task_output.pydantic:
                        if i == 0:  # analyze_target_audience_task
                            target_audience_result = task_output.pydantic
                            logger.info("✅ 获取到用户分析结果")
                        elif i == 1:  # develop_topic_strategy_task
                            topic_strategy_result = task_output.pydantic
                            logger.info("✅ 获取到选题策略结果")
                        elif i == 2:  # create_content_creation_guide_task
                            content_creation_result = task_output.pydantic
                            logger.info("✅ 获取到内容创作结果")
                
                # 如果某些结果为空，使用默认值
                if not target_audience_result:
                    target_audience_result = TargetAudienceStrategy(**self._create_basic_ta_strategy(strategy_input))
                    logger.warning("⚠️ 用户分析结果为空，使用默认值")
                    
                if not topic_strategy_result:
                    topic_strategy_result = TopicStrategy(**self._create_basic_topic_strategy(strategy_input))
                    logger.warning("⚠️ 选题策略结果为空，使用默认值")
                    
                if not content_creation_result:
                    content_creation_result = ContentCreationGuide(**self._create_basic_content_guide(strategy_input))
                    logger.warning("⚠️ 内容创作结果为空，使用默认值")
                
            else:
                # 如果无法获取任务输出，使用默认值
                logger.warning("⚠️ 无法获取任务输出，使用默认策略")
                target_audience_result = TargetAudienceStrategy(**self._create_basic_ta_strategy(strategy_input))
                topic_strategy_result = TopicStrategy(**self._create_basic_topic_strategy(strategy_input))
                content_creation_result = ContentCreationGuide(**self._create_basic_content_guide(strategy_input))
            
            # 生成综合建议
            key_recommendations = self._generate_key_recommendations(
                topic_strategy_result, target_audience_result, content_creation_result
            )
            
            # 创建结构化策略报告
            strategy_report = StrategyReport(
                business_context=strategy_input["business_context"],
                target_product=strategy_input["target_product"],
                analysis_base=f"基于内容分析报告的三维度策略制定",
                topic_strategy=topic_strategy_result,
                target_audience_strategy=target_audience_result,
                content_creation_guide=content_creation_result,
                key_recommendations=key_recommendations,
                success_factors=strategy_input.get("success_factors", []),
                differentiation_points=self._extract_differentiation_points(
                    topic_strategy_result, target_audience_result, content_creation_result
                ),
                generation_timestamp=datetime.now().isoformat(),
                report_summary=f"针对{strategy_input['target_product']}的完整策略制定：用户分析+选题策略+创作指导"
            )
            
            logger.info("✅ 策略结果汇总完成")
            return strategy_report
            
        except Exception as e:
            logger.error(f"❌ 汇总策略结果失败: {e}")
            logger.error(f"错误详情: {str(e)}")
            import traceback
            logger.error(f"堆栈跟踪: {traceback.format_exc()}")
            return self._create_fallback_strategy(
                strategy_input["business_context"], 
                strategy_input["target_product"]
            )

    def _extract_differentiation_points(self, topic_strategy: TopicStrategy, 
                                      target_audience_strategy: TargetAudienceStrategy,
                                      content_creation_guide: ContentCreationGuide) -> List[str]:
        """从三个策略组件中提取差异化要点"""
        differentiation_points = []
        
        # 从选题策略中提取差异化点
        if hasattr(topic_strategy, 'recommended_topics') and topic_strategy.recommended_topics:
            differentiation_points.append(f"聚焦{len(topic_strategy.recommended_topics)}个精选选题方向")
        
        # 从用户策略中提取差异化点
        if hasattr(target_audience_strategy, 'core_needs') and target_audience_strategy.core_needs:
            differentiation_points.append(f"针对用户{len(target_audience_strategy.core_needs)}大核心需求")
            
        # 从创作指导中提取差异化点
        if hasattr(content_creation_guide, 'topic_content_packages') and content_creation_guide.topic_content_packages:
            differentiation_points.append(f"提供{len(content_creation_guide.topic_content_packages)}个完整的创作素材包")
            
        # 默认差异化要点
        if not differentiation_points:
            differentiation_points = [
                "基于数据分析的精准策略制定",
                "完整的创作执行指导",
                "结构化的用户需求匹配"
            ]
            
        return differentiation_points

    def _parse_text_results(self, text_results: str) -> Dict[str, Any]:
        """从文本结果中解析策略信息"""
        # 简单的文本解析，提取关键信息
        logger.info(f"解析文本结果: {text_results[:100]}...")
        return {
            "topic_strategy": {},
            "target_audience_strategy": {},
            "content_creation_guide": {}
        }

    def _create_basic_topic_strategy(self, strategy_input: Dict[str, Any]) -> Dict[str, Any]:
        """创建基础选题策略"""
        business_context = strategy_input.get("business_context", "")
        target_product = strategy_input.get("target_product", "")
        
        return {
            "business_domain": business_context,
            "target_product": target_product,
            "recommended_topics": [
                {
                    "title": "基础选题示例1",
                    "rationale": f"基于{target_product}的实用价值",
                    "target_audience": "目标用户群体",
                    "expected_engagement": "预期高互动",
                    "execution_difficulty": "中等",
                    "priority_score": 8
                }
            ],
            "topic_formulas": ["数字型标题", "疑问型标题", "对比型标题"],
            "keyword_clusters": {"核心关键词": ["关键词1", "关键词2"]},
            "competition_analysis": {"竞争态势": "分析要点"}
        }

    def _create_basic_ta_strategy(self, strategy_input: Dict[str, Any]) -> Dict[str, Any]:
        """创建基础TA策略"""
        target_product = strategy_input.get("target_product", "")
        
        return {
            "primary_persona": {"name": "目标用户", "age": "25-35", "interests": ["职场发展"]},
            "secondary_personas": [],
            "demographics": {"年龄段": "25-35", "职业": "白领"},
            "psychographics": {"价值观": ["效率", "成长"]},
            "behavioral_patterns": ["移动端使用", "社交分享"],
            "core_needs": ["效率提升", "技能学习", "职业发展"],
            "pain_points": [f"{target_product}相关痛点", "时间管理困难"],
            "motivations": ["自我提升", "职业发展"],
            "content_preferences": {"内容类型": "实用教程"},
            "engagement_triggers": ["实用价值", "共鸣感"],
            "conversion_points": ["内容互动", "私信咨询"]
        }

    def _create_basic_content_guide(self, strategy_input: Dict[str, Any]) -> Dict[str, Any]:
        """创建基础内容创作指南 - 返回匹配新ContentCreationGuide模型的数据"""
        target_product = strategy_input.get("target_product", "")
        business_context = strategy_input.get("business_context", "")
        
        return {
            "topic_content_packages": [
                {
                    "topic_title": f"{target_product}基础选题示例",
                    "business_value": f"基于{business_context}的实用价值导向，提升用户对{target_product}的认知和转化",
                    "target_pain_point": "用户缺乏相关知识和解决方案",
                    "complete_copywriting": {
                        "complete_title": f"新手必看！{target_product}完整攻略",
                        "full_content": f"你是否还在为{target_product}相关问题而困扰？\n\n今天给大家分享一个完整的解决方案...\n\n[具体步骤和方法]\n\n最后总结：掌握这些技巧，你也能...\n\n💡 关注我，了解更多{target_product}相关内容",
                        "content_length": 200,
                        "posting_time_suggestion": "晚上8-10点",
                        "content_type": "图文笔记"
                    },
                    "video_script": None,  # 图文笔记不需要视频脚本
                    "image_descriptions": [
                        {
                            "image_purpose": "首图",
                            "composition_details": "清晰的标题文字 + 产品/场景展示",
                            "character_appearance": "年轻专业人士，简洁着装",
                            "environment_setting": "简洁明亮的背景，突出主题",
                            "lighting_and_tone": "自然光，清新明亮的色调",
                            "ai_prompt_ready": "clean background, professional person, bright lighting, minimalist design"
                        },
                        {
                            "image_purpose": "内容图",
                            "composition_details": "步骤说明 + 示例展示",
                            "character_appearance": "与首图保持一致",
                            "environment_setting": "实际操作场景",
                            "lighting_and_tone": "自然光，专业感",
                            "ai_prompt_ready": "step-by-step guide, clean layout, professional presentation"
                        },
                        {
                            "image_purpose": "产品图",
                            "composition_details": "产品特写 + 使用效果展示",
                            "character_appearance": "手部特写或使用场景",
                            "environment_setting": "简洁背景，突出产品",
                            "lighting_and_tone": "柔和光线，突出质感",
                            "ai_prompt_ready": "product showcase, soft lighting, clean background, high quality"
                        }
                    ]
                }
            ],
            "overall_execution_tips": {
                "content_quality_standards": ["标题吸引力强", "内容有实用价值", "视觉美观度高", "互动引导清晰"],
                "platform_best_practices": ["使用相关话题标签", "发布时间选择用户活跃期", "积极回复评论互动"],
                "engagement_optimization": ["设置互动问题", "引导用户分享经验", "及时回复评论建立连接"]
            }
        }

    def _generate_key_recommendations(self, topic_strategy: TopicStrategy, 
                                    target_audience_strategy: TargetAudienceStrategy,
                                    content_creation_guide: ContentCreationGuide) -> List[str]:
        """基于三个策略组件生成综合建议"""
        recommendations = []
        
        # 基于选题策略的建议
        if topic_strategy.recommended_topics:
            recommendations.append(f"重点关注{len(topic_strategy.recommended_topics)}个精选选题方向")
        
        # 基于TA策略的建议  
        if target_audience_strategy.core_needs:
            recommendations.append(f"聚焦用户{len(target_audience_strategy.core_needs)}大核心需求")
            
        # 基于创作指南的建议
        if content_creation_guide.topic_content_packages:
            recommendations.append(f"提供{len(content_creation_guide.topic_content_packages)}个完整的创作素材包")
            
        # 默认通用建议
        if not recommendations:
            recommendations = ["聚焦核心用户群体", "建立标准化创作流程", "持续优化内容质量"]
            
        return recommendations

    def _create_fallback_strategy(self, business_context: str, target_product: str) -> StrategyReport:
        """创建备用策略报告"""
        
        # 基础选题策略 - 使用recommended_topics而不是trending_topics
        recommended_topics = [
            RecommendedTopic(
                title="热门话题1",
                rationale="基础话题选择理由",
                target_audience="目标用户群体",
                expected_engagement="高互动预期",
                execution_difficulty="中等",
                priority_score=8
            )
        ]
        
        topic_strategy = TopicStrategy(
            business_domain=business_context,
            target_product=target_product,
            recommended_topics=recommended_topics,
            topic_formulas=["数字型标题", "疑问型标题", "对比型标题"]
        )
        
        # 基础TA策略
        target_audience_strategy = TargetAudienceStrategy(
            primary_persona={"name": "目标用户", "age": "25-35", "interests": ["职场发展"]},
            core_needs=["效率提升", "技能学习", "职业发展"]
        )
        
        # 基础创作指南 - 使用新的模型结构
        complete_copywriting = CompleteCopywriting(
            complete_title=f"新手必看！{target_product}基础攻略",
            full_content=f"你是否还在为{target_product}相关问题而困扰？\\n\\n今天给大家分享一个完整的解决方案...\\n\\n最后总结：掌握这些技巧，你也能...\\n\\n💡 关注我，了解更多相关内容",
            content_length=180,
            posting_time_suggestion="晚上8-10点",
            content_type="图文笔记"
        )
        
        image_descriptions = [
            ImageDescription(
                image_purpose="首图",
                composition_details="清晰的标题文字 + 产品展示",
                character_appearance="年轻专业人士，简洁着装",
                environment_setting="简洁明亮的背景",
                lighting_and_tone="自然光，清新明亮的色调",
                ai_prompt_ready="clean background, professional person, bright lighting"
            ),
            ImageDescription(
                image_purpose="内容图",
                composition_details="步骤说明 + 示例展示",
                character_appearance="与首图保持一致",
                environment_setting="实际操作场景",
                lighting_and_tone="自然光，专业感",
                ai_prompt_ready="step-by-step guide, clean layout"
            ),
            ImageDescription(
                image_purpose="产品图",
                composition_details="产品特写 + 使用效果展示",
                character_appearance="手部特写或使用场景",
                environment_setting="简洁背景，突出产品",
                lighting_and_tone="柔和光线，突出质感",
                ai_prompt_ready="product showcase, soft lighting, clean background"
            )
        ]
        
        topic_content_package = TopicContentPackage(
            topic_title="基础选题示例",
            business_value=f"基于{business_context}的实用价值导向",
            target_pain_point="用户缺乏相关知识和解决方案",
            complete_copywriting=complete_copywriting,
            video_script=None,  # 图文笔记不需要视频脚本
            image_descriptions=image_descriptions
        )
        
        overall_execution_tips = OverallExecutionTips(
            content_quality_standards=["标题吸引力强", "内容有实用价值", "视觉美观度高"],
            platform_best_practices=["使用相关话题标签", "发布时间选择用户活跃期", "积极回复评论互动"],
            engagement_optimization=["设置互动问题", "引导用户分享经验", "及时回复评论"]
        )
        
        content_creation_guide = ContentCreationGuide(
            topic_content_packages=[topic_content_package],
            overall_execution_tips=overall_execution_tips
        )
        
        return StrategyReport(
            business_context=business_context,
            target_product=target_product,
            analysis_base="基础策略模板",
            topic_strategy=topic_strategy,
            target_audience_strategy=target_audience_strategy,
            content_creation_guide=content_creation_guide,
            key_recommendations=["聚焦核心用户群体", "建立标准化创作流程"],
            generation_timestamp=datetime.now().isoformat(),
            report_summary="基础实战策略已生成"
        )

    def save_strategy_results(self, strategy_report: StrategyReport, output_dir: str = "output"):
        """保存策略结果到文件"""
        try:
            output_path = Path(output_dir)
            output_path.mkdir(exist_ok=True)
            
            # 保存JSON格式的详细数据
            json_file = output_path / "strategy_report.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(strategy_report.model_dump(), f, ensure_ascii=False, indent=2)
            
            # 保存Markdown格式的可读报告
            markdown_file = output_path / "strategy_report.md"
            self._save_markdown_strategy_report(strategy_report, markdown_file)
            
            # 保存策略摘要
            summary_file = output_path / "strategy_summary.txt"
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(f"实战策略摘要\\n")
                f.write("=" * 50 + "\\n\\n")
                f.write(f"目标产品: {strategy_report.target_product}\\n")
                f.write(f"生成时间: {strategy_report.generation_timestamp}\\n\\n")
                
                f.write("核心建议:\\n")
                for rec in strategy_report.key_recommendations:
                    f.write(f"  • {rec}\\n")
                
                f.write("\\n成功要素:\\n")
                for factor in strategy_report.success_factors:
                    f.write(f"  • {factor}\\n")
                
                if strategy_report.differentiation_points:
                    f.write("\\n差异化要点:\\n")
                    for point in strategy_report.differentiation_points:
                        f.write(f"  • {point}\\n")
            
            logger.info(f"✅ JSON数据已保存到: {json_file}")
            logger.info(f"📋 Markdown报告已保存到: {markdown_file}")
            logger.info(f"📝 策略摘要已保存到: {summary_file}")
            
        except Exception as e:
            logger.error(f"❌ 保存策略结果失败: {e}")

    def _save_markdown_strategy_report(self, report: StrategyReport, file_path: Path):
        """保存Markdown格式策略报告"""
        with open(file_path, 'w', encoding='utf-8') as f:
            # 标题和概览
            f.write(f"# {report.target_product} 实战策略报告\\n\\n")
            f.write(f"**生成时间**: {report.generation_timestamp}\\n")
            f.write(f"**策略版本**: {report.strategy_version}\\n")
            f.write(f"**有效期**: {report.validity_period}\\n")
            f.write(f"**报告摘要**: {report.report_summary}\\n\\n")
            
            # 业务背景
            f.write("## 📋 业务背景\\n\\n")
            f.write(f"{report.business_context}\\n\\n")
            f.write(f"**分析基础**: {report.analysis_base}\\n\\n")
            
            # 核心建议
            if report.key_recommendations:
                f.write("## 🎯 核心建议\\n\\n")
                for i, rec in enumerate(report.key_recommendations, 1):
                    f.write(f"{i}. {rec}\\n")
                f.write("\\n")
            
            # 选题策略
            f.write("## 📝 选题策略\\n\\n")
            topic = report.topic_strategy
            if topic.recommended_topics:
                f.write("### 精选推荐选题\\n\\n")
                for topic_item in topic.recommended_topics:
                    # topic_item是RecommendedTopic对象，访问其title属性
                    f.write(f"- **{topic_item.title}** (优先级: {topic_item.priority_score}/10)\\n")
                    f.write(f"  - 理由: {topic_item.rationale}\\n")
                    f.write(f"  - 目标用户: {topic_item.target_audience}\\n")
                f.write("\\n")
            
            if topic.topic_formulas:
                f.write("### 选题公式\\n\\n")
                for formula in topic.topic_formulas:
                    f.write(f"- {formula}\\n")
                f.write("\\n")
            
            # TA策略
            f.write("## 👥 目标用户策略\\n\\n")
            ta = report.target_audience_strategy
            if ta.primary_persona:
                f.write("### 主要用户画像\\n\\n")
                for key, value in ta.primary_persona.items():
                    f.write(f"- **{key}**: {value}\\n")
                f.write("\\n")
            
            if ta.core_needs:
                f.write("### 核心需求\\n\\n")
                for need in ta.core_needs:
                    f.write(f"- {need}\\n")
                f.write("\\n")
            
            # 内容创作指南
            f.write("## 🎨 内容创作指南\\n\\n")
            guide = report.content_creation_guide
            
            # 选题内容包
            if guide.topic_content_packages:
                f.write("### 选题内容包\\n\\n")
                for i, package in enumerate(guide.topic_content_packages, 1):
                    f.write(f"#### {i}. {package.topic_title}\\n\\n")
                    f.write(f"**商业价值**: {package.business_value}\\n\\n")
                    f.write(f"**目标痛点**: {package.target_pain_point}\\n\\n")
                    
                    # 完整文案
                    if package.complete_copywriting:
                        f.write("**完整文案**:\\n")
                        f.write(f"- **标题**: {package.complete_copywriting.complete_title}\\n")
                        f.write(f"- **内容类型**: {package.complete_copywriting.content_type}\\n")
                        f.write(f"- **字数**: {package.complete_copywriting.content_length}\\n")
                        f.write("\\n")
                    
                    # 配图描述
                    if package.image_descriptions:
                        f.write(f"**配图描述** ({len(package.image_descriptions)}张):\\n")
                        for j, img_desc in enumerate(package.image_descriptions, 1):
                            f.write(f"  {j}. **{img_desc.image_purpose}**: {img_desc.composition_details}\\n")
                        f.write("\\n")
                    
                    f.write("---\\n\\n")
            
            # 整体执行建议
            if hasattr(guide, 'overall_execution_tips') and guide.overall_execution_tips:
                f.write("### 整体执行建议\\n\\n")
                tips = guide.overall_execution_tips
                if tips.content_quality_standards:
                    f.write("**内容质量标准**:\\n")
                    for standard in tips.content_quality_standards:
                        f.write(f"- {standard}\\n")
                    f.write("\\n")
                
                if tips.platform_best_practices:
                    f.write("**平台最佳实践**:\\n")
                    for practice in tips.platform_best_practices:
                        f.write(f"- {practice}\\n")
                    f.write("\\n")
            
            # 差异化要点
            if report.differentiation_points:
                f.write("## 🎯 差异化要点\\n\\n")
                for point in report.differentiation_points:
                    f.write(f"- {point}\\n")
                f.write("\\n")
            
            # 成功要素
            if report.success_factors:
                f.write("## ✨ 成功要素\\n\\n")
                for factor in report.success_factors:
                    f.write(f"- {factor}\\n")
                f.write("\\n")


def create_strategy_maker() -> StrategyMakerCrew:
    """创建策略制定器实例"""
    return StrategyMakerCrew()


if __name__ == "__main__":
    # 测试代码
    strategy_maker = create_strategy_maker()
    print("✅ StrategyMakerCrew创建成功")