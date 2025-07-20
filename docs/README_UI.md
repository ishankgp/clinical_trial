# Clinical Trial Analysis Tool - Web UI

A modern, interactive web interface for analyzing clinical trials and comparing different OpenAI models.

## 🚀 Features

### 📊 Single Trial Analysis
- Upload JSON files or enter NCT IDs
- Choose from multiple OpenAI models (GPT-4o, GPT-4o-mini, o4-mini, GPT-4)
- Real-time analysis with progress tracking
- Comprehensive results display with categorized tabs
- Download results as CSV

### 🧪 Model Comparison Testing
- Test multiple models on the same trial data
- Comprehensive tabular comparison with all key fields
- Performance metrics (speed, quality, field counts)
- Summary statistics (averages, fastest, best quality)
- Optional individual model result viewing
- Batch analysis capabilities

### 📈 Results History
- View recent analysis files
- System status monitoring
- Cache management
- File download history

## 🛠️ Installation

1. **Install Dependencies:**
   ```bash
   pip install -r requirements_ui.txt
   ```

2. **Set up Environment:**
   Create a `.env` file in the project root:
   ```
   OPENAI_API_KEY=your-openai-api-key-here
   ```

3. **Run the Application:**
   ```bash
   python run_ui.py
   ```
   
   Or directly with Streamlit:
   ```bash
   streamlit run app.py
   ```

## 🎯 Usage

### Single Trial Analysis
1. Go to the "Single Trial Analysis" tab
2. Choose input method:
   - Upload JSON file
   - Enter NCT ID
   - Use sample file (NCT07046273.json)
3. Select your preferred OpenAI model
4. Click "Start Analysis"
5. View results in organized tabs
6. Download results as CSV

### Model Comparison
1. Go to the "Model Comparison" tab
2. Configure test data (same options as single analysis)
3. Select multiple models to compare
4. Click "Run Model Comparison"
5. View comprehensive comparison table with all metrics
6. Optionally view individual model results
7. Download comparison report

### Results History
- View recent analysis files
- Check system status
- Monitor cache usage

## 📊 Supported Models

| Model | JSON Schema | Reasoning | Speed | Cost |
|-------|-------------|-----------|-------|------|
| GPT-4o | ✅ | ✅ | Fast | Medium |
| GPT-4o-mini | ✅ | ✅ | Very Fast | Low |
| o4-mini | ✅ | ✅ | Very Fast | Low |
| GPT-4 | ❌ | ✅ | Slow | High |

## 🎨 UI Features

- **Responsive Design:** Works on desktop and mobile
- **Real-time Updates:** Live progress tracking
- **Comprehensive Tables:** Detailed tabular comparisons
- **Organized Results:** Categorized display tabs
- **Error Handling:** User-friendly error messages
- **File Management:** Easy upload and download

## 🔧 Technical Details

### Architecture
- **Frontend:** Streamlit (Python web framework)
- **Charts:** Plotly for interactive visualizations
- **Data Processing:** Pandas for data manipulation
- **AI Models:** OpenAI API integration
- **File Handling:** Local file system with caching

### Performance
- **Caching:** Automatic caching of API responses
- **Parallel Processing:** Model comparison runs sequentially for stability
- **Memory Management:** Efficient data handling for large files
- **Error Recovery:** Graceful handling of API failures

## 🐛 Troubleshooting

### Common Issues

1. **"OpenAI API Key not found"**
   - Ensure `.env` file exists with correct API key
   - Check file permissions

2. **"Missing dependencies"**
   - Run: `pip install -r requirements_ui.txt`
   - Check Python version (3.8+ required)

3. **"Sample file not found"**
   - Ensure `NCT07046273.json` exists in project root
   - Or upload your own JSON file

4. **"Model not available"**
   - Check your OpenAI API access level
   - Some models may require specific API access

### Performance Tips

- Use GPT-4o-mini for faster analysis
- Enable caching for repeated analyses
- Close unused browser tabs to free memory
- Use smaller JSON files for quicker processing

## 📝 File Structure

```
clinical_trial/
├── app.py                 # Main Streamlit application
├── run_ui.py             # Launcher script
├── requirements_ui.txt   # UI dependencies
├── README_UI.md         # This file
├── .env                 # Environment variables
├── NCT07046273.json    # Sample trial data
└── cache/              # Cached API responses
```

## 🔄 Updates

- **v1.0:** Initial release with basic analysis
- **v1.1:** Added model comparison features
- **v1.2:** Enhanced UI with charts and history
- **v1.3:** Added o4-mini model support

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the technical documentation
3. Open an issue on GitHub
4. Contact the development team

---

**Happy Analyzing! 🏥📊** 