#!/usr/bin/env python3
"""
Test the exact SQL query that hybrid search is generating.
"""

import asyncio
import os
import asyncpg

# Set environment variables
os.environ['DATABASE_URL'] = 'postgresql://adas_user:adas_password@localhost:5434/adas_diagnostics'

async def test_sql():
    """Test the SQL query directly."""
    print("🔍 Testing SQL query directly...")
    print("=" * 50)
    
    try:
        # Connect to database
        conn = await asyncpg.connect(os.environ['DATABASE_URL'])
        print("✅ Connected to database")
        
        # Simulate the hybrid search logic
        query_text = "ADAS camera"
        
        # Filter stop words (same logic as in hybrid search)
        stop_words = {'what', 'is', 'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'how', 'why', 'when', 'where', 'who', 'which', 'that', 'this', 'these', 'those', '?', '.', ',', '!'}
        search_terms = [term.strip('.,!?') for term in query_text.lower().split() if term.strip('.,!?') not in stop_words and len(term.strip('.,!?')) > 2]
        
        print(f"Original query: {query_text}")
        print(f"Filtered search terms: {search_terms}")
        
        # Build the SQL query (same logic as hybrid search)
        search_conditions = []
        search_values = []
        param_count = 1
        
        if search_terms:
            term_conditions = []
            for term in search_terms:
                term_conditions.append(f"(LOWER(c.content) LIKE ${param_count} OR LOWER(d.title) LIKE ${param_count})")
                search_values.append(f"%{term}%")
                param_count += 1
            
            # Use OR logic for search terms
            search_conditions.append(f"({' OR '.join(term_conditions)})")
        else:
            search_conditions.append("TRUE")
        
        where_clause = " AND ".join(search_conditions) if search_conditions else "TRUE"
        
        # Build the full query
        search_query = f"""
        SELECT 
            c.id as chunk_id,
            c.document_id,
            c.content,
            c.chunk_index,
            d.title as document_title,
            d.filename as document_filename,
            d.content_type,
            d.vehicle_system,
            d.component_name,
            d.supplier,
            d.severity_level,
            1.0 as relevance_score
        FROM chunks c
        JOIN documents d ON c.document_id = d.id
        WHERE {where_clause}
        ORDER BY
            CASE WHEN LOWER(d.title) LIKE '%camera%' THEN 1 ELSE 2 END,
            CASE WHEN LOWER(d.title) LIKE '%adas%' THEN 1 ELSE 2 END,
            d.created_at DESC
        LIMIT ${param_count}
        """
        
        search_values.append(10)  # max_results
        
        print(f"\nSQL Query:")
        print(search_query)
        print(f"\nParameters: {search_values}")
        
        # Execute the query
        rows = await conn.fetch(search_query, *search_values)
        
        print(f"\n📊 Results: {len(rows)}")
        for i, row in enumerate(rows[:5]):
            print(f"\n   Result {i+1}:")
            print(f"     - Title: {row['document_title']}")
            print(f"     - Content: {row['content'][:100]}...")
            print(f"     - Filename: {row['document_filename']}")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_sql())
