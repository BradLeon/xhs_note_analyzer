#!/usr/bin/env python

"""
Data Models
共享数据模型定义，供整个项目使用
"""

from typing import List, Dict, Any
from pydantic import BaseModel, Field


class NoteData(BaseModel):
    """笔记基础数据模型"""
    note_id: str = ""    # 笔记ID
    note_title: str = ""
    note_url: str = ""
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
    basic_info: NoteData = NoteData()
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
    business_goals: Dict[str, Any] = {}  # 业务目标和约束条件
    
    # 第一步：笔记查找结果
    found_notes: List[NoteData] = []
    notes_search_completed: bool = False
    
    # 第二步：内容获取结果
    detailed_notes: List[NoteContentData] = []
    content_fetch_completed: bool = False
    
    # 第三步：内容分析结果
    content_analysis: List[ContentAdvice] = []
    content_analysis_report: Any = None  # 避免循环导入
    analysis_completed: bool = False
    
    # 第四步：策略制定结果
    strategy_report: Any = None  # 避免循环导入
    strategy_completed: bool = False
    
    # 最终输出
    final_recommendations: Dict[str, Any] = {}


# 从 content_analyzer_crew 移动过来的分析模型
class ContentStructureAnalysis(BaseModel):
    """内容结构分析结果"""
    note_id: str = ""
    
    # 标题分析
    title_pattern: str = ""
    title_keywords: List[str] = []
    title_emotion: str = ""
    
    # 开头分析
    opening_strategy: str = ""
    opening_hook: str = ""
    opening_impact: str = ""
    
    # 正文分析
    content_framework: str = ""
    content_logic: List[str] = []
    paragraph_structure: str = ""
    
    # 结尾分析
    ending_technique: str = ""
    ending_cta: str = ""
    ending_resonance: str = ""
    
    # 整体结构
    word_count: int = 0
    readability_score: float = 0.0
    structure_completeness: float = 0.0


class EmotionalValueAnalysis(BaseModel):
    """情感价值分析结果"""
    note_id: str = ""
    
    # 痛点分析
    pain_points: List[str] = []
    pain_intensity: str = ""
    
    # 价值主张
    value_propositions: List[str] = []
    value_hierarchy: List[str] = []
    
    # 情感触发
    emotional_triggers: List[str] = []
    emotional_intensity: float = 0.0
    
    # 可信度建设
    credibility_signals: List[str] = []
    authority_indicators: List[str] = []
    
    # 心理驱动
    urgency_indicators: List[str] = []
    social_proof: List[str] = []
    scarcity_elements: List[str] = []
    
    # 利益驱动
    benefit_appeals: List[str] = []
    transformation_promise: str = ""


class VisualElementAnalysis(BaseModel):
    """视觉元素分析结果"""
    note_id: str = ""
    
    # 图片基础信息
    image_count: int = 0
    image_quality: str = ""
    
    # 视觉风格
    image_style: str = ""
    color_scheme: str = ""
    visual_tone: str = ""
    
    # 排版设计
    layout_style: str = ""
    text_overlay: bool = False
    visual_hierarchy: str = ""
    
    # 品牌一致性
    brand_consistency: str = ""
    personal_style: str = ""
    
    # 吸引力分析
    thumbnail_appeal: str = ""
    visual_storytelling: str = ""
    scroll_stopping_power: str = ""


# 主要分析结果模型
class ContentAnalysisResult(BaseModel):
    """完整内容分析结果"""
    note_id: str = ""
    note_title: str = ""
    
    # 三个维度的分析结果
    structure_analysis: ContentStructureAnalysis = None
    emotional_analysis: EmotionalValueAnalysis = None  
    visual_analysis: VisualElementAnalysis = None
    
    # 综合评估
    overall_score: float = 0.0
    success_factors: List[str] = []
    improvement_suggestions: List[str] = []
    replicability_score: float = 0.0
    
    # 元数据
    analysis_timestamp: str = ""
    analysis_version: str = "1.0"


class ContentAnalysisReport(BaseModel):
    """多篇笔记分析报告"""
    analysis_results: List[ContentAnalysisResult] = []
    
    # 统计信息
    total_notes: int = 0
    average_score: float = 0.0
    
    # 模式总结
    common_patterns: Dict[str, List[str]] = Field(default_factory=dict, description="共同模式")
    success_formulas: List[str] = Field(default_factory=list, description="成功公式")

    # 深度洞察分析
    pattern_insights: Dict[str, str] = Field(default_factory=dict, description="模式背后的深度洞察分析")
    success_mechanisms: List[str] = Field(default_factory=list, description="成功机制的底层逻辑")
    replication_strategies: List[str] = Field(default_factory=list, description="可操作的复制策略")
    
    
    # 报告元数据
    report_timestamp: str = ""
    report_summary: str = ""


class PatternSynthesisResult(BaseModel):
    """智能模式合成与成功公式提取结果"""
    
    # 智能模式识别
    common_patterns: Dict[str, List[str]] = Field(default_factory=dict, description="LLM识别的深度共同模式")
    success_formulas: List[str] = Field(default_factory=list, description="LLM提取的成功公式")
    
    # 深度洞察分析
    pattern_insights: Dict[str, str] = Field(default_factory=dict, description="模式背后的深度洞察分析")
    success_mechanisms: List[str] = Field(default_factory=list, description="成功机制的底层逻辑")
    replication_strategies: List[str] = Field(default_factory=list, description="可操作的复制策略")
    
    # 元数据
    analysis_timestamp: str = ""