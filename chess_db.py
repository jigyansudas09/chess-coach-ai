import psycopg2
from psycopg2.extras import RealDictCursor
import json

class ChessDatabase:
    def __init__(self):
        self.connection = psycopg2.connect(
            host="localhost",
            database="chess_coach",
            user="postgres",
            password="zirconOrder",
        )
    def get_game_by_id(self, game_id):
        """Get specific game by ID"""
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT id, pgn, final_fen, game_name, created_at
                FROM games
                WHERE id = %s
            """, (game_id,))
            return cursor.fetchone()

    def delete_game(self, game_id):
        """Delete specific game"""
        with self.connection.cursor() as cursor:
            cursor.execute("DELETE FROM games WHERE id = %s", (game_id,))
            self.connection.commit()
            return cursor.rowcount > 0

    def delete_move(self, move_id):
        """Delete specific move"""
        with self.connection.cursor() as cursor:
            cursor.execute("DELETE FROM moves WHERE id = %s", (move_id,))
            self.connection.commit()
            return cursor.rowcount > 0

    
    def save_game(self, pgn, final_fen, game_name=None):
        """Save complete game to database"""
        with self.connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO games (pgn, final_fen, game_name)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (pgn, final_fen, game_name))
            self.connection.commit()
            return cursor.fetchone()[0]
    
    def save_move(self, fen, move_notation, analysis_data):
        """Save bookmarked move with analysis"""
        tags = analysis_data.get('tags', [])
        
        with self.connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO moves (fen, move_notation, position_assessment, 
                                 best_move_1, best_move_2, best_move_3,
                                 tactical_opportunities, strategic_advice, tags)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                fen, move_notation,
                analysis_data.get('position_assessment'),
                analysis_data.get('best_move_1'),
                analysis_data.get('best_move_2'),
                analysis_data.get('best_move_3'),
                analysis_data.get('tactical_opportunities'),
                analysis_data.get('strategic_advice'),
                tags
            ))
            self.connection.commit()
            return cursor.fetchone()[0]
    
    def get_games(self, limit=50, offset=0):
        """Get games list with pagination"""
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT id, game_name, final_fen, created_at
                FROM games
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """, (limit, offset))
            return cursor.fetchall()
    
    def search_moves(self, search_query, limit=50, offset=0):
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            if not search_query or not search_query.strip():
                cursor.execute("""
                    SELECT * FROM moves
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                """, (limit, offset))
                return cursor.fetchall()
            
            cleaned_query = search_query.strip().lower()
            search_pattern = f'%{cleaned_query}%'
            
            cursor.execute("""
                SELECT * FROM moves
                WHERE EXISTS (
                    SELECT 1 FROM unnest(tags) AS tag
                    WHERE tag ILIKE %s
                )
                OR position_assessment ILIKE %s
                OR move_notation ILIKE %s
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """, (search_pattern, search_pattern, search_pattern, limit, offset))
            
            return cursor.fetchall()

            
    
    def get_all_moves(self, limit=50, offset=0):
        """Get all moves with pagination"""
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT * FROM moves
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """, (limit, offset))
            return cursor.fetchall()

# Add to your existing ChessCoach class
chess_db = ChessDatabase()
