#!/usr/bin/env python3
"""
Global Patent Intelligence Data Pipeline - Data Cleaner
Cleans and processes patent data using pandas
"""

import pandas as pd
import numpy as np
import re
from pathlib import Path
from datetime import datetime
import json

class PatentDataCleaner:
    def __init__(self, data_dir="../data"):
        self.data_dir = Path(data_dir)
        self.processed_dir = self.data_dir / "processed"
        self.processed_dir.mkdir(exist_ok=True)
        
    def load_data(self, filename="sample_patent_data.csv"):
        """Load raw patent data"""
        file_path = self.data_dir / filename
        try:
            df = pd.read_csv(file_path)
            print(f"Loaded {len(df)} records from {file_path}")
            return df
        except FileNotFoundError:
            print(f"Error: File {file_path} not found")
            return None
    
    def clean_text_fields(self, df):
        """Clean text fields (titles, abstracts)"""
        text_columns = ['patent_title', 'patent_abstract']
        
        for col in text_columns:
            if col in df.columns:
                # Remove extra whitespace
                df[col] = df[col].astype(str).str.strip()
                # Remove special characters but keep basic punctuation
                df[col] = df[col].apply(lambda x: re.sub(r'[^\w\s\.\,\-\:]', '', x))
                # Handle missing values
                df[col] = df[col].replace('nan', np.nan)
                
        print("Text fields cleaned")
        return df
    
    def clean_dates(self, df):
        """Clean and standardize date fields"""
        date_columns = ['patent_date']
        
        for col in date_columns:
            if col in df.columns:
                # Convert to datetime
                df[col] = pd.to_datetime(df[col], errors='coerce')
                # Extract year, month for analysis
                df[f'{col}_year'] = df[col].dt.year
                df[f'{col}_month'] = df[col].dt.month
                
        print("Date fields cleaned")
        return df
    
    def clean_inventor_names(self, df):
        """Clean inventor name fields"""
        name_columns = ['inventor_first_name', 'inventor_last_name']
        
        for col in name_columns:
            if col in df.columns:
                # Convert to string, strip whitespace, title case
                df[col] = df[col].astype(str).str.strip().str.title()
                # Handle missing values
                df[col] = df[col].replace('Nan', np.nan)
                
        # Create full inventor name
        if 'inventor_first_name' in df.columns and 'inventor_last_name' in df.columns:
            df['inventor_full_name'] = df['inventor_first_name'] + ' ' + df['inventor_last_name']
            df['inventor_full_name'] = df['inventor_full_name'].str.strip()
            
        print("Inventor names cleaned")
        return df
    
    def clean_company_names(self, df):
        """Clean company/assignee names"""
        company_columns = ['assignee_organization']
        
        for col in company_columns:
            if col in df.columns:
                # Convert to string, strip whitespace
                df[col] = df[col].astype(str).str.strip()
                # Remove common legal entity suffixes for standardization
                df[col] = df[col].apply(lambda x: re.sub(r'\s+(Inc|LLC|Corp|Corporation|Ltd|Limited)\.?$', '', x, flags=re.IGNORECASE))
                
        print("Company names cleaned")
        return df
    
    def clean_classification_codes(self, df):
        """Clean patent classification codes"""
        classification_columns = ['cpc_section', 'cpc_subsection']
        
        for col in classification_columns:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip().str.upper()
                df[col] = df[col].replace('NAN', np.nan)
                
        print("Classification codes cleaned")
        return df
    
    def handle_missing_values(self, df):
        """Handle missing values in the dataset"""
        # Show missing value summary
        missing_summary = df.isnull().sum()
        print("\nMissing values before cleaning:")
        print(missing_summary[missing_summary > 0])
        
        # Strategy for different column types
        text_columns = ['patent_title', 'patent_abstract', 'inventor_first_name', 
                       'inventor_last_name', 'assignee_organization']
        numeric_columns = ['patent_number_cited_by_us_patents']
        
        # Fill missing text values with appropriate placeholders
        for col in text_columns:
            if col in df.columns:
                df[col] = df[col].fillna('Unknown')
                
        # Fill missing numeric values with 0
        for col in numeric_columns:
            if col in df.columns:
                df[col] = df[col].fillna(0)
                
        # Drop rows with missing critical data
        critical_columns = ['patent_number', 'patent_title']
        df = df.dropna(subset=critical_columns)
        
        print(f"\nMissing values handled. Dataset now has {len(df)} records")
        return df
    
    def create_derived_features(self, df):
        """Create derived features for analysis"""
        # Title length
        if 'patent_title' in df.columns:
            df['title_length'] = df['patent_title'].str.len()
            
        # Abstract length
        if 'patent_abstract' in df.columns:
            df['abstract_length'] = df['patent_abstract'].str.len()
            
        # Citation ranges
        if 'patent_number_cited_by_us_patents' in df.columns:
            df['citation_category'] = pd.cut(df['patent_number_cited_by_us_patents'], 
                                           bins=[0, 5, 15, 50, float('inf')],
                                           labels=['Low', 'Medium', 'High', 'Very High'])
            
        print("Derived features created")
        return df
    
    def validate_data(self, df):
        """Validate data quality"""
        validation_results = {}
        
        # Check for duplicate patent numbers
        if 'patent_number' in df.columns:
            duplicates = df['patent_number'].duplicated().sum()
            validation_results['duplicate_patents'] = duplicates
            
        # Check date ranges
        if 'patent_date_year' in df.columns:
            invalid_years = df[(df['patent_date_year'] < 1976) | (df['patent_date_year'] > 2025)].shape[0]
            validation_results['invalid_years'] = invalid_years
            
        # Check for empty critical fields
        if 'patent_title' in df.columns:
            empty_titles = df[df['patent_title'] == ''].shape[0]
            validation_results['empty_titles'] = empty_titles
            
        print("\nData Validation Results:")
        for key, value in validation_results.items():
            print(f"  {key}: {value}")
            
        return df, validation_results
    
    def save_cleaned_data(self, df, filename="cleaned_patent_data.csv"):
        """Save cleaned data"""
        output_path = self.processed_dir / filename
        df.to_csv(output_path, index=False)
        print(f"Cleaned data saved to {output_path}")
        
        # Also save as JSON for API usage
        json_path = self.processed_dir / filename.replace('.csv', '.json')
        df.to_json(json_path, orient='records', indent=2)
        print(f"Data also saved as JSON to {json_path}")
        
        return output_path
    
    def generate_data_summary(self, df):
        """Generate data summary statistics"""
        summary = {
            'total_records': len(df),
            'date_range': {
                'start': df['patent_date'].min().strftime('%Y-%m-%d') if 'patent_date' in df.columns else None,
                'end': df['patent_date'].max().strftime('%Y-%m-%d') if 'patent_date' in df.columns else None
            },
            'unique_inventors': df['inventor_full_name'].nunique() if 'inventor_full_name' in df.columns else 0,
            'unique_companies': df['assignee_organization'].nunique() if 'assignee_organization' in df.columns else 0,
            'columns': list(df.columns),
            'data_types': df.dtypes.to_dict()
        }
        
        # Save summary
        summary_path = self.processed_dir / "data_summary.json"
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
            
        print(f"Data summary saved to {summary_path}")
        return summary
    
    def run_full_cleaning_pipeline(self, input_filename="sample_patent_data.csv"):
        """Run the complete data cleaning pipeline"""
        print("Starting data cleaning pipeline...")
        
        # Load data
        df = self.load_data(input_filename)
        if df is None:
            return None
            
        # Apply cleaning steps
        df = self.clean_text_fields(df)
        df = self.clean_dates(df)
        df = self.clean_inventor_names(df)
        df = self.clean_company_names(df)
        df = self.clean_classification_codes(df)
        df = self.handle_missing_values(df)
        df = self.create_derived_features(df)
        df, validation_results = self.validate_data(df)
        
        # Save cleaned data
        self.save_cleaned_data(df)
        
        # Generate summary
        summary = self.generate_data_summary(df)
        
        print("\nData cleaning pipeline completed successfully!")
        return df, summary, validation_results

if __name__ == "__main__":
    cleaner = PatentDataCleaner()
    
    # Run the full cleaning pipeline
    cleaned_df, summary, validation = cleaner.run_full_cleaning_pipeline()
    
    if cleaned_df is not None:
        print(f"\nFinal dataset shape: {cleaned_df.shape}")
        print("\nSample of cleaned data:")
        print(cleaned_df.head())
        
        print(f"\nNext step: Run database_setup.py to store data in SQL database")
