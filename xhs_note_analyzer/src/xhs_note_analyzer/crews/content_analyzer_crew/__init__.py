"""
Content Analyzer Crew
小红书内容多维度分析模块

提供四个维度的深度内容分析：
1. 内容结构分析 - 标题、开头、正文、结尾
2. 情感价值分析 - 痛点、价值主张、情感触发  
3. 视觉元素分析 - 图片风格、色彩、排版
4. 互动机制分析 - 评论引导、分享机制、社群建设
"""

from .content_analyzer_crew import ContentAnalyzerCrew, create_content_analyzer
from .models import (
    ContentAnalysisResult,
    ContentStructureAnalysis, 
    EmotionalValueAnalysis,
    VisualElementAnalysis,
    EngagementMechanismAnalysis,
    ContentAnalysisReport
)

__all__ = [
    'ContentAnalyzerCrew',
    'create_content_analyzer',
    'ContentAnalysisResult',
    'ContentStructureAnalysis',
    'EmotionalValueAnalysis', 
    'VisualElementAnalysis',
    'EngagementMechanismAnalysis',
    'ContentAnalysisReport'
]