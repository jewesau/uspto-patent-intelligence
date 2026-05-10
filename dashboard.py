#!/usr/bin/env python3
"""
Global Patent Intelligence Data Pipeline - Streamlit Dashboard
Interactive web dashboard for patent intelligence analysis
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sqlite3
from pathlib import Path
import json

# Page configuration
st.set_page_config(
    page_title="Patent Intelligence Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .stDataFrame {
        border-radius: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

class PatentDashboard:
    def __init__(self, db_path="database/patent_intelligence.db"):
        self.db_path = Path(db_path)
        
    def connect(self):
        """Establish database connection"""
        return sqlite3.connect(self.db_path)
    
    def get_overview_stats(self):
        """Get overview statistics"""
        conn = self.connect()
        query = '''
            SELECT 
                COUNT(*) as total_patents,
                COUNT(DISTINCT i.id) as unique_inventors,
                COUNT(DISTINCT c.id) as unique_companies,
                COUNT(DISTINCT inventor_country) as unique_countries,
                MIN(patent_date) as earliest_patent,
                MAX(patent_date) as latest_patent,
                AVG(patent_number_cited_by_us_patents) as avg_citations
            FROM patents p
            LEFT JOIN patent_inventors pi ON p.patent_number = pi.patent_number
            LEFT JOIN inventors i ON pi.inventor_id = i.id
            LEFT JOIN patent_companies pc ON p.patent_number = pc.patent_number
            LEFT JOIN companies c ON pc.company_id = c.id
        '''
        stats = pd.read_sql_query(query, conn)
        conn.close()
        return stats.iloc[0]
    
    def get_top_inventors(self, limit=10):
        """Get top inventors"""
        conn = self.connect()
        query = '''
            SELECT 
                i.inventor_full_name as name,
                COUNT(pi.patent_number) as patents,
                AVG(p.patent_number_cited_by_us_patents) as avg_citations
            FROM inventors i
            JOIN patent_inventors pi ON i.id = pi.inventor_id
            JOIN patents p ON pi.patent_number = p.patent_number
            WHERE i.inventor_full_name NOT LIKE '%Unknown%'
            GROUP BY i.inventor_full_name
            ORDER BY patents DESC
            LIMIT ?
        '''
        df = pd.read_sql_query(query, conn, params=(limit,))
        conn.close()
        return df
    
    def get_top_companies(self, limit=10):
        """Get top companies"""
        conn = self.connect()
        query = '''
            SELECT 
                c.company_name as name,
                COUNT(pc.patent_number) as patents,
                AVG(p.patent_number_cited_by_us_patents) as avg_citations
            FROM companies c
            JOIN patent_companies pc ON c.id = pc.company_id
            JOIN patents p ON pc.patent_number = p.patent_number
            WHERE c.company_name NOT LIKE '%Unknown%'
            GROUP BY c.company_name
            ORDER BY patents DESC
            LIMIT ?
        '''
        df = pd.read_sql_query(query, conn, params=(limit,))
        conn.close()
        return df
    
    def get_country_stats(self):
        """Get country statistics"""
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
        '''
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    
    def get_technology_stats(self):
        """Get technology category statistics"""
        conn = self.connect()
        query = '''
            SELECT 
                cpc_section,
                COUNT(*) as patents,
                AVG(patent_number_cited_by_us_patents) as avg_citations
            FROM patents 
            WHERE cpc_section IS NOT NULL
            GROUP BY cpc_section
            ORDER BY patents DESC
        '''
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    
    def get_patent_trends(self):
        """Get patent trends over time"""
        conn = self.connect()
        query = '''
            SELECT 
                patent_date_year as year,
                patent_date_month as month,
                COUNT(*) as patents
            FROM patents 
            WHERE patent_date_year IS NOT NULL
            GROUP BY patent_date_year, patent_date_month
            ORDER BY year, month
        '''
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df

def main():
    # Initialize dashboard
    dashboard = PatentDashboard()
    
    # Header
    st.markdown('<h1 class="main-header">📊 Patent Intelligence Dashboard</h1>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Sidebar
    st.sidebar.markdown("## 🎛️ Dashboard Controls")
    
    # Refresh button
    if st.sidebar.button("🔄 Refresh Data"):
        st.experimental_rerun()
    
    # Main content
    try:
        # Overview Statistics
        st.markdown("## 📈 Overview Statistics")
        stats = dashboard.get_overview_stats()
        
        # Create metrics columns
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Patents", f"{int(stats['total_patents']):,}")
        
        with col2:
            st.metric("Unique Inventors", f"{int(stats['unique_inventors']):,}")
        
        with col3:
            st.metric("Unique Companies", f"{int(stats['unique_companies']):,}")
        
        with col4:
            st.metric("Avg Citations", f"{stats['avg_citations']:.1f}")
        
        st.markdown("---")
        
        # Charts Section
        st.markdown("## 📊 Visual Analytics")
        
        # Get data
        top_inventors = dashboard.get_top_inventors()
        top_companies = dashboard.get_top_companies()
        country_stats = dashboard.get_country_stats()
        tech_stats = dashboard.get_technology_stats()
        patent_trends = dashboard.get_patent_trends()
        
        # Create chart layout
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🏆 Top Inventors")
            if not top_inventors.empty:
                fig_inventors = px.bar(
                    top_inventors, 
                    x='patents', 
                    y='name',
                    orientation='h',
                    title='Patents by Inventor',
                    color='avg_citations',
                    color_continuous_scale='Blues'
                )
                fig_inventors.update_layout(height=400)
                st.plotly_chart(fig_inventors, width='stretch')
            else:
                st.info("No inventor data available")
        
        with col2:
            st.markdown("### 🏢 Top Companies")
            if not top_companies.empty:
                fig_companies = px.bar(
                    top_companies, 
                    x='patents', 
                    y='name',
                    orientation='h',
                    title='Patents by Company',
                    color='avg_citations',
                    color_continuous_scale='Reds'
                )
                fig_companies.update_layout(height=400)
                st.plotly_chart(fig_companies, width='stretch')
            else:
                st.info("No company data available")
        
        # Second row of charts
        col3, col4 = st.columns(2)
        
        with col3:
            st.markdown("### 🌍 Country Distribution")
            if not country_stats.empty:
                fig_countries = px.pie(
                    country_stats, 
                    values='patents', 
                    names='country',
                    title='Patents by Country'
                )
                fig_countries.update_layout(height=400)
                st.plotly_chart(fig_countries, width='stretch')
            else:
                st.info("No country data available")
        
        with col4:
            st.markdown("### 🔬 Technology Categories")
            if not tech_stats.empty:
                fig_tech = px.bar(
                    tech_stats, 
                    x='cpc_section', 
                    y='patents',
                    title='Patents by Technology Category',
                    color='avg_citations',
                    color_continuous_scale='Viridis'
                )
                fig_tech.update_layout(height=400)
                st.plotly_chart(fig_tech, width='stretch')
            else:
                st.info("No technology data available")
        
        # Patent trends
        st.markdown("### 📅 Patent Trends Over Time")
        if not patent_trends.empty:
            fig_trends = px.line(
                patent_trends, 
                x='year', 
                y='patents',
                title='Patent Filing Trends',
                markers=True
            )
            fig_trends.update_layout(height=400)
            st.plotly_chart(fig_trends, width='stretch')
        else:
            st.info("No trend data available")
        
        st.markdown("---")
        
        # Data Tables Section
        st.markdown("## 📋 Detailed Data Tables")
        
        # Tabs for different data views
        tab1, tab2, tab3, tab4 = st.tabs(["🏆 Top Inventors", "🏢 Top Companies", "🌍 Countries", "🔬 Technologies"])
        
        with tab1:
            if not top_inventors.empty:
                st.dataframe(top_inventors, width='stretch')
            else:
                st.info("No inventor data available")
        
        with tab2:
            if not top_companies.empty:
                st.dataframe(top_companies, width='stretch')
            else:
                st.info("No company data available")
        
        with tab3:
            if not country_stats.empty:
                st.dataframe(country_stats, width='stretch')
            else:
                st.info("No country data available")
        
        with tab4:
            if not tech_stats.empty:
                st.dataframe(tech_stats, width='stretch')
            else:
                st.info("No technology data available")
        
        # Footer
        st.markdown("---")
        st.markdown("### 📊 About This Dashboard")
        st.markdown("""
        This interactive dashboard provides real-time insights into patent intelligence data. 
        It visualizes key metrics including inventor productivity, company performance, 
        geographic distribution, and technology trends.
        
        **Data Source:** USPTO PatentsView Database  
        **Pipeline:** Global Patent Intelligence Data Pipeline  
        **Last Updated: """ + pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S') + """
        """)
        
    except Exception as e:
        st.error(f"Error loading dashboard: {str(e)}")
        st.info("Please make sure the pipeline has been run first by executing: `python main.py`")

if __name__ == "__main__":
    main()
