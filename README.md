# USPTO Patent Intelligence Pipeline

## 🎯 **Project Overview**
A comprehensive data engineering pipeline for processing real USPTO patent data from the PatentsView database. This project demonstrates complete data intelligence capabilities from raw data extraction to interactive visualization.

## 🚀 Features
- **Automated Data Pipeline**: End-to-end processing of patent data
- **Data Cleaning**: Robust data validation and cleaning using pandas
- **SQL Database**: Normalized database design with proper relationships
- **Comprehensive Analysis**: Patent trends, inventor productivity, company performance
- **Multiple Output Formats**: CSV, JSON, and console reports
- **Modular Architecture**: Easy to extend and maintain

## 📊 Pipeline Steps
1. **Data Source** - Access USPTO PatentsView data
2. **Python Script** - Parse and process raw patent data
3. **Data Cleaning** - Handle missing values, standardize formats
4. **SQL Database** - Store in normalized database structure
5. **Analysis** - Extract insights using SQL queries
6. **Reporting** - Generate reports in multiple formats

## 🛠️ Tools Used
- **Python** - Data extraction and pipeline orchestration
- **pandas** - Data cleaning and manipulation
- **SQL** - Data storage and analysis
- **SQLite** - Database management
- **GitHub** - Version control and collaboration

## 📁 Project Structure
```
patent_intelligence_pipeline/
├── data/                  # Data storage
│   ├── raw/              # Raw downloaded data
│   └── processed/        # Cleaned processed data
├── scripts/              # Python pipeline modules
│   ├── data_downloader.py
│   ├── data_cleaner.py
│   ├── database_setup.py
│   ├── analysis_queries.py
│   └── report_generator.py
├── database/             # SQLite database files
├── reports/              # Generated analysis reports
├── tests/                # Unit tests (future)
├── main.py              # Pipeline entry point
├── requirements.txt     # Python dependencies
├── README.md           # This file
├── LICENSE             # MIT License
├── CONTRIBUTING.md     # Contribution guidelines
└── .gitignore         # Git ignore rules
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Installation
1. Clone the repository:
```bash
git clone https://github.com/yourusername/patent-intelligence-pipeline.git
cd patent-intelligence-pipeline
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the complete pipeline:
```bash
python main.py
```

### Running Individual Steps
You can run specific pipeline steps:
```bash
python main.py --step download    # Download/generate sample data
python main.py --step clean       # Clean and process data
python main.py --step database    # Setup database and load data
python main.py --step analyze     # Run analysis queries
python main.py --step reports     # Generate reports
```

## 📈 Data Extracted
- **Patent Information**: Titles, abstracts, dates, types
- **Inventor Details**: Names, collaboration patterns
- **Company Information**: Assignee organizations, performance metrics
- **Technology Categories**: CPC classification codes
- **Citation Data**: Patent citation counts and analysis

## 📊 Generated Reports
The pipeline generates comprehensive reports including:
- **Executive Summary**: Key statistics and insights
- **Patent Trends**: Year-over-year patent activity
- **Top Innovators**: Inventor productivity rankings
- **Company Analysis**: Patent performance by organization
- **Technology Categories**: Innovation trends by sector
- **Citation Analysis**: Patent impact metrics

## 🔧 Configuration

### Data Sources
The pipeline supports multiple data sources:
- **Sample Data**: Built-in sample patent data for testing
- **USPTO API**: Real-time data from PatentsView API
- **Bulk Downloads**: Processed USPTO bulk data files

### Database Configuration
Default SQLite database location: `database/patent_intelligence.db`

### Report Customization
Modify the `scripts/report_generator.py` to customize:
- Report formats and content
- Analysis metrics and KPIs
- Output destinations

## 🧪 Testing
```bash
# Run pipeline with sample data
python main.py

# Test individual components
python scripts/data_downloader.py
python scripts/data_cleaner.py
python scripts/database_setup.py
```

## 📝 Data Source
- **Primary Source**: PatentsView Granted Patent Disambiguated Data
- **URL**: https://data.uspto.gov/bulid/data/datasets/pvgrantdfileDataFromDate=1976-01-01&fileDataToDate=2025-09-30
- **Documentation**: PV_grant_data_dictionary.pdf
- **Coverage**: Patents from 1976 to present

## 🤝 Contributing
We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License
This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.

## 📚 Course Context
This project was developed for a data engineering course assignment focusing on building a complete data pipeline for patent intelligence analysis.

## 🔍 Sample Output
After running the pipeline, you'll find:
- **Database**: `database/patent_intelligence.db` with normalized patent data
- **Reports**: CSV and JSON files in `reports/` directory
- **Console Output**: Comprehensive analysis summary
- **Processed Data**: Cleaned datasets in `data/processed/`

## 🐛 Troubleshooting
- **Data Issues**: Ensure data files are properly downloaded and accessible
- **Database Errors**: Check file permissions and disk space
- **Import Errors**: Verify all dependencies are installed via `requirements.txt`

## 📞 Support
For issues and questions:
1. Check the troubleshooting section
2. Review the code comments and documentation
3. Open an issue on GitHub

---

**Built with ❤️ for data engineering and patent intelligence analysis**
