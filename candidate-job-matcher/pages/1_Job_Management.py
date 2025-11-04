"""
Job Management Page
Create, view, edit, and manage job postings
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
from datetime import datetime

from app.database import DatabaseSession, Job, JobStatus
from app.utils.validators import validate_job_title, validate_job_description
from app.utils.helpers import format_datetime, get_time_ago

# Page config
st.set_page_config(
    page_title="Job Management",
    page_icon="📝",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .job-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 5px solid #1f77b4;
    }
    .job-title {
        font-size: 1.5rem;
        font-weight: bold;
        color: #1f77b4;
    }
    .job-meta {
        color: #666;
        font-size: 0.9rem;
        margin-top: 0.5rem;
    }
    .status-active {
        background-color: #28a745;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 5px;
        font-size: 0.85rem;
    }
    .status-draft {
        background-color: #6c757d;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 5px;
        font-size: 0.85rem;
    }
    .status-closed {
        background-color: #dc3545;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 5px;
        font-size: 0.85rem;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.title("Job Management")
st.markdown("Create and manage job postings for candidate matching")
st.markdown("---")

# Tabs
tab1, tab2 = st.tabs(["View Jobs", "Create New Job"])

# ==========================================
# TAB 1: View Jobs
# ==========================================

with tab1:
    st.subheader("Active Job Postings")
    
    # Filters
    filter_col1, filter_col2, filter_col3 = st.columns([2, 2, 1])
    
    with filter_col1:
        status_filter = st.selectbox(
            "Filter by Status",
            ["All", "Active", "Draft", "Closed"],
            key="status_filter"
        )
    
    with filter_col2:
        search_query = st.text_input(
            "Search Jobs",
            placeholder="Search by title or description...",
            key="search_query"
        )
    
    with filter_col3:
        st.markdown("<br>", unsafe_allow_html=True)
        refresh_btn = st.button("Refresh", use_container_width=True)
    
    st.markdown("---")
    
    # Fetch jobs
    try:
        with DatabaseSession() as db:
            query = db.query(Job)
            
            # Apply status filter
            if status_filter != "All":
                status_enum = JobStatus[status_filter.upper()]
                query = query.filter(Job.status == status_enum)
            
            # Apply search filter
            if search_query:
                search_pattern = f"%{search_query}%"
                query = query.filter(
                    (Job.title.ilike(search_pattern)) | 
                    (Job.description.ilike(search_pattern))
                )
            
            jobs = query.order_by(Job.created_at.desc()).all()
            
            if not jobs:
                st.info("No jobs found. Create your first job in the 'Create New Job' tab!")
            else:
                st.markdown(f"**Found {len(jobs)} job(s)**")
                
                for job in jobs:
                    # Job card
                    with st.container():
                        col1, col2 = st.columns([4, 1])
                        
                        with col1:
                            # Status badge
                            status_class = f"status-{job.status.value}"
                            st.markdown(f'<span class="{status_class}">{job.status.value.upper()}</span>', unsafe_allow_html=True)
                            
                            # Job title
                            st.markdown(f'<div class="job-title">{job.title}</div>', unsafe_allow_html=True)
                            
                            # Metadata
                            candidate_count = len(job.candidates) if job.candidates else 0
                            created_ago = get_time_ago(job.created_at)
                            
                            st.markdown(
                                f'<div class="job-meta">Created {created_ago} | {candidate_count} candidates</div>',
                                unsafe_allow_html=True
                            )
                            
                            # Description preview
                            desc_preview = job.description[:200] + "..." if len(job.description) > 200 else job.description
                            st.markdown(f"**Description:** {desc_preview}")
                            
                            # Additional info
                            if job.location or job.department or job.experience_level:
                                info_parts = []
                                if job.location:
                                    info_parts.append(f"Location: {job.location}")
                                if job.department:
                                    info_parts.append(f"Department: {job.department}")
                                if job.experience_level:
                                    info_parts.append(f"Experience: {job.experience_level}")
                                st.markdown(" | ".join(info_parts))
                        
                        with col2:
                            # Action buttons
                            if st.button("View", key=f"view_{job.id}", use_container_width=True):
                                st.session_state[f"show_details_{job.id}"] = True
                            
                            if st.button("Edit", key=f"edit_{job.id}", use_container_width=True):
                                st.session_state.edit_job_id = job.id
                                st.rerun()
                            
                            if st.button("Delete", key=f"delete_{job.id}", use_container_width=True, type="secondary"):
                                st.session_state.delete_job_id = job.id
                        
                        # Show details if toggled
                        if st.session_state.get(f"show_details_{job.id}", False):
                            with st.expander("Full Details", expanded=True):
                                st.markdown("**Full Description:**")
                                st.text_area("", job.description, height=150, disabled=True, key=f"desc_{job.id}")
                                
                                if job.requirements:
                                    st.markdown("**Requirements:**")
                                    st.text_area("", job.requirements, height=100, disabled=True, key=f"req_{job.id}")
                                
                                if job.salary_range:
                                    st.markdown(f"**Salary Range:** {job.salary_range}")
                                
                                if job.employment_type:
                                    st.markdown(f"**Employment Type:** {job.employment_type}")
                                
                                if st.button("Close", key=f"close_{job.id}"):
                                    st.session_state[f"show_details_{job.id}"] = False
                                    st.rerun()
                        
                        st.markdown("---")
                    
                    # Handle delete confirmation
                    if st.session_state.get("delete_job_id") == job.id:
                        st.warning(f"Are you sure you want to delete '{job.title}'? This will also delete all associated candidates and analysis results.")
                        
                        del_col1, del_col2, del_col3 = st.columns([1, 1, 3])
                        with del_col1:
                            if st.button("Yes, Delete", key=f"confirm_delete_{job.id}", type="primary"):
                                with DatabaseSession() as del_db:
                                    job_to_delete = del_db.query(Job).filter(Job.id == job.id).first()
                                    if job_to_delete:
                                        del_db.delete(job_to_delete)
                                        del_db.commit()
                                        st.success(f"Job '{job.title}' deleted successfully!")
                                        del st.session_state.delete_job_id
                                        st.rerun()
                        
                        with del_col2:
                            if st.button("Cancel", key=f"cancel_delete_{job.id}"):
                                del st.session_state.delete_job_id
                                st.rerun()
    
    except Exception as e:
        st.error(f"Error loading jobs: {str(e)}")

# ==========================================
# TAB 2: Create New Job
# ==========================================

with tab2:
    st.subheader("Create New Job Posting")
    
    with st.form("create_job_form"):
        # Basic Information
        st.markdown("### Basic Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            job_title = st.text_input(
                "Job Title *",
                placeholder="e.g., Senior Python Developer",
                help="Enter the job title"
            )
            
            location = st.text_input(
                "Location",
                placeholder="e.g., Remote, New York, NY",
                help="Job location or remote"
            )
            
            employment_type = st.selectbox(
                "Employment Type",
                ["", "Full-time", "Part-time", "Contract", "Internship"],
                help="Type of employment"
            )
        
        with col2:
            department = st.text_input(
                "Department",
                placeholder="e.g., Engineering, Marketing",
                help="Department or team"
            )
            
            experience_level = st.selectbox(
                "Experience Level",
                ["", "Entry Level", "Mid Level", "Senior Level", "Lead/Principal"],
                help="Required experience level"
            )
            
            salary_range = st.text_input(
                "Salary Range",
                placeholder="e.g., $80,000 - $120,000",
                help="Optional salary range"
            )
        
        # Job Description
        st.markdown("### Job Description *")
        job_description = st.text_area(
            "Description",
            placeholder="Describe the role, responsibilities, and what the candidate will be doing...",
            height=200,
            help="Provide a detailed job description"
        )
        
        # Requirements
        st.markdown("### Requirements")
        job_requirements = st.text_area(
            "Requirements",
            placeholder="List required skills, qualifications, and experience...",
            height=150,
            help="Specify job requirements and qualifications"
        )
        
        # Status
        job_status = st.selectbox(
            "Status",
            ["Active", "Draft"],
            help="Set job status - Active jobs can accept candidates"
        )
        
        # Submit button
        submitted = st.form_submit_button("Create Job", use_container_width=True, type="primary")
        
        if submitted:
            # Validate inputs
            is_valid_title, title_msg = validate_job_title(job_title)
            is_valid_desc, desc_msg = validate_job_description(job_description)
            
            if not is_valid_title:
                st.error(f"Invalid job title: {title_msg}")
            elif not is_valid_desc:
                st.error(f"Invalid job description: {desc_msg}")
            else:
                try:
                    # Create job in database
                    with DatabaseSession() as db:
                        new_job = Job(
                            title=job_title.strip(),
                            description=job_description.strip(),
                            requirements=job_requirements.strip() if job_requirements else None,
                            location=location.strip() if location else None,
                            department=department.strip() if department else None,
                            employment_type=employment_type if employment_type else None,
                            experience_level=experience_level if experience_level else None,
                            salary_range=salary_range.strip() if salary_range else None,
                            status=JobStatus.ACTIVE if job_status == "Active" else JobStatus.DRAFT
                        )
                        
                        db.add(new_job)
                        db.commit()
                        
                        st.success(f"Job '{job_title}' created successfully!")
                        st.info("Navigate to 'Candidate Upload' to start adding candidates.")
                        
                        # Clear form by rerunning
                        st.balloons()
                
                except Exception as e:
                    st.error(f"Error creating job: {str(e)}")

# Footer
st.markdown("---")
st.markdown("**Note:** Fields marked with * are required")