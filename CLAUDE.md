# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **XHS Note Analyzer** (小红书笔记分析器) - an intelligent content analysis tool that helps content creators quickly produce high-quality content by analyzing excellent XiaoHongShu (Little Red Book) notes. The project uses **CrewAI Flow + browser_use + MediaCrawler** to create a comprehensive four-step analysis and strategy pipeline.

## Architecture

### Core Technologies
- **CrewAI Flow**: Orchestrates the four-step analysis and strategy pipeline
- **browser_use**: Automated browser agent for note discovery on XiaoHongShu ad platform
- **MediaCrawler API**: Fetches detailed note content from XiaoHongShu
- **Multi-modal LLM**: Analyzes content and generates actionable strategies

### Four-Step Analysis and Strategy Pipeline

1. **Note Discovery** (`tools/hot_note_finder_tool.py`)
   - Uses browser_use agent to automatically find related high-quality notes
   - Navigates XiaoHongShu Jiguang (spotlight) platform
   - Implements precise element locators and state management

2. **Content Fetching** (`tools/mediacrawler_client.py`)
   - Retrieves detailed note content via MediaCrawler API
   - Handles batch processing for multiple notes
   - Processes images, videos, author info, and interaction data

3. **Content Analysis** (`crews/content_analyzer_crew/`)
   - Uses multi-modal LLM (Claude 3.5 Sonnet) for deep analysis
   - **Three-dimensional analysis**:
     - Content Structure Analysis (title, opening, framework, ending)
     - Emotional Value Analysis (pain points, value propositions, triggers)
     - Visual Element Analysis (image style, color scheme, layout)
   - Generates structured analysis reports and success patterns

4. **Strategy Making** (`crews/strategy_maker_crew/`)
   - Creates actionable content strategies based on analysis results
   - **Three strategic dimensions**:
     - Topic Strategy (trending topics, keyword clusters, competition analysis)
     - Target Audience Strategy (user personas, needs analysis, engagement tactics)
     - Content Creation Guide (copywriting templates, visual guidelines, video scripts)
   - Outputs comprehensive strategy reports and implementation guidance

## Key Files and Structure

### Main Flow Controller
- `src/xhs_note_analyzer/main.py` - Main CrewAI Flow implementation with four-step pipeline
- `run_analysis.py` - Interactive script for running analysis with different scenarios

### Tools and Utilities
- `src/xhs_note_analyzer/tools/hot_note_finder_tool.py` - Step1: Note discovery tool
- `src/xhs_note_analyzer/tools/mediacrawler_client.py` - Step2: MediaCrawler API client

### CrewAI Components
- `src/xhs_note_analyzer/crews/content_analyzer_crew/` - Step3: Three-dimensional content analysis
- `src/xhs_note_analyzer/crews/strategy_maker_crew/` - Step4: Strategic planning and guidance
- Each crew has `config/agents.yaml` and `config/tasks.yaml` for configuration

### Browser Automation (Optional)
- `src/xhs_note_analyzer/browser_agent/` - Alternative browser automation approach
- Uses XiaoHongShu authentication stored in `xiaohongshu_auth.json`

## Common Development Commands

### Environment Setup
```bash
# Install dependencies
pip install -r xhs_note_analyzer/requirements.txt

# Install the package in development mode
cd xhs_note_analyzer
pip install -e .
```

### Running the Application
```bash
# Run the interactive analysis script (recommended for beginners)
python xhs_note_analyzer/run_analysis.py

# Run the main flow programmatically
python xhs_note_analyzer/src/xhs_note_analyzer/main.py

# Use the project scripts (defined in pyproject.toml)
kickoff  # Main analysis flow
run_crew  # Alternative to kickoff
plot     # Generate flow diagram

# Quick function call for programmatic use
python -c "from xhs_note_analyzer.main import kickoff_content_analysis; kickoff_content_analysis('your_target', 'your_context')"
```

### Testing Components
```bash
# Test MediaCrawler client (Step2)
python xhs_note_analyzer/src/xhs_note_analyzer/tools/mediacrawler_client.py

# Test content analysis (Step3)
python xhs_note_analyzer/src/xhs_note_analyzer/crews/content_analyzer_crew/content_analyzer_crew.py

# Test strategy making (Step4)
python xhs_note_analyzer/src/xhs_note_analyzer/crews/strategy_maker_crew/strategy_maker_crew.py
```

### Dependency Management
```bash
# Check all dependencies are defined in requirements.txt
pip install -r xhs_note_analyzer/requirements.txt

# Update dependencies (requires manual review)
pip list --outdated
```

## Environment Configuration

### Required Environment Variables
```bash
# OpenRouter API for LLM services (required for all LLM operations)
export OPENROUTER_API_KEY="your_openrouter_api_key"
```

### Environment File Setup
```bash
# Copy and configure environment file
cp xhs_note_analyzer/env.example xhs_note_analyzer/.env
# Edit .env file with your actual API keys and configuration
```

### Optional Environment Variables
```bash
# MediaCrawler API configuration
export MEDIACRAWLER_API_ENDPOINT="http://localhost:8000"
export MEDIACRAWLER_API_KEY="your_api_key"
```

### MediaCrawler API Server Setup
```bash
# Clone and setup MediaCrawler API server
git clone https://github.com/BradLeon/MediaCrawler-API-Server.git
cd MediaCrawler-API-Server
git checkout Api-server-branch
python app/main.py
```

## Development Guidelines

### Working with CrewAI Flow
- Main flow is defined in `XHSContentAnalysisFlow` class in `main.py`
- **Four sequential steps**: Note Discovery → Content Fetching → Content Analysis → Strategy Making
- Each step is decorated with `@listen()` and follows sequential execution
- State management is handled through `XHSContentAnalysisState` Pydantic model
- Use `flow.kickoff()` to execute the complete pipeline
- Flow supports both mock data (for testing) and real API calls
- **Business goals input**: Support for custom business context and goals
- Key implementation areas: hot note discovery, MediaCrawler API integration, multi-dimensional analysis, and strategic planning

### Project Dependencies
- **CrewAI >= 0.70.0**: Core framework for multi-agent workflows
- **browser-use >= 1.5.0**: Browser automation for XHS platform navigation
- **langchain-openai**: LLM integration via OpenRouter
- **pydantic >= 2.0.0**: Data validation and settings management
- **playwright >= 1.40.0**: Browser automation backend

### Browser Automation Development
- Custom controller actions are defined in `create_precision_controller()`
- Use `ActionStateManager` for state management between actions
- Authentication state is persisted in `xiaohongshu_auth.json`
- Debug information is saved to `output/debug/` directory
- Browser agent uses Chrome browser with specific profile settings
- Supports both headless and visual modes for debugging
- Critical actions: `navigate_and_login_xiaohongshu_ad_platform`, `get_core_note_titles`, `extract_related_titles`, `process_all_related_notes`

### Adding New Analysis Dimensions
1. Create new agent in `ContentAnalyzerCrew` (`crews/content_analyzer_crew/`)
2. Define corresponding task in `config/tasks.yaml`
3. Update analysis models in `models.py`
4. Update analysis parsing logic in the crew implementation

### Adding New Strategy Dimensions
1. Create new agent in `StrategyMakerCrew` (`crews/strategy_maker_crew/`)
2. Define corresponding task in `config/tasks.yaml`
3. Update strategy models in `models.py`
4. Update strategy integration logic in `_integrate_strategy_results()`

### Integrating New Data Sources
1. Create new client in `tools/` directory
2. Implement proper data validation with Pydantic models
3. Update flow logic in `main.py` to handle new data source
4. Add error handling and fallback mechanisms

## Output and Results

### Generated Files
**Step3 - Content Analysis:**
- `output/content_analysis_results.json` - Detailed analysis data
- `output/content_analysis_report.md` - Professional markdown report
- `output/content_analysis_summary.txt` - Human-readable summary

**Step4 - Strategy Making:**
- `output/strategy_report.json` - Complete strategy data
- `output/strategy_report.md` - Professional strategy report
- `output/strategy_summary.txt` - Strategy implementation summary

**Complete Flow:**
- `output/xhs_content_analysis_result.json` - Complete pipeline state
- `output/analysis_summary.txt` - Full workflow summary

### Analysis and Strategy Results Include
**Content Analysis (Step3):**
- Three-dimensional analysis results (structure, emotional, visual)
- Success factors identification and patterns
- Comprehensive scoring and evaluation
- Replicable content formulas

**Strategy Making (Step4):**
- Topic strategy with trending and evergreen suggestions
- Target audience personas and engagement tactics
- Content creation guides (copywriting, visual, video)
- Actionable recommendations and differentiation points

## Performance and Monitoring

### Execution Logging
- Complete conversation history saved to `output/debug/conversation/`
- Browser automation recorded as GIF in `output/debug/debug_execution.gif`
- State management logs for debugging action sequences

### Error Handling
- Graceful fallback to mock data if APIs are unavailable
- Emergency backup system for collected data
- Comprehensive error logging and state recovery

## API Integration Notes

### MediaCrawler API
- Reference: [API Documentation](https://github.com/BradLeon/MediaCrawler-API-Server/blob/Api-server-branch/API接口规范文档.md)
- Supports batch note crawling and Supabase storage
- Provides content caching to avoid duplicate requests

### LLM Configuration
- Default model: `anthropic/claude-3.5-sonnet` for content analysis
- Alternative models: `google/gemini-2.5-flash` for planning tasks
- All models accessed through OpenRouter API

## Security and Authentication

### XiaoHongShu Authentication
- Browser session state persisted in `xiaohongshu_auth.json`
- Credentials configured in `sensitive_data` dictionary
- Support for headless and visual debugging modes

### API Security
- MediaCrawler API supports optional authentication
- Environment variables used for all sensitive configuration
- No hardcoded credentials in source code

## Compact Deployment Mode

- Supports `/compact` mode for lightweight, resource-efficient deployment
- Reduces computational and memory overhead
- Optimizes for low-resource environments
- Minimizes external API calls and caching
- Provides streamlined analysis with core functionalities