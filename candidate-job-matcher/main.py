"""
Candidate-Job Matcher Application
Main Streamlit Entry Point - Home Page
"""

import streamlit as st
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="Candidate-Job Matcher",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #555;
        text-align: center;
        margin-bottom: 2rem;
    }
    .feature-box {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .feature-title {
        font-size: 1.3rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .feature-desc {
        color: #666;
        font-size: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# Main content
st.markdown('<div class="main-header">LLM-Powered Candidate-Job Matcher</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Intelligent Resume Analysis Using AI</div>', unsafe_allow_html=True)

st.markdown("---")

# Introduction
st.markdown("""
### Welcome to the Candidate-Job Matching System

This application uses **Azure OpenAI GPT-4** to analyze candidate resumes against job descriptions, 
providing intelligent matching, skill analysis, and actionable feedback.
""")

# Features
st.markdown("## Key Features")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="feature-box">
        <div class="feature-title">Job Management</div>
        <div class="feature-desc">
            Create and manage job descriptions with detailed requirements and qualifications.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="feature-box">
        <div class="feature-title">Resume Parsing</div>
        <div class="feature-desc">
            Upload resumes in PDF, DOCX, or TXT format. Automatic text extraction and parsing.
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-box">
        <div class="feature-title">AI-Powered Analysis</div>
        <div class="feature-desc">
            Advanced LLM analysis providing relevance scores, skill matching, and detailed feedback.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="feature-box">
        <div class="feature-title">Interactive Results</div>
        <div class="feature-desc">
            View ranked candidates with sortable tables, visualizations, and export capabilities.
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# How it works
st.markdown("## How It Works")

step_col1, step_col2, step_col3, step_col4 = st.columns(4)

with step_col1:
    st.markdown("### 1. Create Job")
    st.markdown("Define job title, description, and requirements")

with step_col2:
    st.markdown("### 2. Upload Resumes")
    st.markdown("Upload candidate resumes in supported formats")

with step_col3:
    st.markdown("### 3. Analyze")
    st.markdown("AI analyzes each resume against job requirements")

with step_col4:
    st.markdown("### 4. Review Results")
    st.markdown("View ranked candidates with detailed insights")

st.markdown("---")

# Statistics (if database has data)
try:
    from app.database import DatabaseSession, Job, Candidate, AnalysisResult
    
    with DatabaseSession() as db:
        total_jobs = db.query(Job).count()
        total_candidates = db.query(Candidate).count()
        total_analyses = db.query(AnalysisResult).count()
    
    st.markdown("## System Statistics")
    
    stat_col1, stat_col2, stat_col3 = st.columns(3)
    
    with stat_col1:
        st.metric("Total Jobs", total_jobs)
    
    with stat_col2:
        st.metric("Total Candidates", total_candidates)
    
    with stat_col3:
        st.metric("Analyses Completed", total_analyses)

except Exception as e:
    pass

st.markdown("---")

# Quick start guide
st.markdown("## Quick Start Guide")

with st.expander("Getting Started"):
    st.markdown("""
    1. **Navigate to Job Management** (sidebar) to create your first job posting
    2. **Go to Candidate Upload** to upload resumes for that job
    3. **Visit Analysis Results** to run AI analysis and view results
    4. **Use Export Data** to download results as CSV or JSON
    
    Need help? Each page has detailed instructions and helpful tooltips.
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem;">
    <p>Powered by Azure OpenAI GPT-4 | Built with Streamlit & LangChain</p>
    <p>Version 1.0.0</p>
</div>
""", unsafe_allow_html=True)