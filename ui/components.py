"""
Streamlit UI components for ADAS Diagnostics Co-pilot.

This module provides reusable UI components for the chat interface,
tool usage display, and source references.
"""

import streamlit as st
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from agent.models import ToolCall, SearchResult


def render_chat_message(role: str, content: str, timestamp: Optional[datetime] = None):
    """Render a chat message with proper styling."""
    with st.chat_message(role):
        st.write(content)
        if timestamp:
            st.caption(f"*{timestamp.strftime('%H:%M:%S')}*")


def render_tool_usage(tools_used: List[ToolCall]):
    """Render tool usage information for transparency."""
    if not tools_used:
        return

    with st.expander("🔧 Tools Used", expanded=False):
        for i, tool in enumerate(tools_used):
            # Handle both dict and object formats
            if isinstance(tool, dict):
                tool_name = tool.get('tool_name', 'Unknown Tool')
                tool_args = tool.get('args', {})
                tool_success = tool.get('success', True)
                tool_result = tool.get('result')
            else:
                tool_name = tool.tool_name
                tool_args = tool.args
                tool_success = tool.success
                tool_result = tool.result

            st.subheader(f"{i+1}. {tool_name}")

            # Tool arguments
            with st.container():
                st.write("**Arguments:**")
                if tool_args:
                    for key, value in tool_args.items():
                        st.write(f"- **{key}:** {value}")
                else:
                    st.write("*No arguments*")

            # Tool result
            if tool_success and tool_result:
                with st.container():
                    st.write("**Result:**")
                    if isinstance(tool_result, dict):
                        # Format result nicely
                        if "results" in tool_result:
                            st.write(f"Found {len(tool_result['results'])} results")
                        if "summary" in tool_result:
                            st.write(tool_result["summary"])
                        if "timeline" in tool_result:
                            st.write(f"Timeline: {len(tool_result['timeline'])} events")
                        if "dependencies" in tool_result:
                            st.write(f"Dependencies: {len(tool_result['dependencies'])} relationships")
                    else:
                        st.write(str(tool_result))
            elif not tool_success:
                # Handle both dict and object formats for error message
                if isinstance(tool, dict):
                    error_msg = tool.get('error_message', 'Unknown error')
                else:
                    error_msg = tool.error_message
                st.error(f"Tool failed: {error_msg}")

            # Execution time
            if isinstance(tool, dict):
                execution_time = tool.get('execution_time')
            else:
                execution_time = tool.execution_time
            if execution_time:
                st.caption(f"*Execution time: {execution_time:.2f}s*")
            
            if i < len(tools_used) - 1:
                st.divider()


def render_sources(sources: List[Any]):
    """Render source documents and references."""
    if not sources:
        return

    with st.expander("📚 Sources", expanded=False):
        for i, source in enumerate(sources):
            with st.container():
                # Handle both dict and object formats
                if isinstance(source, dict):
                    document_filename = source.get('document_filename', 'Unknown Document')
                    content_type = source.get('content_type', 'unknown')
                    content = source.get('content', '')
                    vehicle_system = source.get('vehicle_system')
                    component_name = source.get('component_name')
                    score = source.get('score', 0)
                else:
                    document_filename = source.document_filename
                    content_type = source.content_type
                    content = source.content
                    vehicle_system = source.vehicle_system
                    component_name = source.component_name
                    score = source.score

                # Document title and type
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**{document_filename}**")
                with col2:
                    st.write(f"**{content_type}**")
                   

                # Content preview
                if content:
                    content_preview = content[:200] + "..." if len(content) > 200 else content
                    st.write(content_preview)

                # Metadata
                metadata_cols = st.columns(3)
                if vehicle_system:
                    with metadata_cols[0]:
                        # Handle vehicle_system as string or enum
                        if hasattr(vehicle_system, 'value'):
                            st.caption(f"System: {vehicle_system.value}")
                        else:
                            st.caption(f"System: {vehicle_system}")
                if component_name:
                    with metadata_cols[1]:
                        st.caption(f"Component: {component_name}")
                
                # Similarity score if available
                if hasattr(source, 'similarity_score'):
                    with metadata_cols[2]:
                        score_color = "green" if source.similarity_score > 0.8 else "orange" if source.similarity_score > 0.6 else "red"
                        st.caption(f"Relevance: {source.similarity_score:.2f}")
                
                if i < len(sources) - 1:
                    st.divider()



def render_system_status():
    """Render system status indicators."""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Agent status
        if st.session_state.get('agent_status', 'unknown') == 'healthy':
            st.success("🤖 Agent Online")
        else:
            st.error("🤖 Agent Offline")
    
    with col2:
        # Database status
        if st.session_state.get('db_status', 'unknown') == 'connected':
            st.success("🗄️ Database Connected")
        else:
            st.error("🗄️ Database Disconnected")
    
    with col3:
        # Knowledge graph status - currently not available
        st.info("🕸️ Graph Not Available")


def render_search_filters():
    """Render search filters in sidebar."""
    st.sidebar.header("🔍 Search Filters")
    
    # Content type filter
    content_types = ["All", "Service Manual", "Diagnostic Guide", "ADAS System", "OTA Update", "Technical Bulletin"]
    selected_content_type = st.sidebar.selectbox(
        "Content Type",
        content_types,
        key="content_type_filter"
    )

    # Mercedes E-Class system filter
    vehicle_systems = ["All", "Engine (M264)", "9G-TRONIC Transmission", "ADAS Camera", "Brake System", "Mercedes me connect"]
    selected_vehicle_system = st.sidebar.selectbox(
        "E-Class System",
        vehicle_systems,
        key="vehicle_system_filter"
    )
    
    # Search type
    search_types = ["Hybrid", "Vector"]
    selected_search_type = st.sidebar.selectbox(
        "Search Type",
        search_types,
        key="search_type_filter"
    )
    
    return {
        "content_type": None if selected_content_type == "All" else selected_content_type.upper().replace(" ", "_"),
        "vehicle_system": None if selected_vehicle_system == "All" else selected_vehicle_system.upper(),
        "search_type": selected_search_type.lower()
    }


def render_ingestion_panel():
    """Render document ingestion panel."""
    st.sidebar.header("📄 Document Ingestion")
    
    # Sample data ingestion
    if st.sidebar.button("📝 Load Sample Data", use_container_width=True):
        st.session_state.ingest_sample_data = True
        st.rerun()
    
    st.sidebar.divider()
    
    # File upload
    uploaded_files = st.sidebar.file_uploader(
        "Upload Documents",
        accept_multiple_files=True,
        type=['pdf', 'txt', 'md', 'csv', 'json'],
        key="file_uploader"
    )
    
    if uploaded_files:
        if st.sidebar.button("🚀 Process Files", use_container_width=True):
            st.session_state.uploaded_files = uploaded_files
            st.session_state.process_uploaded_files = True
            st.rerun()
    
    # Directory ingestion
    st.sidebar.subheader("Directory Ingestion")
    directory_path = st.sidebar.text_input(
        "Directory Path",
        placeholder="/path/to/documents",
        key="directory_path"
    )
    
    recursive = st.sidebar.checkbox("Include Subdirectories", key="recursive_ingestion")
    
    if directory_path and st.sidebar.button("📁 Process Directory", use_container_width=True):
        st.session_state.directory_path = directory_path
        st.session_state.recursive_ingestion = recursive
        st.session_state.process_directory = True
        st.rerun()


def render_statistics():
    """Render system statistics."""
    if 'system_stats' in st.session_state:
        stats = st.session_state.system_stats
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Documents", stats.get('documents', 0))
        
        with col2:
            st.metric("Chunks", stats.get('chunks', 0))
        
        with col3:
            st.metric("Sessions", stats.get('sessions', 0))
        
        with col4:
            status = stats.get('status', 'unknown')
            color = "🟢" if status == 'operational' else "🔴"
            st.metric("Status", f"{color} {status.title()}")


def render_diagnostic_context():
    """Render diagnostic context panel."""
    st.sidebar.header("🚗 Diagnostic Context")
    
    # VIN input
    vin = st.sidebar.text_input(
        "Vehicle VIN",
        placeholder="1HGBH41JXMN109186",
        max_chars=17,
        key="diagnostic_vin"
    )
    
    # System selection
    systems = ["", "ADAS", "Braking", "Steering", "Powertrain", "Infotainment"]
    selected_system = st.sidebar.selectbox(
        "Vehicle System",
        systems,
        key="diagnostic_system"
    )
    
    # Component input
    component = st.sidebar.text_input(
        "Component",
        placeholder="e.g., Lane Keeping Assist Module",
        key="diagnostic_component"
    )
    
    # DTC codes
    dtc_codes = st.sidebar.text_area(
        "DTC Codes",
        placeholder="P0123, B1234, U0100",
        key="diagnostic_dtc_codes"
    )
    
    return {
        "vin": vin if vin else None,
        "system": selected_system if selected_system else None,
        "component": component if component else None,
        "dtc_codes": [code.strip() for code in dtc_codes.split(",") if code.strip()] if dtc_codes else None
    }


def format_diagnostic_context(context: Dict[str, Any]) -> str:
    """Format diagnostic context for inclusion in chat messages."""
    if not any(context.values()):
        return ""
    
    context_parts = []
    if context.get("vin"):
        context_parts.append(f"VIN: {context['vin']}")
    if context.get("system"):
        context_parts.append(f"System: {context['system']}")
    if context.get("component"):
        context_parts.append(f"Component: {context['component']}")
    if context.get("dtc_codes"):
        context_parts.append(f"DTC Codes: {', '.join(context['dtc_codes'])}")
    
    if context_parts:
        return f"\n\n**Diagnostic Context:**\n" + "\n".join(f"- {part}" for part in context_parts)
    
    return ""
