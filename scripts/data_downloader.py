#!/usr/bin/env python3
"""
Global Patent Intelligence Data Pipeline - Data Downloader
Handles downloading and processing of patent data from USPTO PatentsView and real USPTO files
"""

import pandas as pd
import requests
import json
import time
from pathlib import Path
import random
import numpy as np
from uspto_data_processor import USPTODataProcessor

class PatentDataDownloader:
    def __init__(self, data_dir="../data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # USPTO PatentsView API endpoints
        self.base_url = "https://api.patentsview.org"
        self.bulk_data_url = "https://download.patentsview.org"
        
    def download_via_api(self, query, entity="patent", per_page=100):
        """
        Download patent data using PatentsView API
        Entity options: patent, inventor, assignee, location
        """
        url = f"{self.base_url}/{entity}/query.json"
        
        all_data = []
        page = 1
        
        while True:
            payload = {
                "q": query,
                "f": ["patent_number", "patent_title", "patent_abstract", 
                      "patent_date", "patent_type", "patent_number_cited_by_us_patents"],
                "o": {"per_page": per_page, "page": page}
            }
            
            try:
                response = requests.post(url, json=payload)
                response.raise_for_status()
                
                data = response.json()
                patents = data.get('patents', [])
                
                if not patents:
                    break
                    
                all_data.extend(patents)
                print(f"Downloaded page {page}, {len(patents)} patents")
                page += 1
                time.sleep(1)  # Rate limiting
                
            except requests.exceptions.RequestException as e:
                print(f"Error downloading data: {e}")
                break
                
        return all_data
    
    def process_real_uspto_data(self):
        """Process real USPTO data files from lecturer"""
        print("Processing real USPTO patent data files...")
        
        try:
            processor = USPTODataProcessor(self.data_dir)
            processed_df = processor.process_uspto_data(sample_size=None)  # Process all data
            
            if processed_df is not None:
                print(f"Successfully processed {len(processed_df)} patent records")
                return processed_df
            else:
                print("Failed to process USPTO data")
                return None
                
        except Exception as e:
            print(f"Error processing USPTO data: {e}")
            return None
    
    def download_patent_data(self):
        """Download patent data from USPTO PatentsView API"""
        print("Downloading patent data from USPTO PatentsView...")
        
        try:
            # First try to process real USPTO data files
            real_data = self.process_real_uspto_data()
            if real_data is not None:
                return real_data
            
            # Fallback to API data if real data not available
            print("Real USPTO data not found, using API data...")
            return self.download_via_api()
        except Exception as e:
            print(f"Data acquisition failed: {e}")
            return self.create_sample_data()
    
    def create_sample_data(self):
        """
        Create sample patent data for demonstration when API is not accessible
        """
        sample_data = [
            {
                "patent_number": "US1234567",
                "patent_title": "Method for Processing Data Using Machine Learning",
                "patent_abstract": "A method and system for processing large datasets using advanced machine learning algorithms...",
                "patent_date": "2023-05-15",
                "patent_type": "utility",
                "inventor_first_name": "John",
                "inventor_last_name": "Smith",
                "assignee_organization": "Tech Innovations Inc.",
                "cpc_subsection": "G",
                "cpc_section": "G06F",
                "patent_number_cited_by_us_patents": 15,
                "inventor_country": "USA",
                "assignee_country": "USA"
            },
            {
                "patent_number": "US1234568",
                "patent_title": "Advanced Battery Technology for Electric Vehicles",
                "patent_abstract": "An improved battery system for electric vehicles that provides extended range and faster charging...",
                "patent_date": "2023-06-20",
                "patent_type": "utility",
                "inventor_first_name": "Sarah",
                "inventor_last_name": "Johnson",
                "assignee_organization": "Green Energy Solutions",
                "cpc_subsection": "H",
                "cpc_section": "H01M",
                "patent_number_cited_by_us_patents": 8,
                "inventor_country": "USA",
                "assignee_country": "USA"
            },
            {
                "patent_number": "US1234569",
                "patent_title": "Medical Device for Patient Monitoring",
                "patent_abstract": "A wearable medical device that continuously monitors vital signs and alerts healthcare providers...",
                "patent_date": "2023-07-10",
                "patent_type": "utility",
                "inventor_first_name": "Michael",
                "inventor_last_name": "Brown",
                "assignee_organization": "MedTech Corp",
                "cpc_subsection": "A",
                "cpc_section": "A61B",
                "patent_number_cited_by_us_patents": 12,
                "inventor_country": "USA",
                "assignee_country": "USA"
            },
            {
                "patent_number": "US1234570",
                "patent_title": "Artificial Intelligence System for Data Analysis",
                "patent_abstract": "An AI-powered system for automated analysis of complex datasets and pattern recognition...",
                "patent_date": "2023-08-01",
                "patent_type": "utility",
                "inventor_first_name": "Emily",
                "inventor_last_name": "Davis",
                "assignee_organization": "AI Research Labs",
                "cpc_subsection": "G",
                "cpc_section": "G06N",
                "patent_number_cited_by_us_patents": 25,
                "inventor_country": "USA",
                "assignee_country": "USA"
            },
            {
                "patent_number": "US1234571",
                "patent_title": "Sustainable Packaging Material",
                "patent_abstract": "A biodegradable packaging material made from renewable resources that reduces environmental impact...",
                "patent_date": "2023-09-05",
                "patent_type": "utility",
                "inventor_first_name": "Robert",
                "inventor_last_name": "Wilson",
                "assignee_organization": "EcoPack Solutions",
                "cpc_subsection": "B",
                "cpc_section": "B65D",
                "patent_number_cited_by_us_patents": 6,
                "inventor_country": "USA",
                "assignee_country": "USA"
            }
        ]
        
        # Save sample data
        df = pd.DataFrame(sample_data)
        sample_file = self.data_dir / "sample_patent_data.csv"
        df.to_csv(sample_file, index=False)
        print(f"Sample data saved to {sample_file}")
        
        return df
    
    def download_bulk_data(self, dataset_name="pg_patents"):
        """
        Attempt to download bulk data from PatentsView
        Note: This may require manual download due to website restrictions
        """
        print("Bulk data download requires manual access to USPTO website")
        print("Please visit: https://data.uspto.gov/bulkdata/datasets")
        print("Download the PV_grant_data_dictionary.pdf and relevant data files")
        return None

if __name__ == "__main__":
    downloader = PatentDataDownloader()
    
    # Create sample data for demonstration
    print("Creating sample patent data...")
    sample_df = downloader.create_sample_data()
    
    print("\nSample data preview:")
    print(sample_df.head())
    
    print(f"\nData saved to: {downloader.data_dir}")
    print("Next step: Run data_cleaner.py to process the data")
