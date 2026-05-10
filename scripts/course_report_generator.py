#!/usr/bin/env python3
"""
Global Patent Intelligence Data Pipeline - Course Report Generator
Creates reports that match the exact course requirements:
1. Console Report (Total Patents, Top Inventors, Top Companies, Top Countries)
2. Exported Files: top_inventors.csv, top_companies.csv, country_trends.csv
3. JSON Report with specific structure
"""

import pandas as pd
import json
from pathlib import Path
from datetime import datetime
import sqlite3

class CourseReportGenerator:
    def __init__(self, db_path="../database/patent_intelligence.db", reports_dir="../reports"):
        self.db_path = Path(db_path)
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(exist_ok=True)
        
    def connect(self):
        """Establish database connection"""
        return sqlite3.connect(self.db_path)
    
    def get_top_inventors(self, limit=10):
        """Get top inventors by patent count"""
        conn = self.connect()
        query = '''
            SELECT 
                i.inventor_full_name as name,
                COUNT(pi.patent_number) as patents
            FROM inventors i
            JOIN patent_inventors pi ON i.id = pi.inventor_id
            WHERE i.inventor_full_name NOT LIKE '%Unknown%'
            GROUP BY i.inventor_full_name
            ORDER BY patents DESC
            LIMIT ?
        '''
        
        df = pd.read_sql_query(query, conn, params=(limit,))
        conn.close()
        return df
    
    def get_top_companies(self, limit=10):
        """Get top companies by patent count"""
        conn = self.connect()
        query = '''
            SELECT 
                c.company_name as name,
                COUNT(pc.patent_number) as patents
            FROM companies c
            JOIN patent_companies pc ON c.id = pc.company_id
            WHERE c.company_name NOT LIKE '%Unknown%'
            GROUP BY c.company_name
            ORDER BY patents DESC
            LIMIT ?
        '''
        
        df = pd.read_sql_query(query, conn, params=(limit,))
        conn.close()
        return df
    
    def get_top_countries(self, limit=10):
        """Get top countries by patent count"""
        conn = self.connect()
        query = '''
            SELECT 
                inventor_country as country,
                COUNT(*) as patents,
                ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM patents WHERE inventor_country IS NOT NULL), 2) as share
            FROM patents 
            WHERE inventor_country IS NOT NULL
            GROUP BY inventor_country
            ORDER BY patents DESC
            LIMIT ?
        '''
        
        df = pd.read_sql_query(query, conn, params=(limit,))
        conn.close()
        return df
    
    def get_country_trends(self):
        """Get country trends over time"""
        conn = self.connect()
        query = '''
            SELECT 
                inventor_country as country,
                patent_date_year as year,
                COUNT(*) as patent_count
            FROM patents 
            WHERE inventor_country IS NOT NULL AND patent_date_year IS NOT NULL
            GROUP BY inventor_country, patent_date_year
            ORDER BY year DESC, patent_count DESC
        '''
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    
    def get_total_patents(self):
        """Get total patent count"""
        conn = self.connect()
        query = 'SELECT COUNT(*) as total_patents FROM patents'
        result = pd.read_sql_query(query, conn)
        conn.close()
        return result.iloc[0]['total_patents']
    
    def generate_console_report(self):
        """Generate console report as required by course"""
        print("\n" + "="*60)
        print("PATENT INTELLIGENCE REPORT")
        print("="*60)
        
        # Total Patents
        total_patents = self.get_total_patents()
        print(f"\nTotal Patents: {total_patents}")
        
        # Top Inventors
        print("\nTop Inventors:")
        inventors_df = self.get_top_inventors(5)
        for _, row in inventors_df.iterrows():
            print(f"  {row['name']}: {row['patents']} patents")
        
        # Top Companies
        print("\nTop Companies:")
        companies_df = self.get_top_companies(5)
        for _, row in companies_df.iterrows():
            print(f"  {row['name']}: {row['patents']} patents")
        
        # Top Countries
        print("\nTop Countries:")
        countries_df = self.get_top_countries(5)
        for _, row in countries_df.iterrows():
            print(f"  {row['country']}: {row['patents']} patents ({row['share']}%)")
        
        print("="*60)
    
    def generate_csv_reports(self):
        """Generate required CSV files"""
        print("Generating CSV reports...")
        
        # top_inventors.csv
        inventors_df = self.get_top_inventors()
        inventors_df.to_csv(self.reports_dir / "top_inventors.csv", index=False)
        print(f"  Generated: top_inventors.csv ({len(inventors_df)} records)")
        
        # top_companies.csv
        companies_df = self.get_top_companies()
        companies_df.to_csv(self.reports_dir / "top_companies.csv", index=False)
        print(f"  Generated: top_companies.csv ({len(companies_df)} records)")
        
        # country_trends.csv
        trends_df = self.get_country_trends()
        trends_df.to_csv(self.reports_dir / "country_trends.csv", index=False)
        print(f"  Generated: country_trends.csv ({len(trends_df)} records)")
    
    def generate_json_report(self):
        """Generate JSON report with exact structure required by course"""
        print("Generating JSON report...")
        
        # Get data
        total_patents = self.get_total_patents()
        inventors_df = self.get_top_inventors()
        companies_df = self.get_top_companies()
        countries_df = self.get_top_countries()
        
        # Create JSON structure
        json_report = {
            "total_patents": int(total_patents),
            "top_inventors": [
                {"name": row['name'], "patents": int(row['patents'])}
                for _, row in inventors_df.iterrows()
            ],
            "top_companies": [
                {"name": row['name'], "patents": int(row['patents'])}
                for _, row in companies_df.iterrows()
            ],
            "top_countries": [
                {"country": row['country'], "share": float(row['share'])}
                for _, row in countries_df.iterrows()
            ]
        }
        
        # Save JSON
        with open(self.reports_dir / "patent_report.json", 'w') as f:
            json.dump(json_report, f, indent=2)
        
        print(f"  Generated: patent_report.json")
        print(f"    - Total patents: {json_report['total_patents']}")
        print(f"    - Top inventors: {len(json_report['top_inventors'])}")
        print(f"    - Top companies: {len(json_report['top_companies'])}")
        print(f"    - Top countries: {len(json_report['top_countries'])}")
        
        return json_report
    
    def generate_all_reports(self):
        """Generate all required reports for course submission"""
        print("Generating course-compliant patent intelligence reports...")
        print(f"Report directory: {self.reports_dir.absolute()}")
        
        # Generate all three report types
        self.generate_console_report()
        self.generate_csv_reports()
        json_data = self.generate_json_report()
        
        print(f"\nAll reports generated successfully!")
        
        # List generated files
        csv_files = list(self.reports_dir.glob("*.csv"))
        json_files = list(self.reports_dir.glob("*.json"))
        
        print(f"\nGenerated {len(csv_files)} CSV files:")
        for file in sorted(csv_files):
            print(f"  - {file.name}")
        
        print(f"\nGenerated {len(json_files)} JSON files:")
        for file in sorted(json_files):
            print(f"  - {file.name}")
        
        return json_data

if __name__ == "__main__":
    generator = CourseReportGenerator()
    generator.generate_all_reports()
