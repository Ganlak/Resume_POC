"""
Candidate Upload Page
Upload and manage candidate resumes for job positions
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import os
from datetime import datetime

from app.database import DatabaseSession, Job, Candidate, JobStatus
from app.services.document_parser import parse_resume
from app.utils.helpers import (
    generate_unique_filename,
    safe_file_path,
    ensure_directory_exists,
    format_file_size,
    get_time_ago
)
from app.config import settings

# Page config
st.set_page_config(
    page_title="Candidate Upload",
    page_icon="👥",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .upload-section {
        background-color: #f0f2f6;
        padding: 2rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .candidate-card {
        background-color: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 4px solid #1f77b4;
    }
    .candidate-name {
        font-size: 1.2rem;
        font-weight: bold;
        color: #1f77b4;
    }
    .candidate-info {
        color: #666;
        font-size: 0.9rem;
    }
    .success-badge {
        background-color: #28a745;
        color: white;
        padding: 0.2rem 0.6rem;
        border-radius: 4px;
        font-size: 0.8rem;
    }
    .pending-badge {
        background-color: #ffc107;
        color: black;
        padding: 0.2rem 0.6rem;
        border-radius: 4px;
        font-size: 0.8rem;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.title("Candidate Upload")
st.markdown("Upload candidate resumes for analysis")
st.markdown("---")

# ==========================================
# Job Selection
# ==========================================

st.subheader("Step 1: Select Job Position")

try:
    with DatabaseSession() as db:
        # Fetch active jobs
        jobs = db.query(Job).filter(Job.status == JobStatus.ACTIVE).order_by(Job.created_at.desc()).all()
        
        if not jobs:
            st.warning("No active jobs found. Please create a job in the 'Job Management' page first.")
            st.stop()
        
        # Job selection dropdown
        job_options = {f"{job.title} (ID: {job.id})": job.id for job in jobs}
        selected_job_display = st.selectbox(
            "Select Job Position",
            options=list(job_options.keys()),
            help="Choose the job position for which you want to upload candidates"
        )
        
        selected_job_id = job_options[selected_job_display]
        
        # Get selected job details
        selected_job = db.query(Job).filter(Job.id == selected_job_id).first()
        
        # Display job info
        with st.expander("Job Details", expanded=False):
            st.markdown(f"**Title:** {selected_job.title}")
            st.markdown(f"**Description:** {selected_job.description[:300]}...")
            if selected_job.location:
                st.markdown(f"**Location:** {selected_job.location}")
            if selected_job.department:
                st.markdown(f"**Department:** {selected_job.department}")
            
            # Show existing candidates count
            candidate_count = len(selected_job.candidates) if selected_job.candidates else 0
            st.markdown(f"**Current Candidates:** {candidate_count}")

except Exception as e:
    st.error(f"Error loading jobs: {str(e)}")
    st.stop()

st.markdown("---")

# ==========================================
# File Upload Section
# ==========================================

st.subheader("Step 2: Upload Resume Files")

st.markdown(f"""
**Supported Formats:** PDF, DOCX, TXT  
**Maximum File Size:** {settings.MAX_FILE_SIZE / (1024 * 1024):.0f} MB per file  
**Multiple Files:** You can upload multiple resumes at once
""")

# File uploader
uploaded_files = st.file_uploader(
    "Choose resume files",
    type=settings.ALLOWED_EXTENSIONS,
    accept_multiple_files=True,
    help="Upload one or more resume files in PDF, DOCX, or TXT format"
)

if uploaded_files:
    st.markdown(f"**{len(uploaded_files)} file(s) selected**")
    
    # Upload button
    if st.button("Upload and Parse Resumes", type="primary", use_container_width=True):
        
        # Progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        upload_results = []
        
        # Ensure upload directory exists
        upload_dir = settings.get_upload_path()
        
        for idx, uploaded_file in enumerate(uploaded_files):
            try:
                status_text.text(f"Processing {idx + 1}/{len(uploaded_files)}: {uploaded_file.name}")
                
                # Generate unique filename
                unique_filename = generate_unique_filename(uploaded_file.name)
                file_path = safe_file_path(str(upload_dir), unique_filename)
                
                # Save file
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                file_size = os.path.getsize(file_path)
                
                # Parse resume
                parse_result = parse_resume(
                    file_path=str(file_path),
                    filename=uploaded_file.name,
                    file_size=file_size
                )
                
                if parse_result["success"]:
                    # Save to database
                    with DatabaseSession() as db:
                        candidate_info = parse_result["candidate_info"]
                        
                        new_candidate = Candidate(
                            job_id=selected_job_id,
                            name=candidate_info.get("name", uploaded_file.name),
                            email=candidate_info.get("email"),
                            phone=candidate_info.get("phone"),
                            file_name=uploaded_file.name,
                            file_path=str(file_path),
                            file_type=parse_result["file_info"]["file_type"],
                            file_size=file_size,
                            parsed_text=parse_result["cleaned_text"]
                        )
                        
                        db.add(new_candidate)
                        db.commit()
                        
                        upload_results.append({
                            "filename": uploaded_file.name,
                            "success": True,
                            "name": new_candidate.name,
                            "email": new_candidate.email,
                            "message": "Successfully uploaded and parsed"
                        })
                else:
                    # Delete file if parsing failed
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    
                    upload_results.append({
                        "filename": uploaded_file.name,
                        "success": False,
                        "error": parse_result["error"]
                    })
                
            except Exception as e:
                upload_results.append({
                    "filename": uploaded_file.name,
                    "success": False,
                    "error": str(e)
                })
            
            # Update progress
            progress_bar.progress((idx + 1) / len(uploaded_files))
        
        status_text.empty()
        progress_bar.empty()
        
        # Display results
        st.markdown("---")
        st.subheader("Upload Results")
        
        success_count = sum(1 for r in upload_results if r["success"])
        failed_count = len(upload_results) - success_count
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Successful", success_count)
        with col2:
            st.metric("Failed", failed_count)
        
        # Show detailed results
        for result in upload_results:
            if result["success"]:
                st.success(f"SUCCESS: {result['filename']}")
                st.markdown(f"- **Name:** {result['name']}")
                if result['email']:
                    st.markdown(f"- **Email:** {result['email']}")
            else:
                st.error(f"FAILED: {result['filename']}")
                st.markdown(f"- **Error:** {result['error']}")
        
        if success_count > 0:
            st.info(f"{success_count} candidate(s) uploaded successfully! Navigate to 'Analysis Results' to analyze them.")

st.markdown("---")

# ==========================================
# View Uploaded Candidates
# ==========================================

st.subheader("Step 3: View Uploaded Candidates")

try:
    with DatabaseSession() as db:
        candidates = db.query(Candidate).filter(
            Candidate.job_id == selected_job_id
        ).order_by(Candidate.uploaded_at.desc()).all()
        
        if not candidates:
            st.info("No candidates uploaded yet for this job.")
        else:
            st.markdown(f"**Total Candidates: {len(candidates)}**")
            
            # Search/Filter
            search_candidate = st.text_input(
                "Search Candidates",
                placeholder="Search by name or email...",
                key="search_candidates"
            )
            
            # Filter candidates
            filtered_candidates = candidates
            if search_candidate:
                search_lower = search_candidate.lower()
                filtered_candidates = [
                    c for c in candidates
                    if search_lower in c.name.lower() or
                    (c.email and search_lower in c.email.lower())
                ]
            
            st.markdown(f"**Showing {len(filtered_candidates)} candidate(s)**")
            
            # Display candidates
            for candidate in filtered_candidates:
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 1])
                    
                    with col1:
                        st.markdown(f'<div class="candidate-name">{candidate.name}</div>', unsafe_allow_html=True)
                        
                        info_parts = []
                        if candidate.email:
                            info_parts.append(f"Email: {candidate.email}")
                        if candidate.phone:
                            info_parts.append(f"Phone: {candidate.phone}")
                        
                        if info_parts:
                            st.markdown(f'<div class="candidate-info">{" | ".join(info_parts)}</div>', unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown(f"**File:** {candidate.file_name}")
                        st.markdown(f"**Size:** {format_file_size(candidate.file_size)}")
                        st.markdown(f"**Uploaded:** {get_time_ago(candidate.uploaded_at)}")
                    
                    with col3:
                        # Analysis status
                        if candidate.analysis_result:
                            st.markdown('<span class="success-badge">Analyzed</span>', unsafe_allow_html=True)
                        else:
                            st.markdown('<span class="pending-badge">Pending</span>', unsafe_allow_html=True)
                        
                        # Delete button
                        if st.button("Delete", key=f"del_cand_{candidate.id}", use_container_width=True):
                            st.session_state[f"delete_candidate_{candidate.id}"] = True
                    
                    # Delete confirmation
                    if st.session_state.get(f"delete_candidate_{candidate.id}", False):
                        st.warning(f"Delete candidate '{candidate.name}'?")
                        
                        confirm_col1, confirm_col2 = st.columns(2)
                        with confirm_col1:
                            if st.button("Yes", key=f"confirm_del_{candidate.id}"):
                                with DatabaseSession() as del_db:
                                    cand_to_delete = del_db.query(Candidate).filter(
                                        Candidate.id == candidate.id
                                    ).first()
                                    
                                    if cand_to_delete:
                                        # Delete file
                                        if cand_to_delete.file_path and os.path.exists(cand_to_delete.file_path):
                                            os.remove(cand_to_delete.file_path)
                                        
                                        del_db.delete(cand_to_delete)
                                        del_db.commit()
                                        
                                        st.success(f"Candidate '{candidate.name}' deleted!")
                                        del st.session_state[f"delete_candidate_{candidate.id}"]
                                        st.rerun()
                        
                        with confirm_col2:
                            if st.button("Cancel", key=f"cancel_del_{candidate.id}"):
                                del st.session_state[f"delete_candidate_{candidate.id}"]
                                st.rerun()
                    
                    st.markdown("---")

except Exception as e:
    st.error(f"Error loading candidates: {str(e)}")

# Footer
st.markdown("---")
st.markdown("**Tips:**")
st.markdown("- Ensure resumes contain clear text (avoid scanned images)")
st.markdown("- Best results with standard resume formats")
st.markdown("- Review parsed information before running analysis")