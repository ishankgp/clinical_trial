# 🏥 Clinical Trial Analysis System

A comprehensive AI-powered system for analyzing clinical trials using OpenAI's reasoning models and Model Context Protocol (MCP).

## 🚀 Features

- **AI-Driven Search**: Uses OpenAI's reasoning models (o3-mini) for intelligent natural language query understanding
- **MCP Integration**: Model Context Protocol for standardized AI tool access
- **Direct API Integration**: Fetches real trial data from ClinicalTrials.gov API
- **Web Interface**: Streamlit-based UI for easy interaction
- **Database Management**: SQLite database for storing and querying trial data
- **Advanced Analysis**: Multi-model analysis with reasoning capabilities

## 🏗️ Architecture

```
clinical_trial/
├── src/
│   ├── analysis/          # AI analysis modules
│   ├── database/          # Database management
│   ├── mcp/              # Model Context Protocol servers
│   ├── ui/               # Streamlit web interface
│   └── utils/            # Utility functions
├── data/                 # Data storage
├── docs/                 # Documentation
├── tests/                # Test files
└── config/               # Configuration files
```

## 🛠️ Installation

### Prerequisites

- Python 3.8+
- OpenAI API key
- Git

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd clinical_trial
   ```

2. **Install dependencies**
   ```bash
   pip install -r config/requirements.txt
   pip install -r config/requirements_ui.txt
   ```

3. **Environment setup**
   ```bash
   python setup_env.py
   ```

4. **Configure API keys**
   Create a `.env` file in the root directory:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   ```

## 🚀 Usage

### Quick Start

1. **Start the web interface**
   ```bash
   python main.py ui
   ```

2. **Open your browser**
   Navigate to `http://localhost:8502`

3. **Start analyzing trials**
   Use the chat interface to ask questions like:
   - "Find diabetes trials"
   - "Compare Phase 3 cancer immunotherapy trials"
   - "Show me recruiting bladder cancer trials"

### Command Line Interface

```bash
# Setup and configuration
python main.py setup

# Start web interface
python main.py ui

# Process all trials
python main.py process

# Populate database with trials
python main.py populate

# Run tests
python main.py test

# Test reasoning models
python main.py test-reasoning

# Test MCP functionality
python main.py test-mcp-query
python main.py test-mcp-chat
```

## 🤖 AI Features

### Reasoning Models
- **o3-mini**: Default reasoning model for complex analysis
- **o3**: Advanced reasoning for detailed insights
- **o4-mini**: Latest reasoning capabilities

### Natural Language Understanding
The system uses AI to understand complex queries:
- "Find diabetes trials with semaglutide"
- "Compare Phase 3 cancer immunotherapy trials"
- "What bladder cancer trials are recruiting?"

### MCP Tools
- `search_trials`: Intelligent trial search
- `smart_search`: Natural language search
- `get_trial_details`: Detailed trial information
- `store_trial`: Add new trials to database
- `reasoning_query`: Advanced reasoning analysis

## 📊 Database Schema

The system uses a SQLite database with the following main table:

```sql
CREATE TABLE clinical_trials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nct_id TEXT UNIQUE NOT NULL,
    trial_name TEXT,
    trial_phase TEXT,
    trial_status TEXT,
    patient_enrollment INTEGER,
    sponsor TEXT,
    primary_endpoints TEXT,
    secondary_endpoints TEXT,
    inclusion_criteria TEXT,
    exclusion_criteria TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🔧 Configuration

### Environment Variables
- `OPENAI_API_KEY`: Your OpenAI API key
- `DATABASE_PATH`: Path to SQLite database (default: clinical_trials.db)
- `CACHE_DIR`: Cache directory for API responses

### Model Configuration
- Default reasoning model: `o3-mini`
- Token limits: 1500 for completion tokens
- Temperature: 0.1 for consistent results

## 🧪 Testing

### Run All Tests
```bash
python main.py test
```

### Test Specific Components
```bash
# Test reasoning models
python main.py test-reasoning

# Test MCP server
python main.py test-mcp-query

# Test MCP chat
python main.py test-mcp-chat
```

### Manual Testing
```bash
# Test UI functionality
python quick_ui_test.py
```

## 📚 Documentation

- [MCP Implementation Guide](docs/MCP_IMPLEMENTATION_SUMMARY.md)
- [UI Improvements Summary](docs/UI_IMPROVEMENTS_SUMMARY.md)
- [Reasoning Model Guide](docs/REASONING_MODEL_IMPROVEMENTS.md)
- [Troubleshooting](docs/CHAT_ASSISTANT_TROUBLESHOOTING.md)

## 🔍 API Integration

### ClinicalTrials.gov API
- Direct integration with `https://clinicaltrials.gov/api/v2/studies`
- Real-time trial data fetching
- Automatic data processing and storage

### OpenAI API
- Reasoning model integration
- Natural language processing
- Advanced query understanding

## 🚀 Deployment

### Local Development
```bash
python main.py ui
```

### Production Considerations
- Use environment variables for API keys
- Set up proper database backups
- Configure logging levels
- Use HTTPS in production

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the [troubleshooting guide](docs/CHAT_ASSISTANT_TROUBLESHOOTING.md)
2. Review the [documentation](docs/)
3. Open an issue on GitHub

## 🎯 Roadmap

- [ ] Add more reasoning models
- [ ] Implement trial comparison features
- [ ] Add statistical analysis tools
- [ ] Enhance UI with advanced visualizations
- [ ] Add support for more data sources
- [ ] Implement real-time trial monitoring

---

**Built with ❤️ using OpenAI's reasoning models and Model Context Protocol**

Updated on 22nd July
