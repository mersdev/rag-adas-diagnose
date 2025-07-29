-- Migration script to add session management tables
-- Run this script on existing databases to add session functionality

-- Check if sessions table exists, if not create it
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'sessions') THEN
        -- Sessions table for chat session management
        CREATE TABLE sessions (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id VARCHAR(255) NOT NULL DEFAULT 'default_user',
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP WITH TIME ZONE
        );
        
        -- Create indexes for sessions table
        CREATE INDEX idx_sessions_user_id ON sessions(user_id);
        CREATE INDEX idx_sessions_expires_at ON sessions(expires_at);
        CREATE INDEX idx_sessions_created_at ON sessions(created_at);
        
        RAISE NOTICE 'Created sessions table with indexes';
    ELSE
        RAISE NOTICE 'Sessions table already exists';
    END IF;
END
$$;

-- Check if messages table exists, if not create it
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'messages') THEN
        -- Messages table for storing conversation history
        CREATE TABLE messages (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
            role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
            content TEXT NOT NULL,
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Create indexes for messages table
        CREATE INDEX idx_messages_session_id ON messages(session_id);
        CREATE INDEX idx_messages_role ON messages(role);
        CREATE INDEX idx_messages_created_at ON messages(created_at);
        
        RAISE NOTICE 'Created messages table with indexes';
    ELSE
        RAISE NOTICE 'Messages table already exists';
    END IF;
END
$$;

-- Create a trigger to update the updated_at timestamp for sessions
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM information_schema.triggers WHERE trigger_name = 'update_sessions_updated_at') THEN
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $trigger$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $trigger$ LANGUAGE plpgsql;
        
        CREATE TRIGGER update_sessions_updated_at
            BEFORE UPDATE ON sessions
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
            
        RAISE NOTICE 'Created updated_at trigger for sessions table';
    ELSE
        RAISE NOTICE 'Sessions updated_at trigger already exists';
    END IF;
END
$$;

RAISE NOTICE 'Session management migration completed successfully';
