"""
ADAS Diagnostics Co-pilot - Streamlit Web Application

This is the main web interface for the automotive diagnostics assistant,
providing a two-column layout with chat interface and tool transparency.
"""

import asyncio
import logging
import streamlit as st
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
from pathlib import Path
import tempfile
import os

from agent.models import ChatRequest, ChatResponse, HealthResponse
from ui.components import (
    render_chat_message,
    render_tool_usage,
    render_sources,
    render_system_status
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Mercedes-Benz E-Class Diagnostics Co-pilot",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8058")


def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "agent_status" not in st.session_state:
        st.session_state.agent_status = "unknown"

    if "system_stats" not in st.session_state:
        st.session_state.system_stats = {}

    if "session_id" not in st.session_state:
        st.session_state.session_id = None

    if "session_initialized" not in st.session_state:
        st.session_state.session_initialized = False


def check_api_health():
    """Check API health and update status."""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            st.session_state.agent_status = health_data.get("status", "unknown")
            st.session_state.db_status = "connected" if health_data.get("agent_initialized") else "disconnected"
            return True
        else:
            st.session_state.agent_status = "unhealthy"
            return False
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        st.session_state.agent_status = "offline"
        return False


def get_system_stats():
    """Get system statistics."""
    try:
        response = requests.get(f"{API_BASE_URL}/stats", timeout=5)
        if response.status_code == 200:
            st.session_state.system_stats = response.json()
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")


def create_or_get_session():
    """Create a new session or get existing one."""
    try:
        if not st.session_state.session_id:
            # Create new session
            session_data = {
                "user_id": "default_user",
                "metadata": {
                    "vehicle_make": "Mercedes-Benz",
                    "vehicle_model": "E-Class",
                    "interface": "streamlit"
                }
            }

            response = requests.post(
                f"{API_BASE_URL}/sessions",
                json=session_data,
                timeout=10
            )

            if response.status_code == 200:
                session_info = response.json()
                st.session_state.session_id = session_info["id"]
                logger.info(f"Created new session: {st.session_state.session_id}")
                return True
            else:
                logger.error(f"Failed to create session: {response.text}")
                return False
        else:
            # Verify existing session
            response = requests.get(
                f"{API_BASE_URL}/sessions/{st.session_state.session_id}",
                timeout=5
            )

            if response.status_code == 200:
                return True
            else:
                # Session expired or invalid, create new one
                st.session_state.session_id = None
                return create_or_get_session()

    except Exception as e:
        logger.error(f"Session management failed: {e}")
        return False


def load_conversation_history():
    """Load conversation history from backend."""
    try:
        if not st.session_state.session_id:
            return

        response = requests.get(
            f"{API_BASE_URL}/sessions/{st.session_state.session_id}/messages",
            timeout=10
        )

        if response.status_code == 200:
            messages = response.json()
            st.session_state.messages = []

            for msg in messages:
                message_data = {
                    "role": msg["role"],
                    "content": msg["content"],
                    "timestamp": datetime.fromisoformat(msg["created_at"].replace('Z', '+00:00'))
                }

                # Add tools and sources for assistant messages
                if msg["role"] == "assistant" and msg.get("metadata"):
                    metadata = msg["metadata"]
                    message_data["tools_used"] = metadata.get("tools_used", [])
                    message_data["sources"] = metadata.get("sources", [])

                st.session_state.messages.append(message_data)

            logger.info(f"Loaded {len(messages)} messages from session")

    except Exception as e:
        logger.error(f"Failed to load conversation history: {e}")





def send_chat_message(message: str) -> Optional[Dict[str, Any]]:
    """Send a chat message to the agent."""
    try:
        chat_request = {
            "message": message,
            "user_id": "default_user",
            "session_id": st.session_state.session_id,
            "search_type": "hybrid",
            "max_results": 10
        }

        response = requests.post(
            f"{API_BASE_URL}/chat",
            json=chat_request,
            timeout=30
        )

        if response.status_code == 200:
            response_data = response.json()
            # Update session_id if it was created by the backend
            if response_data.get("session_id"):
                st.session_state.session_id = response_data["session_id"]
            return response_data
        else:
            st.error(f"Chat request failed: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Chat request failed: {e}")
        st.error(f"Chat request failed: {str(e)}")
        return None


def process_sample_data():
    """Process sample automotive data."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/ingest",
            json={"sample_data": True},
            timeout=60
        )
        
        if response.status_code == 200:
            st.success("✅ Sample data processing started!")
            return True
        else:
            st.error(f"Failed to process sample data: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Failed to process sample data: {e}")
        st.error(f"Failed to process sample data: {str(e)}")
        return False


def process_uploaded_files(files):
    """Process uploaded files."""
    try:
        # Save uploaded files to temporary directory
        temp_dir = tempfile.mkdtemp()
        file_paths = []
        
        for file in files:
            file_path = Path(temp_dir) / file.name
            with open(file_path, "wb") as f:
                f.write(file.getbuffer())
            file_paths.append(str(file_path))
        
        # Send to API
        response = requests.post(
            f"{API_BASE_URL}/ingest",
            json={"file_paths": file_paths},
            timeout=120
        )
        
        if response.status_code == 200:
            st.success(f"✅ Processing {len(files)} files started!")
            return True
        else:
            st.error(f"Failed to process files: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Failed to process files: {e}")
        st.error(f"Failed to process files: {str(e)}")
        return False


def main():
    """Main Streamlit application."""
    initialize_session_state()

    # Check API health
    api_healthy = check_api_health()
    get_system_stats()

    # Header
    st.title("🚗 ADAS Diagnostics Co-pilot")
    st.markdown("*AI-powered automotive diagnostics assistant*")

    # System status
    render_system_status()

    if not api_healthy:
        st.error("⚠️ API is not available. Please ensure the backend is running.")
        st.stop()

    # Initialize session and load conversation history
    if not st.session_state.session_initialized:
        with st.spinner("🔄 Initializing session..."):
            if create_or_get_session():
                load_conversation_history()
                st.session_state.session_initialized = True
            else:
                st.error("⚠️ Failed to initialize session. Some features may not work properly.")
    
    # Sidebar - Clean and simple
    with st.sidebar:
        st.header("🚗 Mercedes-Benz E-Class")
        st.markdown("**Diagnostics Co-pilot**")

        st.divider()

        # Session management
        if st.session_state.session_id:
            st.subheader("💬 Conversation")
            st.caption(f"Session: {st.session_state.session_id[:8]}...")

            if st.button("🆕 New Conversation", use_container_width=True):
                # Clear current session and start new one
                st.session_state.session_id = None
                st.session_state.session_initialized = False
                st.session_state.messages = []
                st.rerun()

        st.divider()

        # System status
        render_system_status()
    
    # Single column clean chat interface
    st.header("💬 Mercedes-Benz E-Class Diagnostics Assistant")
    st.markdown("Ask me anything about your Mercedes-Benz E-Class diagnostics, maintenance, or technical questions.")

    # Display chat messages
    for message in st.session_state.messages:
        # Prepare enhanced data for assistant messages
        enhanced_data = None
        if message["role"] == "assistant":
            enhanced_data = {
                "suggestions": message.get("suggestions", []),
                "next_steps": message.get("next_steps", []),
                "related_topics": message.get("related_topics", []),
                "diagnostic_guidance": message.get("diagnostic_guidance"),
                "safety_considerations": message.get("safety_considerations", []),
                "quick_actions": message.get("quick_actions", []),
                "preventive_tips": message.get("preventive_tips", []),
                "common_issues": message.get("common_issues", [])
            }

        render_chat_message(
            message["role"],
            message["content"],
            message.get("timestamp"),
            enhanced_data
        )

        # Show tool usage and sources for assistant messages
        if message["role"] == "assistant":
            if message.get("tools_used"):
                render_tool_usage(message["tools_used"])

            if message.get("sources"):
                render_sources(message["sources"])

    # Chat input
    if prompt := st.chat_input("Ask about Mercedes-Benz E-Class diagnostics..."):
        # Add user message to local state for immediate display
        user_message = {
            "role": "user",
            "content": prompt,
            "timestamp": datetime.now()
        }
        st.session_state.messages.append(user_message)

        # Get AI response
        with st.spinner("🤖 Analyzing your question..."):
            response = send_chat_message(prompt)

            if response:
                assistant_message = {
                    "role": "assistant",
                    "content": response.get("message", "Sorry, I couldn't process your request."),
                    "timestamp": datetime.now(),
                    "tools_used": response.get("tools_used", []),
                    "sources": response.get("sources", []),
                    # Enhanced proactive information
                    "suggestions": response.get("suggestions", []),
                    "next_steps": response.get("next_steps", []),
                    "related_topics": response.get("related_topics", []),
                    "diagnostic_guidance": response.get("diagnostic_guidance"),
                    "safety_considerations": response.get("safety_considerations", []),
                    "quick_actions": response.get("quick_actions", []),
                    "preventive_tips": response.get("preventive_tips", []),
                    "common_issues": response.get("common_issues", [])
                }
                st.session_state.messages.append(assistant_message)
                st.rerun()
            else:
                # Remove user message if response failed
                st.session_state.messages.pop()
        
        if not st.session_state.get("last_tools_used") and not st.session_state.get("last_sources"):
            st.info("Tool usage and source references will appear here during conversations.")


if __name__ == "__main__":
    main()
