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
    ChatRequest, ChatResponse, ToolCall, Suggestion, NextStep,
    RelatedTopic, DiagnosticGuidance, SafetyConsideration
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

Your role is to assist automotive engineers and technicians by providing comprehensive, proactive guidance for Mercedes-Benz E-Class diagnostics and problem-solving. You have access to comprehensive Mercedes-Benz E-Class documentation including:

- OTA (Over-The-Air) update release notes
- Hardware specifications and datasheets
- System architecture documents
- Diagnostic trouble codes (DTCs)
- Technician repair notes
- Supplier documentation

**Your enhanced capabilities include:**

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

**Your Proactive Approach:**

1. **ALWAYS search the knowledge base FIRST** - For any automotive-related question, you MUST use the hybrid_search tool to search the knowledge base before providing an answer
2. **Provide comprehensive, proactive responses** - Instead of asking users for more information, provide rich, detailed responses that anticipate their needs
3. **Include contextual suggestions** - Always suggest related topics, preventive measures, and next steps
4. **Offer diagnostic guidance** - Provide step-by-step procedures and troubleshooting tips
5. **Highlight safety considerations** - Include relevant safety warnings and precautions
6. **Suggest related components** - Mention connected systems and components that might be affected

**Proactive Information to Include:**

- **Related Topics**: Suggest connected systems, components, or procedures
- **Next Steps**: Provide clear diagnostic or maintenance steps
- **Preventive Tips**: Include maintenance recommendations to prevent issues
- **Common Issues**: Mention typical problems associated with discussed components
- **Safety Considerations**: Highlight any safety-critical aspects
- **Quick Actions**: Suggest immediate checks or verifications

**Enhanced Response Guidelines:**

- Provide immediate, comprehensive diagnostic insights with contextual information
- Reference relevant documentation and sources when available
- Explain your reasoning process clearly and include related considerations
- Prioritize safety-critical issues and highlight safety considerations
- Consider both hardware and software factors, including connected systems
- Suggest practical next steps, verification procedures, and preventive measures
- Be transparent about which tools you're using and why
- Proactively suggest related topics and potential follow-up actions

**Enhanced Problem-Solving Process:**

1. **MANDATORY**: Use hybrid_search to search the knowledge base for relevant information about the user's question
2. Analyze the retrieved documents and extract comprehensive information
3. Provide detailed answers based on the search results, citing specific documents
4. Include proactive suggestions for related topics and components
5. Offer specific diagnostic steps or solutions with safety considerations
6. Suggest preventive maintenance tips and common issue awareness
7. Provide quick actions and immediate verification steps
8. Anticipate follow-up questions and provide contextual information

**Response Structure - Always Include:**
- Main answer based on knowledge base search
- Related topics and connected systems
- Suggested next steps or diagnostic procedures
- Preventive maintenance tips when relevant
- Safety considerations if applicable
- Quick actions for immediate verification
- Common issues associated with the topic

**CRITICAL**: You must ALWAYS search the knowledge base using hybrid_search before answering automotive questions. Provide comprehensive, proactive responses that anticipate user needs rather than asking for more information unless absolutely critical for safety or accuracy.

You should be helpful, knowledgeable, and focused on providing rich, contextual information that guides users through complete diagnostic and maintenance processes."""
    
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

    def _generate_proactive_information(self, message: str, sources: List[Any]) -> Dict[str, Any]:
        """Generate proactive information based on the message and sources."""
        suggestions = []
        next_steps = []
        related_topics = []
        safety_considerations = []
        quick_actions = []
        preventive_tips = []
        common_issues = []

        # Analyze message content for keywords and context
        message_lower = message.lower()

        # Generate suggestions based on content
        if any(keyword in message_lower for keyword in ["brake", "braking", "abs", "esp"]):
            suggestions.extend([
                Suggestion(
                    title="Check Brake Fluid Level",
                    description="Verify brake fluid level and condition as part of brake system diagnosis",
                    category="diagnostic",
                    priority="high",
                    action_type="diagnostic"
                ),
                Suggestion(
                    title="Inspect Brake Pads",
                    description="Visual inspection of brake pad thickness and wear patterns",
                    category="maintenance",
                    priority="medium",
                    action_type="maintenance"
                )
            ])

            next_steps.extend([
                NextStep(
                    step_number=1,
                    title="Visual Inspection",
                    description="Perform visual inspection of brake components",
                    estimated_time="10-15 minutes",
                    required_tools=["Flashlight", "Jack", "Jack stands"],
                    safety_notes=["Ensure vehicle is on level ground", "Use proper jack points"]
                ),
                NextStep(
                    step_number=2,
                    title="Brake Fluid Check",
                    description="Check brake fluid level and color",
                    estimated_time="5 minutes",
                    required_tools=["Clean cloth"],
                    safety_notes=["Do not contaminate brake fluid"]
                )
            ])

            safety_considerations.append(
                SafetyConsideration(
                    level="critical",
                    title="Brake System Safety",
                    description="Brake system issues can affect vehicle safety",
                    precautions=["Test brakes in safe environment", "Do not drive with brake warnings"]
                )
            )

            quick_actions.extend([
                "Check brake warning lights on dashboard",
                "Test brake pedal feel and travel",
                "Listen for unusual brake noises"
            ])

            preventive_tips.extend([
                "Replace brake fluid every 2-3 years",
                "Inspect brake pads every 12,000 miles",
                "Avoid hard braking when possible"
            ])

            common_issues.extend([
                "Brake pad wear causing squealing",
                "Brake fluid contamination",
                "ABS sensor malfunction"
            ])

        if any(keyword in message_lower for keyword in ["adas", "camera", "lane", "assist", "distronic"]):
            suggestions.extend([
                Suggestion(
                    title="Camera Calibration Check",
                    description="ADAS cameras may need recalibration after windshield replacement or alignment",
                    category="diagnostic",
                    priority="high",
                    action_type="diagnostic"
                ),
                Suggestion(
                    title="Software Version Check",
                    description="Verify ADAS software is up to date",
                    category="maintenance",
                    priority="medium",
                    action_type="diagnostic"
                )
            ])

            safety_considerations.append(
                SafetyConsideration(
                    level="important",
                    title="ADAS Limitations",
                    description="ADAS systems are driver assistance only, not autonomous driving",
                    precautions=["Always maintain attention while driving", "Understand system limitations"]
                )
            )

        # Generate related topics based on sources
        for source in sources[:3]:  # Limit to top 3 sources
            if hasattr(source, 'component_name') and source.component_name:
                related_topics.append(
                    RelatedTopic(
                        title=f"Related: {source.component_name}",
                        description=f"Component related to your query from {source.document_filename}",
                        relationship="related_component",
                        relevance_score=getattr(source, 'score', 0.0)
                    )
                )

        return {
            "suggestions": suggestions,
            "next_steps": next_steps,
            "related_topics": related_topics,
            "safety_considerations": safety_considerations,
            "quick_actions": quick_actions,
            "preventive_tips": preventive_tips,
            "common_issues": common_issues
        }
    
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

            # Generate proactive information
            proactive_info = self._generate_proactive_information(request.message, sources)

            return ChatResponse(
                message=result.data,
                tools_used=context.tools_used,
                sources=sources,
                processing_time=processing_time,
                suggestions=proactive_info["suggestions"],
                next_steps=proactive_info["next_steps"],
                related_topics=proactive_info["related_topics"],
                safety_considerations=proactive_info["safety_considerations"],
                quick_actions=proactive_info["quick_actions"],
                preventive_tips=proactive_info["preventive_tips"],
                common_issues=proactive_info["common_issues"]
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
