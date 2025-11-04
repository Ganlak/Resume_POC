"""
Export Data Page
Export candidate analysis results to CSV, JSON, and PDF formats
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import pandas as pd
from datetime import datetime
import io
import json

from app.database import DatabaseSession, Job, Candidate, AnalysisResult, AnalysisStatus
from app.services.analysis_service import get_candidates_with_analysis
from app.services.export_service import generate_pdf_report
from app.config import settings

# Page config
st.set_page_config(
    page_title="Export Data",
    page_icon="📥",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .export-card {
        background-color: #f0f2f6;
        padding: 2rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .format-option {
        background-color: white;
        padding: 1.5rem;
        border-radius: 8px;
        margin: 1rem 0;
        border: 2px solid #1f77b4;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.title("Export Data")
st.markdown("Export candidate analysis results to various formats")
st.markdown("---")

# ==========================================
# Job Selection
# ==========================================

st.subheader("Select Job to Export")

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
            key="selected_job_export"
        )
        
        selected_job_id = job_options[selected_job_display]
        selected_job_obj = db.query(Job).filter(Job.id == selected_job_id).first()
        
        # Extract data while still in session
        selected_job = {
            'id': selected_job_obj.id,
            'title': selected_job_obj.title,
            'description': selected_job_obj.description,
            'requirements': selected_job_obj.requirements,
            'location': selected_job_obj.location,
            'department': selected_job_obj.department
        }
        
        # Get analyzed candidates count
        analyzed_count = db.query(AnalysisResult).join(Candidate).filter(
            Candidate.job_id == selected_job_id,
            AnalysisResult.status == AnalysisStatus.COMPLETED
        ).count()
        
        if analyzed_count == 0:
            st.info("No analyzed candidates found for this job. Please run analysis first in the 'Analysis Results' page.")
            st.stop()
        
        st.success(f"Found {analyzed_count} analyzed candidate(s) ready for export")

except Exception as e:
    st.error(f"Error loading jobs: {str(e)}")
    st.stop()

st.markdown("---")

# ==========================================
# Export Options
# ==========================================

st.subheader("Export Options")

export_format = st.radio(
    "Select Export Format",
    ["CSV (Spreadsheet)", "Detailed CSV (with Feedback)", "JSON", "PDF Report"],
    key="export_format"
)

# Filter options
st.markdown("### Filters")

filter_col1, filter_col2 = st.columns(2)

with filter_col1:
    min_score_export = st.slider(
        "Minimum Relevance Score",
        min_value=0,
        max_value=100,
        value=0,
        step=5,
        key="min_score_export"
    )

with filter_col2:
    sort_by_export = st.selectbox(
        "Sort By",
        ["Relevance Score (High to Low)", "Relevance Score (Low to High)", "Name (A-Z)"],
        key="sort_export"
    )

st.markdown("---")

# ==========================================
# Preview Data
# ==========================================

st.subheader("Data Preview")

# Get candidates data
candidates_data = get_candidates_with_analysis(selected_job_id, sort_by="score")

# Apply filters
candidates_data = [c for c in candidates_data if c["has_analysis"] and c["analysis"]["relevance_score"] >= min_score_export]

# Apply sorting
if sort_by_export == "Relevance Score (High to Low)":
    candidates_data = sorted(
        candidates_data,
        key=lambda x: x["analysis"]["relevance_score"],
        reverse=True
    )
elif sort_by_export == "Relevance Score (Low to High)":
    candidates_data = sorted(
        candidates_data,
        key=lambda x: x["analysis"]["relevance_score"],
        reverse=False
    )
elif sort_by_export == "Name (A-Z)":
    candidates_data = sorted(candidates_data, key=lambda x: x["name"])

if not candidates_data:
    st.warning("No candidates match the selected filters.")
    st.stop()

st.info(f"Ready to export {len(candidates_data)} candidate(s)")

# ==========================================
# Generate Export Data
# ==========================================

def generate_csv_basic(candidates_data, job_title):
    """Generate basic CSV export"""
    data = []
    for idx, candidate in enumerate(candidates_data, 1):
        analysis = candidate["analysis"]
        data.append({
            "Rank": idx,
            "Name": candidate["name"],
            "Email": candidate.get("email", ""),
            "Phone": candidate.get("phone", ""),
            "Relevance Score": f"{analysis['relevance_score']:.2f}",
            "Matched Skills Count": len(analysis["matched_skills"]),
            "Missing Skills Count": len(analysis["missing_skills"]),
            "Matched Skills": ", ".join(analysis["matched_skills"]),
            "Missing Skills": ", ".join(analysis["missing_skills"]),
            "Experience Match": f"{analysis.get('experience_match', 0):.1f}%" if analysis.get('experience_match') else "",
            "Education Match": f"{analysis.get('education_match', 0):.1f}%" if analysis.get('education_match') else "",
            "File Name": candidate["file_name"],
            "Uploaded Date": candidate["uploaded_at"].strftime("%Y-%m-%d %H:%M:%S"),
            "Analyzed Date": analysis["analyzed_at"].strftime("%Y-%m-%d %H:%M:%S") if analysis["analyzed_at"] else ""
        })
    
    df = pd.DataFrame(data)
    return df

def generate_csv_detailed(candidates_data, job_title):
    """Generate detailed CSV export with feedback"""
    data = []
    for idx, candidate in enumerate(candidates_data, 1):
        analysis = candidate["analysis"]
        data.append({
            "Rank": idx,
            "Name": candidate["name"],
            "Email": candidate.get("email", ""),
            "Phone": candidate.get("phone", ""),
            "Relevance Score": f"{analysis['relevance_score']:.2f}",
            "Matched Skills": ", ".join(analysis["matched_skills"]),
            "Missing Skills": ", ".join(analysis["missing_skills"]),
            "Strengths": ", ".join(analysis.get("strengths", [])),
            "Weaknesses": ", ".join(analysis.get("weaknesses", [])),
            "Feedback": analysis["feedback"],
            "Experience Match": f"{analysis.get('experience_match', 0):.1f}%" if analysis.get('experience_match') else "",
            "Education Match": f"{analysis.get('education_match', 0):.1f}%" if analysis.get('education_match') else "",
            "File Name": candidate["file_name"],
            "Uploaded Date": candidate["uploaded_at"].strftime("%Y-%m-%d %H:%M:%S"),
            "Analyzed Date": analysis["analyzed_at"].strftime("%Y-%m-%d %H:%M:%S") if analysis["analyzed_at"] else ""
        })
    
    df = pd.DataFrame(data)
    return df

def generate_json_export(candidates_data, job_info):
    """Generate JSON export"""
    export_data = {
        "job": {
            "id": job_info['id'],
            "title": job_info['title'],
            "description": job_info['description'],
            "export_date": datetime.now().isoformat()
        },
        "candidates": []
    }
    
    for idx, candidate in enumerate(candidates_data, 1):
        analysis = candidate["analysis"]
        export_data["candidates"].append({
            "rank": idx,
            "name": candidate["name"],
            "email": candidate.get("email", ""),
            "phone": candidate.get("phone", ""),
            "relevance_score": analysis["relevance_score"],
            "matched_skills": analysis["matched_skills"],
            "missing_skills": analysis["missing_skills"],
            "strengths": analysis.get("strengths", []),
            "weaknesses": analysis.get("weaknesses", []),
            "feedback": analysis["feedback"],
            "experience_match": analysis.get("experience_match"),
            "education_match": analysis.get("education_match"),
            "file_name": candidate["file_name"],
            "uploaded_at": candidate["uploaded_at"].isoformat(),
            "analyzed_at": analysis["analyzed_at"].isoformat() if analysis["analyzed_at"] else None
        })
    
    return export_data

# Preview table
if export_format in ["CSV (Spreadsheet)", "Detailed CSV (with Feedback)"]:
    if export_format == "CSV (Spreadsheet)":
        preview_df = generate_csv_basic(candidates_data, selected_job['title'])
    else:
        preview_df = generate_csv_detailed(candidates_data, selected_job['title'])
    
    st.dataframe(preview_df.head(10), use_container_width=True)
    if len(preview_df) > 10:
        st.caption(f"Showing first 10 of {len(preview_df)} rows")

elif export_format == "JSON":
    json_data = generate_json_export(candidates_data, selected_job)
    st.json(json_data, expanded=False)

elif export_format == "PDF Report":
    st.info("PDF report will include: title page, executive summary, statistics, and detailed candidate analysis.")
    
    # Preview what will be in PDF
    st.markdown("**Report Contents:**")
    st.markdown(f"- Job Position: {selected_job['title']}")
    st.markdown(f"- Total Candidates: {len(candidates_data)}")
    avg_score = sum(c["analysis"]["relevance_score"] for c in candidates_data) / len(candidates_data)
    st.markdown(f"- Average Score: {avg_score:.1f}/100")
    st.markdown(f"- Generated: {datetime.now().strftime('%B %d, %Y')}")
    
    st.markdown("**Sections:**")
    st.markdown("1. Title Page")
    st.markdown("2. Executive Summary with Statistics")
    st.markdown("3. Top Candidates Ranking Table")
    st.markdown("4. Detailed Analysis for Each Candidate")

st.markdown("---")

# ==========================================
# Export Buttons
# ==========================================

st.subheader("Download Export")

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
job_title_safe = selected_job['title'].replace(" ", "_").replace("/", "_")

if export_format == "CSV (Spreadsheet)":
    df = generate_csv_basic(candidates_data, selected_job['title'])
    csv = df.to_csv(index=False)
    filename = f"candidates_analysis_{job_title_safe}_{timestamp}.csv"
    
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name=filename,
        mime="text/csv",
        type="primary",
        use_container_width=True
    )

elif export_format == "Detailed CSV (with Feedback)":
    df = generate_csv_detailed(candidates_data, selected_job['title'])
    csv = df.to_csv(index=False)
    filename = f"candidates_detailed_{job_title_safe}_{timestamp}.csv"
    
    st.download_button(
        label="Download Detailed CSV",
        data=csv,
        file_name=filename,
        mime="text/csv",
        type="primary",
        use_container_width=True
    )

elif export_format == "JSON":
    json_data = generate_json_export(candidates_data, selected_job)
    json_str = json.dumps(json_data, indent=2)
    filename = f"candidates_analysis_{job_title_safe}_{timestamp}.json"
    
    st.download_button(
        label="Download JSON",
        data=json_str,
        file_name=filename,
        mime="application/json",
        type="primary",
        use_container_width=True
    )

elif export_format == "PDF Report":
    try:
        # Generate PDF
        with st.spinner("Generating PDF report... This may take a few seconds."):
            pdf_buffer = generate_pdf_report(
                job_info=selected_job,
                candidates_data=candidates_data
            )
        
        filename = f"candidates_report_{job_title_safe}_{timestamp}.pdf"
        
        st.download_button(
            label="Download PDF Report",
            data=pdf_buffer,
            file_name=filename,
            mime="application/pdf",
            type="primary",
            use_container_width=True
        )
        
        st.success("PDF report generated successfully! Click the button above to download.")
    
    except Exception as e:
        st.error(f"Error generating PDF: {str(e)}")
        with st.expander("View Error Details"):
            st.exception(e)

st.markdown("---")

# ==========================================
# Export Summary
# ==========================================

st.subheader("Export Summary")

summary_col1, summary_col2, summary_col3 = st.columns(3)

with summary_col1:
    st.metric("Job Title", selected_job['title'])

with summary_col2:
    st.metric("Candidates Exported", len(candidates_data))

with summary_col3:
    avg_score = sum(c["analysis"]["relevance_score"] for c in candidates_data) / len(candidates_data)
    st.metric("Average Score", f"{avg_score:.1f}/100")

# Additional info
with st.expander("Export Information"):
    st.markdown(f"**Export Format:** {export_format}")
    st.markdown(f"**Minimum Score Filter:** {min_score_export}")
    st.markdown(f"**Sort Order:** {sort_by_export}")
    st.markdown(f"**Export Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    st.markdown(f"**Job Description:**")
    job_desc = selected_job['description']
    st.text(job_desc[:300] + "..." if len(job_desc) > 300 else job_desc)

# Footer
st.markdown("---")
st.markdown("**Export Formats:**")
st.markdown("- **CSV (Spreadsheet):** Basic candidate information and scores - Easy to open in Excel")
st.markdown("- **Detailed CSV:** Includes full feedback and analysis details - Complete data export")
st.markdown("- **JSON:** Machine-readable format for further processing and integrations")
st.markdown("- **PDF Report:** Professional formatted report with charts and detailed analysis")