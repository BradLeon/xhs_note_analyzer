#!/usr/bin/env python

"""
Data Models
共享数据模型定义，供整个项目使用
"""

from typing import List, Dict, Any
from pydantic import BaseModel


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