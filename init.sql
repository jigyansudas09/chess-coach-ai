-- =====================================================
-- Chess Coach Database Initialization Script
-- Complete setup for chess game and move storage
-- =====================================================

-- Create database (run this separately as superuser if needed)
-- CREATE DATABASE chess_coach;

-- Connect to the database
-- \c chess_coach;

-- =====================================================
-- EXTENSIONS
-- =====================================================

-- Enable pg_trgm extension for fast partial text search
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- =====================================================
-- TABLES
-- =====================================================

-- Create games table for storing complete chess games
CREATE TABLE IF NOT EXISTS games (
    id SERIAL PRIMARY KEY,
    pgn TEXT NOT NULL,
    final_fen TEXT NOT NULL,
    game_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create moves table for storing bookmarked moves with analysis
CREATE TABLE IF NOT EXISTS moves (
    id SERIAL PRIMARY KEY,
    fen TEXT NOT NULL,
    move_notation VARCHAR(20),
    position_assessment TEXT,
    best_move_1 TEXT,
    best_move_2 TEXT,
    best_move_3 TEXT,
    tactical_opportunities TEXT,
    strategic_advice TEXT,
    tags TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================

-- Primary indexes for core functionality
CREATE INDEX IF NOT EXISTS idx_moves_tags ON moves USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_moves_fen ON moves(fen);
CREATE INDEX IF NOT EXISTS idx_games_created_at ON games(created_at DESC);

-- Trigram indexes for fast partial text search
CREATE INDEX IF NOT EXISTS idx_moves_notation_trgm ON moves USING GIN(move_notation gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_moves_assessment_trgm ON moves USING GIN(position_assessment gin_trgm_ops);

-- Additional performance indexes
CREATE INDEX IF NOT EXISTS idx_games_name ON games(game_name) WHERE game_name IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_moves_created_at ON moves(created_at DESC);

-- =====================================================
-- CONSTRAINTS FOR DATA QUALITY
-- =====================================================

-- Ensure data integrity
ALTER TABLE games ADD CONSTRAINT IF NOT EXISTS check_pgn_not_empty 
    CHECK (LENGTH(TRIM(pgn)) > 0);

ALTER TABLE games ADD CONSTRAINT IF NOT EXISTS check_fen_not_empty 
    CHECK (LENGTH(TRIM(final_fen)) > 0);

ALTER TABLE moves ADD CONSTRAINT IF NOT EXISTS check_fen_not_empty 
    CHECK (LENGTH(TRIM(fen)) > 0);

-- =====================================================
-- TRIGGERS
-- =====================================================

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to auto-update updated_at on games table
DROP TRIGGER IF EXISTS update_games_updated_at ON games;
CREATE TRIGGER update_games_updated_at 
    BEFORE UPDATE ON games 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- SAMPLE DATA (OPTIONAL)
-- =====================================================

-- Insert sample game (uncomment if you want test data)
/*
INSERT INTO games (pgn, final_fen, game_name) 
VALUES (
    '[Event "Sample Game"]
[Site "Chess Coach"]
[Date "2025.07.03"]
[Round "1"]
[White "Player1"]
[Black "Player2"]
[Result "*"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 *',
    'r1bqkbnr/1ppp1ppp/p1n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 4',
    'Sample Opening Game'
);
*/

-- Insert sample move with analysis (uncomment if you want test data)
/*
INSERT INTO moves (
    fen, 
    move_notation, 
    position_assessment,
    best_move_1,
    best_move_2,
    best_move_3,
    tactical_opportunities,
    strategic_advice,
    tags
) VALUES (
    'rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1',
    'e4',
    'White opens with the King''s Pawn, controlling the center and allowing for quick development.',
    'e4 - King''s Pawn Opening, strong central control',
    'd4 - Queen''s Pawn Opening, equally strong',
    'Nf3 - Knight development, flexible approach',
    'Control the center early and develop pieces quickly',
    'Focus on central control and piece development in the opening',
    ARRAY['opening', 'center', 'development', 'tactics']
);
*/

-- =====================================================
-- UTILITY QUERIES FOR VERIFICATION
-- =====================================================

-- Check table structures
/*
\d games;
\d moves;
*/

-- Check indexes
/*
SELECT 
    indexname, 
    tablename, 
    indexdef 
FROM pg_indexes 
WHERE tablename IN ('games', 'moves') 
ORDER BY tablename, indexname;
*/

-- Check extensions
/*
SELECT extname, extversion FROM pg_extension WHERE extname = 'pg_trgm';
*/

-- Count records
/*
SELECT 
    'games' as table_name, COUNT(*) as record_count 
FROM games
UNION ALL
SELECT 
    'moves' as table_name, COUNT(*) as record_count 
FROM moves;
*/

-- =====================================================
-- HELPFUL QUERIES FOR DEVELOPMENT
-- =====================================================

-- Search moves by tag (example)
/*
SELECT * FROM moves 
WHERE 'tactics' = ANY(tags)
ORDER BY created_at DESC;
*/

-- Search moves by partial text (example)
/*
SELECT * FROM moves 
WHERE position_assessment ILIKE '%center%'
   OR move_notation ILIKE '%e4%'
ORDER BY created_at DESC;
*/

-- Get game with moves count
/*
SELECT 
    g.id,
    g.game_name,
    g.created_at,
    LENGTH(g.pgn) as pgn_length,
    (SELECT COUNT(*) FROM moves m WHERE m.fen = g.final_fen) as related_moves
FROM games g
ORDER BY g.created_at DESC;
*/

-- =====================================================
-- CLEANUP QUERIES (USE WITH CAUTION)
-- =====================================================

-- Uncomment these only if you need to reset the database
/*
-- DROP TABLE IF EXISTS moves CASCADE;
-- DROP TABLE IF EXISTS games CASCADE;
-- DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;
-- DROP EXTENSION IF EXISTS pg_trgm CASCADE;
*/

-- =====================================================
-- SCRIPT COMPLETION
-- =====================================================

-- Display completion message
DO $$
BEGIN
    RAISE NOTICE 'Chess Coach database initialization completed successfully!';
    RAISE NOTICE 'Tables created: games, moves';
    RAISE NOTICE 'Indexes created: 6 performance indexes';
    RAISE NOTICE 'Extensions enabled: pg_trgm';
    RAISE NOTICE 'Triggers created: auto-update timestamps';
    RAISE NOTICE 'Ready for chess analysis application!';
END $$;

-- Show final table counts
SELECT 
    'Database initialization complete' as status,
    (SELECT COUNT(*) FROM games) as games_count,
    (SELECT COUNT(*) FROM moves) as moves_count,
    CURRENT_TIMESTAMP as completed_at;
