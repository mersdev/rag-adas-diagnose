#!/usr/bin/env python3
"""
Test script to verify RAG functionality is working correctly.
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set environment variables
os.environ['DATABASE_URL'] = 'postgresql://adas_user:adas_password@localhost:5435/adas_diagnostics'

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from agent.agent import ADASAgent
from agent.models import ChatRequest
from agent.db_utils import initialize_database

async def test_rag():
    """Test that RAG is working by asking about Mercedes-Benz E-Class Primary Camera Unit."""
    print("🚗 Testing RAG functionality...")
    print("=" * 50)
    
    try:
        # Initialize database first
        await initialize_database(os.environ['DATABASE_URL'])
        print("✅ Database initialized successfully")

        # Initialize the agent
        agent = ADASAgent()
        await agent.initialize()
        print("✅ Agent initialized successfully")
        
        # Test question that should trigger RAG
        test_question = "Explain how the brake system works in modern vehicles"
        print(f"\n❓ Test Question: {test_question}")
        
        # Create chat request
        request = ChatRequest(
            message=test_question,
            user_id="test_user"
        )
        
        # Get response
        print("\n🔍 Processing request...")
        response = await agent.chat(request)
        
        # Check if tools were used
        print(f"\n📊 Tools used: {len(response.tools_used)}")
        for tool in response.tools_used:
            print(f"   - {tool.tool_name}: {'✅ Success' if tool.success else '❌ Failed'}")
        
        # Check if sources were found
        print(f"\n📚 Sources found: {len(response.sources)}")
        for i, source in enumerate(response.sources[:3]):  # Show first 3 sources
            if hasattr(source, 'document_title'):
                print(f"   {i+1}. {source.document_title} (Score: {source.score})")
            else:
                print(f"   {i+1}. {source.get('document_title', 'Unknown')} (Score: {source.get('score', 'N/A')})")
        
        # Show response
        print(f"\n🤖 Response:")
        print("-" * 30)
        print(response.message)
        print("-" * 30)
        
        # Verify RAG is working
        if response.tools_used and any(tool.tool_name == "hybrid_search" for tool in response.tools_used):
            print("\n✅ RAG IS WORKING! The agent used hybrid_search tool.")
        else:
            print("\n❌ RAG IS NOT WORKING! The agent did not use hybrid_search tool.")
            
        if response.sources:
            print("✅ Sources were retrieved from the knowledge base.")
        else:
            print("❌ No sources were retrieved from the knowledge base.")
            
        print(f"\n⏱️  Processing time: {response.processing_time:.2f}s")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_rag())
