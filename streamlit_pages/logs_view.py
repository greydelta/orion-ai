import streamlit as st
import asyncio
from database import fetch_data
from zoneinfo import ZoneInfo

local_tz = ZoneInfo("Asia/Kuala_Lumpur")

def render_tab2():

    st.title("🔍 :green[Supabase Data Viewer]")

    query = st.text_area("SQL Query", """
        SELECT 
            a.cycle_id,
            ag.role_name,
            lm.model_name,
            a.step_number,
            a.raw_input, 
            a.raw_output, 
            a.validated_json, 
            a.status, 
            a.created_at  
        FROM agent_step a
        JOIN llm_model lm ON a.llm_model_id = lm.id
        JOIN agent ag ON a.agent_id = ag.id
        LIMIT 10
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

    col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 2, 1, 2, 1])
    col1.markdown("**Cycle ID**")
    col2.markdown("**Role Name**")
    col3.markdown("**Model Name**")
    col4.markdown("**Status**")
    col5.markdown("**Created At**")
    col6.markdown("**Action**")

    # Table view with View buttons
    for idx, row in enumerate(rows):
        col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 2, 1, 2, 1])
        col1.markdown(f"**{row['cycle_id'][:8]}...**")
        col2.markdown(row["role_name"])
        col3.markdown(row["model_name"])
        col4.markdown(f":green[{row["status"]}]")
        converted_date = row["created_at"].astimezone(local_tz)
        date = converted_date.strftime('%Y-%m-%d')
        time = converted_date.strftime('%H:%M:%S')
        col5.markdown(f"**{date}**  {time}")

        if col6.button("View", key=f"view_{idx}"):
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
                st.code(v, language="json")
            else:
                st.markdown(f"**{k}:** `{v}`")

    if st.button("Clear selection"):
        st.session_state.pop("selected_row", None)
