"""
Analysis Results Page
View and manage candidate analysis results
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

from app.database import DatabaseSession, Job, Candidate, AnalysisResult, AnalysisStatus
from app.services.analysis_service import (
    analyze_and_store_candidate,
    analyze_all_candidates_for_job,
    get_candidates_with_analysis,
    get_analysis_statistics
)
from app.utils.helpers import format_percentage, get_time_ago

# Page config
st.set_page_config(
    page_title="Analysis Results",
    page_icon="📊",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
    }
    .score-high {
        color: #28a745;
        font-size: 2rem;
        font-weight: bold;
    }
    .score-medium {
        color: #ffc107;
        font-size: 2rem;
        font-weight: bold;
    }
    .score-low {
        color: #dc3545;
        font-size: 2rem;
        font-weight: bold;
    }
    .candidate-card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 5px solid #1f77b4;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .skill-badge {
        display: inline-block;
        background-color: #e3f2fd;
        color: #1976d2;
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        margin: 0.2rem;
        font-size: 0.85rem;
    }
    .skill-badge-missing {
        display: inline-block;
        background-color: #ffebee;
        color: #c62828;
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        margin: 0.2rem;
        font-size: 0.85rem;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.title("Analysis Results")
st.markdown("AI-powered candidate analysis and ranking")
st.markdown("---")

# ==========================================
# Job Selection
# ==========================================

st.subheader("Select Job Position")

try:
    with DatabaseSession() as db:
        jobs = db.query(Job).order_by(Job.created_at.desc()).all()
        
        if not jobs:
            st.warning("No jobs found. Please create a job first.")
            st.stop()
        
        # Job selection
        job_options = {f"{job.title} (ID: {job.id})": job.id for job in jobs}
        selected_job_display = st.selectbox(
            "Choose Job",
            options=list(job_options.keys()),
            key="selected_job_analysis"
        )
        
        selected_job_id = job_options[selected_job_display]
        selected_job = db.query(Job).filter(Job.id == selected_job_id).first()
        
        # Get candidates count
        candidates_count = db.query(Candidate).filter(Candidate.job_id == selected_job_id).count()
        
        if candidates_count == 0:
            st.info("No candidates found for this job. Please upload resumes in the 'Candidate Upload' page.")
            st.stop()

except Exception as e:
    st.error(f"Error loading jobs: {str(e)}")
    st.stop()

st.markdown("---")

# ==========================================
# Statistics Section
# ==========================================

st.subheader("Analysis Statistics")

stats = get_analysis_statistics(selected_job_id)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Candidates", stats["total_candidates"])

with col2:
    st.metric("Analyzed", stats["analyzed"])

with col3:
    st.metric("Pending", stats["pending"])

with col4:
    st.metric("Average Score", f"{stats['average_score']:.1f}/100" if stats['analyzed'] > 0 else "N/A")

# Progress bar
if stats["total_candidates"] > 0:
    progress = stats["analyzed"] / stats["total_candidates"]
    st.progress(progress)
    st.caption(f"Analysis Progress: {format_percentage(stats['completion_rate'])}")

st.markdown("---")

# ==========================================
# Analysis Actions
# ==========================================

st.subheader("Run Analysis")

action_col1, action_col2 = st.columns(2)

with action_col1:
    if st.button("Analyze All Candidates", type="primary", use_container_width=True):
        if stats["pending"] == 0:
            st.info("All candidates have already been analyzed!")
        else:
            with st.spinner(f"Analyzing {stats['pending']} candidate(s)... This may take a few minutes."):
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                result = analyze_all_candidates_for_job(selected_job_id)
                
                progress_bar.empty()
                status_text.empty()
                
                if result["success"]:
                    st.success(f"Analysis complete! {result['analyzed']}/{result['total_candidates']} candidates analyzed successfully.")
                    if result["failed"] > 0:
                        st.warning(f"{result['failed']} candidate(s) failed analysis.")
                    st.rerun()
                else:
                    st.error(f"Analysis failed: {result['error']}")

with action_col2:
    if st.button("Refresh Results", use_container_width=True):
        st.rerun()

st.markdown("---")

# ==========================================
# Results Display
# ==========================================

st.subheader("Candidate Rankings")

# Get candidates with analysis
candidates_data = get_candidates_with_analysis(selected_job_id, sort_by="score")

# Filter options
filter_col1, filter_col2 = st.columns([2, 2])

with filter_col1:
    sort_option = st.selectbox(
        "Sort By",
        ["Relevance Score (High to Low)", "Relevance Score (Low to High)", "Name (A-Z)", "Upload Date (Recent First)"],
        key="sort_candidates"
    )
    
    # Apply sorting
    if sort_option == "Relevance Score (High to Low)":
        candidates_data = sorted(
            candidates_data,
            key=lambda x: x["analysis"]["relevance_score"] if x["has_analysis"] else -1,
            reverse=True
        )
    elif sort_option == "Relevance Score (Low to High)":
        candidates_data = sorted(
            candidates_data,
            key=lambda x: x["analysis"]["relevance_score"] if x["has_analysis"] else 999,
            reverse=False
        )
    elif sort_option == "Name (A-Z)":
        candidates_data = sorted(candidates_data, key=lambda x: x["name"])
    elif sort_option == "Upload Date (Recent First)":
        candidates_data = sorted(candidates_data, key=lambda x: x["uploaded_at"], reverse=True)

with filter_col2:
    min_score = st.slider(
        "Minimum Relevance Score",
        min_value=0,
        max_value=100,
        value=0,
        step=5,
        key="min_score_filter"
    )
    
    # Filter by score
    candidates_data = [c for c in candidates_data if c["has_analysis"] and c["analysis"]["relevance_score"] >= min_score]

# Display mode
display_mode = st.radio(
    "Display Mode",
    ["Detailed Cards", "Summary Table"],
    horizontal=True,
    key="display_mode"
)

st.markdown("---")

if not candidates_data:
    st.info("No candidates match the current filters or no analysis has been completed yet.")
else:
    st.markdown(f"**Showing {len(candidates_data)} candidate(s)**")
    
    # ==========================================
    # Detailed Cards View
    # ==========================================
    
    if display_mode == "Detailed Cards":
        
        for idx, candidate in enumerate(candidates_data, 1):
            analysis = candidate["analysis"]
            score = analysis["relevance_score"]
            
            # Score color
            if score >= 80:
                score_class = "score-high"
            elif score >= 60:
                score_class = "score-medium"
            else:
                score_class = "score-low"
            
            with st.container():
                # Header row
                header_col1, header_col2 = st.columns([4, 1])
                
                with header_col1:
                    st.markdown(f"### {idx}. {candidate['name']}")
                    if candidate['email']:
                        st.caption(f"Email: {candidate['email']}")
                
                with header_col2:
                    st.markdown(f'<div class="{score_class}">{score:.1f}/100</div>', unsafe_allow_html=True)
                    st.caption("Relevance Score")
                
                # Metrics row
                metric_col1, metric_col2, metric_col3 = st.columns(3)
                
                with metric_col1:
                    matched_count = len(analysis["matched_skills"])
                    st.metric("Matched Skills", matched_count)
                
                with metric_col2:
                    missing_count = len(analysis["missing_skills"])
                    st.metric("Missing Skills", missing_count)
                
                with metric_col3:
                    if analysis.get("experience_match"):
                        st.metric("Experience Match", f"{analysis['experience_match']:.0f}%")
                
                # Skills section
                st.markdown("**Matched Skills:**")
                if analysis["matched_skills"]:
                    skills_html = " ".join([f'<span class="skill-badge">{skill}</span>' for skill in analysis["matched_skills"]])
                    st.markdown(skills_html, unsafe_allow_html=True)
                else:
                    st.caption("None identified")
                
                st.markdown("**Missing Skills:**")
                if analysis["missing_skills"]:
                    skills_html = " ".join([f'<span class="skill-badge-missing">{skill}</span>' for skill in analysis["missing_skills"]])
                    st.markdown(skills_html, unsafe_allow_html=True)
                else:
                    st.caption("None identified")
                
                # Feedback section
                with st.expander("View Detailed Feedback"):
                    st.markdown("**AI Analysis:**")
                    st.write(analysis["feedback"])
                    
                    if analysis.get("strengths"):
                        st.markdown("**Strengths:**")
                        for strength in analysis["strengths"]:
                            st.markdown(f"- {strength}")
                    
                    if analysis.get("weaknesses"):
                        st.markdown("**Areas for Improvement:**")
                        for weakness in analysis["weaknesses"]:
                            st.markdown(f"- {weakness}")
                    
                    st.caption(f"Analyzed: {get_time_ago(analysis['analyzed_at'])}")
                
                st.markdown("---")
    
    # ==========================================
    # Summary Table View
    # ==========================================
    
    else:
        # Prepare dataframe
        table_data = []
        for idx, candidate in enumerate(candidates_data, 1):
            analysis = candidate["analysis"]
            table_data.append({
                "Rank": idx,
                "Name": candidate["name"],
                "Email": candidate.get("email", "N/A"),
                "Score": f"{analysis['relevance_score']:.1f}",
                "Matched Skills": len(analysis["matched_skills"]),
                "Missing Skills": len(analysis["missing_skills"]),
                "Experience Match": f"{analysis.get('experience_match', 0):.0f}%" if analysis.get('experience_match') else "N/A"
            })
        
        df = pd.DataFrame(table_data)
        
        # Display table
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Score": st.column_config.NumberColumn(
                    "Score",
                    help="Relevance score out of 100",
                    format="%.1f"
                )
            }
        )
        
        # Download CSV
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download Table as CSV",
            data=csv,
            file_name=f"candidates_analysis_{selected_job.title}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )

# ==========================================
# Visualizations
# ==========================================

if candidates_data:
    st.markdown("---")
    st.subheader("Analysis Visualizations")
    
    viz_col1, viz_col2 = st.columns(2)
    
    with viz_col1:
        # Score distribution
        scores = [c["analysis"]["relevance_score"] for c in candidates_data if c["has_analysis"]]
        
        fig = px.histogram(
            scores,
            nbins=10,
            title="Score Distribution",
            labels={"value": "Relevance Score", "count": "Number of Candidates"},
            color_discrete_sequence=["#1f77b4"]
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    with viz_col2:
        # Top candidates bar chart
        top_n = min(10, len(candidates_data))
        top_candidates = candidates_data[:top_n]
        
        names = [c["name"] for c in top_candidates]
        scores = [c["analysis"]["relevance_score"] for c in top_candidates]
        
        fig = go.Figure(data=[
            go.Bar(
                x=scores,
                y=names,
                orientation='h',
                marker_color='#1f77b4'
            )
        ])
        fig.update_layout(
            title=f"Top {top_n} Candidates",
            xaxis_title="Relevance Score",
            yaxis_title="Candidate",
            yaxis=dict(autorange="reversed")
        )
        st.plotly_chart(fig, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("**Note:** Analysis is powered by Azure OpenAI GPT-4 and considers skills, experience, and overall fit.")