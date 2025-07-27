# XHS Note Analyzer - 测试脚本

这个目录包含了 XHS Note Analyzer 项目的完整测试套件。

## 测试结构

### 四个步骤的单独测试
1. **`test_step1_find_hot_notes.py`** - Step1: 查找相关优质笔记
   - 限定查找第一页以提高效率
   - 测试browser_use代理的笔记发现功能
   - 生成模拟数据作为后续步骤的输入

2. **`test_step2_fetch_note_content.py`** - Step2: 采集笔记详细内容
   - 基于Step1的结果进行内容采集
   - 测试MediaCrawler API客户端
   - 支持API不可用时的模拟数据模式

3. **`test_step3_multi_dimensional_analysis.py`** - Step3: 多维度内容分析
   - 选择3个note进行分析以提高效率
   - 测试三维度分析：结构、情感、视觉
   - 使用OpenRouter API进行LLM分析

4. **`test_step4_strategy_making.py`** - Step4: 实战策略制定
   - 基于Step3的分析结果制定策略
   - 测试三个策略维度：选题、TA、创作指导
   - 生成完整的策略报告

### 主测试脚本
- **`run_all_tests.py`** - 运行所有测试的主脚本
  - 按序执行四个步骤
  - 环境检查和依赖验证
  - 生成测试摘要报告

## 使用方法

### 环境准备
```bash
# 设置必需的环境变量
export OPENROUTER_API_KEY="your_openrouter_api_key"

# 可选：设置MediaCrawler API（如果可用）
export MEDIACRAWLER_API_ENDPOINT="http://localhost:8000"
export MEDIACRAWLER_API_KEY="your_api_key"
```

### 运行测试

#### 1. 运行所有测试（推荐）
```bash
cd xhs_note_analyzer/tests
python run_all_tests.py
```

#### 2. 运行单个步骤测试
```bash
# Step1: 查找笔记
python test_step1_find_hot_notes.py

# Step2: 采集内容
python test_step2_fetch_note_content.py

# Step3: 内容分析（需要OPENROUTER_API_KEY）
python test_step3_multi_dimensional_analysis.py

# Step4: 策略制定（需要OPENROUTER_API_KEY）
python test_step4_strategy_making.py
```

## 测试输出

每个步骤的测试都会在 `tests/output/` 目录下生成相应的输出文件：

### Step1 输出
- `step1/test_result.json` - 测试结果
- 可能的笔记数据文件（如果真实API可用）

### Step2 输出  
- `step2/step2_content_results.json` - 详细内容数据
- `step2/step2_summary.txt` - 采集摘要

### Step3 输出
- `step3/content_analysis_results.json` - 分析详细数据
- `step3/content_analysis_report.md` - Markdown格式报告
- `step3/content_analysis_summary.txt` - 分析摘要
- `step3/step3_analysis_test_results.json` - 测试专用结果

### Step4 输出
- `step4/strategy_report.json` - 策略详细数据
- `step4/strategy_report.md` - Markdown格式策略报告
- `step4/strategy_summary.txt` - 策略摘要
- `step4/step4_strategy_test_results.json` - 测试专用结果

### 综合输出
- `test_summary.txt` - 所有测试的摘要报告

## 注意事项

### 1. 环境要求
- Python 3.8+
- 必需：`OPENROUTER_API_KEY` (Step3和Step4需要)
- 可选：MediaCrawler API配置 (Step2可用，但有fallback)

### 2. 测试特点
- **渐进式依赖**：Step2依赖Step1的输出，Step3依赖Step2，Step4依赖Step3
- **智能fallback**：当真实API不可用时，自动使用模拟数据
- **限制规模**：为提高测试效率，限制了处理的数据量
- **调试友好**：包含详细的调试日志和状态信息

### 3. 常见问题
- **API Key错误**：确保`OPENROUTER_API_KEY`设置正确
- **网络问题**：Step1的browser_use可能需要稳定网络连接
- **依赖缺失**：确保所有Python依赖包已安装
- **权限问题**：确保对输出目录有写入权限

### 4. 故障排除
1. 检查环境变量设置
2. 查看具体的日志文件（每个测试都生成日志文件）
3. 单独运行失败的步骤进行调试
4. 检查网络连接状态

## 测试设计原则

1. **独立性**：每个步骤都能独立测试
2. **可靠性**：有fallback机制，避免外部依赖导致测试失败
3. **效率性**：限制数据量，快速完成测试
4. **可观测性**：详细的日志和状态报告
5. **实用性**：测试结果可用于验证真实业务流程

这个测试套件确保了XHS Note Analyzer的每个核心功能都能正常工作，并提供了完整的端到端测试验证。