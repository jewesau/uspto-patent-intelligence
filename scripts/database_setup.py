#!/usr/bin/env python3
"""
Global Patent Intelligence Data Pipeline - Database Setup
Sets up SQL database and stores cleaned patent data
"""

import sqlite3
import pandas as pd
from pathlib import Path
import json
from datetime import datetime

class PatentDatabase:
    def __init__(self, db_path="../database/patent_intelligence.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self.connection = None
        
    def connect(self):
        """Establish database connection"""
        self.connection = sqlite3.connect(self.db_path)
        return self.connection
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            
    def create_tables(self):
        """Create database tables for patent data"""
        conn = self.connect()
        cursor = conn.cursor()
        
        # Patents table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patents (
                patent_number TEXT PRIMARY KEY,
                patent_title TEXT NOT NULL,
                patent_abstract TEXT,
                patent_date DATE,
                patent_type TEXT,
                patent_date_year INTEGER,
                patent_date_month INTEGER,
                title_length INTEGER,
                abstract_length INTEGER,
                patent_number_cited_by_us_patents INTEGER,
                citation_category TEXT,
                cpc_section TEXT,
                cpc_subsection TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Inventors table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                inventor_first_name TEXT,
                inventor_last_name TEXT,
                inventor_full_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(inventor_first_name, inventor_last_name)
            )
        ''')
        
        # Companies table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Patent-Inventor relationship table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patent_inventors (
                patent_number TEXT,
                inventor_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patent_number) REFERENCES patents(patent_number),
                FOREIGN KEY (inventor_id) REFERENCES inventors(id),
                PRIMARY KEY (patent_number, inventor_id)
            )
        ''')
        
        # Patent-Company relationship table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patent_companies (
                patent_number TEXT,
                company_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patent_number) REFERENCES patents(patent_number),
                FOREIGN KEY (company_id) REFERENCES companies(id),
                PRIMARY KEY (patent_number, company_id)
            )
        ''')
        
        conn.commit()
        print("Database tables created successfully")
        self.close()
        
    def load_cleaned_data(self, data_path="../data/processed/cleaned_patent_data.csv"):
        """Load cleaned patent data"""
        data_path = Path(__file__).parent / data_path
        try:
            df = pd.read_csv(data_path)
            print(f"Loaded {len(df)} records from {data_path}")
            return df
        except FileNotFoundError:
            print(f"Error: File {data_path} not found")
            return None
    
    def insert_patent_data(self, df):
        """Insert patent data into database"""
        conn = self.connect()
        cursor = conn.cursor()
        
        patents_inserted = 0
        inventors_inserted = 0
        companies_inserted = 0
        
        for _, row in df.iterrows():
            try:
                # Insert patent
                patent_data = {
                    'patent_number': row.get('patent_number'),
                    'patent_title': row.get('patent_title'),
                    'patent_abstract': row.get('patent_abstract'),
                    'patent_date': row.get('patent_date'),
                    'patent_type': row.get('patent_type'),
                    'patent_date_year': row.get('patent_date_year'),
                    'patent_date_month': row.get('patent_date_month'),
                    'title_length': row.get('title_length'),
                    'abstract_length': row.get('abstract_length'),
                    'patent_number_cited_by_us_patents': row.get('patent_number_cited_by_us_patents'),
                    'citation_category': row.get('citation_category'),
                    'cpc_section': row.get('cpc_section'),
                    'cpc_subsection': row.get('cpc_subsection')
                }
                
                cursor.execute('''
                    INSERT OR REPLACE INTO patents 
                    (patent_number, patent_title, patent_abstract, patent_date, patent_type,
                     patent_date_year, patent_date_month, title_length, abstract_length,
                     patent_number_cited_by_us_patents, citation_category, cpc_section, cpc_subsection)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', tuple(patent_data.values()))
                
                patents_inserted += 1
                
                # Insert inventor if exists
                inventor_full_name = row.get('inventor_full_name')
                if inventor_full_name and inventor_full_name != 'Unknown Unknown':
                    cursor.execute('''
                        INSERT OR IGNORE INTO inventors 
                        (inventor_first_name, inventor_last_name, inventor_full_name)
                        VALUES (?, ?, ?)
                    ''', (row.get('inventor_first_name'), row.get('inventor_last_name'), inventor_full_name))
                    
                    # Get inventor ID
                    cursor.execute('''
                        SELECT id FROM inventors WHERE inventor_full_name = ?
                    ''', (inventor_full_name,))
                    inventor_id = cursor.fetchone()[0]
                    
                    # Link patent to inventor
                    cursor.execute('''
                        INSERT OR IGNORE INTO patent_inventors (patent_number, inventor_id)
                        VALUES (?, ?)
                    ''', (row.get('patent_number'), inventor_id))
                    
                    inventors_inserted += 1
                
                # Insert company if exists
                company_name = row.get('assignee_organization')
                if company_name and company_name != 'Unknown':
                    cursor.execute('''
                        INSERT OR IGNORE INTO companies (company_name)
                        VALUES (?)
                    ''', (company_name,))
                    
                    # Get company ID
                    cursor.execute('''
                        SELECT id FROM companies WHERE company_name = ?
                    ''', (company_name,))
                    company_id = cursor.fetchone()[0]
                    
                    # Link patent to company
                    cursor.execute('''
                        INSERT OR IGNORE INTO patent_companies (patent_number, company_id)
                        VALUES (?, ?)
                    ''', (row.get('patent_number'), company_id))
                    
                    companies_inserted += 1
                    
            except Exception as e:
                print(f"Error inserting patent {row.get('patent_number')}: {e}")
                continue
        
        conn.commit()
        print(f"Inserted {patents_inserted} patents, {inventors_inserted} inventor relationships, {companies_inserted} company relationships")
        self.close()
        
        return patents_inserted, inventors_inserted, companies_inserted
    
    def create_indexes(self):
        """Create database indexes for better query performance"""
        conn = self.connect()
        cursor = conn.cursor()
        
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_patents_date ON patents(patent_date)",
            "CREATE INDEX IF NOT EXISTS idx_patents_year ON patents(patent_date_year)",
            "CREATE INDEX IF NOT EXISTS idx_patents_citation ON patents(patent_number_cited_by_us_patents)",
            "CREATE INDEX IF NOT EXISTS idx_patents_cpc ON patents(cpc_section)",
            "CREATE INDEX IF NOT EXISTS idx_inventors_name ON inventors(inventor_full_name)",
            "CREATE INDEX IF NOT EXISTS idx_companies_name ON companies(company_name)"
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
            
        conn.commit()
        print("Database indexes created")
        self.close()
    
    def get_database_stats(self):
        """Get database statistics"""
        conn = self.connect()
        cursor = conn.cursor()
        
        stats = {}
        
        # Count records in each table
        cursor.execute("SELECT COUNT(*) FROM patents")
        stats['total_patents'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM inventors")
        stats['total_inventors'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM companies")
        stats['total_companies'] = cursor.fetchone()[0]
        
        # Date range
        cursor.execute("SELECT MIN(patent_date), MAX(patent_date) FROM patents")
        date_range = cursor.fetchone()
        stats['date_range'] = {'start': date_range[0], 'end': date_range[1]}
        
        # Top companies
        cursor.execute('''
            SELECT c.company_name, COUNT(pc.patent_number) as patent_count
            FROM companies c
            JOIN patent_companies pc ON c.id = pc.company_id
            GROUP BY c.company_name
            ORDER BY patent_count DESC
            LIMIT 5
        ''')
        stats['top_companies'] = cursor.fetchall()
        
        self.close()
        return stats
    
    def run_database_setup(self):
        """Run complete database setup"""
        print("Starting database setup...")
        
        # Create tables
        self.create_tables()
        
        # Load cleaned data
        df = self.load_cleaned_data()
        if df is None:
            print("No data to load. Please run data_cleaner.py first.")
            return None
            
        # Insert data
        patent_count, inventor_count, company_count = self.insert_patent_data(df)
        
        # Create indexes
        self.create_indexes()
        
        # Get statistics
        stats = self.get_database_stats()
        
        print("\nDatabase setup completed successfully!")
        print(f"Database location: {self.db_path}")
        print(f"Statistics: {json.dumps(stats, indent=2, default=str)}")
        
        return stats

if __name__ == "__main__":
    db = PatentDatabase()
    
    # Run complete setup
    stats = db.run_database_setup()
    
    if stats:
        print(f"\nNext step: Run analysis_queries.py to analyze the data")
