#!/usr/bin/env python
"""
测试脚本 - Step2: 采集笔记详细内容
基于Step1的结果进行数据采集
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import List

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from xhs_note_analyzer.tools.mediacrawler_client import MediaCrawlerClient
from xhs_note_analyzer.main import NoteData, NoteContentData

# 配置测试日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_step2_fetch_note_content.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_step1_results(step1_output_dir: str = "tests/output/step1") -> List[NoteData]:
    """从Step1的结果中加载笔记数据"""
    try:
        # 尝试从test_result.json加载
        test_result_file = Path(step1_output_dir) / "test_result.json"
        if test_result_file.exists():
            with open(test_result_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if "result" in data and "data" in data["result"]:
                    note_list = data["result"]["data"]["note_data_list"]
                    return [NoteData(**note) for note in note_list]
        
        # 尝试寻找其他可能的文件
        for json_file in Path(step1_output_dir).glob("*.json"):
            if json_file.name != "test_result.json":
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if "notes" in data:
                            return [NoteData(**note) for note in data["notes"]]
                except Exception as e:
                    logger.warning(f"无法从{json_file}加载数据: {e}")
        
        logger.warning("未找到Step1的结果数据，使用模拟数据")
        return create_mock_note_data()
        
    except Exception as e:
        logger.error(f"加载Step1结果失败: {e}")
        return create_mock_note_data()

def create_mock_note_data() -> List[NoteData]:
    """创建模拟的笔记数据用于测试，使用真实的带token完整URL"""
    # 使用参考代码中的真实测试URL
    return [
        NoteData(
            note_id="65728c2a000000003403fc88",
            note_title="国企求职攻略分享",
            note_url="https://www.xiaohongshu.com/explore/65728c2a000000003403fc88?xsec_token=ZBBMPkZKZC66wNYHvcBT26aYWhVGGRQZBgbpYzClweEPc=&xsec_source=pc_ad",
            impression=50000, click=8000, like=1200, collect=800, comment=150, engage=2150
        ),
        NoteData(
            note_id="67d95153000000001d01d6a5",
            note_title="央企面试技巧大全",
            note_url="https://www.xiaohongshu.com/explore/67d95153000000001d01d6a5?xsec_token=ZBfzpWi9xD-KsHutTewgjNpM-hqNu6ymhBK86y05hmiVk=&xsec_source=pc_ad", 
            impression=30000, click=5000, like=800, collect=500, comment=100, engage=1400
        ),
        NoteData(
            note_id="676a4d0a000000001f00c58c",
            note_title="求职简历模板分享",
            note_url="https://www.xiaohongshu.com/explore/676a4d0a000000001f00c58c?xsec_token=MNOpqr456_mockToken3_STUVWX&xsec_source=pc_ad",
            impression=40000, click=6500, like=1000, collect=600, comment=120, engage=1720
        )
    ]

def test_mediacrawler_connection():
    """测试MediaCrawler API连接"""
    print("🔧 测试 MediaCrawler API 连接...")
    
    try:
        # 创建带调试功能的客户端
        client = MediaCrawlerClient(debug_requests=True)
        
        # 检查健康状态
        print("\n🏥 执行健康检查...")
        is_healthy = client.health_check()
        print(f"API健康状态: {'✅ 正常' if is_healthy else '❌ 不可用'}")
        
        if not is_healthy:
            print("⚠️ MediaCrawler API不可用，将使用模拟数据进行测试")
        
        return is_healthy, client
        
    except Exception as e:
        logger.warning(f"MediaCrawler连接测试异常: {e}")
        print(f"❌ API连接异常: {e}")
        return False, None

def test_note_id_extraction():
    """测试note_id提取功能"""
    print("\n🧪 测试 note_id 提取功能...")
    
    client = MediaCrawlerClient(debug_requests=False)  # ID提取不需要调试HTTP请求
    
    test_cases = [
        ("https://www.xiaohongshu.com/explore/65728c2a000000003403fc88", "65728c2a000000003403fc88"),
        ("https://www.xiaohongshu.com/note/65728c2a000000003403fc88", "65728c2a000000003403fc88"),
        ("https://www.xiaohongshu.com/explore/65728c2a000000003403fc88?xsec_token=ZBBMPkZKZC66wNYHvcBT26aYWhVGGRQZBgbpYzClweEPc=&xsec_source=pc_ad", "65728c2a000000003403fc88"),  # 带token的URL
        ("65728c2a000000003403fc88", "65728c2a000000003403fc88"),  # 纯ID
    ]
    
    success_count = 0
    for test_url, expected in test_cases:
        result = client.extract_note_id_from_url(test_url)
        status = "✅" if result == expected else "❌"
        print(f"  {status} {test_url[:40]}... -> {result}")
        if result == expected:
            success_count += 1
    
    print(f"note_id提取测试: {success_count}/{len(test_cases)} 通过")
    return success_count == len(test_cases)

async def test_step2_fetch_content_async():
    """测试Step2：采集笔记详细内容"""
    print("\n🚀 开始测试 Step2: 采集笔记详细内容")
    print("=" * 60)
    
    try:
        # 加载Step1的结果
        print("📥 加载 Step1 结果数据...")
        note_list = load_step1_results()
        note_list = note_list[:5]
        print(f"加载到 {len(note_list)} 条笔记数据")
        
        if not note_list:
            print("❌ 没有可用的笔记数据")
            return False
        
        # 显示将要处理的笔记
        print("\n📋 待处理的笔记:")
        for i, note in enumerate(note_list, 1):  # 只处理前5条
            print(f"  {i}. {note.note_title}")
            print(f"     URL: {note.note_url}")
        
        # 检查API连接
        api_available, client = test_mediacrawler_connection()
        
        output_dir = "tests/output/step2"
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # 开始采集内容 - 使用批量方式
        print(f"\n🔍 开始批量采集详细内容...")
        detailed_notes = []
        note_urls = [note.note_url for note in note_list]  # 限制只处理前5条
        
        if api_available and client:
            try:
                # 使用新的API流程: 创建任务 -> 监控任务 -> 查询结果
                print(f"  📡 使用 MediaCrawler API采集 {len(note_urls)} 个笔记...")
                print(f"  📋 测试URL格式: {[url[:80] + '...' for url in note_urls]}")
                
                # 使用完整的API流程
                results = client.batch_crawl_notes(note_urls, fetch_comments=False)
                
                # 处理批量采集结果
                for i, (note, result) in enumerate(zip(note_list, results), 1):
                    print(f"\n处理笔记 {i}/{len(note_list)}: {note.note_title}")
                    
                    if result.get("success") and result.get("data"):
                        # API成功，转换数据
                        detailed_content = convert_api_result_to_note_content(note, result)
                        print("  ✅ API采集成功")
                    
                    detailed_notes.append(detailed_content)
                
                print(f"  ✅ 批量采集完成")
                
            except Exception as e:
                logger.warning(f"API调用异常: {e}")
                print(f"  ⚠️ API异常，使用模拟数据")
         
        # 保存结果
        print(f"\n💾 保存采集结果...")
        
        # 保存为JSON
        result_file = Path(output_dir) / "step2_content_results.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": str(asyncio.get_event_loop().time()),
                "total_notes": len(detailed_notes),
                "detailed_notes": [note.model_dump() for note in detailed_notes]
            }, f, ensure_ascii=False, indent=2)
        
        # 保存摘要
        summary_file = Path(output_dir) / "step2_summary.txt"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("Step2 笔记内容采集结果摘要\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"处理笔记数: {len(detailed_notes)}\n")
            f.write(f"API状态: {'可用' if api_available else '不可用'}\n\n")
            
            f.write("详细内容:\n")
            f.write("-" * 30 + "\n")
            for i, note in enumerate(detailed_notes, 1):
                f.write(f"\n{i}. {note.title}\n")
                f.write(f"   ID: {note.note_id}\n")
                f.write(f"   内容长度: {len(note.content)} 字符\n")
                f.write(f"   图片数量: {len(note.images)}\n")
                f.write(f"   标签数量: {len(note.tags)}\n")
        
        print(f"✅ 结果已保存到:")
        print(f"  📄 详细数据: {result_file}")
        print(f"  📋 摘要信息: {summary_file}")
        
        # 验证结果
        print(f"\n🔍 验证采集结果:")
        success_count = 0
        api_success_count = 0
        mock_count = 0
        
        for i, note in enumerate(detailed_notes):

            
            # 检查基本数据质量
            has_meaningful_content = len(note.content) > 50  # 至少有50个字符
            has_basic_info = note.title and len(note.title) > 1
  
            if has_meaningful_content and has_basic_info:
                # API成功采集的数据，无论图片数量多少都算成功
                status = "✅"  # API成功
                data_source = "API采集"
                api_success_count += 1
                success_count += 1
            else:
                status = "❌"  # 失败
                data_source = "数据不完整"
            
            print(f"  {status} {note.title}: 内容({len(note.content)}字符) 图片({len(note.images)}张) [{data_source}]")
            
          
        print(f"\n📊 Step2 测试结果:")
        print(f"API成功采集: {api_success_count}/{len(detailed_notes)} ({api_success_count/len(detailed_notes)*100:.1f}%)")
        print(f"使用模拟数据: {mock_count}/{len(detailed_notes)} ({mock_count/len(detailed_notes)*100:.1f}%)")
        print(f"总体成功率: {(api_success_count + mock_count)/len(detailed_notes)*100:.1f}%")
        
        # 返回成功条件：至少有60%的笔记通过API成功采集，或总体成功率（API+模拟）达到80%
        total_valid = api_success_count + mock_count
        success_rate = total_valid / len(detailed_notes)
        api_success_rate = api_success_count / len(detailed_notes)
        
        # 如果API成功率超过60%，或者总体成功率超过80%，都认为测试通过
        return api_success_rate >= 0.6 or success_rate >= 0.8
        
        
    except Exception as e:
        logger.error(f"❌ Step2 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def convert_api_result_to_note_content(note: NoteData, api_result: dict) -> NoteContentData:
    """将API返回结果转换为NoteContentData格式，适配新的API响应格式"""
    raw_data = api_result.get("data", {})
    
    # 处理图片URL列表
    images = []
    if raw_data.get("images"):
        images = raw_data["images"] if isinstance(raw_data["images"], list) else [raw_data["images"]]
    elif raw_data.get("image_list"):
        images = raw_data["image_list"] if isinstance(raw_data["image_list"], list) else [raw_data["image_list"]]
    
    # 处理作者信息 - 适配多种字段名
    author_info = {}
    if raw_data.get("nickname"):
        author_info["name"] = raw_data["nickname"] 
    elif raw_data.get("user_name"):
        author_info["name"] = raw_data["user_name"]
    
    if raw_data.get("user_id"):
        author_info["user_id"] = raw_data["user_id"]
    if raw_data.get("follower_count"):
        author_info["followers"] = raw_data["follower_count"]
    
    # 处理标签
    tags = []
    if raw_data.get("tags"):
        tags = raw_data["tags"] if isinstance(raw_data["tags"], list) else [raw_data["tags"]]
    elif raw_data.get("note_tag_list"):
        # 从note_tag_list提取标签名
        tag_list = raw_data["note_tag_list"]
        if isinstance(tag_list, list):
            tags = [tag.get("name", str(tag)) for tag in tag_list if tag]
    
    # 处理视频URL
    video_url = ""
    if raw_data.get("video_url"):
        video_url = raw_data["video_url"]
    elif raw_data.get("video") and isinstance(raw_data["video"], dict):
        video_url = raw_data["video"].get("url", "")
    
    # 处理发布时间
    create_time = ""
    if raw_data.get("last_update_time"):
        create_time = raw_data["last_update_time"]
    elif raw_data.get("publish_time"):
        create_time = raw_data["publish_time"]
    elif raw_data.get("create_time"):
        create_time = raw_data["create_time"]
    
    return  NoteContentData(
        note_id=raw_data.get("note_id"),
        title=raw_data.get("title"),
        basic_info=note,
        content=raw_data.get("desc", raw_data.get("content", f"这是{note.note_title}的详细内容...")),
        images=images,
        video_url=video_url,
        author_info=author_info,
        tags=tags,
        create_time=create_time
    )


# Removed unused async functions - using batch_crawl_notes instead


def validate_step2_output(output_dir: str):
    """验证Step2的输出文件"""
    print("\n🔍 验证 Step2 输出文件...")
    
    output_path = Path(output_dir)
    expected_files = [
        "step2_content_results.json",
        "step2_summary.txt"
    ]
    
    missing_files = []
    for file_name in expected_files:
        file_path = output_path / file_name
        if not file_path.exists():
            missing_files.append(file_name)
        else:
            print(f"✅ 找到文件: {file_path}")
    
    if missing_files:
        print(f"⚠️ 缺失文件: {missing_files}")
    else:
        print("✅ 所有预期文件都已生成")
    
    return len(missing_files) == 0

async def main():
    """主测试函数"""
    print("🧪 Step2 采集笔记详细内容 - 测试脚本")
    print("=" * 80)
    
    # 测试前置检查
    print("🔧 前置检查...")
    id_extraction_ok = test_note_id_extraction()
    
    # 执行主要测试  
    success1 = await test_step2_fetch_content_async()
    
    # 验证输出
    success2 = validate_step2_output("tests/output/step2")
    
    # 总结
    print("\n" + "=" * 80)
    print("📊 Step2 测试总结:")
    print(f"ID提取功能: {'✅ 通过' if id_extraction_ok else '❌ 失败'}")
    print(f"内容采集测试: {'✅ 通过' if success1 else '❌ 失败'}")
    print(f"输出验证测试: {'✅ 通过' if success2 else '❌ 失败'}")
    
    overall_success = id_extraction_ok and success1 and success2
    print(f"\n🎯 整体测试结果: {'✅ 全部通过' if overall_success else '❌ 存在失败'}")
    
    if overall_success:
        print("\n✨ Step2 测试完成，可以继续执行 Step3 测试")
        print("💡 提示: Step2 的结果将被 Step3 使用进行内容分析")
    else:
        print("\n⚠️ 请检查并修复失败的测试项")
    
    return overall_success

if __name__ == "__main__":
    # 检查环境变量
    import os
    api_endpoint = os.getenv("MEDIACRAWLER_API_ENDPOINT", "http://localhost:8000")
    print(f"🔧 MediaCrawler API地址: {api_endpoint}")
    
    if not os.getenv("OPENROUTER_API_KEY"):
        print("⚠️ 警告: 未设置 OPENROUTER_API_KEY 环境变量")
    
    print()
    
    # 运行测试
    result = asyncio.run(main())
    
    # 退出码
    sys.exit(0 if result else 1)