#!/usr/bin/env python3
"""
Global Patent Intelligence Data Pipeline - Analysis Queries
Performs SQL analysis on patent data and generates insights
"""

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import json
from datetime import datetime

class PatentAnalyzer:
    def __init__(self, db_path="../database/patent_intelligence.db"):
        self.db_path = Path(db_path)
        self.connection = None
        self.reports_dir = Path("../reports")
        self.reports_dir.mkdir(exist_ok=True)
        
    def connect(self):
        """Establish database connection"""
        self.connection = sqlite3.connect(self.db_path)
        return self.connection
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
    
    def execute_query(self, query, params=None):
        """Execute SQL query and return results as DataFrame"""
        conn = self.connect()
        try:
            if params:
                df = pd.read_sql_query(query, conn, params=params)
            else:
                df = pd.read_sql_query(query, conn)
            return df
        except Exception as e:
            print(f"Error executing query: {e}")
            return None
        finally:
            self.close()
    
    def get_patent_trends_over_time(self):
        """Analyze patent filing trends over time"""
        query = '''
            SELECT 
                patent_date_year as year,
                COUNT(*) as patent_count,
                AVG(patent_number_cited_by_us_patents) as avg_citations
            FROM patents 
            WHERE patent_date_year IS NOT NULL
            GROUP BY patent_date_year
            ORDER BY patent_date_year
        '''
        
        df = self.execute_query(query)
        if df is not None and not df.empty:
            print("Patent Trends Over Time:")
            print(df.to_string(index=False))
            
            # Save to CSV
            df.to_csv(self.reports_dir / "patent_trends.csv", index=False)
            
        return df
    
    def get_top_innovators(self, limit=10):
        """Get top inventors by patent count"""
        query = '''
            SELECT 
                i.inventor_full_name,
                COUNT(pi.patent_number) as patent_count,
                AVG(p.patent_number_cited_by_us_patents) as avg_citations,
                MIN(p.patent_date_year) as first_patent_year,
                MAX(p.patent_date_year) as last_patent_year
            FROM inventors i
            JOIN patent_inventors pi ON i.id = pi.inventor_id
            JOIN patents p ON pi.patent_number = p.patent_number
            WHERE i.inventor_full_name NOT LIKE '%Unknown%'
            GROUP BY i.inventor_full_name
            ORDER BY patent_count DESC
            LIMIT ?
        '''
        
        df = self.execute_query(query, (limit,))
        if df is not None and not df.empty:
            print(f"\nTop {limit} Inventors by Patent Count:")
            print(df.to_string(index=False))
            
            # Save to CSV
            df.to_csv(self.reports_dir / "top_inventors.csv", index=False)
            
        return df
    
    def get_top_companies(self, limit=10):
        """Get top companies by patent count"""
        query = '''
            SELECT 
                c.company_name,
                COUNT(pc.patent_number) as patent_count,
                AVG(p.patent_number_cited_by_us_patents) as avg_citations,
                MIN(p.patent_date_year) as first_patent_year,
                MAX(p.patent_date_year) as last_patent_year
            FROM companies c
            JOIN patent_companies pc ON c.id = pc.company_id
            JOIN patents p ON pc.patent_number = p.patent_number
            WHERE c.company_name NOT LIKE '%Unknown%'
            GROUP BY c.company_name
            ORDER BY patent_count DESC
            LIMIT ?
        '''
        
        df = self.execute_query(query, (limit,))
        if df is not None and not df.empty:
            print(f"\nTop {limit} Companies by Patent Count:")
            print(df.to_string(index=False))
            
            # Save to CSV
            df.to_csv(self.reports_dir / "top_companies.csv", index=False)
            
        return df
    
    def get_technology_categories(self):
        """Analyze patents by technology categories (CPC sections)"""
        query = '''
            SELECT 
                cpc_section,
                COUNT(*) as patent_count,
                AVG(patent_number_cited_by_us_patents) as avg_citations,
                COUNT(DISTINCT patent_number_cited_by_us_patents) as unique_citation_counts
            FROM patents 
            WHERE cpc_section IS NOT NULL
            GROUP BY cpc_section
            ORDER BY patent_count DESC
        '''
        
        df = self.execute_query(query)
        if df is not None and not df.empty:
            print("\nPatents by Technology Category:")
            print(df.to_string(index=False))
            
            # Save to CSV
            df.to_csv(self.reports_dir / "technology_categories.csv", index=False)
            
        return df
    
    def get_citation_analysis(self):
        """Analyze patent citation patterns"""
        query = '''
            SELECT 
                citation_category,
                COUNT(*) as patent_count,
                AVG(title_length) as avg_title_length,
                AVG(abstract_length) as avg_abstract_length
            FROM patents 
            WHERE citation_category IS NOT NULL
            GROUP BY citation_category
            ORDER BY 
                CASE citation_category
                    WHEN 'Very High' THEN 1
                    WHEN 'High' THEN 2
                    WHEN 'Medium' THEN 3
                    WHEN 'Low' THEN 4
                END
        '''
        
        df = self.execute_query(query)
        if df is not None and not df.empty:
            print("\nPatent Citation Analysis:")
            print(df.to_string(index=False))
            
            # Save to CSV
            df.to_csv(self.reports_dir / "citation_analysis.csv", index=False)
            
        return df
    
    def get_collaboration_network(self):
        """Analyze inventor collaboration patterns"""
        query = '''
            SELECT 
                patent_number,
                COUNT(DISTINCT inventor_id) as inventor_count
            FROM patent_inventors
            GROUP BY patent_number
            ORDER BY inventor_count DESC
        '''
        
        df = self.execute_query(query)
        if df is not None and not df.empty:
            collaboration_stats = df['inventor_count'].value_counts().sort_index()
            print("\nInventor Collaboration Patterns:")
            print(collaboration_stats.to_string())
            
            # Save collaboration stats
            collaboration_stats_df = pd.DataFrame(collaboration_stats)
            collaboration_stats_df.to_csv(self.reports_dir / "collaboration_patterns.csv", header=['patent_count'])
            
            return collaboration_stats
        return None
    
    def get_company_inventor_analysis(self):
        """Analyze company-inventor relationships"""
        query = '''
            SELECT 
                c.company_name,
                COUNT(DISTINCT i.id) as unique_inventors,
                COUNT(pc.patent_number) as patent_count,
                COUNT(pc.patent_number) / COUNT(DISTINCT i.id) as patents_per_inventor
            FROM companies c
            JOIN patent_companies pc ON c.id = pc.company_id
            JOIN patent_inventors pi ON pc.patent_number = pi.patent_number
            JOIN inventors i ON pi.inventor_id = i.id
            WHERE c.company_name NOT LIKE '%Unknown%'
            GROUP BY c.company_name
            HAVING COUNT(pc.patent_number) >= 2
            ORDER BY patent_count DESC
            LIMIT 15
        '''
        
        df = self.execute_query(query)
        if df is not None and not df.empty:
            print("\nCompany-Inventor Analysis:")
            print(df.to_string(index=False))
            
            # Save to CSV
            df.to_csv(self.reports_dir / "company_inventor_analysis.csv", index=False)
            
        return df
    
    def generate_summary_report(self):
        """Generate comprehensive summary report"""
        print("Generating comprehensive analysis report...")
        
        # Run all analyses
        trends_df = self.get_patent_trends_over_time()
        inventors_df = self.get_top_innovators()
        companies_df = self.get_top_companies()
        tech_df = self.get_technology_categories()
        citation_df = self.get_citation_analysis()
        collaboration_stats = self.get_collaboration_network()
        company_inventor_df = self.get_company_inventor_analysis()
        
        # Create summary dictionary
        summary = {
            "report_generated": datetime.now().isoformat(),
            "database_path": str(self.db_path),
            "analyses_performed": [
                "Patent trends over time",
                "Top inventors analysis", 
                "Top companies analysis",
                "Technology categories analysis",
                "Citation patterns analysis",
                "Collaboration patterns analysis",
                "Company-inventor relationships analysis"
            ]
        }
        
        # Add key insights
        if trends_df is not None and not trends_df.empty:
            summary["patent_trends"] = {
                "total_years_analyzed": len(trends_df),
                "year_range": f"{trends_df['year'].min()}-{trends_df['year'].max()}",
                "total_patents": trends_df['patent_count'].sum(),
                "peak_year": trends_df.loc[trends_df['patent_count'].idxmax(), 'year']
            }
        
        if companies_df is not None and not companies_df.empty:
            summary["top_company"] = companies_df.iloc[0]['company_name'] if len(companies_df) > 0 else None
        
        # Save summary as JSON
        with open(self.reports_dir / "analysis_summary.json", 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        print(f"\nAnalysis completed! Reports saved to {self.reports_dir}")
        return summary
    
    def run_custom_query(self, query):
        """Execute custom SQL query"""
        print(f"Executing custom query: {query[:100]}...")
        df = self.execute_query(query)
        
        if df is not None and not df.empty:
            print("Query Results:")
            print(df.to_string(index=False))
            
            # Save custom query results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"custom_query_{timestamp}.csv"
            df.to_csv(self.reports_dir / filename, index=False)
            print(f"Results saved to {filename}")
            
        return df

if __name__ == "__main__":
    analyzer = PatentAnalyzer()
    
    # Run comprehensive analysis
    summary = analyzer.generate_summary_report()
    
    print(f"\nNext step: Run report_generator.py to create final reports")
