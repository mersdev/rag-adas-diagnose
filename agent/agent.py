"""
Main Pydantic AI agent for ADAS Diagnostics Co-pilot.

This module implements the core conversational agent with automotive-specific
tools and context management for diagnostic assistance.
"""

import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel
from pydantic_ai import Agent, RunContext

from .config import get_settings
from .models import (
    ChatRequest, ChatResponse, ToolCall
)
from .db_utils import get_db_manager
from .tools import AutomotiveTools, TimelineQuery, DependencyQuery, HybridSearchQuery
from .graph_utils import get_graph_manager, AutomotiveGraphRepository

logger = logging.getLogger(__name__)


class AutomotiveContext(BaseModel):
    """Context for automotive diagnostic conversations."""
    user_id: str
    active_vin: Optional[str] = None
    active_system: Optional[str] = None
    active_component: Optional[str] = None
    tools_used: List[ToolCall] = []


class ADASAgent:
    """ADAS Diagnostics Co-pilot Agent."""
    
    def __init__(self):
        """Initialize the ADAS agent."""
        self.settings = get_settings()
        self.tools = AutomotiveTools()
        self.db_manager = None
        self.graph_repo = None
        
        # Initialize Pydantic AI agent
        self.agent = Agent(
            model=self._get_model_config(),
            system_prompt=self._get_system_prompt(),
            deps_type=AutomotiveContext
        )
        
        # Register tools
        self._register_tools()
    
    def _get_model_config(self) -> str:
        """Get model configuration for Pydantic AI."""
        provider, base_url, api_key, model_choice = self.settings.llm.llm_provider.value, self.settings.llm.llm_base_url, self.settings.llm.llm_api_key, self.settings.llm.llm_choice

        if provider == "openai":
            return f"openai:{model_choice}"
        elif provider == "ollama":
            return f"ollama:{model_choice}"
        elif provider == "gemini":
            # Use Google Generative Language API (google-gla) provider for Gemini
            return f"google-gla:{model_choice}"
        elif provider == "groq":
            return f"groq:{model_choice}"
        else:
            return f"openai:{model_choice}"  # Default fallback
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for the agent."""
        return """You are an AI-powered ADAS (Advanced Driver-Assistance Systems) Diagnostics Co-pilot specialized in Mercedes-Benz E-Class vehicles.

Your role is to assist automotive engineers and technicians by providing immediate, actionable guidance for Mercedes-Benz E-Class diagnostics and problem-solving. You have access to comprehensive Mercedes-Benz E-Class documentation including:

- OTA (Over-The-Air) update release notes
- Hardware specifications and datasheets
- System architecture documents
- Diagnostic trouble codes (DTCs)
- Technician repair notes
- Supplier documentation

**Your capabilities include:**

1. **Timeline Analysis**: Track chronological events, software updates, and component changes for specific vehicles or systems
2. **Dependency Mapping**: Analyze component relationships, supplier dependencies, and system interactions
3. **Hybrid Search**: Perform semantic search across automotive documentation using vector similarity

**Mercedes-Benz E-Class System Knowledge:**

**E-Class Braking System:**
- Brake pads, brake discs (rotors), brake calipers with Mercedes-Benz specific components
- ABS (Anti-lock Braking System) with ESP (Electronic Stability Program)
- Brake Assist (BAS) and Active Brake Assist systems
- Common symptoms: ABS warning light, spongy brakes, brake pedal pulsation, noise, pulling to one side

**E-Class Key Systems:**
- Engine management (M264 4-cylinder, M256 6-cylinder engines)
- 9G-TRONIC automatic transmission
- AIRMATIC air suspension (on equipped models)
- Mercedes-Benz ADAS: DISTRONIC, Active Lane Keeping Assist, Active Brake Assist
- COMAND/MBUX infotainment system
- Mercedes me connect telematics

**Your Approach:**

1. **ALWAYS search the knowledge base FIRST** - For any automotive-related question, you MUST use the hybrid_search tool to search the knowledge base before providing an answer
2. **Base answers on retrieved documents** - Use the search results to provide accurate, document-backed responses
3. **Focus on problem-solving** - Emphasize solutions, next steps, and diagnostic procedures from the retrieved documentation
4. **Ask for specific information only when needed** - If additional details would significantly improve your assistance, ask targeted questions
5. **Be conversational and helpful** - Maintain a professional but approachable tone

**When additional information would help:**

- **VIN**: Ask only when vehicle-specific recalls, TSBs, or configuration details are relevant to the problem
- **Specific symptoms**: Request details when general descriptions could apply to multiple issues
- **Timeline**: Ask about timing only when it's crucial for diagnosis (e.g., recent updates, intermittent issues)

**Guidelines:**

- Provide immediate, actionable diagnostic insights
- Reference relevant documentation and sources when available
- Explain your reasoning process clearly
- Prioritize safety-critical issues
- Consider both hardware and software factors
- Suggest practical next steps and verification procedures
- Be transparent about which tools you're using and why

**Problem-Solving Process:**

1. **MANDATORY**: Use hybrid_search to search the knowledge base for relevant information about the user's question
2. Analyze the retrieved documents and extract relevant information
3. Provide answers based on the search results, citing specific documents when possible
4. Offer specific diagnostic steps or solutions from the retrieved documentation
5. Suggest next actions and verification procedures based on the knowledge base
6. Ask for additional information only if it would significantly improve your assistance

**CRITICAL**: You must ALWAYS search the knowledge base using hybrid_search before answering automotive questions. Do not rely on general knowledge when specific documentation is available.

You should be helpful, knowledgeable, and focused on getting users to a solution quickly. When users describe problems, acknowledge their situation and provide actionable advice rather than immediately requesting more information."""
    
    def _register_tools(self):
        """Register automotive diagnostic tools with the agent."""
        
        @self.agent.tool
        async def timeline_analysis(ctx: RunContext[AutomotiveContext], query: TimelineQuery) -> Dict[str, Any]:
            """
            Analyze timeline of events for a specific vehicle, system, or component.
            
            Use this tool to track chronological changes, updates, and issues.
            Helpful for understanding what changed before a problem occurred.
            """
            try:
                if not self.tools.db_manager:
                    await self.tools.initialize()
                
                result = await self.tools.timeline_analysis(query)
                
                # Track tool usage
                tool_call = ToolCall(
                    tool_name="timeline_analysis",
                    args=query.model_dump(),
                    result=result,
                    success=True
                )
                ctx.deps.tools_used.append(tool_call)
                
                return result
                
            except Exception as e:
                logger.error(f"Timeline analysis tool failed: {e}")
                tool_call = ToolCall(
                    tool_name="timeline_analysis",
                    args=query.model_dump(),
                    success=False,
                    error_message=str(e)
                )
                ctx.deps.tools_used.append(tool_call)
                return {"error": f"Timeline analysis failed: {str(e)}"}
        
        @self.agent.tool
        async def dependency_mapping(ctx: RunContext[AutomotiveContext], query: DependencyQuery) -> Dict[str, Any]:
            """
            Map dependencies and relationships for automotive components.
            
            Use this tool to understand component relationships, supplier dependencies,
            and system interactions. Helpful for impact analysis.
            """
            try:
                if not self.tools.db_manager:
                    await self.tools.initialize()
                
                result = await self.tools.dependency_mapping(query)
                
                # Track tool usage
                tool_call = ToolCall(
                    tool_name="dependency_mapping",
                    args=query.model_dump(),
                    result=result,
                    success=True
                )
                ctx.deps.tools_used.append(tool_call)
                
                return result
                
            except Exception as e:
                logger.error(f"Dependency mapping tool failed: {e}")
                tool_call = ToolCall(
                    tool_name="dependency_mapping",
                    args=query.model_dump(),
                    success=False,
                    error_message=str(e)
                )
                ctx.deps.tools_used.append(tool_call)
                return {"error": f"Dependency mapping failed: {str(e)}"}
        
        @self.agent.tool
        async def hybrid_search(ctx: RunContext[AutomotiveContext], query: HybridSearchQuery) -> Dict[str, Any]:
            """
            Perform hybrid search combining vector similarity and keyword matching.
            
            Use this tool to search across automotive documentation for relevant
            information about symptoms, components, or diagnostic procedures.
            """
            try:
                if not self.tools.db_manager:
                    await self.tools.initialize()
                
                result = await self.tools.hybrid_search(query)
                
                # Track tool usage
                tool_call = ToolCall(
                    tool_name="hybrid_search",
                    args=query.model_dump(),
                    result=result,
                    success=True
                )
                ctx.deps.tools_used.append(tool_call)
                
                return result
                
            except Exception as e:
                logger.error(f"Hybrid search tool failed: {e}")
                tool_call = ToolCall(
                    tool_name="hybrid_search",
                    args=query.model_dump(),
                    success=False,
                    error_message=str(e)
                )
                ctx.deps.tools_used.append(tool_call)
                return {"error": f"Hybrid search failed: {str(e)}"}
    
    async def initialize(self):
        """Initialize agent dependencies."""
        try:
            # Initialize database connections
            self.db_manager = await get_db_manager()
            
            # Initialize graph repository
            try:
                graph_manager = await get_graph_manager()
                self.graph_repo = AutomotiveGraphRepository(graph_manager)
            except Exception as e:
                logger.warning(f"Graph repository initialization failed: {e}")
                self.graph_repo = None
            
            # Initialize tools
            await self.tools.initialize()
            
            logger.info("ADAS Agent initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize ADAS Agent: {e}")
            raise
    
    async def chat(self, request: ChatRequest) -> ChatResponse:
        """Process a chat request and return response."""
        start_time = datetime.utcnow()

        try:
            # Create context
            context = AutomotiveContext(
                user_id=request.user_id,
                tools_used=[]
            )

            # Run agent
            result = await self.agent.run(request.message, deps=context)

            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()

            # Extract sources from tool results
            sources = []
            for tool_call in context.tools_used:
                if tool_call.success and tool_call.result:
                    if "results" in tool_call.result:
                        # From hybrid_search - results are dictionaries from model_dump()
                        for result_data in tool_call.result["results"]:
                            if isinstance(result_data, dict):
                                # Convert dict to SearchResult
                                from .models import SearchResult
                                try:
                                    search_result = SearchResult(**result_data)
                                    sources.append(search_result)
                                except Exception as e:
                                    logger.error(f"Failed to convert result to SearchResult: {e}")
                                    logger.error(f"Result data: {result_data}")
                            else:
                                # Already a SearchResult object
                                sources.append(result_data)

            return ChatResponse(
                message=result.data,
                tools_used=context.tools_used,
                sources=sources,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Chat processing failed: {e}")
            processing_time = (datetime.utcnow() - start_time).total_seconds()

            return ChatResponse(
                message=f"I apologize, but I encountered an error while processing your request: {str(e)}",
                tools_used=[],
                sources=[],
                processing_time=processing_time
            )


# Global agent instance
adas_agent: Optional[ADASAgent] = None


async def get_agent() -> ADASAgent:
    """Get the global ADAS agent instance."""
    global adas_agent
    if not adas_agent:
        raise RuntimeError("ADAS Agent not initialized")
    return adas_agent


async def initialize_agent() -> None:
    """Initialize the global ADAS agent."""
    global adas_agent
    adas_agent = ADASAgent()
    await adas_agent.initialize()


async def close_agent() -> None:
    """Close the global ADAS agent."""
    global adas_agent
    if adas_agent:
        # No specific cleanup needed for Pydantic AI agent
        adas_agent = None
