"""
Streamlit UI components for ADAS Diagnostics Co-pilot.

This module provides reusable UI components for the chat interface,
tool usage display, and source references.
"""

import streamlit as st
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from agent.models import (
    ToolCall, SearchResult, Suggestion, NextStep, RelatedTopic,
    DiagnosticGuidance, SafetyConsideration
)


def render_chat_message(role: str, content: str, timestamp: Optional[datetime] = None, enhanced_data: Optional[Dict[str, Any]] = None):
    """Render a chat message with proper styling and enhanced information."""
    with st.chat_message(role):
        st.write(content)
        if timestamp:
            st.caption(f"*{timestamp.strftime('%H:%M:%S')}*")

        # Render enhanced information for assistant messages
        if role == "assistant" and enhanced_data:
            # Safety considerations first (most important)
            if enhanced_data.get("safety_considerations"):
                render_safety_considerations(enhanced_data["safety_considerations"])

            # Quick actions for immediate steps
            if enhanced_data.get("quick_actions"):
                render_quick_actions(enhanced_data["quick_actions"])

            # Diagnostic guidance if available
            if enhanced_data.get("diagnostic_guidance"):
                render_diagnostic_guidance(enhanced_data["diagnostic_guidance"])

            # Next steps
            if enhanced_data.get("next_steps"):
                render_next_steps(enhanced_data["next_steps"])

            # Suggestions and related information
            if enhanced_data.get("suggestions"):
                render_suggestions(enhanced_data["suggestions"])

            # Related topics
            if enhanced_data.get("related_topics"):
                render_related_topics(enhanced_data["related_topics"])

            # Preventive tips
            if enhanced_data.get("preventive_tips"):
                render_preventive_tips(enhanced_data["preventive_tips"])

            # Common issues
            if enhanced_data.get("common_issues"):
                render_common_issues(enhanced_data["common_issues"])


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


def render_suggestions(suggestions: List[Any]):
    """Render contextual suggestions."""
    if not suggestions:
        return

    with st.expander("💡 Suggestions & Related Information", expanded=True):
        # Group suggestions by category
        categories = {}
        for suggestion in suggestions:
            # Handle both dict and object formats
            if isinstance(suggestion, dict):
                category = suggestion.get('category', 'general')
                title = suggestion.get('title', 'Suggestion')
                description = suggestion.get('description', '')
                priority = suggestion.get('priority', 'medium')
                action_type = suggestion.get('action_type', 'information')
            else:
                category = suggestion.category
                title = suggestion.title
                description = suggestion.description
                priority = suggestion.priority
                action_type = suggestion.action_type

            if category not in categories:
                categories[category] = []
            categories[category].append({
                'title': title,
                'description': description,
                'priority': priority,
                'action_type': action_type
            })

        for category, items in categories.items():
            st.subheader(f"🔍 {category.replace('_', ' ').title()}")

            for suggestion in items:
                priority_icon = "🔴" if suggestion['priority'] == "high" else "🟡" if suggestion['priority'] == "medium" else "🟢"

                with st.container():
                    col1, col2 = st.columns([0.1, 0.9])
                    with col1:
                        st.write(priority_icon)
                    with col2:
                        st.write(f"**{suggestion['title']}**")
                        st.write(suggestion['description'])
                        if suggestion['action_type'] != "information":
                            st.caption(f"*Action Type: {suggestion['action_type'].replace('_', ' ').title()}*")

                if suggestion != items[-1]:  # Don't add divider after last item
                    st.divider()


def render_next_steps(next_steps: List[Any]):
    """Render suggested next steps."""
    if not next_steps:
        return

    with st.expander("📋 Suggested Next Steps", expanded=True):
        for step in next_steps:
            # Handle both dict and object formats
            if isinstance(step, dict):
                step_number = step.get('step_number', 1)
                title = step.get('title', 'Step')
                description = step.get('description', '')
                estimated_time = step.get('estimated_time')
                required_tools = step.get('required_tools', [])
                safety_notes = step.get('safety_notes', [])
            else:
                step_number = step.step_number
                title = step.title
                description = step.description
                estimated_time = step.estimated_time
                required_tools = step.required_tools
                safety_notes = step.safety_notes

            with st.container():
                col1, col2 = st.columns([0.1, 0.9])
                with col1:
                    st.write(f"**{step_number}**")
                with col2:
                    st.write(f"**{title}**")
                    st.write(description)

                    if estimated_time:
                        st.caption(f"⏱️ Estimated time: {estimated_time}")

                    if required_tools:
                        st.caption(f"🔧 Required tools: {', '.join(required_tools)}")

                    if safety_notes:
                        for note in safety_notes:
                            st.warning(f"⚠️ Safety: {note}")

                if step != next_steps[-1]:  # Don't add divider after last item
                    st.divider()


def render_related_topics(related_topics: List[Any]):
    """Render related topics and components."""
    if not related_topics:
        return

    with st.expander("🔗 Related Topics & Components", expanded=False):
        # Group by relationship type
        relationships = {}
        for topic in related_topics:
            # Handle both dict and object formats
            if isinstance(topic, dict):
                relationship = topic.get('relationship', 'related')
                title = topic.get('title', 'Related Topic')
                description = topic.get('description', '')
                relevance_score = topic.get('relevance_score', 0.0)
            else:
                relationship = topic.relationship
                title = topic.title
                description = topic.description
                relevance_score = topic.relevance_score

            if relationship not in relationships:
                relationships[relationship] = []
            relationships[relationship].append({
                'title': title,
                'description': description,
                'relevance_score': relevance_score
            })

        for relationship, items in relationships.items():
            st.subheader(f"📌 {relationship.replace('_', ' ').title()}")

            for topic in items:
                with st.container():
                    col1, col2 = st.columns([0.8, 0.2])
                    with col1:
                        st.write(f"**{topic['title']}**")
                        st.write(topic['description'])
                    with col2:
                        if topic['relevance_score'] > 0:
                            score_color = "green" if topic['relevance_score'] > 0.8 else "orange" if topic['relevance_score'] > 0.6 else "red"
                            st.metric("Relevance", f"{topic['relevance_score']:.2f}")

                if topic != items[-1]:  # Don't add divider after last item
                    st.divider()


def render_diagnostic_guidance(guidance: Any):
    """Render diagnostic guidance with detailed procedures."""
    if not guidance:
        return

    # Handle both dict and object formats
    if isinstance(guidance, dict):
        procedure_name = guidance.get('procedure_name', 'Diagnostic Procedure')
        prerequisites = guidance.get('prerequisites', [])
        steps = guidance.get('steps', [])
        expected_results = guidance.get('expected_results', [])
        troubleshooting_tips = guidance.get('troubleshooting_tips', [])
    else:
        procedure_name = guidance.procedure_name
        prerequisites = guidance.prerequisites
        steps = guidance.steps
        expected_results = guidance.expected_results
        troubleshooting_tips = guidance.troubleshooting_tips

    with st.expander(f"🔧 Diagnostic Procedure: {procedure_name}", expanded=True):
        if prerequisites:
            st.subheader("📋 Prerequisites")
            for prereq in prerequisites:
                st.write(f"• {prereq}")

        if steps:
            st.subheader("🔄 Procedure Steps")
            render_next_steps(steps)

        if expected_results:
            st.subheader("✅ Expected Results")
            for result in expected_results:
                st.success(f"✓ {result}")

        if troubleshooting_tips:
            st.subheader("💡 Troubleshooting Tips")
            for tip in troubleshooting_tips:
                st.info(f"💡 {tip}")


def render_safety_considerations(safety_considerations: List[Any]):
    """Render safety considerations with appropriate styling."""
    if not safety_considerations:
        return

    # Group by safety level - handle both dict and object formats
    critical_items = []
    important_items = []
    advisory_items = []

    for item in safety_considerations:
        # Handle both dict and object formats
        if isinstance(item, dict):
            level = item.get('level', 'advisory')
            title = item.get('title', 'Safety Consideration')
            description = item.get('description', '')
            precautions = item.get('precautions', [])
        else:
            level = item.level
            title = item.title
            description = item.description
            precautions = item.precautions

        safety_item = {
            'level': level,
            'title': title,
            'description': description,
            'precautions': precautions
        }

        if level == "critical":
            critical_items.append(safety_item)
        elif level == "important":
            important_items.append(safety_item)
        else:
            advisory_items.append(safety_item)

    if critical_items:
        with st.expander("🚨 Critical Safety Considerations", expanded=True):
            for item in critical_items:
                st.error(f"**{item['title']}**")
                st.error(item['description'])
                if item['precautions']:
                    for precaution in item['precautions']:
                        st.error(f"⚠️ {precaution}")
                if item != critical_items[-1]:
                    st.divider()

    if important_items:
        with st.expander("⚠️ Important Safety Considerations", expanded=True):
            for item in important_items:
                st.warning(f"**{item['title']}**")
                st.warning(item['description'])
                if item['precautions']:
                    for precaution in item['precautions']:
                        st.warning(f"⚠️ {precaution}")
                if item != important_items[-1]:
                    st.divider()

    if advisory_items:
        with st.expander("ℹ️ Safety Advisory", expanded=False):
            for item in advisory_items:
                st.info(f"**{item['title']}**")
                st.info(item['description'])
                if item['precautions']:
                    for precaution in item['precautions']:
                        st.info(f"ℹ️ {precaution}")
                if item != advisory_items[-1]:
                    st.divider()


def render_quick_actions(quick_actions: List[str]):
    """Render quick actions as actionable buttons or checkboxes."""
    if not quick_actions:
        return

    with st.expander("⚡ Quick Actions", expanded=True):
        st.write("**Immediate checks and verifications:**")
        for i, action in enumerate(quick_actions):
            col1, col2 = st.columns([0.1, 0.9])
            with col1:
                st.checkbox("", key=f"quick_action_{i}")
            with col2:
                st.write(action)


def render_preventive_tips(preventive_tips: List[str]):
    """Render preventive maintenance tips."""
    if not preventive_tips:
        return

    with st.expander("🛡️ Preventive Maintenance Tips", expanded=False):
        for tip in preventive_tips:
            st.info(f"🛡️ {tip}")


def render_common_issues(common_issues: List[str]):
    """Render common issues related to the topic."""
    if not common_issues:
        return

    with st.expander("⚠️ Common Issues to Watch For", expanded=False):
        for issue in common_issues:
            st.warning(f"⚠️ {issue}")
