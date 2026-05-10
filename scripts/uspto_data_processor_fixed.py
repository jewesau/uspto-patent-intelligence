#!/usr/bin/env python3
"""
USPTO Data Processor
Handles loading and processing of real USPTO patent data files
"""

import pandas as pd
import numpy as np
from pathlib import Path
import zipfile
import os

class USPTODataProcessor:
    def __init__(self, data_dir="data"):
        self.data_dir = Path(data_dir)
        self.raw_dir = self.data_dir / "raw"
        self.processed_dir = self.data_dir / "processed"
        
        # Create directories
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
    
    def load_uspto_data_from_zip(self):
        """Load USPTO data from user's zip file"""
        zip_path = Path(r"C:\Users\user\Desktop\un zipped cloud files.zip")
        
        if not zip_path.exists():
            print(f"Error: Zip file not found at {zip_path}")
            return None, None, None, None
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Extract to raw directory
                zip_ref.extractall(self.raw_dir)
                print(f"Extracted USPTO data from {zip_path}")
                
                # Load individual files
                patents_df = self._load_file("un zipped cloud files/g_patent.tsv")
                inventors_df = self._load_file("un zipped cloud files/g_inventor.tsv")
                assignees_df = self._load_file("un zipped cloud files/g_assignee_disambiguated.tsv")
                locations_df = self._load_file("un zipped cloud files/g_location.tsv")
                
                return patents_df, inventors_df, assignees_df, locations_df
                
        except Exception as e:
            print(f"Error loading from zip: {e}")
            return None, None, None, None
    
    def _load_file(self, filename):
        """Load TSV file with error handling"""
        file_path = self.raw_dir / filename
        
        if not file_path.exists():
            print(f"Warning: {filename} not found at {file_path}")
            return None
            
        try:
            # Try different encodings
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    df = pd.read_csv(file_path, sep='\t', encoding=encoding, low_memory=False)
                    print(f"Successfully loaded {filename} with {encoding} encoding")
                    return df
                except UnicodeDecodeError:
                    continue
                    
            print(f"Error: Could not read {filename} with any encoding")
            return None
            
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            return None
    
    def _merge_patent_data(self, patents_df, inventors_df, assignees_df, locations_df):
        """Merge patent data with inventor, assignee, and location information"""
        print("Merging patent data...")
        
        # Start with patents as base
        merged_df = patents_df.copy()
        
        # Merge with inventors (many-to-many relationship)
        if inventors_df is not None and not inventors_df.empty:
            # Group inventors by patent_id
            inventor_groups = inventors_df.groupby('patent_id').agg({
                'inventor_id': lambda x: list(x),
                'inventor_first_name': lambda x: list(x),
                'inventor_last_name': lambda x: list(x)
            }).reset_index()
            
            # Merge with patents
            merged_df = pd.merge(merged_df, inventor_groups, on='patent_id', how='left')
            
            # Merge with assignees
            if assignees_df is not None and not assignees_df.empty:
                merged_df = pd.merge(merged_df, assignees_df, on='patent_id', how='left')
            
            # Merge with locations
            if locations_df is not None and not locations_df.empty:
                merged_df = pd.merge(merged_df, locations_df, on='location_id', how='left')
            
            print(f"Merged data with {len(merged_df)} records")
            return merged_df
        else:
            print("No data to merge")
            return None
    
    def standardize_columns(self, df):
        """Standardize column names to match our pipeline"""
        print("Standardizing column names...")
        
        # Create column mapping based on typical USPTO field names
        column_mapping = {
            # Patent fields
            'patent_id': 'patent_number',
            'patent_title': 'patent_title', 
            'patent_abstract': 'patent_abstract',
            'patent_date': 'patent_date',
            'patent_type': 'patent_type',
            
            # Inventor fields
            'inventor_first_name': 'inventor_first_name',
            'inventor_last_name': 'inventor_last_name',
            'inventor_country': 'inventor_country',
            
            # Assignee fields
            'assignee_organization': 'assignee_organization',
            'assignee_country': 'assignee_country',
            
            # Location fields
            'location_country': 'inventor_country',
            
            # Technology fields
            'cpc_section': 'cpc_section',
            'cpc_subsection': 'cpc_subsection',
            
            # Citation fields
            'patent_number_cited_by_us_patents': 'patent_number_cited_by_us_patents'
        }
        
        # Rename columns based on mapping
        standardized_df = df.rename(columns=column_mapping)
        
        print(f"Standardized {len(standardized_df)} columns")
        return standardized_df
    
    def clean_data(self, df):
        """Clean and validate patent data"""
        print("Cleaning data...")
        
        if df is None or df.empty:
            print("No data to clean")
            return None
        
        # Create a copy to avoid SettingWithCopyWarning
        cleaned_df = df.copy()
        
        # Handle missing values
        print("Handling missing values...")
        
        # Fill missing text fields with 'Unknown'
        text_fields = ['patent_title', 'patent_abstract', 'patent_type', 
                     'inventor_first_name', 'inventor_last_name', 
                     'assignee_organization', 'cpc_section', 'cpc_subsection']
        
        for field in text_fields:
            if field in cleaned_df.columns:
                cleaned_df[field] = cleaned_df[field].fillna('Unknown')
        
        # Fill missing numeric fields with 0
        numeric_fields = ['patent_number_cited_by_us_patents']
        for field in numeric_fields:
            if field in cleaned_df.columns:
                cleaned_df[field] = cleaned_df[field].fillna(0)
        
        # Handle date fields
        if 'patent_date' in cleaned_df.columns:
            cleaned_df['patent_date'] = pd.to_datetime(cleaned_df['patent_date'], errors='coerce')
        
        # Create derived fields
        print("Creating derived fields...")
        
        # Full inventor name
        if 'inventor_first_name' in cleaned_df.columns and 'inventor_last_name' in cleaned_df.columns:
            cleaned_df['inventor_full_name'] = (
                cleaned_df['inventor_first_name'].astype(str) + ' ' + 
                cleaned_df['inventor_last_name'].astype(str)
            ).str.strip()
        
        # Title length
        if 'patent_title' in cleaned_df.columns:
            cleaned_df['title_length'] = cleaned_df['patent_title'].astype(str).str.len()
        
        # Abstract length
        if 'patent_abstract' in cleaned_df.columns:
            cleaned_df['abstract_length'] = cleaned_df['patent_abstract'].astype(str).str.len()
        
        # Extract year and month from date
        if 'patent_date' in cleaned_df.columns:
            cleaned_df['patent_date_year'] = cleaned_df['patent_date'].dt.year
            cleaned_df['patent_date_month'] = cleaned_df['patent_date'].dt.month
        
        # Citation categories
        if 'patent_number_cited_by_us_patents' in cleaned_df.columns:
            cleaned_df['citation_category'] = pd.cut(
                cleaned_df['patent_number_cited_by_us_patents'],
                bins=[-1, 0, 10, 50, float('inf')],
                labels=['No citations', 'Low', 'Medium', 'High']
            )
        
        print(f"Cleaned {len(cleaned_df)} records")
        return cleaned_df
    
    def save_processed_data(self, df, filename="cleaned_patent_data.csv"):
        """Save processed data to CSV file"""
        output_path = self.processed_dir / filename
        df.to_csv(output_path, index=False)
        print(f"Processed data saved to {output_path}")
        return output_path
    
    def generate_sample(self, df, sample_size=1000):
        """Generate a sample of the data for testing"""
        if len(df) > sample_size:
            sample_df = df.sample(n=sample_size, random_state=42)
        else:
            sample_df = df
        
        sample_path = self.processed_dir / "sample_uspto_data.csv"
        sample_df.to_csv(sample_path, index=False)
        print(f"Sample data ({len(sample_df)} records) saved to {sample_path}")
        return sample_path
    
    def process_uspto_data(self, sample_size=None):
        """Complete USPTO data processing pipeline"""
        print("=" * 60)
        print("USPTO PATENT DATA PROCESSOR")
        print("=" * 60)
        
        # Load raw data from user's zip file
        patents_df, inventors_df, assignees_df, locations_df = self.load_uspto_data_from_zip()
        if patents_df is None:
            print("Failed to load USPTO data from zip file")
            return None
        
        print(f"Loaded {len(patents_df)} raw patent records")
        
        # Merge patent data
        merged_df = self._merge_patent_data(patents_df, inventors_df, assignees_df, locations_df)
        if merged_df is None:
            print("Failed to merge patent data")
            return None
        
        print(f"Merged {len(merged_df)} records")
        
        # Standardize columns
        standardized_df = self.standardize_columns(merged_df)
        if standardized_df is None:
            print("Failed to standardize columns")
            return None
        
        print(f"Standardized {len(standardized_df)} records")
        
        # Clean data
        cleaned_df = self.clean_data(standardized_df)
        if cleaned_df is None:
            print("Failed to clean data")
            return None
        
        print(f"Cleaned {len(cleaned_df)} records")
        
        # Create sample if requested
        if sample_size and len(cleaned_df) > sample_size:
            sample_df = cleaned_df.sample(n=sample_size, random_state=42)
            print(f"Created sample of {len(sample_df)} records")
        else:
            sample_df = cleaned_df
        
        # Save processed data
        output_path = self.save_processed_data(cleaned_df)
        print(f"Processed data saved to {output_path}")
        
        # Generate sample for testing
        self.generate_sample(cleaned_df, sample_size=1000)
        
        # Print summary
        print("\n" + "=" * 60)
        print("PROCESSING SUMMARY")
        print("=" * 60)
        print(f"Total patents processed: {len(cleaned_df)}")
        if 'patent_date' in cleaned_df.columns:
            print(f"Date range: {cleaned_df['patent_date'].min()} to {cleaned_df['patent_date'].max()}")
        if 'inventor_full_name' in cleaned_df.columns:
            print(f"Unique inventors: {cleaned_df['inventor_full_name'].nunique()}")
        if 'assignee_organization' in cleaned_df.columns:
            print(f"Unique assignees: {cleaned_df['assignee_organization'].nunique()}")
        if 'inventor_country' in cleaned_df.columns:
            print(f"Unique countries: {cleaned_df['inventor_country'].nunique()}")
        print(f"Output file: {output_path}")
        print("=" * 60)
        
        return cleaned_df

if __name__ == "__main__":
    processor = USPTODataProcessor()
    processor.process_uspto_data(sample_size=1000)  # Generate sample for testing
