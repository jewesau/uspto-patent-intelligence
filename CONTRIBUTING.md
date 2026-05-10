# Contributing to Patent Intelligence Pipeline

Thank you for your interest in contributing to this project! This document provides guidelines for contributors.

## How to Contribute

### Reporting Issues
- Use GitHub Issues to report bugs or request features
- Provide detailed description of the issue
- Include steps to reproduce if reporting a bug

### Making Changes
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests if applicable
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Code Style
- Follow PEP 8 for Python code
- Use descriptive variable and function names
- Add comments for complex logic
- Include docstrings for functions and classes

## Project Structure
```
patent_intelligence_pipeline/
├── data/              # Data files (raw and processed)
├── scripts/           # Python scripts for pipeline
├── database/          # SQLite database files
├── reports/           # Generated reports
├── tests/             # Unit tests (if added)
├── requirements.txt   # Python dependencies
├── main.py           # Main pipeline entry point
└── README.md         # Project documentation
```

## Development Setup
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run the pipeline: `python main.py`

## Data Sources
- USPTO PatentsView data
- Ensure compliance with data usage terms
- Do not commit large data files to the repository

## License
By contributing, you agree that your contributions will be licensed under the MIT License.
