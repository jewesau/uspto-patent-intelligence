#!/usr/bin/env python3
"""
Global Patent Intelligence Data Pipeline - Report Generator
Creates final reports in CSV, JSON, and console formats
"""

import pandas as pd
import json
from pathlib import Path
from datetime import datetime
import sqlite3

class ReportGenerator:
    def __init__(self, db_path="../database/patent_intelligence.db", reports_dir="../reports"):
        self.db_path = Path(db_path)
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(exist_ok=True)
        
    def connect(self):
        """Establish database connection"""
        return sqlite3.connect(self.db_path)
    
    def generate_executive_summary(self):
        """Generate executive summary report"""
        conn = self.connect()
        
        # Get key statistics
        stats_query = '''
            SELECT 
                COUNT(*) as total_patents,
                COUNT(DISTINCT DATE(patent_date, 'start of year')) as years_covered,
                MIN(patent_date) as earliest_patent,
                MAX(patent_date) as latest_patent,
                AVG(patent_number_cited_by_us_patents) as avg_citations,
                MAX(patent_number_cited_by_us_patents) as max_citations
            FROM patents
        '''
        
        stats_df = pd.read_sql_query(stats_query, conn)
        
        # Get top technologies
        tech_query = '''
            SELECT cpc_section, COUNT(*) as count
            FROM patents 
            WHERE cpc_section IS NOT NULL
            GROUP BY cpc_section
            ORDER BY count DESC
            LIMIT 5
        '''
        
        tech_df = pd.read_sql_query(tech_query, conn)
        
        # Get top companies
        company_query = '''
            SELECT c.company_name, COUNT(pc.patent_number) as patent_count
            FROM companies c
            JOIN patent_companies pc ON c.id = pc.company_id
            WHERE c.company_name NOT LIKE '%Unknown%'
            GROUP BY c.company_name
            ORDER BY patent_count DESC
            LIMIT 5
        '''
        
        company_df = pd.read_sql_query(company_query, conn)
        
        conn.close()
        
        # Create executive summary
        summary = {
            "report_title": "Global Patent Intelligence Report",
            "generated_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "key_metrics": stats_df.iloc[0].to_dict(),
            "top_technologies": tech_df.to_dict('records'),
            "top_companies": company_df.to_dict('records')
        }
        
        return summary
    
    def generate_csv_reports(self):
        """Generate CSV format reports"""
        print("Generating CSV reports...")
        
        conn = self.connect()
        
        # Reports to generate
        reports = {
            "patent_summary.csv": '''
                SELECT 
                    patent_number,
                    patent_title,
                    patent_date,
                    assignee_organization as company,
                    inventor_full_name,
                    cpc_section as technology_category,
                    patent_number_cited_by_us_patents as citations
                FROM patents p
                LEFT JOIN patent_companies pc ON p.patent_number = pc.patent_number
                LEFT JOIN companies c ON pc.company_id = c.id
                LEFT JOIN patent_inventors pi ON p.patent_number = pi.patent_number
                LEFT JOIN inventors i ON pi.inventor_id = i.id
                ORDER BY p.patent_date DESC
            ''',
            
            "yearly_patents.csv": '''
                SELECT 
                    patent_date_year as year,
                    COUNT(*) as patent_count,
                    COUNT(DISTINCT c.id) as unique_companies,
                    COUNT(DISTINCT i.id) as unique_inventors
                FROM patents p
                LEFT JOIN patent_companies pc ON p.patent_number = pc.patent_number
                LEFT JOIN companies c ON pc.company_id = c.id
                LEFT JOIN patent_inventors pi ON p.patent_number = pi.patent_number
                LEFT JOIN inventors i ON pi.inventor_id = i.id
                WHERE patent_date_year IS NOT NULL
                GROUP BY patent_date_year
                ORDER BY year
            ''',
            
            "technology_analysis.csv": '''
                SELECT 
                    cpc_section,
                    cpc_subsection,
                    COUNT(*) as patent_count,
                    AVG(patent_number_cited_by_us_patents) as avg_citations,
                    COUNT(DISTINCT c.id) as unique_companies
                FROM patents p
                LEFT JOIN patent_companies pc ON p.patent_number = pc.patent_number
                LEFT JOIN companies c ON pc.company_id = c.id
                WHERE cpc_section IS NOT NULL
                GROUP BY cpc_section, cpc_subsection
                ORDER BY patent_count DESC
            ''',
            
            "company_performance.csv": '''
                SELECT 
                    c.company_name,
                    COUNT(pc.patent_number) as patent_count,
                    AVG(p.patent_number_cited_by_us_patents) as avg_citations,
                    MIN(p.patent_date_year) as first_patent_year,
                    MAX(p.patent_date_year) as last_patent_year,
                    COUNT(DISTINCT p.cpc_section) as technology_diversity
                FROM companies c
                JOIN patent_companies pc ON c.id = pc.company_id
                JOIN patents p ON pc.patent_number = p.patent_number
                WHERE c.company_name NOT LIKE '%Unknown%'
                GROUP BY c.company_name
                HAVING patent_count >= 2
                ORDER BY patent_count DESC
            ''',
            
            "inventor_productivity.csv": '''
                SELECT 
                    i.inventor_full_name,
                    COUNT(pi.patent_number) as patent_count,
                    AVG(p.patent_number_cited_by_us_patents) as avg_citations,
                    COUNT(DISTINCT c.id) as companies_worked_with,
                    MIN(p.patent_date_year) as first_patent_year,
                    MAX(p.patent_date_year) as last_patent_year
                FROM inventors i
                JOIN patent_inventors pi ON i.id = pi.inventor_id
                JOIN patents p ON pi.patent_number = p.patent_number
                LEFT JOIN patent_companies pc ON p.patent_number = pc.patent_number
                LEFT JOIN companies c ON pc.company_id = c.id
                WHERE i.inventor_full_name NOT LIKE '%Unknown%'
                GROUP BY i.inventor_full_name
                HAVING patent_count >= 1
                ORDER BY patent_count DESC
            '''
        }
        
        for filename, query in reports.items():
            try:
                df = pd.read_sql_query(query, conn)
                output_path = self.reports_dir / filename
                df.to_csv(output_path, index=False)
                print(f"  Generated: {filename} ({len(df)} records)")
            except Exception as e:
                print(f"  Error generating {filename}: {e}")
        
        conn.close()
    
    def generate_json_reports(self):
        """Generate JSON format reports"""
        print("Generating JSON reports...")
        
        # Executive summary
        summary = self.generate_executive_summary()
        
        with open(self.reports_dir / "executive_summary.json", 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        print("  Generated: executive_summary.json")
        
        # Detailed dashboard data
        conn = self.connect()
        
        dashboard_data = {
            "metadata": {
                "generated_date": datetime.now().isoformat(),
                "database_path": str(self.db_path)
            },
            "charts": {}
        }
        
        # Patent trends over time
        trends_query = '''
            SELECT patent_date_year as year, COUNT(*) as count
            FROM patents 
            WHERE patent_date_year IS NOT NULL
            GROUP BY patent_date_year
            ORDER BY year
        '''
        
        trends_df = pd.read_sql_query(trends_query, conn)
        dashboard_data["charts"]["patent_trends"] = trends_df.to_dict('records')
        
        # Technology distribution
        tech_query = '''
            SELECT cpc_section, COUNT(*) as count
            FROM patents 
            WHERE cpc_section IS NOT NULL
            GROUP BY cpc_section
            ORDER BY count DESC
        '''
        
        tech_df = pd.read_sql_query(tech_query, conn)
        dashboard_data["charts"]["technology_distribution"] = tech_df.to_dict('records')
        
        # Company rankings
        company_query = '''
            SELECT c.company_name, COUNT(pc.patent_number) as patent_count
            FROM companies c
            JOIN patent_companies pc ON c.id = pc.company_id
            WHERE c.company_name NOT LIKE '%Unknown%'
            GROUP BY c.company_name
            ORDER BY patent_count DESC
            LIMIT 10
        '''
        
        company_df = pd.read_sql_query(company_query, conn)
        dashboard_data["charts"]["top_companies"] = company_df.to_dict('records')
        
        conn.close()
        
        with open(self.reports_dir / "dashboard_data.json", 'w') as f:
            json.dump(dashboard_data, f, indent=2, default=str)
        
        print("  Generated: dashboard_data.json")
    
    def generate_console_report(self):
        """Generate console format report"""
        print("\n" + "="*80)
        print("GLOBAL PATENT INTELLIGENCE REPORT")
        print("="*80)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Database: {self.db_path}")
        print()
        
        conn = self.connect()
        
        # Key Statistics
        print("KEY STATISTICS")
        print("-" * 40)
        
        stats_query = '''
            SELECT 
                COUNT(*) as total_patents,
                COUNT(DISTINCT DATE(patent_date, 'start of year')) as years_covered,
                MIN(patent_date) as earliest_patent,
                MAX(patent_date) as latest_patent,
                COUNT(DISTINCT c.id) as unique_companies,
                COUNT(DISTINCT i.id) as unique_inventors
            FROM patents p
            LEFT JOIN patent_companies pc ON p.patent_number = pc.patent_number
            LEFT JOIN companies c ON pc.company_id = c.id
            LEFT JOIN patent_inventors pi ON p.patent_number = pi.patent_number
            LEFT JOIN inventors i ON pi.inventor_id = i.id
        '''
        
        stats_df = pd.read_sql_query(stats_query, conn)
        stats = stats_df.iloc[0]
        
        print(f"Total Patents:           {stats['total_patents']:,}")
        print(f"Years Covered:           {stats['years_covered']}")
        print(f"Unique Companies:        {stats['unique_companies']:,}")
        print(f"Unique Inventors:        {stats['unique_inventors']:,}")
        print(f"Date Range:              {stats['earliest_patent']} to {stats['latest_patent']}")
        print()
        
        # Top Technologies
        print("TOP TECHNOLOGY CATEGORIES")
        print("-" * 40)
        
        tech_query = '''
            SELECT 
                cpc_section,
                COUNT(*) as patent_count,
                ROUND(AVG(patent_number_cited_by_us_patents), 2) as avg_citations
            FROM patents 
            WHERE cpc_section IS NOT NULL
            GROUP BY cpc_section
            ORDER BY patent_count DESC
            LIMIT 5
        '''
        
        tech_df = pd.read_sql_query(tech_query, conn)
        for _, row in tech_df.iterrows():
            print(f"{row['cpc_section']:8} | {row['patent_count']:6,} patents | {row['avg_citations']:6.1f} avg citations")
        print()
        
        # Top Companies
        print("TOP COMPANIES BY PATENT COUNT")
        print("-" * 40)
        
        company_query = '''
            SELECT 
                c.company_name,
                COUNT(pc.patent_number) as patent_count,
                ROUND(AVG(p.patent_number_cited_by_us_patents), 2) as avg_citations
            FROM companies c
            JOIN patent_companies pc ON c.id = pc.company_id
            JOIN patents p ON pc.patent_number = p.patent_number
            WHERE c.company_name NOT LIKE '%Unknown%'
            GROUP BY c.company_name
            ORDER BY patent_count DESC
            LIMIT 5
        '''
        
        company_df = pd.read_sql_query(company_query, conn)
        for _, row in company_df.iterrows():
            company_name = (row['company_name'][:25] + '...') if len(row['company_name']) > 25 else row['company_name']
            print(f"{company_name:28} | {row['patent_count']:6,} patents | {row['avg_citations']:6.1f} avg citations")
        print()
        
        # Recent Trends
        print("RECENT PATENT ACTIVITY")
        print("-" * 40)
        
        recent_query = '''
            SELECT 
                patent_date_year as year,
                COUNT(*) as patent_count
            FROM patents 
            WHERE patent_date_year >= (SELECT MAX(patent_date_year) - 4 FROM patents)
            GROUP BY patent_date_year
            ORDER BY year DESC
        '''
        
        recent_df = pd.read_sql_query(recent_query, conn)
        for _, row in recent_df.iterrows():
            print(f"{row['year']:6} | {row['patent_count']:6,} patents")
        
        conn.close()
        print("\n" + "="*80)
    
    def generate_all_reports(self):
        """Generate all report formats"""
        print("Generating comprehensive patent intelligence reports...")
        
        # Generate all formats
        self.generate_csv_reports()
        self.generate_json_reports()
        self.generate_console_report()
        
        print(f"\nAll reports generated successfully!")
        print(f"Report directory: {self.reports_dir.absolute()}")
        
        # List generated files
        report_files = list(self.reports_dir.glob("*.csv")) + list(self.reports_dir.glob("*.json"))
        print(f"\nGenerated {len(report_files)} report files:")
        for file in sorted(report_files):
            print(f"  - {file.name}")

if __name__ == "__main__":
    generator = ReportGenerator()
    generator.generate_all_reports()
