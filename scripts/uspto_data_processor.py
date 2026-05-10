#!/usr/bin/env python3
"""
USPTO Patent Data Processor
Handles real USPTO patent data files: g_patent, g_inventor, g_assignee_disambiguated, g_location
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json

class USPTODataProcessor:
    def __init__(self, data_dir="../data"):
        self.data_dir = Path(data_dir)
        self.raw_dir = self.data_dir / "raw"
        self.processed_dir = self.data_dir / "processed"
        self.processed_dir.mkdir(exist_ok=True)
        
    def load_uspto_data(self):
        """Load and merge USPTO patent data files"""
        print("Loading USPTO patent data files...")
        
        # Load individual files
        patents_df = self._load_file("g_patent.tsv")
        inventors_df = self._load_file("g_inventor.tsv")
        assignees_df = self._load_file("g_assignee_disambiguated.tsv")
        locations_df = self._load_file("g_location.tsv")
        
        if patents_df is None:
            print("Error: g_patent.tsv not found")
            return None
            
        print(f"Loaded {len(patents_df)} patents")
        print(f"Loaded {len(inventors_df) if inventors_df is not None else 0} inventors")
        print(f"Loaded {len(assignees_df) if assignees_df is not None else 0} assignees")
        print(f"Loaded {len(locations_df) if locations_df is not None else 0} locations")
        
        # Merge data
        merged_df = self._merge_patent_data(patents_df, inventors_df, assignees_df, locations_df)
        
        return merged_df
    
    def _load_file(self, filename):
        """Load TSV file with error handling"""
        file_path = self.raw_dir / filename
        if not file_path.exists():
            print(f"Warning: {filename} not found in {self.raw_dir}")
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
            print(f"Error loading {filename}: {str(e)}")
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
            
            merged_df = pd.merge(merged_df, inventor_groups, on='patent_id', how='left')
        
        # Merge with assignees
        if assignees_df is not None and not assignees_df.empty:
            merged_df = pd.merge(merged_df, assignees_df, on='patent_id', how='left')
        
        # Merge with locations
        if locations_df is not None and not locations_df.empty:
            merged_df = pd.merge(merged_df, locations_df, on='location_id', how='left')
        
        print(f"Merged dataset has {len(merged_df)} records")
        return merged_df
    
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
            'citation_count': 'patent_number_cited_by_us_patents',
            
            # Technology fields
            'cpc_section': 'cpc_section',
            'cpc_subsection': 'cpc_subsection',
            
            # Inventor fields
            'inventor_first_name': 'inventor_first_name',
            'inventor_last_name': 'inventor_last_name',
            'inventor_full_name': 'inventor_full_name',
            
            # Assignee fields
            'assignee_organization': 'assignee_organization',
            'assignee_name': 'assignee_organization',
            
            # Location fields
            'country': 'inventor_country',
            'location_country': 'inventor_country',
            'assignee_country': 'assignee_country'
        }
        
        # Rename columns
        df = df.rename(columns=column_mapping)
        
        # Create derived fields
        df['inventor_full_name'] = df.apply(self._create_full_name, axis=1)
        
        # Extract date components
        if 'patent_date' in df.columns:
            df['patent_date'] = pd.to_datetime(df['patent_date'], errors='coerce')
            df['patent_date_year'] = df['patent_date'].dt.year
            df['patent_date_month'] = df['patent_date'].dt.month
        
        # Calculate text lengths
        if 'patent_title' in df.columns:
            df['title_length'] = df['patent_title'].astype(str).str.len()
        if 'patent_abstract' in df.columns:
            df['abstract_length'] = df['patent_abstract'].astype(str).str.len()
        
        # Create citation categories
        if 'patent_number_cited_by_us_patents' in df.columns:
            df['citation_category'] = pd.cut(
                df['patent_number_cited_by_us_patents'],
                bins=[-1, 5, 20, float('inf')],
                labels=['Low', 'Medium', 'High']
            )
        
        print(f"Standardized {len(df)} records")
        return df
    
    def _create_full_name(self, row):
        """Create full inventor name from first and last name"""
        first = row.get('inventor_first_name', '')
        last = row.get('inventor_last_name', '')
        
        if pd.isna(first) or first == '':
            return str(last) if not pd.isna(last) else 'Unknown'
        if pd.isna(last) or last == '':
            return str(first)
        
        return f"{first} {last}"
    
    def clean_data(self, df):
        """Clean and validate patent data"""
        print("Cleaning patent data...")
        
        # Handle missing values
        if 'patent_title' in df.columns:
            df['patent_title'] = df['patent_title'].fillna('Unknown Title')
        if 'patent_abstract' in df.columns:
            df['patent_abstract'] = df['patent_abstract'].fillna('No abstract available')
        if 'inventor_country' in df.columns:
            df['inventor_country'] = df['inventor_country'].fillna('Unknown')
        if 'assignee_organization' in df.columns:
            df['assignee_organization'] = df['assignee_organization'].fillna('Unknown Organization')
        
        # Clean text fields
        if 'patent_title' in df.columns:
            df['patent_title'] = df['patent_title'].astype(str).str.replace(r'\s+', ' ', regex=True).str.strip()
        if 'patent_abstract' in df.columns:
            df['patent_abstract'] = df['patent_abstract'].astype(str).str.replace(r'\s+', ' ', regex=True).str.strip()
        
        # Fill missing numeric values
        if 'patent_number_cited_by_us_patents' in df.columns:
            df['patent_number_cited_by_us_patents'] = df['patent_number_cited_by_us_patents'].fillna(0)
        
        print(f"Cleaned {len(df)} records")
        return df
    
    def save_processed_data(self, df, filename="uspto_patent_data.csv"):
        """Save processed data"""
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
        
        # Load raw data
        raw_df = self.load_uspto_data()
        if raw_df is None:
            print("Failed to load USPTO data")
            return None
        
        # Standardize columns
        standardized_df = self.standardize_columns(raw_df)
        
        # Clean data
        cleaned_df = self.clean_data(standardized_df)
        
        # Generate sample if requested
        if sample_size:
            self.generate_sample(cleaned_df, sample_size)
        
        # Save processed data
        output_path = self.save_processed_data(cleaned_df)
        
        # Print summary
        print("\n" + "=" * 60)
        print("PROCESSING SUMMARY")
        print("=" * 60)
        print(f"Total patents processed: {len(cleaned_df):,}")
        print(f"Date range: {cleaned_df['patent_date'].min()} to {cleaned_df['patent_date'].max()}")
        print(f"Unique inventors: {cleaned_df['inventor_full_name'].nunique()}")
        print(f"Unique assignees: {cleaned_df['assignee_organization'].nunique()}")
        print(f"Unique countries: {cleaned_df['inventor_country'].nunique()}")
        print(f"Output file: {output_path}")
        print("=" * 60)
        
        return cleaned_df

if __name__ == "__main__":
    processor = USPTODataProcessor()
    processor.process_uspto_data(sample_size=1000)  # Generate sample for testing
