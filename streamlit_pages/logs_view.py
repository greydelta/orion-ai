import json

import streamlit as st
import asyncio
from zoneinfo import ZoneInfo

from database import fetch_data

local_tz = ZoneInfo("Asia/Kuala_Lumpur")

def render_tab2(is_repo_analysis):

    st.markdown("""
        <style>
        /* Wrap long lines inside st.code blocks */
        .streamlit-expander .stCode > div, .stCode > div {
            overflow-x: auto !important;
            white-space: pre-wrap !important;
            word-break: break-word !important;
        }
        </style>
    """, unsafe_allow_html=True)

    st.subheader(":green[Logs Viewer]")

    # Step 1: Fetch distinct project_ids
    project_id_query = "SELECT DISTINCT project_id FROM temp_agent_step ORDER BY project_id"
    try:
        project_id_rows = asyncio.run(fetch_data(project_id_query))
        all_project_ids = [row['project_id'] for row in project_id_rows]
    except Exception as e:
        st.error(f"❌ Failed to load project IDs: {e}")
        st.stop()

    # Step 2: Project filter with "Select All"
    default_selection = all_project_ids  # Pre-select all by default
    selected_projects = st.multiselect(
        "Filter by Project ID(s):",
        options=all_project_ids,
        default=default_selection,
        help="Select one or more projects to filter logs"
    )

    # Step 3: Build WHERE clause based on selection
    project_filter_sql = ""
    if selected_projects and len(selected_projects) < len(all_project_ids):
        formatted = ','.join(f"'{pid}'" for pid in selected_projects)
        project_filter_sql = f"WHERE project_id IN ({formatted})"

    # Manual query
    if st.button("Run Custom Query"):
        try:
            rows = asyncio.run(fetch_data(query))
        except Exception as e:
            st.error(f"❌ Failed to load records: {e}")
            st.stop()

    query = st.text_area("Custom SQL Query", f"""
        SELECT 
            project_id,
            run_id,
            cycle_id,
            step_number,
            agent_id,
            agent_role,
            llm_model_id,
            llm_model_name,
            llm_model_temperature,
            llm_model_top_p,
            prompt_id,
            prompt_type, 
            raw_input,
            raw_output,
            validated_json,
            confidence,
            status,
            file_path,
            created_at  
        FROM temp_agent_step
        {project_filter_sql}
        ORDER BY created_at DESC
        LIMIT 100
    """    
    ,height=300
    )

    # Run asyncpg query
    try:
        rows = asyncio.run(fetch_data(query))
    except Exception as e:
        st.error(f"❌ Failed to load records: {e}")
        st.stop()

    # Convert rows to simpler view
    if not rows:
        st.warning("No records found.")
        st.stop()

    col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns([1, 2, 1, 2, 1, 1, 1, 1, 1])
    col1.markdown("**Project/Run ID**")
    col2.markdown("**File**")
    col3.markdown("**Cycle ID/Step**")
    col4.markdown("**Role**")
    col5.markdown("**Model**")
    col6.markdown("**Prompt**")
    col7.markdown("**Status**")
    col8.markdown("**Created At**")
    col9.markdown("**Action**")

    # Table view with View buttons
    for idx, row in enumerate(rows):
        col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns([1, 2, 1, 2, 1, 1, 1, 1, 1])
        temp = row['llm_model_temperature'] if row['llm_model_temperature'] is not None else 'N/A'
        top_p = row['llm_model_top_p'] if row['llm_model_top_p'] is not None else 'N/A'
        status = row['status'] or 'N/A'
        status_icon = {"passed": "✅", "generated": "ℹ️", "failed": "❌"}.get(status.lower(), "🟡")
        if status.lower() == "passed":
            status_color = "green"
        elif status.lower() == "generated":
            status_color = "blue"
        elif status.lower() == "failed":
            status_color = "red"
        else:
            status_color = "gray"

        col1.markdown(
            f"<span style='color: gray;'>{row['project_id']}</span><br><strong>{row['run_id']}</strong>",
            unsafe_allow_html=True
        )
        col2.markdown(
            f"<span style='color: gray;'>Type: {'Repo' if is_repo_analysis else 'Single'}</span><br><strong>{row['file_path']}</strong>",
            unsafe_allow_html=True
        )
        col3.markdown(
            f"<span style='color: gray;'>{row['cycle_id']}</span><br><strong>{row['step_number']}</strong>",
            unsafe_allow_html=True
        )
        col4.markdown(
            f"<span style='color: gray;'>{row['agent_id']}</span><br><strong>{row['agent_role']}</strong>",
            unsafe_allow_html=True
        )
        col5.markdown(
            f"""<span style='color: gray;'>{row['llm_model_id']}</span><br><strong>{row['llm_model_name']}</strong>
            <span style='color: gray; font-size: small;'>(te: {temp}, tp: {top_p})</span>""",
            unsafe_allow_html=True
        )
        col6.markdown(
            f"<span style='color: gray;'>{row['prompt_id']}</span><br><strong>{row['prompt_type']}</strong>",
            unsafe_allow_html=True
        )
        col7.markdown(
            f"""
            <span style='color: gray;'>Confidence: </span><br>
            <span style='color: {status_color};'>{status_icon} <strong>{status}</strong></span>
            """,
            unsafe_allow_html=True
        )
        converted_date = row["created_at"].astimezone(local_tz)
        date = converted_date.strftime('%Y-%m-%d')
        time = converted_date.strftime('%H:%M:%S')
        col8.markdown(
            f"<span style='color: gray;'>{date}</span><br><strong>{time}</strong>",
            unsafe_allow_html=True
        )

        if col9.button("View", key=f"view_{idx}"):
            st.session_state["selected_row"] = row

    # Divider
    st.markdown("---")

    # Form-like detail view for selected row
    selected_row = st.session_state.get("selected_row")
    if selected_row:
        st.subheader("📄 Detailed Record")
        for k, v in selected_row.items():
            if (k == "raw_input" or k == "raw_output"):
                st.markdown(f"**{k}:**")
                st.code(v, language="text")
            elif (k == "validated_json"):
                st.markdown(f"**{k}:**")
                if isinstance(v, dict):
                    pretty = json.dumps(v, indent=2)
                elif isinstance(v, str):
                    try:
                        parsed = json.loads(v)
                        pretty = json.dumps(parsed, indent=2)
                    except json.JSONDecodeError:
                        pretty = v
                st.code(pretty, language="json")
            else:
                st.markdown(f"**{k}:** `{v}`")

    if st.button("Clear selection"):
        st.session_state.pop("selected_row", None)
