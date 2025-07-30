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
    TopicStrategy,
    TargetAudienceStrategy,
    ContentCreationGuide,
    CopywritingGuide,
    VisualGuide,
    VideoScriptGuide,
    TopicSpecificGuide,
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

    @agent
    def strategy_integration_coordinator(self) -> Agent:
        """策略整合协调专家"""
        return Agent(
            config=self.agents_config['strategy_integration_coordinator'],
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

    @task
    def coordinate_strategy_integration_task(self) -> Task:
        """策略整合协调任务 - 第四步，整合所有策略"""
        return Task(
            config=self.tasks_config['coordinate_strategy_integration'],
            agent=self.strategy_integration_coordinator(),
            context=[
                self.analyze_target_audience_task(),
                self.develop_topic_strategy_task(),
                self.create_content_creation_guide_task()
            ],
            output_pydantic=StrategyReport
        )


    @crew
    def crew(self) -> Crew:
        """创建策略制定Crew"""
        return Crew(
            agents=[
                self.target_audience_analyst(),
                self.topic_strategy_expert(),
                self.content_creation_guide(),
                self.strategy_integration_coordinator()
            ],
            tasks=[
                self.analyze_target_audience_task(),
                self.develop_topic_strategy_task(),
                self.create_content_creation_guide_task(),
                self.coordinate_strategy_integration_task()
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
        
        # 提取内容分析的关键洞察
        success_cases = []
        if content_analysis_report and content_analysis_report.analysis_results:
            for result in content_analysis_report.analysis_results:
                success_cases.append({
                    "note_title": result.note_title,
                    "overall_score": result.overall_score,
                    "success_factors": result.success_factors,
                    "structure_insights": {
                        "title_pattern": result.structure_analysis.title_pattern,
                        "opening_strategy": result.structure_analysis.opening_strategy,
                        "content_framework": result.structure_analysis.content_framework
                    },
                    "emotional_insights": {
                        "pain_points": result.emotional_analysis.pain_points,
                        "value_propositions": result.emotional_analysis.value_propositions,
                        "emotional_triggers": result.emotional_analysis.emotional_triggers
                    },
                    "visual_insights": {
                        "image_style": result.visual_analysis.image_style,
                        "color_scheme": result.visual_analysis.color_scheme,
                        "layout_style": result.visual_analysis.layout_style
                    }
                })
        
        # 构建策略输入
        strategy_input = {
            "business_context": business_context,
            "target_product": target_product,
            "analysis_report": content_analysis_report.model_dump() if content_analysis_report else {},
            #"success_cases": success_cases, 摘取的数据太片面，且内容属于content_analysis_report的子集
            "user_insights": self._extract_user_insights(content_analysis_report), # 主要包括痛点、价值主张、情绪触点
            #"behavior_analysis": self._extract_behavior_patterns(content_analysis_report), #现有输入无法提取有价值的用户行为
            "content_analysis": self._extract_content_patterns(content_analysis_report),
            "success_factors": content_analysis_report.success_formulas if content_analysis_report else [],
            "visual_insights": self._extract_visual_patterns(content_analysis_report),
            "creation_requirements": business_goals or {}
        }
        
        return strategy_input

    def _extract_user_insights(self, report: 'ContentAnalysisReport') -> Dict[str, Any]:
        """从分析报告中提取用户洞察"""
        if not report or not report.analysis_results:
            return {}
        
        # 聚合用户相关的洞察
        all_pain_points = []
        all_value_props = []
        all_triggers = []
        
        for result in report.analysis_results:
            all_pain_points.extend(result.emotional_analysis.pain_points)
            all_value_props.extend(result.emotional_analysis.value_propositions)
            all_triggers.extend(result.emotional_analysis.emotional_triggers)
        
        return {
            "common_pain_points": list(set(all_pain_points)),
            "value_propositions": list(set(all_value_props)),
            "emotional_triggers": list(set(all_triggers))
        }

    def _extract_behavior_patterns(self, report: 'ContentAnalysisReport') -> Dict[str, Any]:
        """提取用户行为模式"""
        if not report or not report.analysis_results:
            return {}
        
        patterns = {
            "high_engagement_patterns": [],
            "content_preferences": [],
            "interaction_styles": []
        }
        
        # 基于高分内容提取行为模式
        high_score_content = [r for r in report.analysis_results if r.overall_score >= 80.0]
        
        for result in high_score_content:
            if result.success_factors:
                patterns["high_engagement_patterns"].extend(result.success_factors)
        
        return patterns

    def _extract_content_patterns(self, report: 'ContentAnalysisReport') -> Dict[str, Any]:
        """提取内容创作模式"""
        if not report or not report.analysis_results:
            return {}
        
        patterns = {
            "successful_structures": [],
            "effective_openings": [],
            "winning_frameworks": []
        }
        
        for result in report.analysis_results:
            if result.structure_analysis.title_pattern:
                patterns["successful_structures"].append(result.structure_analysis.title_pattern)
            if result.structure_analysis.opening_strategy:
                patterns["effective_openings"].append(result.structure_analysis.opening_strategy)
            if result.structure_analysis.content_framework:
                patterns["winning_frameworks"].append(result.structure_analysis.content_framework)
            # content_logic?
        
        return patterns

    def _extract_visual_patterns(self, report: 'ContentAnalysisReport') -> Dict[str, Any]:
        """提取视觉设计模式"""
        if not report or not report.analysis_results:
            return {}
        
        patterns = {
            "popular_styles": [],
            "effective_colors": [],
            "layout_trends": []
        }
        
        for result in report.analysis_results:
            if result.visual_analysis.image_style:
                patterns["popular_styles"].append(result.visual_analysis.image_style)
            if result.visual_analysis.color_scheme:
                patterns["effective_colors"].append(result.visual_analysis.color_scheme)
            if result.visual_analysis.layout_style:
                patterns["layout_trends"].append(result.visual_analysis.layout_style)
        
        return patterns

    def _integrate_strategy_results(self, crew_results, strategy_input: Dict[str, Any]) -> StrategyReport:
        """整合三个任务的结果为完整策略报告"""
        try:
            # CrewAI执行结果通常是最后一个任务的输出
            # 但我们需要从结果中提取各个任务的输出
            
            # 解析结果
            if isinstance(crew_results, str):
                # 如果是字符串，尝试解析为JSON
                try:
                    results_data = json.loads(crew_results)
                except:
                    # 如果无法解析，创建基础结构
                    results_data = self._parse_text_results(crew_results)
            else:
                results_data = crew_results if isinstance(crew_results, dict) else {}
            
            # 提取各个策略组件
            topic_strategy = TopicStrategy(**results_data.get("topic_strategy", self._create_basic_topic_strategy(strategy_input)))
            target_audience_strategy = TargetAudienceStrategy(**results_data.get("target_audience_strategy", self._create_basic_ta_strategy(strategy_input)))
            
            # 创建内容创作指南
            content_guide_data = results_data.get("content_creation_guide", self._create_basic_content_guide(strategy_input))
            copywriting_guide = CopywritingGuide(**content_guide_data.get("copywriting_guide", {}))
            visual_guide = VisualGuide(**content_guide_data.get("visual_guide", {}))
            video_script_guide = VideoScriptGuide(**content_guide_data.get("video_script_guide", {}))
            
            # 处理topic_specific_guides
            topic_guides = []
            for guide_data in content_guide_data.get("topic_specific_guides", []):
                topic_guides.append(TopicSpecificGuide(**guide_data))
            
            content_creation_guide = ContentCreationGuide(
                copywriting_guide=copywriting_guide,
                visual_guide=visual_guide,
                video_script_guide=video_script_guide,
                creation_workflow=content_guide_data.get("creation_workflow", []),
                quality_checklist=content_guide_data.get("quality_checklist", []),
                topic_specific_guides=topic_guides
            )
            
            # 生成综合建议
            key_recommendations = self._generate_key_recommendations(
                topic_strategy, target_audience_strategy, content_creation_guide
            )
            
            # 创建完整策略报告
            strategy_report = StrategyReport(
                business_context=strategy_input["business_context"],
                target_product=strategy_input["target_product"],
                analysis_base=f"基于{len(strategy_input.get('success_cases', []))}个成功案例的分析",
                topic_strategy=topic_strategy,
                target_audience_strategy=target_audience_strategy,
                content_creation_guide=content_creation_guide,
                key_recommendations=key_recommendations,
                success_factors=results_data.get("success_factors", []),
                differentiation_points=results_data.get("differentiation_points", []),
                generation_timestamp=datetime.now().isoformat(),
                report_summary=f"针对{strategy_input['target_product']}的三维度实战策略制定完成"
            )
            
            return strategy_report
            
        except Exception as e:
            logger.warning(f"⚠️ 整合策略结果失败，使用fallback: {e}")
            return self._create_fallback_strategy(
                strategy_input["business_context"], 
                strategy_input["target_product"]
            )

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
        """创建基础内容创作指南"""
        target_product = strategy_input.get("target_product", "")
        business_context = strategy_input.get("business_context", "")
        
        return {
            "copywriting_guide": {
                "title_templates": ["如何...", "...的N个方法", "...攻略分享"],
                "opening_hooks": ["痛点开头", "数据开头", "故事开头"],
                "content_frameworks": ["AIDA框架", "问题-解决方案-结果", "故事-观点-行动"],
                "storytelling_formulas": ["英雄之旅", "冲突-解决", "前后对比"],
                "persuasion_techniques": ["社会认同", "稀缺性", "权威背书"],
                "cta_templates": ["立即行动", "了解更多", "分享经验"],
                "tone_guidelines": {"正式度": "亲和", "情感色彩": "积极", "专业度": "实用"}
            },
            "visual_guide": {
                "style_direction": "简约清新",
                "color_palette": ["#F5F5F5", "#333333", "#FF6B6B"],
                "image_types": ["生活场景", "产品展示", "信息图表"],
                "composition_rules": ["三分法则", "对称构图", "引导线构图"],
                "layout_templates": ["九宫格", "左右分屏", "上下分层"],
                "shooting_tips": ["自然光拍摄", "多角度取景", "细节特写"]
            },
            "video_script_guide": {
                "script_templates": ["开头-正文-结尾", "问题-解决-总结"],
                "opening_sequences": ["疑问式开头", "冲突式开头", "数据式开头"],
                "scene_breakdowns": [{"场景1": "开场介绍"}, {"场景2": "核心内容"}, {"场景3": "总结呼吁"}],
                "shot_compositions": ["中景介绍", "特写强调", "全景总结"],
                "transition_techniques": ["淡入淡出", "快切", "旋转过渡"],
                "duration_guidelines": {"短视频": "15-60秒", "长视频": "3-10分钟"}
            },
            "creation_workflow": ["选题确定", "内容策划", "素材准备", "制作执行", "发布优化"],
            "quality_checklist": ["标题吸引力", "内容价值度", "视觉美观度", "互动引导性"],
            "topic_specific_guides": [
                {
                    "topic_title": f"{target_product}基础选题示例",
                    "content_angle": f"基于{business_context}的实用价值导向",
                    "key_messages": ["解决用户痛点", "提供实用技巧", "引发共鸣"],
                    "execution_steps": ["确定核心价值", "搭建内容框架", "制作视觉素材", "优化发布策略"],
                    "success_metrics": ["点赞率>5%", "评论率>2%", "分享率>1%"]
                }
            ]
        }

    def _generate_key_recommendations(self, topic_strategy: TopicStrategy, 
                                    target_audience_strategy: TargetAudienceStrategy,
                                    content_creation_guide: ContentCreationGuide) -> List[str]:
        """基于三个策略组件生成综合建议"""
        recommendations = []
        
        # 基于选题策略的建议
        if topic_strategy.trending_topics:
            recommendations.append(f"重点关注{len(topic_strategy.trending_topics)}个热门选题方向")
        
        # 基于TA策略的建议  
        if target_audience_strategy.core_needs:
            recommendations.append(f"聚焦用户{len(target_audience_strategy.core_needs)}大核心需求")
            
        # 基于创作指南的建议
        if content_creation_guide.copywriting_guide.title_templates:
            recommendations.append("使用标准化的标题模板提升点击率")
            
        # 默认通用建议
        if not recommendations:
            recommendations = ["聚焦核心用户群体", "建立标准化创作流程", "持续优化内容质量"]
            
        return recommendations

    def _create_fallback_strategy(self, business_context: str, target_product: str) -> StrategyReport:
        """创建备用策略报告"""
        
        # 基础选题策略
        topic_strategy = TopicStrategy(
            business_domain=business_context,
            target_product=target_product,
            trending_topics=["热门话题1", "热门话题2", "热门话题3"],
            topic_formulas=["数字型标题", "疑问型标题", "对比型标题"]
        )
        
        # 基础TA策略
        target_audience_strategy = TargetAudienceStrategy(
            primary_persona={"name": "目标用户", "age": "25-35", "interests": ["职场发展"]},
            core_needs=["效率提升", "技能学习", "职业发展"]
        )
        
        # 基础创作指南
        copywriting_guide = CopywritingGuide(
            title_templates=["如何...", "...的N个方法", "...攻略分享"],
            opening_hooks=["痛点开头", "数据开头", "故事开头"]
        )
        
        visual_guide = VisualGuide(
            style_direction="简约清新",
            color_palette=["#F5F5F5", "#333333", "#FF6B6B"]
        )
        
        video_script_guide = VideoScriptGuide(
            script_templates=["开头-正文-结尾", "问题-解决-总结"]
        )
        
        # 基础选题指导
        topic_specific_guide = TopicSpecificGuide(
            topic_title="基础选题示例",
            content_angle="实用价值导向",
            key_messages=["解决用户痛点", "提供实用技巧", "引发共鸣"],
            execution_steps=["确定核心价值", "搭建内容框架", "制作视觉素材", "优化发布策略"],
            success_metrics=["点赞率>5%", "评论率>2%", "分享率>1%"]
        )
        
        content_creation_guide = ContentCreationGuide(
            copywriting_guide=copywriting_guide,
            visual_guide=visual_guide,
            video_script_guide=video_script_guide,
            creation_workflow=["选题确定", "内容策划", "素材准备", "制作执行", "发布优化"],
            quality_checklist=["标题吸引力", "内容价值度", "视觉美观度", "互动引导性"],
            topic_specific_guides=[topic_specific_guide]
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
            if topic.trending_topics:
                f.write("### 热门选题\\n\\n")
                for topic_item in topic.trending_topics:
                    f.write(f"- {topic_item}\\n")
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
            
            # 文案指南
            f.write("### 文案创作\\n\\n")
            if guide.copywriting_guide.title_templates:
                f.write("**标题模板**:\\n")
                for template in guide.copywriting_guide.title_templates:
                    f.write(f"- {template}\\n")
                f.write("\\n")
            
            # 视觉指南
            f.write("### 视觉设计\\n\\n")
            if guide.visual_guide.style_direction:
                f.write(f"**整体风格**: {guide.visual_guide.style_direction}\\n\\n")
            
            if guide.visual_guide.color_palette:
                f.write("**配色方案**: ")
                f.write(", ".join(guide.visual_guide.color_palette))
                f.write("\\n\\n")
            
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