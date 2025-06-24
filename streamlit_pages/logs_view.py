import json

import streamlit as st
import asyncio
from database import fetch_data
from zoneinfo import ZoneInfo

local_tz = ZoneInfo("Asia/Kuala_Lumpur")

def render_tab2():

    st.title(":green[Logs Viewer]")

    query = st.text_area("SQL Query", """
        SELECT 
            project_id,
            run_id,
            cycle_id,
            step_number,
            agent_id,
            agent_role,
            llm_model_id,
            llm_model_name,
            prompt_id,
            prompt_type, 
            raw_input,
            raw_output,
            validated_json,
            confidence,
            status, 
            created_at  
        FROM temp_agent_step
        ORDER BY created_at DESC
        LIMIT 20
    """)

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

    col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([1, 1, 2, 1, 1, 1, 1, 1])
    col1.markdown("**Project/Run ID**")
    col2.markdown("**Cycle ID/Step**")
    col3.markdown("**Role**")
    col4.markdown("**Model**")
    col5.markdown("**Prompt**")
    col6.markdown("**Status**")
    col7.markdown("**Created At**")
    col8.markdown("**Action**")

    # Table view with View buttons
    for idx, row in enumerate(rows):
        col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([1, 1, 2, 1, 1, 1, 1, 1])
        col1.markdown(
            f"<span style='color: gray;'>{row['project_id']}</span><br><strong>{row['run_id'][:8]}</strong>",
            unsafe_allow_html=True
        )
        col2.markdown(
            f"<span style='color: gray;'>N/A</span><br><strong>{row['step_number']}</strong>",
            unsafe_allow_html=True
        )
        col3.markdown(
            f"<span style='color: gray;'>{row['agent_id']}</span><br><strong>{row['agent_role']}</strong>",
            unsafe_allow_html=True
        )
        col4.markdown(
            f"<span style='color: gray;'>{row['llm_model_id']}</span><br><strong>{row['llm_model_name']}</strong>",
            unsafe_allow_html=True
        )
        col5.markdown(
            f"<span style='color: gray;'>{row['prompt_id']}</span><br><strong>{row['prompt_type']}</strong>",
            unsafe_allow_html=True
        )
        col6.markdown(
            f"<span style='color: gray;'>Confidence: </span><br><span style='color: green;'><strong>{row['status']}</strong></span>",
            unsafe_allow_html=True
        )
        converted_date = row["created_at"].astimezone(local_tz)
        date = converted_date.strftime('%Y-%m-%d')
        time = converted_date.strftime('%H:%M:%S')
        col7.markdown(
            f"<span style='color: gray;'>{date}</span><br><strong>{time}</strong>",
            unsafe_allow_html=True
        )

        if col8.button("View", key=f"view_{idx}"):
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
