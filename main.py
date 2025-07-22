import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import time
import json

class GitLabDashboard:
    def __init__(self, gitlab_url, access_token):
        self.gitlab_url = gitlab_url.rstrip('/')
        self.access_token = access_token
        self.headers = {'PRIVATE-TOKEN': access_token}
        self.base_api_url = f"{self.gitlab_url}/api/v4"
    
    def get_group_projects(self, group_id):
        """Get all projects in a group"""[22]
        url = f"{self.base_api_url}/groups/{group_id}/projects"
        params = {'per_page': 100, 'simple': True}
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            st.error(f"Error fetching group projects: {str(e)}")
            return []
    
    def get_project_pipelines(self, project_id, per_page=20):
        """Get pipelines for a specific project"""[22]
        url = f"{self.base_api_url}/projects/{project_id}/pipelines"
        params = {'per_page': per_page, 'sort': 'desc'}
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            st.error(f"Error fetching pipelines for project {project_id}: {str(e)}")
            return []
    
    def get_pipeline_jobs(self, project_id, pipeline_id):
        """Get jobs for a specific pipeline"""[36]
        url = f"{self.base_api_url}/projects/{project_id}/pipelines/{pipeline_id}/jobs"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return []
    
    def format_datetime(self, dt_string):
        """Format datetime string for display"""
        if not dt_string:
            return "N/A"
        
        try:
            dt = datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            return dt_string
    
    def get_time_ago(self, dt_string):
        """Get human-readable time difference"""
        if not dt_string:
            return "N/A"
        
        try:
            dt = datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
            now = datetime.now(dt.tzinfo)
            delta = now - dt
            
            if delta.days > 0:
                return f"{delta.days} days ago"
            elif delta.seconds > 3600:
                hours = delta.seconds // 3600
                return f"{hours} hours ago"
            elif delta.seconds > 60:
                minutes = delta.seconds // 60
                return f"{minutes} minutes ago"
            else:
                return "Just now"
        except:
            return "N/A"

def get_status_color(status):
    """Return color based on pipeline status"""[6][10]
    colors = {
        'success': '🟢',
        'failed': '🔴',
        'running': '🔵',
        'pending': '🟡',
        'canceled': '⚪',
        'skipped': '⚫',
        'created': '🟡',
        'manual': '🟠'
    }
    return colors.get(status, '⚪')

def main():
    st.set_page_config(
        page_title="GitLab Pipeline Dashboard",
        page_icon="🚀",
        layout="wide"
    )
    
    st.title("🚀 GitLab Pipeline Dashboard")
    st.markdown("Monitor pipeline status and progress for projects within a GitLab group")
    
    # Sidebar configuration
    st.sidebar.header("Configuration")
    
    gitlab_url = st.sidebar.text_input(
        "GitLab URL",
        value="https://gitlab.com",
        help="Enter your GitLab instance URL"
    )
    
    access_token = st.sidebar.text_input(
        "Access Token",
        type="password",
        help="Enter your GitLab personal access token"
    )
    
    group_id = st.sidebar.text_input(
        "Group ID",
        help="Enter the GitLab group ID to monitor"
    )
    
    auto_refresh = st.sidebar.checkbox("Auto-refresh (30s)", value=False)
    
    if auto_refresh:
        time.sleep(30)
        st.rerun()
    
    # Manual refresh button
    if st.sidebar.button("🔄 Refresh Now"):
        st.rerun()
    
    if not all([gitlab_url, access_token, group_id]):
        st.warning("Please provide GitLab URL, Access Token, and Group ID in the sidebar.")
        return
    
    # Initialize dashboard
    dashboard = GitLabDashboard(gitlab_url, access_token)
    
    # Get projects in the group
    with st.spinner("Fetching group projects..."):
        projects = dashboard.get_group_projects(group_id)
    
    if not projects:
        st.error("No projects found or unable to access the group.")
        return
    
    st.success(f"Found {len(projects)} projects in the group")
    
    # Create tabs for different views
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard Overview", "⏳ Pending Pipelines", "✅ Recent Successes"])
    
    with tab1:
        st.header("Pipeline Status Overview")
        
        # Collect all pipeline data
        all_pipelines_data = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, project in enumerate(projects):
            status_text.text(f"Fetching pipelines for {project['name']}...")
            pipelines = dashboard.get_project_pipelines(project['id'], per_page=5)
            
            for pipeline in pipelines:
                all_pipelines_data.append({
                    'Project': project['name'],
                    'Project ID': project['id'],
                    'Pipeline ID': pipeline['id'],
                    'Status': pipeline['status'],
                    'Branch': pipeline['ref'],
                    'Created': pipeline.get('created_at', ''),
                    'Updated': pipeline.get('updated_at', ''),
                    'Web URL': pipeline.get('web_url', ''),
                    'User': pipeline.get('user', {}).get('name', 'N/A') if pipeline.get('user') else 'N/A'
                })
            
            progress_bar.progress((i + 1) / len(projects))
        
        status_text.empty()
        progress_bar.empty()
        
        if all_pipelines_data:
            df = pd.DataFrame(all_pipelines_data)
            
            # Status summary
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                success_count = len(df[df['Status'] == 'success'])
                st.metric("✅ Successful", success_count)
            
            with col2:
                failed_count = len(df[df['Status'] == 'failed'])
                st.metric("❌ Failed", failed_count)
            
            with col3:
                running_count = len(df[df['Status'] == 'running'])
                st.metric("🔵 Running", running_count)
            
            with col4:
                pending_count = len(df[df['Status'].isin(['pending', 'created'])])
                st.metric("⏳ Pending", pending_count)
            
            # Display recent pipelines
            st.subheader("Recent Pipelines")
            
            # Format the display dataframe
            display_df = df.copy()
            display_df['Status Icon'] = display_df['Status'].apply(get_status_color)
            display_df['Created'] = display_df['Created'].apply(dashboard.format_datetime)
            display_df['Time Ago'] = df['Updated'].apply(dashboard.get_time_ago)
            
            # Select columns for display
            display_columns = ['Status Icon', 'Project', 'Branch', 'Status', 'Created', 'Time Ago', 'User']
            st.dataframe(
                display_df[display_columns],
                use_container_width=True,
                hide_index=True
            )
    
    with tab2:
        st.header("⏳ Pending Pipelines")
        
        if 'all_pipelines_data' in locals():
            pending_df = pd.DataFrame([p for p in all_pipelines_data if p['Status'] in ['pending', 'created', 'running']])
            
            if not pending_df.empty:
                for _, pipeline in pending_df.iterrows():
                    with st.expander(f"{get_status_color(pipeline['Status'])} {pipeline['Project']} - {pipeline['Branch']}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**Status:** {pipeline['Status']}")
                            st.write(f"**Branch:** {pipeline['Branch']}")
                            st.write(f"**Created:** {dashboard.format_datetime(pipeline['Created'])}")
                            st.write(f"**User:** {pipeline['User']}")
                        
                        with col2:
                            if pipeline['Web URL']:
                                st.markdown(f"[View Pipeline]({pipeline['Web URL']})")
                            
                            # Get pipeline jobs for more details
                            jobs = dashboard.get_pipeline_jobs(pipeline['Project ID'], pipeline['Pipeline ID'])
                            if jobs:
                                st.write("**Jobs:**")
                                for job in jobs:
                                    job_status = get_status_color(job['status'])
                                    st.write(f"{job_status} {job['name']} - {job['status']}")
            else:
                st.info("No pending pipelines found!")
    
    with tab3:
        st.header("✅ Recent Successful Pipelines")
        
        if 'all_pipelines_data' in locals():
            success_df = pd.DataFrame([p for p in all_pipelines_data if p['Status'] == 'success'])
            
            if not success_df.empty:
                # Sort by most recent
                success_df = success_df.sort_values('Updated', ascending=False)
                
                for _, pipeline in success_df.head(10).iterrows():  # Show last 10 successes
                    with st.container():
                        col1, col2, col3 = st.columns([3, 2, 1])
                        
                        with col1:
                            st.write(f"✅ **{pipeline['Project']}** - {pipeline['Branch']}")
                        
                        with col2:
                            st.write(f"Completed: {dashboard.get_time_ago(pipeline['Updated'])}")
                        
                        with col3:
                            if pipeline['Web URL']:
                                st.markdown(f"[View]({pipeline['Web URL']})")
                        
                        st.divider()
            else:
                st.info("No successful pipelines found!")
    
    # Footer
    st.markdown("---")
    st.markdown("💡 **Tip:** Use the auto-refresh option to keep the dashboard updated automatically.")

if __name__ == "__main__":
    main()
