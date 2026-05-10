#!/usr/bin/env python3
"""
Global Patent Intelligence Data Pipeline - Main Entry Point
Orchestrates the complete patent data processing pipeline
"""

import sys
import os
from pathlib import Path
import argparse
from datetime import datetime

# Add scripts directory to path
sys.path.append(str(Path(__file__).parent / "scripts"))

from data_downloader import PatentDataDownloader
from data_cleaner import PatentDataCleaner
from database_setup import PatentDatabase
from analysis_queries import PatentAnalyzer
from report_generator import ReportGenerator
from course_report_generator import CourseReportGenerator

class PatentIntelligencePipeline:
    def __init__(self, project_dir=None):
        if project_dir is None:
            project_dir = Path(__file__).parent
        else:
            project_dir = Path(project_dir)
            
        self.project_dir = project_dir
        self.data_dir = project_dir / "data"
        self.scripts_dir = project_dir / "scripts"
        self.database_dir = project_dir / "database"
        self.reports_dir = project_dir / "reports"
        
        # Initialize components
        self.downloader = PatentDataDownloader(str(self.data_dir))
        self.cleaner = PatentDataCleaner(str(self.data_dir))
        self.database = PatentDatabase(str(self.database_dir / "patent_intelligence.db"))
        self.analyzer = PatentAnalyzer(str(self.database_dir / "patent_intelligence.db"))
        self.generator = ReportGenerator(str(self.database_dir / "patent_intelligence.db"), str(self.reports_dir))
        self.course_generator = CourseReportGenerator(str(self.database_dir / "patent_intelligence.db"), str(self.reports_dir))
        
    def run_full_pipeline(self):
        """Run the complete patent intelligence pipeline"""
        print("=" * 80)
        print("GLOBAL PATENT INTELLIGENCE DATA PIPELINE")
        print("=" * 80)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Project Directory: {self.project_dir}")
        print()
        
        try:
            # Step 1: Download/Generate Data
            print("STEP 1: DATA ACQUISITION")
            print("-" * 40)
            sample_df = self.downloader.create_sample_data()
            if sample_df is None:
                print("Failed to create sample data")
                return False
            print("[OK] Data acquisition completed")
            print()
            
            # Step 2: Clean Data
            print("STEP 2: DATA CLEANING")
            print("-" * 40)
            cleaned_df, summary, validation = self.cleaner.run_full_cleaning_pipeline()
            if cleaned_df is None:
                print("Failed to clean data")
                return False
            print("[OK] Data cleaning completed")
            print()
            
            # Step 3: Setup Database
            print("STEP 3: DATABASE SETUP")
            print("-" * 40)
            db_stats = self.database.run_database_setup()
            if db_stats is None:
                print("Failed to setup database")
                return False
            print("[OK] Database setup completed")
            print()
            
            # Step 4: Run Analysis
            print("STEP 4: DATA ANALYSIS")
            print("-" * 40)
            analysis_summary = self.analyzer.generate_summary_report()
            if analysis_summary is None:
                print("Failed to run analysis")
                return False
            print("[OK] Data analysis completed")
            print()
            
            # Step 5: Generate Reports
            print("STEP 5: REPORT GENERATION")
            print("-" * 40)
            self.generator.generate_all_reports()
            print("[OK] Standard reports completed")
            
            # Step 6: Generate Course-Required Reports
            print("STEP 6: COURSE REPORT GENERATION")
            print("-" * 40)
            self.course_generator.generate_all_reports()
            print("[OK] Course reports completed")
            print()
            
            # Final Summary
            print("=" * 80)
            print("PIPELINE COMPLETED SUCCESSFULLY!")
            print("=" * 80)
            print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Total Patents Processed: {len(cleaned_df)}")
            print(f"Reports Generated: {len(list(self.reports_dir.glob('*.csv'))) + len(list(self.reports_dir.glob('*.json')))}")
            print(f"Database Location: {self.database_dir / 'patent_intelligence.db'}")
            print(f"Reports Location: {self.reports_dir}")
            print()
            print("Next Steps:")
            print("1. Review the generated reports in the 'reports' directory")
            print("2. Open the database with any SQLite client for custom queries")
            print("3. Use the analysis_queries.py script for additional analysis")
            print("4. Customize the pipeline for your specific needs")
            
            return True
            
        except Exception as e:
            print(f"Pipeline failed with error: {e}")
            return False
    
    def run_step(self, step_name):
        """Run a specific step of the pipeline"""
        steps = {
            "download": self._run_download,
            "clean": self._run_cleaning,
            "database": self._run_database_setup,
            "analyze": self._run_analysis,
            "reports": self._run_reports
        }
        
        if step_name.lower() not in steps:
            print(f"Unknown step: {step_name}")
            print(f"Available steps: {', '.join(steps.keys())}")
            return False
            
        return steps[step_name.lower()]()
    
    def _run_download(self):
        """Run data download step"""
        print("Running data download...")
        df = self.downloader.create_sample_data()
        return df is not None
    
    def _run_cleaning(self):
        """Run data cleaning step"""
        print("Running data cleaning...")
        result = self.cleaner.run_full_cleaning_pipeline()
        return result[0] is not None
    
    def _run_database_setup(self):
        """Run database setup step"""
        print("Running database setup...")
        stats = self.database.run_database_setup()
        return stats is not None
    
    def _run_analysis(self):
        """Run analysis step"""
        print("Running data analysis...")
        summary = self.analyzer.generate_summary_report()
        return summary is not None
    
    def _run_reports(self):
        """Run report generation step"""
        print("Running report generation...")
        self.generator.generate_all_reports()
        return True

def main():
    parser = argparse.ArgumentParser(description="Global Patent Intelligence Data Pipeline")
    parser.add_argument("--step", choices=["download", "clean", "database", "analyze", "reports"], 
                       help="Run specific pipeline step")
    parser.add_argument("--project-dir", help="Project directory path")
    
    args = parser.parse_args()
    
    # Initialize pipeline
    pipeline = PatentIntelligencePipeline(args.project_dir)
    
    if args.step:
        # Run specific step
        success = pipeline.run_step(args.step)
        sys.exit(0 if success else 1)
    else:
        # Run full pipeline
        success = pipeline.run_full_pipeline()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
