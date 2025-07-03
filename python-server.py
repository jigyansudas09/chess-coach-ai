from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import sys
import os
import traceback

# Import from the chess engine file
from psycopg2.extras import RealDictCursor

from chess_engine import analyze_chess_position
from coach_review import chess_coach
from chess_db import chess_db

app = Flask(__name__)
# Allow all origins for simplicity in a local dev environment
CORS(app, resources={r"/*": {"origins": "*"}})
@app.route('/debug-moves')
def debug_moves():
    try:
        with chess_db.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            # Get all moves with their exact data
            cursor.execute("SELECT id, move_notation, tags, position_assessment FROM moves;")
            all_moves = cursor.fetchall()
            
            # Test specific searches for 'e4'
            cursor.execute("SELECT id, move_notation FROM moves WHERE move_notation ILIKE %s", ('%e4%',))
            like_e4 = cursor.fetchall()
            
            cursor.execute("SELECT id, best_move_1, best_move_2, best_move_3 FROM moves WHERE best_move_1 ILIKE %s OR best_move_2 ILIKE %s OR best_move_3 ILIKE %s", ('%e4%', '%e4%', '%e4%'))
            best_moves_e4 = cursor.fetchall()
            
            return jsonify({
                "total_moves": len(all_moves),
                "all_moves_data": all_moves,
                "move_notation_with_e4": like_e4,
                "best_moves_with_e4": best_moves_e4
            })
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route('/api/game/<int:game_id>')
def get_game(game_id):
    try:
        game = chess_db.get_game_by_id(game_id)
        if game:
            return jsonify(game)
        else:
            return jsonify({'error': 'Game not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/game/<int:game_id>', methods=['DELETE'])
def delete_game(game_id):
    try:
        success = chess_db.delete_game(game_id)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/move/<int:move_id>', methods=['DELETE'])
def delete_move(move_id):
    try:
        success = chess_db.delete_move(move_id)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/save-game', methods=['POST'])
def save_game():
    try:
        data = request.json
        game_id = chess_db.save_game(
            data['pgn'], 
            data['final_fen'], 
            data.get('game_name')
        )
        return jsonify({'id': game_id, 'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/save-move', methods=['POST'])
def save_move():
    try:
        data = request.json
        move_id = chess_db.save_move(
            data['fen'],
            data['move_notation'],
            data['analysis_data']
        )
        return jsonify({'id': move_id, 'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/games')
def get_games():
    try:
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        games = chess_db.get_games(limit, offset)
        return jsonify(games)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/moves')
def get_moves():
    try:
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        moves = chess_db.get_all_moves(limit, offset)
        return jsonify(moves)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search-moves')
def search_moves():
    try:
        query = request.args.get('query')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        print(f"🔍 FLASK DEBUG: query='{query}', limit={limit}, offset={offset}")
        moves = chess_db.search_moves(query, limit, offset)
        print(f"🔍 FLASK DEBUG: Returning {len(moves)} moves")
        return jsonify(moves)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/coach-review', methods=['POST'])
def coach_review():
    """Get AI coach review for a chess position"""
    try:
        data = request.get_json()
        fen = data.get('fen')
        turn = data.get('turn')
        best_moves = data.get('bestMoves', []) 
        
        if not fen:
            return jsonify({"error": "FEN position required"}), 400
            
        print(f"Getting coach review for FEN: {fen}, Turn: {turn}")
        
        # Get coach review using the separate module
        review = chess_coach.get_coach_review(fen, turn, best_moves)
        
        return jsonify({
            "status": "success",
            "review": review
        })
        
    except Exception as e:
        print(f"Coach review error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/', methods=['GET'])
def index():
    """Root endpoint to confirm server is running."""
    return jsonify({
        "message": "Python Chess Engine Server is running.",
        "server_info": {
            "name": "Chess Analysis & Database Server",
            "version": "2.0",
            "features": ["Chess Engine Analysis", "AI Coach Review", "Game Database", "Move Bookmarks"]
        },
        "endpoints": {
            "server_endpoints": {
                "/": "GET - Server information and available endpoints",
                "/health": "GET - Check server health status",
                "/engine-info": "GET - Get chess engine information"
            },
            "chess_analysis": {
                "/analyze": "POST - Analyze chess position with engine",
                "/coach-review": "POST - Get AI coach review for position"
            },
            "database_operations": {
                "/api/save-game": "POST - Save complete game to database",
                "/api/save-move": "POST - Save bookmarked move with analysis",
                "/api/games": "GET - Retrieve saved games (paginated)",
                "/api/moves": "GET - Retrieve bookmarked moves (paginated)",
                "/api/search-moves": "GET - Search moves by tags",
                "/api/game/<id>": "GET/DELETE - Get/delete specific game by ID",
                
                "/api/move/<id>": "DELETE - Delete specific bookmarked move"
            }
        },
        "usage_examples": {
            "analyze_position": "POST /analyze with {fen: 'position', depth: 8}",
            "get_coach_review": "POST /coach-review with {fen: 'position', turn: 'White', bestMoves: [...]}",
            "save_game": "POST /api/save-game with {pgn: 'game', final_fen: 'position', game_name: 'name'}",
            "bookmark_move": "POST /api/save-move with {fen: 'position', move_notation: 'Nf3', analysis_data: {...}}",
            "search_moves": "GET /api/search-moves?query=opening"
        }
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "ok", "engine": "python_chess", "database": "postgresql", "ai_coach": "huggingface"})

@app.route('/analyze', methods=['POST'])
def analyze_position():
    """Main analysis endpoint"""
    try:
        # Check if request has JSON content type
        if not request.is_json:
            return jsonify({"status": "error", "error": "Invalid content type, expected application/json"}), 415

        data = request.get_json()
        
        if not data:
            return jsonify({"status": "error", "error": "No JSON data provided"}), 400
            
        fen = data.get('fen')
        depth = data.get('depth', 8)

        if not fen:
            return jsonify({"status": "error", "error": "FEN string is required"}), 400

        # Validate depth parameter
        try:
            depth = int(depth)
            if not (1 <= depth <= 15):
                depth = 8
        except (ValueError, TypeError):
            depth = 8

        # Call your chess engine
        result_json = analyze_chess_position(fen, depth)
        result = json.loads(result_json)

        return jsonify(result)

    except json.JSONDecodeError as e:
        print(f"Error decoding result from chess engine: {str(e)}")
        return jsonify({
            "status": "error",
            "error": "Internal server error: Failed to process engine output."
        }), 500
    except Exception as e:
        print(f"Error in analyze_position: {str(e)}")
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "error": "An unexpected error occurred on the server."
        }), 500

@app.route('/coach-review', methods=['GET'])
def coach_review_test():
    return jsonify({
        "status": "success",
        "message": "Coach review endpoint is working",
        "usage": "POST to this endpoint with {fen: 'position', turn: 'White/Black', bestMoves: [...]}"
    })

@app.route('/engine-info', methods=['GET'])
def engine_info():
    """Engine information endpoint"""
    return jsonify({
        "name": "FastChessEngine",
        "version": "1.0",
        "author": "Custom",
        "features": ["evaluation", "best_moves", "principal_variation", "ai_coach_review", "database_storage"],
        "max_depth": 15,
        "supported_formats": ["FEN", "PGN"],
        "database": "PostgreSQL",
        "ai_backend": "HuggingFace"
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({"status": "error", "error": "Endpoint not found"}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({"status": "error", "error": "Method not allowed"}), 405

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"status": "error", "error": "Internal server error"}), 500

if __name__ == '__main__':
    print("Starting Python Chess Engine Server...")
    print("Server will run on http://192.168.29.161:8000")
    print("Features: Chess Analysis, AI Coach Review, PostgreSQL Database")
    print("Make sure to install dependencies: pip install flask flask-cors python-chess psycopg2-binary")
    
    try:
        # Use 0.0.0.0 to make server accessible on the network
        app.run(host='0.0.0.0', port=8000, debug=False, threaded=True)
    except Exception as e:
        print(f"Failed to start server: {e}")
        sys.exit(1)
