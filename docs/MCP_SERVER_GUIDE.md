# Clinical Trial MCP Server - Complete Guide

## 🎯 Overview

The Clinical Trial MCP (Model Context Protocol) Server provides a comprehensive solution for storing, analyzing, and querying multiple clinical trials. It integrates with OpenAI models for intelligent analysis and offers powerful search capabilities across trial databases.

## 🚀 Key Features

### **1. Multi-Trial Storage & Analysis**
- Store clinical trials from JSON files or NCT IDs
- Analyze trials with different OpenAI models (GPT-4o, GPT-4o-mini, o4-mini, GPT-4, LLM)
- Force reanalysis of existing trials
- Automatic metadata tracking

### **2. Advanced Search Capabilities**
- **Flexible Filters**: Search by drug, indication, phase, status, sponsor, etc.
- **Natural Language Queries**: Smart search that interprets user intent
- **Range Queries**: Filter by enrollment numbers, dates, etc.
- **Multiple Output Formats**: Table, JSON, or summary views

### **3. Trial Comparison & Analysis**
- Side-by-side comparison of multiple trials
- Statistical analysis grouped by various criteria
- Export functionality (CSV/JSON)
- Detailed trial information retrieval

### **4. Intelligent Query Processing**
- Natural language understanding
- Context-aware search suggestions
- Automated data extraction and formatting
- Error handling and validation

## 🏗️ Architecture

### **Core Components**

```
Clinical Trial MCP Server
├── MCP Server (clinical_trial_mcp_server.py)
│   ├── Tool Registration
│   ├── Request Handling
│   └── Response Formatting
├── Database Layer (clinical_trial_database.py)
│   ├── SQLite Storage
│   ├── Query Processing
│   └── Data Export
├── Analysis Layer
│   ├── ClinicalTrialAnalyzerReasoning
│   ├── ClinicalTrialAnalyzerLLM
│   └── Model Integration
└── Chat Interface (clinical_trial_chat_mcp.py)
    ├── OpenAI Integration
    ├── Function Calling
    └── Conversation Management
```

### **Data Flow**

1. **Input**: User query or trial data
2. **Processing**: MCP server routes to appropriate tool
3. **Analysis**: OpenAI models analyze trial data
4. **Storage**: Results stored in SQLite database
5. **Response**: Formatted results returned to user

## 🛠️ Installation & Setup

### **1. Install Dependencies**
```bash
pip install -r requirements_ui.txt
```

### **2. Environment Configuration**
Create a `.env` file:
```bash
OPENAI_API_KEY=your-api-key-here
```

### **3. Database Setup**
The database is automatically created when you first run the server:
```bash
python clinical_trial_mcp_server.py
```

## 📋 Available Tools

### **1. store_trial**
Store and analyze a clinical trial.

**Parameters:**
- `nct_id` (required): NCT ID of the trial
- `json_file_path` (optional): Path to JSON file
- `analyze_with_model` (optional): Model to use (default: gpt-4o-mini)
- `force_reanalyze` (optional): Force reanalysis (default: false)

**Example:**
```json
{
  "nct_id": "NCT07046273",
  "json_file_path": "NCT07046273.json",
  "analyze_with_model": "gpt-4o-mini"
}
```

### **2. search_trials**
Search clinical trials with flexible filters.

**Parameters:**
- `query` (optional): Natural language search query
- `filters` (optional): Specific filters object
- `limit` (optional): Maximum results (default: 50)
- `format` (optional): Output format (table/json/summary)

**Example:**
```json
{
  "query": "Find diabetes trials with semaglutide",
  "filters": {
    "indication": "diabetes",
    "primary_drug": "semaglutide",
    "trial_phase": "PHASE3"
  },
  "limit": 20,
  "format": "table"
}
```

### **3. get_trial_details**
Get detailed information about a specific trial.

**Parameters:**
- `nct_id` (required): NCT ID of the trial
- `include_raw_data` (optional): Include raw JSON (default: false)

**Example:**
```json
{
  "nct_id": "NCT07046273",
  "include_raw_data": false
}
```

### **4. compare_trials**
Compare multiple clinical trials side by side.

**Parameters:**
- `nct_ids` (required): Array of NCT IDs to compare
- `fields` (optional): Specific fields to compare
- `format` (optional): Output format (table/json)

**Example:**
```json
{
  "nct_ids": ["NCT07046273", "NCT04895709"],
  "fields": ["trial_phase", "primary_drug", "indication"],
  "format": "table"
}
```

### **5. get_trial_statistics**
Generate statistical analysis of trial data.

**Parameters:**
- `group_by` (optional): Grouping criteria (phase/status/sponsor/indication/primary_drug)
- `include_charts` (optional): Include visualizations (default: true)

**Example:**
```json
{
  "group_by": "phase",
  "include_charts": true
}
```

### **6. smart_search**
Intelligent natural language search.

**Parameters:**
- `query` (required): Natural language query
- `limit` (optional): Maximum results (default: 10)
- `format` (optional): Output format (table/json/summary)

**Example:**
```json
{
  "query": "Find all phase 3 recruiting trials for diabetes",
  "limit": 15,
  "format": "summary"
}
```

### **7. get_trials_by_drug**
Find all trials for a specific drug.

**Parameters:**
- `drug_name` (required): Name of the drug
- `include_similar` (optional): Include similar names (default: true)
- `limit` (optional): Maximum results (default: 20)

**Example:**
```json
{
  "drug_name": "semaglutide",
  "include_similar": true,
  "limit": 25
}
```

### **8. get_trials_by_indication**
Find all trials for a specific indication.

**Parameters:**
- `indication` (required): Disease indication
- `include_similar` (optional): Include similar indications (default: true)
- `limit` (optional): Maximum results (default: 20)

**Example:**
```json
{
  "indication": "diabetes",
  "include_similar": true,
  "limit": 30
}
```

### **9. export_trials**
Export trial data to CSV or JSON format.

**Parameters:**
- `format` (optional): Export format (csv/json)
- `filters` (optional): Filters to apply
- `filename` (optional): Output filename

**Example:**
```json
{
  "format": "csv",
  "filters": {
    "trial_phase": "PHASE3",
    "trial_status": "RECRUITING"
  },
  "filename": "phase3_recruiting_trials.csv"
}
```

## 💬 Chat Interface Usage

### **Starting the Chat Interface**
```bash
python clinical_trial_chat_mcp.py
```

### **Example Conversations**

**Store a Trial:**
```
You: Store the trial NCT07046273 from the JSON file
Assistant: I'll store trial NCT07046273 for you using the gpt-4o-mini model for analysis.
✅ Successfully stored trial NCT07046273 using gpt-4o-mini model
```

**Search for Trials:**
```
You: Find all diabetes trials with semaglutide
Assistant: I'll search for diabetes trials involving semaglutide.
🔍 Found 5 trials matching: Find all diabetes trials with semaglutide
```

**Compare Trials:**
```
You: Compare NCT07046273 and NCT04895709
Assistant: I'll compare those two trials for you.
📊 Compared 2 trials: NCT07046273, NCT04895709
```

**Get Statistics:**
```
You: Show me statistics grouped by trial phase
Assistant: I'll generate statistics grouped by trial phase.
📈 Generated statistics grouped by phase
```

## 🧪 Testing

### **Run Test Suite**
```bash
python test_mcp_server.py
```

### **Test Individual Components**
```bash
# Test MCP server
python clinical_trial_mcp_server.py

# Test chat interface
python clinical_trial_chat_mcp.py

# Test database operations
python populate_database.py
```

## 📊 Database Schema

### **Main Tables**

1. **clinical_trials**: Core trial information
2. **drug_info**: Drug-related data
3. **clinical_info**: Clinical trial details
4. **biomarker_info**: Biomarker information
5. **analysis_metadata**: Analysis tracking

### **Key Fields**
- `nct_id`: Unique trial identifier
- `trial_name`: Trial name/title
- `trial_phase`: Trial phase (PHASE1, PHASE2, PHASE3, etc.)
- `trial_status`: Current status (RECRUITING, COMPLETED, etc.)
- `primary_drug`: Main investigational drug
- `indication`: Disease indication
- `sponsor`: Trial sponsor
- `patient_enrollment`: Enrollment numbers

## 🔧 Configuration Options

### **Model Selection**
- **gpt-4o**: Fast, JSON schema support
- **gpt-4o-mini**: Very fast, cost-effective
- **o4-mini**: Reasoning-optimized
- **gpt-4**: Legacy, comprehensive
- **llm**: LLM-based analysis

### **Output Formats**
- **table**: Markdown table format
- **json**: Structured JSON data
- **summary**: Statistical summary

### **Search Filters**
- Drug name, indication, phase, status
- Sponsor, enrollment ranges, dates
- Line of therapy, biomarkers
- Geographic location, trial type

## 🚀 Performance Optimization

### **Caching Strategy**
- Trial data cached locally
- Analysis results stored in database
- API response caching
- Incremental updates

### **Batch Processing**
- Multiple trial analysis
- Bulk data export
- Parallel processing where possible
- Rate limiting for API calls

## 🔒 Security & Error Handling

### **Input Validation**
- NCT ID format validation
- JSON file integrity checks
- Parameter type validation
- SQL injection prevention

### **Error Recovery**
- Graceful API failure handling
- Database connection recovery
- Partial result return
- Detailed error logging

## 📈 Monitoring & Logging

### **Log Levels**
- INFO: Normal operations
- WARNING: Potential issues
- ERROR: Operation failures
- DEBUG: Detailed debugging

### **Metrics Tracking**
- API call counts
- Response times
- Success/failure rates
- Database performance

## 🔮 Future Enhancements

### **Planned Features**
- Real-time trial updates
- Advanced analytics dashboard
- Machine learning insights
- Integration with external APIs
- Multi-language support

### **Scalability Improvements**
- Distributed database support
- API rate limiting
- Advanced caching
- Load balancing
- Microservices architecture

## 🆘 Troubleshooting

### **Common Issues**

**1. MCP Library Not Found**
```bash
pip install mcp
```

**2. OpenAI API Key Missing**
```bash
# Create .env file
echo "OPENAI_API_KEY=your-key-here" > .env
```

**3. Database Connection Error**
```bash
# Check file permissions
ls -la clinical_trials.db
```

**4. Server Won't Start**
```bash
# Check port availability
netstat -an | grep 8501
```

### **Debug Mode**
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python clinical_trial_mcp_server.py
```

## 📚 API Reference

### **MCP Protocol**
- JSON-RPC 2.0 compliant
- Async/await support
- Tool registration
- Error handling

### **OpenAI Integration**
- Function calling
- Model selection
- Token management
- Response formatting

### **Database Operations**
- CRUD operations
- Complex queries
- Data export
- Schema management

---

## 🎉 Getting Started

1. **Install dependencies**: `pip install -r requirements_ui.txt`
2. **Set up environment**: Create `.env` file with API key
3. **Start server**: `python clinical_trial_mcp_server.py`
4. **Test chat**: `python clinical_trial_chat_mcp.py`
5. **Run tests**: `python test_mcp_server.py`

**Ready to analyze clinical trials at scale! 🚀🏥📊** 