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


# 新的内容创作模型，匹配tasks.yaml的expected_output

class CompleteCopywriting(BaseModel):
    """完整文案模型"""
    complete_title: str = Field(description="完整标题（可直接使用）")
    full_content: str = Field(description="完整正文内容（开头+正文+结尾+CTA）")
    content_length: int = Field(description="字数统计")
    posting_time_suggestion: str = Field(description="建议发布时间")
    content_type: str = Field(description="内容形式（图文笔记/视频笔记）")

class VideoScript(BaseModel):
    """视频脚本模型"""
    character_profile: str = Field(description="出镜人物详细设定（年龄、职业、穿着、性格）")
    timeline_script: str = Field(description="按秒标注的时间轴脚本")
    scene_description: str = Field(description="拍摄场景详细描述")
    dialogue_with_emotion: str = Field(description="逐句台词（含语调和情感提示）")
    camera_directions: str = Field(description="镜头切换指导")
    props_and_setup: str = Field(description="道具和布景要求")

class ImageDescription(BaseModel):
    """配图描述模型"""
    image_purpose: str = Field(description="图片用途（首图/内容图/产品图）")
    composition_details: str = Field(description="画面构成详细描述")
    character_appearance: str = Field(description="人物外观详细描述")
    environment_setting: str = Field(description="环境和氛围描述")
    lighting_and_tone: str = Field(description="光线和色调要求")
    ai_prompt_ready: str = Field(description="可直接用于AI绘图的提示词")

class TopicContentPackage(BaseModel):
    """选题内容包模型"""
    topic_title: str = Field(description="选题标题")
    business_value: str = Field(description="该选题的商业价值和转化逻辑")
    target_pain_point: str = Field(description="针对的用户痛点")
    complete_copywriting: CompleteCopywriting = Field(description="一个完整文案")
    video_script: Optional[VideoScript] = Field(default=None, description="视频脚本（仅当content_type为视频笔记时提供）")
    image_descriptions: List[ImageDescription] = Field(default_factory=list, description="配图描述列表(3-5张)")

class OverallExecutionTips(BaseModel):
    """整体执行建议模型"""
    content_quality_standards: List[str] = Field(default_factory=list, description="内容质量标准")
    platform_best_practices: List[str] = Field(default_factory=list, description="小红书平台最佳实践")
    engagement_optimization: List[str] = Field(default_factory=list, description="互动优化建议")

class ContentCreationGuide(BaseModel):
    """内容创作执行手册模型 - 匹配tasks.yaml输出"""
    topic_content_packages: List[TopicContentPackage] = Field(default_factory=list, description="选题内容包列表")
    overall_execution_tips: OverallExecutionTips = Field(description="整体执行建议")




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