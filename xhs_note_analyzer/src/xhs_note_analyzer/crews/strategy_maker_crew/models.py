"""
实战策略制定数据模型
Strategy Making Data Models for Step4 Practical Strategy Development
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class RecommendedTopic(BaseModel):
    """推荐选题模型"""
    title: str = Field(description="选题标题")
    rationale: str = Field(description="选择理由")
    target_audience: str = Field(description="目标用户群")
    expected_engagement: str = Field(description="预期互动效果")
    execution_difficulty: str = Field(description="执行难度评估")
    priority_score: int = Field(description="优先级评分(1-10)")

class TopicStrategy(BaseModel):
    """选题策略模型"""
    
    # 基础信息
    business_domain: str = Field(description="业务领域")
    target_product: str = Field(description="目标产品/服务")
    
    # 精选推荐选题
    recommended_topics: List[RecommendedTopic] = Field(default_factory=list, description="精选推荐选题列表(3-5个)")
    
    # 选题策略
    topic_formulas: List[str] = Field(default_factory=list, description="选题公式模板")
    keyword_clusters: Dict[str, List[str]] = Field(default_factory=dict, description="核心关键词集群")
    competition_analysis: Dict[str, str] = Field(default_factory=dict, description="竞争分析要点")
    content_calendar: Dict[str, str] = Field(default_factory=dict, description="内容发布时间规划")


class TargetAudienceStrategy(BaseModel):
    """目标用户策略模型"""
    
    # 用户画像
    primary_persona: Dict[str, Any] = Field(default_factory=dict, description="主要用户画像")
    secondary_personas: List[Dict[str, Any]] = Field(default_factory=list, description="次要用户画像")
    
    # 用户特征
    demographics: Dict[str, str] = Field(default_factory=dict, description="人口统计学特征")
    psychographics: Dict[str, List[str]] = Field(default_factory=dict, description="心理特征")
    behavioral_patterns: List[str] = Field(default_factory=list, description="行为模式")
    
    # 需求分析
    core_needs: List[str] = Field(default_factory=list, description="核心需求")
    pain_points: List[str] = Field(default_factory=list, description="用户痛点")
    motivations: List[str] = Field(default_factory=list, description="驱动因素")
    
    # 触达策略
    content_preferences: Dict[str, str] = Field(default_factory=dict, description="内容偏好")
    engagement_triggers: List[str] = Field(default_factory=list, description="互动触发器")
    conversion_points: List[str] = Field(default_factory=list, description="转化节点")


class CopywritingGuide(BaseModel):
    """文案创作指南"""
    
    # 标题策略
    title_templates: List[str] = Field(default_factory=list, description="针对每个推荐选题的具体标题模板")
    title_keywords: List[str] = Field(default_factory=list, description="标题关键词")
    title_emotions: List[str] = Field(default_factory=list, description="标题情感词汇")
    
    # 开头策略
    opening_hooks: List[str] = Field(default_factory=list, description="基于用户痛点和选题特点的开头钩子模板")
    opening_templates: List[str] = Field(default_factory=list, description="开头模板")
    
    # 正文结构
    content_frameworks: List[str] = Field(default_factory=list, description="针对不同选题类型的正文结构框架")
    storytelling_formulas: List[str] = Field(default_factory=list, description="适合各选题的故事叙述公式")
    persuasion_techniques: List[str] = Field(default_factory=list, description="针对用户痛点的说服技巧")
    
    # 结尾策略
    cta_templates: List[str] = Field(default_factory=list, description="与选题目标匹配的行动召唤模板")
    engagement_questions: List[str] = Field(default_factory=list, description="互动问题")
    
    # 文案风格
    tone_guidelines: Dict[str, str] = Field(default_factory=dict, description="基于目标用户画像的语调指南")
    vocabulary_suggestions: List[str] = Field(default_factory=list, description="词汇建议")


class VisualGuide(BaseModel):
    """配图创作指南"""
    
    # 视觉风格
    style_direction: str = Field(default="", description="与选题调性匹配的整体风格方向")
    color_palette: List[str] = Field(default_factory=list, description="基于目标用户偏好的配色方案")
    visual_themes: List[str] = Field(default_factory=list, description="视觉主题")
    
    # 图片策略
    image_types: List[str] = Field(default_factory=list, description="各选题推荐的图片类型和风格")
    composition_rules: List[str] = Field(default_factory=list, description="针对选题内容的构图规则")
    photo_ideas: List[str] = Field(default_factory=list, description="拍照创意")
    
    # 设计元素
    layout_templates: List[str] = Field(default_factory=list, description="选题专用的排版模板")
    text_overlay_styles: List[str] = Field(default_factory=list, description="文字叠加样式")
    brand_elements: List[str] = Field(default_factory=list, description="品牌元素")
    
    # 实用建议
    equipment_recommendations: List[str] = Field(default_factory=list, description="设备推荐")
    shooting_tips: List[str] = Field(default_factory=list, description="针对不同选题场景的拍摄技巧")
    editing_guidelines: List[str] = Field(default_factory=list, description="后期处理指南")


class VideoScriptGuide(BaseModel):
    """视频脚本指南"""
    
    # 脚本结构
    script_templates: List[str] = Field(default_factory=list, description="基于推荐选题的具体脚本模板")
    opening_sequences: List[str] = Field(default_factory=list, description="各选题的开头序列设计")
    transition_techniques: List[str] = Field(default_factory=list, description="适合选题内容的转场技巧")
    ending_strategies: List[str] = Field(default_factory=list, description="结尾策略")
    
    # 内容规划
    scene_breakdowns: List[Dict[str, str]] = Field(default_factory=list, description="每个选题的详细场景分解")
    dialogue_suggestions: List[str] = Field(default_factory=list, description="对话建议")
    voiceover_scripts: List[str] = Field(default_factory=list, description="旁白脚本")
    
    # 视觉指导
    shot_compositions: List[str] = Field(default_factory=list, description="选题专用的镜头构图建议")
    lighting_setups: List[str] = Field(default_factory=list, description="灯光设置")
    background_suggestions: List[str] = Field(default_factory=list, description="背景建议")
    
    # 制作建议
    duration_guidelines: Dict[str, str] = Field(default_factory=dict, description="基于选题特点的时长建议")
    pacing_recommendations: List[str] = Field(default_factory=list, description="节奏建议")
    music_suggestions: List[str] = Field(default_factory=list, description="音乐建议")


class TopicSpecificGuide(BaseModel):
    """针对特定选题的创作指导"""
    topic_title: str = Field(description="选题标题")
    content_angle: str = Field(description="内容切入角度")
    key_messages: List[str] = Field(default_factory=list, description="核心传达信息")
    execution_steps: List[str] = Field(default_factory=list, description="具体执行步骤")
    success_metrics: List[str] = Field(default_factory=list, description="成功评估指标")


class ContentCreationGuide(BaseModel):
    """内容创作指南综合模型"""
    
    # 三大创作指南
    copywriting_guide: CopywritingGuide
    visual_guide: VisualGuide
    video_script_guide: VideoScriptGuide
    
    # 创作流程
    creation_workflow: List[str] = Field(default_factory=list, description="针对推荐选题的创作工作流程")
    quality_checklist: List[str] = Field(default_factory=list, description="基于选题要求的质量检查清单")
    optimization_tips: List[str] = Field(default_factory=list, description="优化技巧")
    
    # 选题专项指导
    topic_specific_guides: List[TopicSpecificGuide] = Field(default_factory=list, description="为每个推荐选题提供的专门创作指导")
    
    # 发布策略
    posting_schedule: Dict[str, str] = Field(default_factory=dict, description="发布时间表")
    hashtag_strategy: List[str] = Field(default_factory=list, description="标签策略")
    engagement_tactics: List[str] = Field(default_factory=list, description="互动策略")




class StrategyReport(BaseModel):
    """实战策略报告"""
    
    # 基础信息
    business_context: str = Field(description="业务背景")
    target_product: str = Field(description="目标产品/服务")
    analysis_base: str = Field(description="分析基础数据")
    
    # 三大策略模块
    topic_strategy: TopicStrategy
    target_audience_strategy: TargetAudienceStrategy  
    content_creation_guide: ContentCreationGuide
    
    # 综合建议
    key_recommendations: List[str] = Field(default_factory=list, description="核心建议")
    success_factors: List[str] = Field(default_factory=list, description="成功要素")
    differentiation_points: List[str] = Field(default_factory=list, description="差异化要点")
    
    # 报告元数据
    strategy_version: str = Field(default="1.0", description="策略版本")
    generation_timestamp: str = Field(default="", description="生成时间")
    validity_period: str = Field(default="3个月", description="有效期")
    report_summary: str = Field(default="", description="报告摘要")