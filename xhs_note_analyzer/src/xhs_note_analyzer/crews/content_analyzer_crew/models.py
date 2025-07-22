"""
内容分析结果数据模型
Content Analysis Data Models for Step3 Multi-dimensional Analysis
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class ContentStructureAnalysis(BaseModel):
    """内容结构分析结果"""
    note_id: str = Field(description="笔记ID")
    
    # 标题分析
    title_pattern: str = Field(default="", description="标题套路分析")
    title_keywords: List[str] = Field(default_factory=list, description="标题关键词")
    title_emotion: str = Field(default="", description="标题情感倾向")
    
    # 开头分析
    opening_strategy: str = Field(default="", description="开头策略")
    opening_hook: str = Field(default="", description="开头钩子类型")
    opening_impact: str = Field(default="", description="开头冲击力评估")
    
    # 正文分析
    content_framework: str = Field(default="", description="正文框架结构")
    content_logic: List[str] = Field(default_factory=list, description="内容逻辑层次")
    paragraph_structure: str = Field(default="", description="段落结构特点")
    
    # 结尾分析
    ending_technique: str = Field(default="", description="结尾技巧")
    ending_cta: str = Field(default="", description="行动召唤")
    ending_resonance: str = Field(default="", description="结尾共鸣度")
    
    # 整体结构
    word_count: int = Field(default=0, description="字数统计")
    readability_score: str = Field(default="", description="可读性评分")
    structure_completeness: str = Field(default="", description="结构完整性")


class EmotionalValueAnalysis(BaseModel):
    """情感价值分析结果"""
    note_id: str = Field(description="笔记ID")
    
    # 痛点分析
    pain_points: List[str] = Field(default_factory=list, description="痛点挖掘")
    pain_intensity: str = Field(default="", description="痛点强度评估")
    
    # 价值主张
    value_propositions: List[str] = Field(default_factory=list, description="价值主张")
    value_hierarchy: List[str] = Field(default_factory=list, description="价值层次排序")
    
    # 情感触发
    emotional_triggers: List[str] = Field(default_factory=list, description="情感触发器")
    emotional_intensity: str = Field(default="", description="情感强度")
    
    # 可信度建设
    credibility_signals: List[str] = Field(default_factory=list, description="可信度信号")
    authority_indicators: List[str] = Field(default_factory=list, description="权威性指标")
    
    # 心理驱动
    urgency_indicators: List[str] = Field(default_factory=list, description="紧迫感指标")
    social_proof: List[str] = Field(default_factory=list, description="社会证明")
    scarcity_elements: List[str] = Field(default_factory=list, description="稀缺性元素")
    
    # 利益驱动
    benefit_appeals: List[str] = Field(default_factory=list, description="利益点吸引")
    transformation_promise: str = Field(default="", description="转变承诺")


class VisualElementAnalysis(BaseModel):
    """视觉元素分析结果"""
    note_id: str = Field(description="笔记ID")
    
    # 图片基础信息
    image_count: int = Field(default=0, description="图片数量")
    image_quality: str = Field(default="", description="图片质量评估")
    
    # 视觉风格
    image_style: str = Field(default="", description="图片风格定位")
    color_scheme: str = Field(default="", description="色彩方案分析")
    visual_tone: str = Field(default="", description="视觉调性")
    
    # 排版设计
    layout_style: str = Field(default="", description="排版风格")
    text_overlay: bool = Field(default=False, description="是否有文字覆盖")
    visual_hierarchy: str = Field(default="", description="视觉层次结构")
    
    # 品牌一致性
    brand_consistency: str = Field(default="", description="品牌一致性评估")
    personal_style: str = Field(default="", description="个人风格特点")
    
    # 吸引力分析
    thumbnail_appeal: str = Field(default="", description="首图吸引力分析")
    visual_storytelling: str = Field(default="", description="视觉叙事能力")
    scroll_stopping_power: str = Field(default="", description="滑动停留力")


class ContentAnalysisResult(BaseModel):
    """完整内容分析结果"""
    note_id: str = Field(description="笔记ID")
    note_title: str = Field(default="", description="笔记标题")
    
    # 三个维度的分析结果
    structure_analysis: ContentStructureAnalysis
    emotional_analysis: EmotionalValueAnalysis  
    visual_analysis: VisualElementAnalysis
    
    # 综合评估
    overall_score: float = Field(default=0.0, description="综合评分(0-100)")
    success_factors: List[str] = Field(default_factory=list, description="成功要素总结")
    improvement_suggestions: List[str] = Field(default_factory=list, description="改进建议")
    replicability_score: float = Field(default=0.0, description="可复制性评分(0-100)")
    
    # 元数据
    analysis_timestamp: str = Field(default="", description="分析时间戳")
    analysis_version: str = Field(default="1.0", description="分析版本")


class ContentAnalysisReport(BaseModel):
    """多篇笔记分析报告"""
    analysis_results: List[ContentAnalysisResult] = Field(default_factory=list, description="分析结果列表")
    
    # 统计信息
    total_notes: int = Field(default=0, description="分析笔记总数")
    average_score: float = Field(default=0.0, description="平均评分")
    
    # 模式总结
    common_patterns: Dict[str, List[str]] = Field(default_factory=dict, description="共同模式")
    success_formulas: List[str] = Field(default_factory=list, description="成功公式")
    
    # 报告元数据
    report_timestamp: str = Field(default="", description="报告生成时间")
    report_summary: str = Field(default="", description="报告摘要")