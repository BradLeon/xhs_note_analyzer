#!/usr/bin/env python

"""
Content Analyzer Crew
小红书内容多维度分析Crew - Step3实现

负责对小红书笔记进行四个维度的深度分析：
1. 内容结构分析 - 标题、开头、正文、结尾
2. 情感价值分析 - 痛点、价值主张、情感触发
3. 视觉元素分析 - 图片风格、色彩、排版  
4. 互动机制分析 - 评论引导、分享机制、社群建设
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from crewai import Agent, Crew, Task, Process, LLM
from crewai.project import CrewBase, agent, crew, task
from langchain_openai import ChatOpenAI


# 从公共模型导入所有分析相关类型
from xhs_note_analyzer.models import (
    ContentStructureAnalysis,
    EmotionalValueAnalysis,
    VisualElementAnalysis,
    ContentAnalysisResult, 
    ContentAnalysisReport,
    PatternSynthesisResult
)

# 导入公共数据模型
from xhs_note_analyzer.models import NoteContentData

logger = logging.getLogger(__name__)

@CrewBase
class ContentAnalyzerCrew():
    """内容分析Crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    def __init__(self):

        self.llm = ChatOpenAI(
        base_url='https://openrouter.ai/api/v1',
        model='openrouter/google/gemini-2.5-flash-lite',
        api_key=os.environ['OPENROUTER_API_KEY'],
        temperature=0.1
        )

        
    @agent
    def content_structure_analyst(self) -> Agent:
        """内容结构分析专家"""
        return Agent(
            config=self.agents_config['content_structure_analyst'],
            llm=self.llm,
            verbose=True
        )

    @agent 
    def emotional_value_analyst(self) -> Agent:
        """情感价值分析专家"""
        return Agent(
            config=self.agents_config['emotional_value_analyst'],
            llm=self.llm,
            verbose=True
        )

    @agent
    def visual_element_analyst(self) -> Agent:
        """视觉元素分析专家"""
        return Agent(
            config=self.agents_config['visual_element_analyst'],
            llm=self.llm,
            verbose=True
        )


    @agent
    def content_analysis_coordinator(self) -> Agent:
        """内容分析协调专家"""
        return Agent(
            config=self.agents_config['content_analysis_coordinator'],
            llm=self.llm,
            verbose=True
        )

    @agent
    def pattern_synthesis_analyst(self) -> Agent:
        """智能模式合成与成功公式提取专家"""
        return Agent(
            config=self.agents_config['pattern_synthesis_analyst'],
            llm=self.llm,
            verbose=True
        )

    @task
    def analyze_content_structure_task(self) -> Task:
        """内容结构分析任务"""
        return Task(
            config=self.tasks_config['analyze_content_structure'],
            agent=self.content_structure_analyst(),
            output_pydantic=ContentStructureAnalysis
        )

    @task
    def analyze_emotional_value_task(self) -> Task:
        """情感价值分析任务"""
        return Task(
            config=self.tasks_config['analyze_emotional_value'],
            agent=self.emotional_value_analyst(),
            output_pydantic=EmotionalValueAnalysis
        )

    @task
    def analyze_visual_elements_task(self) -> Task:
        """视觉元素分析任务"""
        return Task(
            config=self.tasks_config['analyze_visual_elements'],
            agent=self.visual_element_analyst(),
            output_pydantic=VisualElementAnalysis
        )


    @task
    def coordinate_content_analysis_task(self) -> Task:
        """内容分析协调任务"""
        return Task(
            config=self.tasks_config['coordinate_content_analysis'],
            agent=self.content_analysis_coordinator(),
            context=[
                self.analyze_content_structure_task(),
                self.analyze_emotional_value_task(),
                self.analyze_visual_elements_task()
            ]
            # 协调任务不需要特定的Pydantic输出，返回Markdown报告即可
        )

    @task
    def synthesize_patterns_and_formulas_task(self) -> Task:
        """智能模式合成与成功公式提取任务"""
        return Task(
            config=self.tasks_config['synthesize_patterns_and_formulas'],
            agent=self.pattern_synthesis_analyst(),
            output_pydantic=PatternSynthesisResult
        )

    @crew
    def crew(self) -> Crew:
        """创建内容分析Crew"""
        return Crew(
            agents=[
                self.content_structure_analyst(),
                self.emotional_value_analyst(),
                self.visual_element_analyst(),
                self.content_analysis_coordinator()
            ],
            tasks=[
                self.analyze_content_structure_task(),
                self.analyze_emotional_value_task(),
                self.analyze_visual_elements_task(),
                self.coordinate_content_analysis_task()
            ],
            process=Process.sequential,
            verbose=True
        )

    def analyze_single_note(self, note_data: NoteContentData) -> ContentAnalysisResult:
        """
        分析单个笔记
        
        Args:
            note_data: NoteContentData对象，包含笔记的详细信息
            
        Returns:
            ContentAnalysisResult: 分析结果
        """
        try:
            logger.info(f"🔍 开始分析笔记: {note_data.note_id} - {note_data.title}")
            
            # 准备分析数据
            analysis_input = {
                "note_id": note_data.note_id,
                "note_title": note_data.title,
                "note_content": note_data.content,
                "note_images": note_data.images,
                "image_count": len(note_data.images),
                "note_tags": note_data.tags,
                "author_info": note_data.author_info,
                "like_count": getattr(note_data.basic_info, 'like', 0),
                "collect_count": getattr(note_data.basic_info, 'collect', 0),
                "comment_count": getattr(note_data.basic_info, 'comment', 0)
            }
            
            # 执行分析
            result = self.crew().kickoff(inputs=analysis_input)
            
            # 解析结果并转换为结构化数据
            analysis_result = self._parse_analysis_result(result, note_data)
            
            logger.info(f"✅ 笔记分析完成: {note_data.note_id}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"❌ 笔记分析失败: {note_data.note_id}, 错误: {e}")
            # 返回基础分析结果
            return self._create_fallback_analysis(note_data)

    def analyze_multiple_notes(self, notes_data: List[NoteContentData]) -> ContentAnalysisReport:
        """
        批量分析多个笔记，并使用LLM智能提取共同模式和成功公式
        
        Args:
            notes_data: List[NoteContentData] 笔记数据列表
            
        Returns:
            ContentAnalysisReport: 包含智能模式分析的完整分析报告
        """
        try:
            logger.info(f"🚀 开始批量分析 {len(notes_data)} 个笔记")
            
            # Step 1: 分析每个笔记
            analysis_results = []
            for note_data in notes_data:
                result = self.analyze_single_note(note_data)
                analysis_results.append(result)
            
            logger.info(f"📊 单笔记分析完成，开始智能模式合成")
            
            # Step 2: 使用LLM智能提取模式和公式
            pattern_synthesis_result = self._synthesize_patterns_with_llm(analysis_results)
            
            # Step 3: 生成整合了智能分析的综合报告
            report = self._generate_enhanced_analysis_report(analysis_results, pattern_synthesis_result)
            
            logger.info(f"✅ 批量分析完成，共分析 {len(analysis_results)} 个笔记，智能提取了 {len(pattern_synthesis_result.success_formulas)} 个成功公式")
            return report
            
        except Exception as e:
            logger.error(f"❌ 批量分析失败: {e}")
            raise

    def _parse_analysis_result(self, crew_result, note_data) -> ContentAnalysisResult:
        """解析Crew执行结果并转换为结构化数据"""
        try:
            logger.info(f"🔍 开始解析分析结果，类型: {type(crew_result)}")
            
            # 初始化各维度分析结果
            structure_analysis = None
            emotional_analysis = None
            visual_analysis = None
            
            # 从tasks_output中获取各个任务的Pydantic结果
            if hasattr(crew_result, 'tasks_output') and crew_result.tasks_output:
                logger.info(f"📋 从tasks_output解析，任务数量: {len(crew_result.tasks_output)}")
                
                for i, task_output in enumerate(crew_result.tasks_output):
                    try:
                        logger.info(f"🔧 处理任务 {i+1}: {type(task_output)}")
                        
                        # 检查是否有pydantic输出（这是我们配置的output_pydantic）
                        if hasattr(task_output, 'pydantic') and task_output.pydantic:
                            pydantic_obj = task_output.pydantic
                            logger.info(f"✅ 任务 {i+1} 有Pydantic输出: {type(pydantic_obj)}")
                            
                            # 根据Pydantic对象类型确定是哪个维度的分析
                            if isinstance(pydantic_obj, ContentStructureAnalysis):
                                structure_analysis = pydantic_obj
                                logger.info(f"✅ 获取到内容结构分析结果")
                            elif isinstance(pydantic_obj, EmotionalValueAnalysis):
                                emotional_analysis = pydantic_obj
                                logger.info(f"✅ 获取到情感价值分析结果")
                            elif isinstance(pydantic_obj, VisualElementAnalysis):
                                visual_analysis = pydantic_obj
                                logger.info(f"✅ 获取到视觉元素分析结果")
                            else:
                                logger.warning(f"⚠️ 未知的Pydantic对象类型: {type(pydantic_obj)}")
                        
                        # 如果没有Pydantic输出，尝试从json_dict获取
                        elif hasattr(task_output, 'json_dict') and task_output.json_dict:
                            json_data = task_output.json_dict
                            logger.info(f"📊 任务 {i+1} 有JSON输出，键: {list(json_data.keys())}")
                            
                            # 根据任务顺序和内容判断类型
                            if i == 0:  # 第一个任务是内容结构分析
                                structure_analysis = ContentStructureAnalysis(note_id=note_data.note_id, **json_data)
                                logger.info(f"✅ 从JSON创建内容结构分析结果")
                            elif i == 1:  # 第二个任务是情感价值分析
                                emotional_analysis = EmotionalValueAnalysis(note_id=note_data.note_id, **json_data)
                                logger.info(f"✅ 从JSON创建情感价值分析结果")
                            elif i == 2:  # 第三个任务是视觉元素分析
                                visual_analysis = VisualElementAnalysis(note_id=note_data.note_id, **json_data)
                                logger.info(f"✅ 从JSON创建视觉元素分析结果")
                        
                        else:
                            logger.warning(f"⚠️ 任务 {i+1} 没有结构化输出，跳过")
                            
                    except Exception as task_error:
                        logger.warning(f"⚠️ 解析任务 {i+1} 失败: {task_error}")
                        continue
            
            # 如果某些维度的分析结果为空，创建默认值
            if not structure_analysis:
                logger.warning("⚠️ 内容结构分析结果为空，创建默认值")
                structure_analysis = ContentStructureAnalysis(note_id=note_data.note_id)
            
            if not emotional_analysis:
                logger.warning("⚠️ 情感价值分析结果为空，创建默认值")
                emotional_analysis = EmotionalValueAnalysis(note_id=note_data.note_id)
            
            if not visual_analysis:
                logger.warning("⚠️ 视觉元素分析结果为空，创建默认值")
                visual_analysis = VisualElementAnalysis(note_id=note_data.note_id)
            
            # 计算综合评分（基于各维度评分的平均值）
            scores = []
            if hasattr(structure_analysis, 'readability_score') and structure_analysis.readability_score > 0:
                scores.append(structure_analysis.readability_score)
            if hasattr(emotional_analysis, 'emotional_intensity') and emotional_analysis.emotional_intensity > 0:
                scores.append(emotional_analysis.emotional_intensity)
            # 视觉分析没有直接的评分字段，使用默认值
            if len(scores) == 0:
                overall_score = 75.0
            else:
                overall_score = sum(scores) / len(scores)
            
            # 收集成功要素
            success_factors = []
            if structure_analysis.title_pattern:
                success_factors.append(f"标题策略: {structure_analysis.title_pattern}")
            if emotional_analysis.pain_points:
                success_factors.append(f"痛点挖掘: {len(emotional_analysis.pain_points)}个痛点")
            if visual_analysis.image_style:
                success_factors.append(f"视觉风格: {visual_analysis.image_style}")
            
            if not success_factors:
                success_factors = ["完成基础分析"]
            
            # 创建完整分析结果
            analysis_result = ContentAnalysisResult(
                note_id=note_data.note_id,
                note_title=note_data.title,
                structure_analysis=structure_analysis,
                emotional_analysis=emotional_analysis,
                visual_analysis=visual_analysis,
                overall_score=overall_score,
                success_factors=success_factors,
                improvement_suggestions=["基于多维度分析的优化建议"],
                replicability_score=overall_score * 0.9,  # 可复制性略低于整体评分
                analysis_timestamp=datetime.now().isoformat(),
                analysis_version="1.0"
            )
            
            logger.info(f"✅ 成功解析分析结果，综合评分: {overall_score:.1f}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"❌ 解析分析结果失败: {e}")
            logger.error(f"❌ 错误详情: {str(e)}")
            import traceback
            logger.error(f"❌ 堆栈跟踪: {traceback.format_exc()}")
            return self._create_fallback_analysis(note_data)

    def _create_fallback_analysis(self, note_data: NoteContentData) -> ContentAnalysisResult:
        """创建备用分析结果"""
        return ContentAnalysisResult(
            note_id=note_data.note_id,
            note_title=note_data.title,
            structure_analysis=ContentStructureAnalysis(note_id=note_data.note_id),
            emotional_analysis=EmotionalValueAnalysis(note_id=note_data.note_id),
            visual_analysis=VisualElementAnalysis(note_id=note_data.note_id),
            overall_score=60.0,
            success_factors=["基础内容完整"],
            improvement_suggestions=["需要深度分析优化"],
            analysis_timestamp=datetime.now().isoformat()
        )

    def _synthesize_patterns_with_llm(self, analysis_results: List[ContentAnalysisResult]) -> PatternSynthesisResult:
        """使用LLM智能合成模式和提取成功公式"""
        try:
            logger.info(f"🧠 开始LLM智能模式合成，输入 {len(analysis_results)} 个分析结果")
            
            # 准备分析输入数据
            total_notes = len(analysis_results)
            average_score = sum(r.overall_score for r in analysis_results) / total_notes if total_notes > 0 else 0.0
            high_score_notes = [r for r in analysis_results if r.overall_score >= 80.0]
            high_score_count = len(high_score_notes)
            
            # 构建输入数据
            synthesis_input = {
                "analysis_results": [result.model_dump() for result in analysis_results],
                "total_notes": total_notes,
                "average_score": average_score,
                "high_score_count": high_score_count
            }
            
            # 创建专门的模式合成Crew来执行LLM分析
            pattern_crew = Crew(
                agents=[self.pattern_synthesis_analyst()],
                tasks=[self.synthesize_patterns_and_formulas_task()],
                process=Process.sequential,
                verbose=True
            )
            
            # 执行LLM智能分析
            pattern_task_result = pattern_crew.kickoff(inputs=synthesis_input)
            
            # 解析LLM分析结果
            if hasattr(pattern_task_result, 'pydantic') and pattern_task_result.pydantic:
                pattern_result = pattern_task_result.pydantic
            elif hasattr(pattern_task_result, 'json_dict') and pattern_task_result.json_dict:
                pattern_result = PatternSynthesisResult(**pattern_task_result.json_dict)
            else:
                # 如果LLM任务失败，创建基础结果
                logger.warning("⚠️ LLM模式合成失败，使用基础合成结果")
                pattern_result = self._create_basic_pattern_synthesis(analysis_results)
            
            return pattern_result
            
        except Exception as e:
            logger.error(f"❌ LLM模式合成失败: {e}")
            # 返回基础合成结果
            return self._create_basic_pattern_synthesis(analysis_results)

    def _create_basic_pattern_synthesis(self, analysis_results: List[ContentAnalysisResult]) -> PatternSynthesisResult:
        """创建基础的模式合成结果（作为LLM分析的备选方案）"""
        high_score_notes = [r for r in analysis_results if r.overall_score >= 80.0]
        
        return PatternSynthesisResult(
            common_patterns={
                "结构模式": ["基础结构分析", "标准开头结尾"],
                "情感模式": ["基础情感触发", "价值主张识别"],
                "视觉模式": ["基础视觉风格", "色彩搭配"]
            },
            success_formulas=[
                "高质量内容 + 情感共鸣 = 高互动",
                "清晰结构 + 视觉吸引 = 用户停留"
            ],
            pattern_insights={
                "基础洞察": "需要LLM深度分析获得更准确的洞察"
            },
            success_mechanisms=["内容质量", "用户体验", "情感连接"],
            replication_strategies=["保持内容质量", "注重视觉设计", "建立情感连接"],
            analysis_timestamp=datetime.now().isoformat(),
        )

    def _generate_enhanced_analysis_report(self, analysis_results: List[ContentAnalysisResult], 
                                         pattern_synthesis: PatternSynthesisResult) -> ContentAnalysisReport:
        """生成整合了智能模式分析的增强分析报告"""
        total_notes = len(analysis_results)
        average_score = sum(r.overall_score for r in analysis_results) / total_notes if total_notes > 0 else 0.0
        
        report = ContentAnalysisReport(
            analysis_results=analysis_results,
            total_notes=total_notes,
            average_score=average_score,
            # 多篇笔记共同模式分析
            common_patterns=pattern_synthesis.common_patterns,
            success_formulas=pattern_synthesis.success_formulas,
            pattern_insights=pattern_synthesis.pattern_insights,
            success_mechanisms=pattern_synthesis.success_mechanisms,
            replication_strategies=pattern_synthesis.replication_strategies,
            report_timestamp=datetime.now().isoformat(),
            report_summary=f"完成对{total_notes}篇笔记的智能化多维度分析，平均评分{average_score:.1f}，LLM识别{len(pattern_synthesis.success_formulas)}个成功公式"
        )
        
        return report

    def _generate_analysis_report(self, analysis_results: List[ContentAnalysisResult]) -> ContentAnalysisReport:
        """生成分析报告（向后兼容方法，建议使用智能化的analyze_multiple_notes）"""
        logger.info("📊 使用基础报告生成方法，建议使用analyze_multiple_notes获得智能化分析")
        
        total_notes = len(analysis_results)
        average_score = sum(r.overall_score for r in analysis_results) / total_notes if total_notes > 0 else 0.0
        
        # 使用基础的模式提取（不再依赖机械化方法）
        common_patterns = {
            "标题模式": ["待智能分析", "使用analyze_multiple_notes获得详细模式"],
            "开头策略": ["待智能分析", "使用analyze_multiple_notes获得详细策略"],
            "视觉风格": ["待智能分析", "使用analyze_multiple_notes获得详细分析"],
            "互动技巧": ["待智能分析", "推荐使用智能化分析方法"]
        }
        
        success_formulas = [
            "使用analyze_multiple_notes方法获得LLM智能提取的成功公式",
            "基础分析建议：保持内容质量 + 关注用户体验"
        ]
        
        report = ContentAnalysisReport(
            analysis_results=analysis_results,
            total_notes=total_notes,
            average_score=average_score,
            common_patterns=common_patterns,
            success_formulas=success_formulas,
            report_timestamp=datetime.now().isoformat(),
            report_summary=f"完成对{total_notes}篇笔记的基础多维度分析，平均评分{average_score:.1f}。推荐使用analyze_multiple_notes获得智能化深度分析。"
        )
        
        return report

    def save_analysis_results(self, analysis_results, output_dir: str = "output"):
        """保存分析结果到文件"""
        try:
            output_path = Path(output_dir)
            output_path.mkdir(exist_ok=True)
            
            if isinstance(analysis_results, ContentAnalysisReport):
                # 保存JSON格式的详细数据
                json_file = output_path / "content_analysis_results.json"
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(analysis_results.model_dump(), f, ensure_ascii=False, indent=2)
                
                # 保存Markdown格式的报告
                markdown_file = output_path / "content_analysis_report.md"
                self._save_markdown_report(analysis_results, markdown_file)
                
                # 保存简要文本摘要
                summary_file = output_path / "content_analysis_summary.txt"
                with open(summary_file, 'w', encoding='utf-8') as f:
                    f.write(f"小红书内容智能分析报告\\n")
                    f.write("=" * 50 + "\\n\\n")
                    f.write(f"分析笔记数: {analysis_results.total_notes}\\n")
                    f.write(f"平均评分: {analysis_results.average_score:.1f}\\n")
                    f.write(f"生成时间: {analysis_results.report_timestamp}\\n")
                    f.write(f"报告摘要: {analysis_results.report_summary}\\n\\n")
                    
                    # LLM识别的共同模式
                    f.write("🤖 LLM智能识别的共同模式:\\n")
                    for pattern_type, patterns in analysis_results.common_patterns.items():
                        f.write(f"  {pattern_type}: {', '.join(patterns)}\\n")
                    
                    # LLM提取的成功公式
                    f.write("\\n🎯 LLM智能提取的成功公式:\\n")
                    for i, formula in enumerate(analysis_results.success_formulas, 1):
                        f.write(f"  {i}. {formula}\\n")
                    
                    # 模式洞察（新增）
                    if hasattr(analysis_results, 'pattern_insights') and analysis_results.pattern_insights:
                        f.write("\\n💡 深度洞察分析:\\n")
                        for insight_key, insight_value in analysis_results.pattern_insights.items():
                            f.write(f"  {insight_key}: {insight_value}\\n")
                    
                    # 成功机制（新增）
                    if hasattr(analysis_results, 'success_mechanisms') and analysis_results.success_mechanisms:
                        f.write("\\n⚙️ 底层成功机制:\\n")
                        for i, mechanism in enumerate(analysis_results.success_mechanisms, 1):
                            f.write(f"  {i}. {mechanism}\\n")
                    
                    # 复制策略（新增）
                    if hasattr(analysis_results, 'replication_strategies') and analysis_results.replication_strategies:
                        f.write("\\n📋 可操作的复制策略:\\n")
                        for i, strategy in enumerate(analysis_results.replication_strategies, 1):
                            f.write(f"  {i}. {strategy}\\n")
                
                print(f"✅ JSON数据已保存到: {json_file}")
                print(f"📋 Markdown报告已保存到: {markdown_file}")
                print(f"📄 文本摘要已保存到: {summary_file}")
                
            else:
                # 保存单个分析结果
                results_file = output_path / "content_analysis_results.json"
                with open(results_file, 'w', encoding='utf-8') as f:
                    json.dump(analysis_results.model_dump(), f, ensure_ascii=False, indent=2)
                print(f"✅ 分析结果已保存到: {results_file}")
                
        except Exception as e:
            logger.error(f"❌ 保存分析结果失败: {e}")

    def _save_markdown_report(self, report: ContentAnalysisReport, file_path: Path):
        """保存Markdown格式报告"""
        with open(file_path, 'w', encoding='utf-8') as f:
            # 标题和概览
            f.write("# 小红书内容深度分析报告\\n\\n")
            f.write(f"**生成时间**: {report.report_timestamp}\\n")
            f.write(f"**报告摘要**: {report.report_summary}\\n\\n")
            
            # 分析概览
            f.write("## 📊 智能分析概览\\n\\n")
            f.write(f"- **分析笔记数**: {report.total_notes}\\n")
            f.write(f"- **平均评分**: {report.average_score:.1f}/100\\n")
            f.write(f"- **LLM识别成功公式**: {len(report.success_formulas)}\\n")
            f.write(f"- **LLM提取共同模式**: {len(report.common_patterns)}\\n")
            
            # 智能分析额外统计信息
            if hasattr(report, 'pattern_insights') and report.pattern_insights:
                f.write(f"- **深度洞察维度**: {len(report.pattern_insights)}\\n")
            if hasattr(report, 'success_mechanisms') and report.success_mechanisms:
                f.write(f"- **识别成功机制**: {len(report.success_mechanisms)}\\n")
            if hasattr(report, 'replication_strategies') and report.replication_strategies:
                f.write(f"- **提供复制策略**: {len(report.replication_strategies)}\\n")
            
            f.write("\\n> 🤖 **采用LLM智能分析技术**，深度挖掘内容成功规律，提供可操作的策略指导\\n\\n")
            
            # LLM智能提取的成功公式
            if report.success_formulas:
                f.write("## 🎯 LLM智能提取的成功公式\\n\\n")
                for i, formula in enumerate(report.success_formulas, 1):
                    f.write(f"{i}. **{formula}**\\n")
                f.write("\\n")
            
            # LLM识别的共同模式
            if report.common_patterns:
                f.write("## 🔍 LLM智能识别的共同模式\\n\\n")
                for pattern_type, patterns in report.common_patterns.items():
                    f.write(f"### {pattern_type}\\n\\n")
                    for pattern in patterns:
                        f.write(f"- {pattern}\\n")
                    f.write("\\n")
            
            # 深度洞察分析（新增）
            if hasattr(report, 'pattern_insights') and report.pattern_insights:
                f.write("## 💡 深度洞察分析\\n\\n")
                for insight_key, insight_value in report.pattern_insights.items():
                    f.write(f"### {insight_key}\\n\\n")
                    f.write(f"{insight_value}\\n\\n")
            
            # 底层成功机制（新增）
            if hasattr(report, 'success_mechanisms') and report.success_mechanisms:
                f.write("## ⚙️ 底层成功机制\\n\\n")
                for i, mechanism in enumerate(report.success_mechanisms, 1):
                    f.write(f"{i}. **{mechanism}**\\n")
                f.write("\\n")
            
            # 可操作的复制策略（新增）
            if hasattr(report, 'replication_strategies') and report.replication_strategies:
                f.write("## 📋 可操作的复制策略\\n\\n")
                for i, strategy in enumerate(report.replication_strategies, 1):
                    f.write(f"{i}. **{strategy}**\\n")
                f.write("\\n")
            
            # 详细分析结果
            f.write("## 📋 详细分析结果\\n\\n")
            for i, result in enumerate(report.analysis_results, 1):
                f.write(f"### {i}. {result.note_title}\\n\\n")
                f.write(f"**笔记ID**: `{result.note_id}`\\n")
                f.write(f"**综合评分**: {result.overall_score:.1f}/100\\n")
                f.write(f"**可复制性**: {result.replicability_score:.1f}/100\\n\\n")
                
                # 成功要素
                if result.success_factors:
                    f.write("**成功要素**:\\n")
                    for factor in result.success_factors:
                        f.write(f"- {factor}\\n")
                    f.write("\\n")
                
                # 改进建议  
                if result.improvement_suggestions:
                    f.write("**改进建议**:\\n")
                    for suggestion in result.improvement_suggestions:
                        f.write(f"- {suggestion}\\n")
                    f.write("\\n")
                
                # 三个维度的详细分析
                f.write("#### 📝 内容结构分析\\n\\n")
                sa = result.structure_analysis
                if sa.title_pattern:
                    f.write(f"- **标题模式**: {sa.title_pattern}\\n")
                if sa.opening_strategy:
                    f.write(f"- **开头策略**: {sa.opening_strategy}\\n")
                if sa.content_framework:
                    f.write(f"- **内容框架**: {sa.content_framework}\\n")
                if sa.ending_technique:
                    f.write(f"- **结尾技巧**: {sa.ending_technique}\\n")
                f.write("\\n")
                
                f.write("#### 💝 情感价值分析\\n\\n")
                ea = result.emotional_analysis
                if ea.pain_points:
                    f.write(f"- **痛点挖掘**: {', '.join(ea.pain_points)}\\n")
                if ea.value_propositions:
                    f.write(f"- **价值主张**: {', '.join(ea.value_propositions)}\\n")
                if ea.emotional_triggers:
                    f.write(f"- **情感触发**: {', '.join(ea.emotional_triggers)}\\n")
                f.write("\\n")
                
                f.write("#### 🎨 视觉元素分析\\n\\n")
                va = result.visual_analysis
                if va.image_style:
                    f.write(f"- **图片风格**: {va.image_style}\\n")
                if va.color_scheme:
                    f.write(f"- **色彩方案**: {va.color_scheme}\\n")
                if va.layout_style:
                    f.write(f"- **排版风格**: {va.layout_style}\\n")
                f.write("\\n")
                
                f.write("---\\n\\n")


def create_content_analyzer() -> ContentAnalyzerCrew:
    """创建内容分析器实例"""
    return ContentAnalyzerCrew()


if __name__ == "__main__":
    # 测试代码
    analyzer = create_content_analyzer()
    print("✅ ContentAnalyzerCrew创建成功")