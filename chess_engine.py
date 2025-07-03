# chess_engine.py - Full strength engine with bitwise operation fixes
import os
import requests
import json
from flask import request, jsonify,Flask
import chess
import time
import json
import hashlib
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
# Add this import at the top with other imports


@dataclass
class MoveResult:
    move: str
    eval_score: float
    pv: List[str]

class FastChessEngine:
    def __init__(self):
        # Enhanced piece values
        self.piece_values = {
            chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330,
            chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 0
        }

        # Complete piece-square tables for all pieces
        self.pst_pawn = [
            0, 0, 0, 0, 0, 0, 0, 0,
            78, 83, 86, 73, 102, 82, 85, 90,
            7, 29, 21, 44, 40, 31, 44, 7,
            -17, 16, -2, 15, 14, 0, 15, -13,
            -26, 3, 10, 9, 6, 1, 0, -23,
            -22, 9, 5, -11, -10, -2, 3, -19,
            -31, 8, -7, -37, -36, -14, 3, -31,
            0, 0, 0, 0, 0, 0, 0, 0
        ]

        self.pst_knight = [
            -167, -89, -34, -49, 61, -97, -15, -107,
            -73, -41, 72, 36, 23, 62, 7, -17,
            -47, 60, 37, 65, 84, 129, 73, 44,
            -9, 17, 19, 53, 37, 69, 18, 22,
            -13, 4, 16, 13, 28, 19, 21, -8,
            -23, -9, 12, 10, 19, 17, 25, -16,
            -29, -53, -12, -3, -1, 18, -14, -19,
            -105, -21, -58, -33, -17, -28, -19, -23
        ]

        self.pst_bishop = [
            -20,-10,-10,-10,-10,-10,-10,-20,
            -10, 0, 0, 0, 0, 0, 0,-10,
            -10, 0, 5, 10, 10, 5, 0,-10,
            -10, 5, 5, 10, 10, 5, 5,-10,
            -10, 0, 10, 10, 10, 10, 0,-10,
            -10, 10, 10, 10, 10, 10, 10,-10,
            -10, 5, 0, 0, 0, 0, 5,-10,
            -20,-10,-10,-10,-10,-10,-10,-20
        ]

        self.pst_rook = [
            0, 0, 0, 0, 0, 0, 0, 0,
            5, 10, 10, 10, 10, 10, 10, 5,
            -5, 0, 0, 0, 0, 0, 0, -5,
            -5, 0, 0, 0, 0, 0, 0, -5,
            -5, 0, 0, 0, 0, 0, 0, -5,
            -5, 0, 0, 0, 0, 0, 0, -5,
            -5, 0, 0, 0, 0, 0, 0, -5,
            0, 0, 0, 5, 5, 0, 0, 0
        ]

        self.pst_queen = [
            -20,-10,-10, -5, -5,-10,-10,-20,
            -10, 0, 0, 0, 0, 0, 0,-10,
            -10, 0, 5, 5, 5, 5, 0,-10,
            -5, 0, 5, 5, 5, 5, 0, -5,
            0, 0, 5, 5, 5, 5, 0, -5,
            -10, 5, 5, 5, 5, 5, 0,-10,
            -10, 0, 5, 0, 0, 0, 0,-10,
            -20,-10,-10, -5, -5,-10,-10,-20
        ]

        self.pst_king_middlegame = [
            -30,-40,-40,-50,-50,-40,-40,-30,
            -30,-40,-40,-50,-50,-40,-40,-30,
            -30,-40,-40,-50,-50,-40,-40,-30,
            -30,-40,-40,-50,-50,-40,-40,-30,
            -20,-30,-30,-40,-40,-30,-30,-20,
            -10,-20,-20,-20,-20,-20,-20,-10,
            20, 20, 0, 0, 0, 0, 20, 20,
            20, 30, 10, 0, 0, 10, 30, 20
        ]

        self.pst_king_endgame = [
            -50,-40,-30,-20,-20,-30,-40,-50,
            -30,-20,-10, 0, 0,-10,-20,-30,
            -30,-10, 20, 30, 30, 20,-10,-30,
            -30,-10, 30, 40, 40, 30,-10,-30,
            -30,-10, 30, 40, 40, 30,-10,-30,
            -30,-10, 20, 30, 30, 20,-10,-30,
            -30,-30, 0, 0, 0, 0,-30,-30,
            -50,-30,-30,-30,-30,-30,-30,-50
        ]

        # Search optimization tables
        self.transposition_table = {}
        self.killer_moves = [[] for _ in range(64)]
        self.history_table = {}

        # Search statistics
        self.nodes_searched = 0
        self.tt_hits = 0
        self.beta_cutoffs = 0

        # Enhanced opening book
        self.opening_book = {
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1": "e2e4",
            "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1": "e7e5",
            "rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq - 0 1": "d7d5",
            "rnbqkbnr/ppp1pppp/8/3p4/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2": "e4d5",
            "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2": "g1f3",
            "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3": "f1b5",
            "rnbqkb1r/pppp1ppp/5n2/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 4 3": "d2d3"
        }

    def analyze_position(self, fen: str, depth: int = 6) -> Dict:
        
        try:
            board = chess.Board(fen)
            start_time = time.time()

            # Reset search statistics
            self.nodes_searched = 0
            self.tt_hits = 0
            self.beta_cutoffs = 0
            self.transposition_table.clear()
            self.killer_moves = [[] for _ in range(64)]

            # Check opening book first
            if fen in self.opening_book:
                book_move = self.opening_book[fen]
                return {
                    "status": "success",
                    "evaluation": 0.15,
                    "depth": 0,
                    "best_moves": [{
                        "move": book_move,
                        "eval_score": 0.15,
                        "principal_variation": [book_move],
                        "type": "book"
                    }],
                    "search_info": {
                        "time_ms": int((time.time() - start_time) * 1000),
                        "nodes": 0,
                        "nps": 0,
                        "source": "opening_book"
                    }
                }

            # Iterative deepening search with time management
            best_moves = []
            final_eval = 0
            max_depth = min(depth, 12)  # Cap depth for performance

            for current_depth in range(1, max_depth + 1):
                try:
                    eval_score, moves = self._search_root(board, current_depth)
                    best_moves = moves
                    final_eval = eval_score

                    # Early termination for forced mate
                    if abs(eval_score) > 5000:
                        break

                    # Time limit check (max 5 seconds per position)
                    if time.time() - start_time > 5.0:
                        break

                except Exception as e:
                    if current_depth == 1:
                        raise e
                    break

            search_time = time.time() - start_time

            # Ensure we have at least 3 moves or pad with available moves
            while len(best_moves) < 3 and len(best_moves) < len(list(board.legal_moves)):
                remaining_moves = [str(move) for move in board.legal_moves
                                 if str(move) not in [m.move for m in best_moves]]
                if remaining_moves:
                    best_moves.append(MoveResult(
                        move=remaining_moves[0],
                        eval_score=final_eval - 50,  # Slightly lower score
                        pv=[remaining_moves[0]]
                    ))
                else:
                    break

            return {
                "status": "success",
                "evaluation": {
                    "value": round(final_eval / 100, 2),
                    "type": "cp",
                    "display": f"+{round(final_eval / 100, 2)}" if final_eval >= 0 else f"{round(final_eval / 100, 2)}"
                },
                "depth": current_depth,
                "bestMoves": [  # Changed from "best_moves"
                    {
                        "move": move.move,
                        "san": self._move_to_san(board, move.move), 
                        "eval_score": round(move.eval_score / 100, 2),
                        "evaluationRaw": round(move.eval_score / 100, 2),
                        "evaluation": f"+{round(move.eval_score / 100, 2)}" if move.eval_score >= 0 else f"{round(move.eval_score / 100, 2)}",
                        "principal_variation": move.pv,
                        "principalVariation": move.pv,  # Frontend expects this name
                        "depth": current_depth,
                        "nodes": self.nodes_searched,
                        "type": "search"
                    }
                    for move in best_moves[:3]
                ],
                "searchInfo": {  # Changed from "search_info"
                    "totalTime": int(search_time * 1000),     # Changed from "time_ms"
                    "totalNodes": self.nodes_searched,        # Changed from "nodes"
                    "nodesPerSecond": int(self.nodes_searched / (search_time + 0.001)),  # Changed from "nps"
                    "depth": current_depth,
                    "ttHits": self.tt_hits,
                    "betaCutoffs": self.beta_cutoffs,
                    "source": "engine_search"
                }
            }


        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "evaluation": 0,
                "best_moves": []
            }

    def _search_root(self, board: chess.Board, depth: int) -> Tuple[float, List[MoveResult]]:
        """Root search with comprehensive move analysis"""
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            if board.is_checkmate():
                return -9999 if board.turn else 9999, []
            return 0, []

        # Advanced move ordering
        ordered_moves = self._order_moves_advanced(board, legal_moves)
        move_results = []
        alpha = -10000
        beta = 10000

        for move in ordered_moves:
            board.push(move)

            # Search this move
            eval_score = -self._negamax(board, depth - 1, -beta, -alpha, 1)

            # Get principal variation
            pv = self._extract_pv_enhanced(board, move, depth - 1)

            move_results.append(MoveResult(
                move=str(move),
                eval_score=eval_score,
                pv=pv
            ))

            board.pop()
            alpha = max(alpha, eval_score)

        # Sort results by evaluation score
        move_results.sort(key=lambda x: x.eval_score, reverse=board.turn)

        best_eval = move_results[0].eval_score if move_results else 0
        return best_eval, move_results
    def _move_to_san(self, board: chess.Board, uci_move: str) -> str:
        """Convert UCI move to SAN notation"""
        try:
            move = chess.Move.from_uci(uci_move)
            return board.san(move)
        except:
            return uci_move  # Fallback to UCI if conversion fails

    def _negamax(self, board: chess.Board, depth: int, alpha: float, beta: float, ply: int) -> float:
        """Enhanced negamax with all optimizations"""
        self.nodes_searched += 1

        # Terminal conditions
        if board.is_game_over():
            if board.is_checkmate():
                return -9999 + ply
            return 0

        # Depth limit with enhanced quiescence
        if depth <= 0:
            return self._quiescence_search_enhanced(board, alpha, beta, 4)

        # Transposition table lookup
        pos_hash = self._position_hash(board)
        if pos_hash in self.transposition_table:
            tt_entry = self.transposition_table[pos_hash]
            if tt_entry['depth'] >= depth:
                self.tt_hits += 1
                return tt_entry['score']

        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return 0

        # Enhanced move ordering
        ordered_moves = self._order_moves_advanced(board, legal_moves)

        best_score = -10000
        best_move = None
        moves_searched = 0

        for move in ordered_moves:
            board.push(move)

            # Late move reduction with conditions
            reduction = 0
            if (moves_searched > 3 and depth > 2 and
                not board.is_capture(move) and not board.is_check() and
                not move.promotion):
                reduction = 1

            # Principal variation search
            if moves_searched == 0:
                # Search first move with full window
                score = -self._negamax(board, depth - 1, -beta, -alpha, ply + 1)
            else:
                # Search with null window first
                score = -self._negamax(board, depth - 1 - reduction, -alpha - 1, -alpha, ply + 1)
                # Re-search if it beats alpha
                if score > alpha and score < beta:
                    score = -self._negamax(board, depth - 1, -beta, -alpha, ply + 1)

            board.pop()
            moves_searched += 1

            if score > best_score:
                best_score = score
                best_move = move

            alpha = max(alpha, score)

            # Alpha-beta cutoff
            if alpha >= beta:
                self.beta_cutoffs += 1
                # Store killer move
                if len(self.killer_moves[ply]) < 2:
                    if move not in self.killer_moves[ply]:
                        self.killer_moves[ply].append(move)

                # Update history table
                move_key = (move.from_square, move.to_square)
                self.history_table[move_key] = self.history_table.get(move_key, 0) + depth * depth
                break

        # Store in transposition table
        if len(self.transposition_table) < 200000:
            self.transposition_table[pos_hash] = {
                'score': best_score,
                'depth': depth,
                'best_move': best_move
            }

        return best_score

    def _quiescence_search_enhanced(self, board: chess.Board, alpha: float, beta: float, depth: int) -> float:
        """Enhanced quiescence search with better move selection"""
        stand_pat = self._evaluate_position_enhanced(board)

        if stand_pat >= beta:
            return beta

        if stand_pat > alpha:
            alpha = stand_pat

        if depth <= 0:
            return stand_pat

        # Get tactical moves (captures, checks, promotions)
        tactical_moves = []
        for move in board.legal_moves:
            if (board.is_capture(move) or board.gives_check(move) or
                move.promotion):
                tactical_moves.append(move)

        # Order tactical moves by value
        tactical_moves.sort(key=lambda m: self._tactical_move_value(board, m), reverse=True)

        for move in tactical_moves:
            # Skip bad captures
            if board.is_capture(move) and self._see_capture_enhanced(board, move) < -50:
                continue

            board.push(move)
            score = -self._quiescence_search_enhanced(board, -beta, -alpha, depth - 1)
            board.pop()

            if score >= beta:
                return beta

            if score > alpha:
                alpha = score

        return alpha

    def _evaluate_position_enhanced(self, board: chess.Board) -> float:
        """Comprehensive position evaluation with game phase detection"""
        if board.is_checkmate():
            return -9999 if board.turn else 9999

        if board.is_stalemate() or board.is_insufficient_material():
            return 0

        score = 0
        total_material = 0

        # Calculate total material for game phase detection
        piece_count = 0
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece and piece.piece_type != chess.KING:
                total_material += self.piece_values[piece.piece_type]
                piece_count += 1

        # Game phase detection
        is_endgame = total_material < 1800 or piece_count < 12

        # Material and positional evaluation
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                piece_value = self.piece_values[piece.piece_type]
                pst_bonus = self._get_pst_bonus(piece, square, is_endgame)
                total_value = piece_value + pst_bonus

                if piece.color:
                    score += total_value
                else:
                    score -= total_value

        # Enhanced mobility evaluation
        score += self._evaluate_mobility_enhanced(board)

        # Pawn structure evaluation
        score += self._evaluate_pawn_structure_enhanced(board)

        # King safety evaluation
        score += self._evaluate_king_safety_enhanced(board, is_endgame)

        # Bishop pair bonus
        score += self._evaluate_bishop_pair(board)

        # Rook on open files
        score += self._evaluate_rook_placement(board)

        return score if board.turn else -score

    def _get_pst_bonus(self, piece, square, is_endgame):
        """Get piece-square table bonus with game phase consideration"""
        if piece.piece_type == chess.PAWN:
            return self.pst_pawn[square if piece.color else 63 - square]
        elif piece.piece_type == chess.KNIGHT:
            return self.pst_knight[square if piece.color else 63 - square]
        elif piece.piece_type == chess.BISHOP:
            return self.pst_bishop[square if piece.color else 63 - square]
        elif piece.piece_type == chess.ROOK:
            return self.pst_rook[square if piece.color else 63 - square]
        elif piece.piece_type == chess.QUEEN:
            return self.pst_queen[square if piece.color else 63 - square]
        elif piece.piece_type == chess.KING:
            if is_endgame:
                return self.pst_king_endgame[square if piece.color else 63 - square]
            else:
                return self.pst_king_middlegame[square if piece.color else 63 - square]
        return 0

    def _evaluate_mobility_enhanced(self, board: chess.Board) -> float:
        """Enhanced mobility evaluation with piece-specific weights"""
        current_mobility = 0

        # Weight different piece types differently
        for move in board.legal_moves:
            piece = board.piece_at(move.from_square)
            if piece:
                if piece.piece_type == chess.QUEEN:
                    current_mobility += 4
                elif piece.piece_type == chess.ROOK:
                    current_mobility += 2
                elif piece.piece_type in [chess.BISHOP, chess.KNIGHT]:
                    current_mobility += 1
                else:
                    current_mobility += 0.5

        # Opponent mobility
        board.turn = not board.turn
        opponent_mobility = 0
        for move in board.legal_moves:
            piece = board.piece_at(move.from_square)
            if piece:
                if piece.piece_type == chess.QUEEN:
                    opponent_mobility += 4
                elif piece.piece_type == chess.ROOK:
                    opponent_mobility += 2
                elif piece.piece_type in [chess.BISHOP, chess.KNIGHT]:
                    opponent_mobility += 1
                else:
                    opponent_mobility += 0.5

        board.turn = not board.turn

        mobility_diff = current_mobility - opponent_mobility
        return mobility_diff * 2

    def _evaluate_pawn_structure_enhanced(self, board: chess.Board) -> float:
        """FIXED: Comprehensive pawn structure evaluation"""
        score = 0

        # Get piece sets as bitboards
        white_pawns = board.pieces(chess.PAWN, chess.WHITE)
        black_pawns = board.pieces(chess.PAWN, chess.BLACK)

        # Convert bitboards to lists of squares for safe iteration
        white_pawn_squares = list(white_pawns)
        black_pawn_squares = list(black_pawns)

        # Doubled pawns
        for file in range(8):
            file_mask = chess.BB_FILES[file]

            # Count pawns on each file using proper bitboard operations
            white_file_pawns = bin(white_pawns & file_mask).count('1')
            black_file_pawns = bin(black_pawns & file_mask).count('1')

            if white_file_pawns > 1:
                score -= (white_file_pawns - 1) * 30
            if black_file_pawns > 1:
                score += (black_file_pawns - 1) * 30

        # Isolated pawns - check each pawn individually
        for square in white_pawn_squares:
            file = chess.square_file(square)
            has_support = False

            # Check adjacent files for supporting pawns
            if file > 0:
                if white_pawns & chess.BB_FILES[file - 1]:
                    has_support = True
            if file < 7:
                if white_pawns & chess.BB_FILES[file + 1]:
                    has_support = True

            if not has_support:
                score -= 25

        for square in black_pawn_squares:
            file = chess.square_file(square)
            has_support = False

            # Check adjacent files for supporting pawns
            if file > 0:
                if black_pawns & chess.BB_FILES[file - 1]:
                    has_support = True
            if file < 7:
                if black_pawns & chess.BB_FILES[file + 1]:
                    has_support = True

            if not has_support:
                score += 25

        # Passed pawns - simplified but correct implementation
        for square in white_pawn_squares:
            rank = chess.square_rank(square)
            file = chess.square_file(square)

            # Check if pawn is passed (no enemy pawns blocking)
            is_passed = True
            for enemy_square in black_pawn_squares:
                enemy_file = chess.square_file(enemy_square)
                enemy_rank = chess.square_rank(enemy_square)

                # Check if enemy pawn can block or capture
                if abs(enemy_file - file) <= 1 and enemy_rank > rank:
                    is_passed = False
                    break

            if is_passed:
                score += 20 + (rank - 1) * 10  # More valuable as it advances

        # Similar for black passed pawns
        for square in black_pawn_squares:
            rank = chess.square_rank(square)
            file = chess.square_file(square)

            is_passed = True
            for enemy_square in white_pawn_squares:
                enemy_file = chess.square_file(enemy_square)
                enemy_rank = chess.square_rank(enemy_square)

                if abs(enemy_file - file) <= 1 and enemy_rank < rank:
                    is_passed = False
                    break

            if is_passed:
                score -= 20 + (6 - rank) * 10

        return score

    def _evaluate_king_safety_enhanced(self, board: chess.Board, is_endgame: bool) -> float:
        """Enhanced king safety evaluation"""
        if is_endgame:
            return 0  # King safety less important in endgame

        score = 0

        for color in [chess.WHITE, chess.BLACK]:
            king_square = board.king(color)
            if king_square is not None:
                # Pawn shield evaluation
                shield_score = self._evaluate_pawn_shield(board, king_square, color)

                # King exposure penalty
                attackers = len(board.attackers(not color, king_square))
                exposure_penalty = attackers * 15

                # King zone attacks
                king_zone_attacks = self._count_king_zone_attacks(board, king_square, not color)

                total_safety = shield_score - exposure_penalty - king_zone_attacks * 5

                if color:
                    score += total_safety
                else:
                    score -= total_safety

        return score

    def _evaluate_pawn_shield(self, board: chess.Board, king_square: int, color: bool) -> int:
        """Evaluate pawn shield in front of king"""
        shield_score = 0
        king_file = chess.square_file(king_square)
        king_rank = chess.square_rank(king_square)

        # Check pawns in front of king
        for file_offset in [-1, 0, 1]:
            file = king_file + file_offset
            if 0 <= file <= 7:
                for rank_offset in [1, 2]:
                    if color:  # White king
                        rank = king_rank + rank_offset
                    else:  # Black king
                        rank = king_rank - rank_offset

                    if 0 <= rank <= 7:
                        square = chess.square(file, rank)
                        piece = board.piece_at(square)
                        if piece and piece.piece_type == chess.PAWN and piece.color == color:
                            shield_score += 10 if rank_offset == 1 else 5

        return shield_score

    def _count_king_zone_attacks(self, board: chess.Board, king_square: int, attacking_color: bool) -> int:
        """Count attacks in king zone"""
        attacks = 0
        king_zone = [king_square + delta for delta in [-9, -8, -7, -1, 1, 7, 8, 9]]

        for square in king_zone:
            if 0 <= square <= 63:
                attacks += len(board.attackers(attacking_color, square))

        return attacks

    def _evaluate_bishop_pair(self, board: chess.Board) -> float:
        """Evaluate bishop pair bonus"""
        score = 0

        white_bishops = len(board.pieces(chess.BISHOP, chess.WHITE))
        black_bishops = len(board.pieces(chess.BISHOP, chess.BLACK))

        if white_bishops >= 2:
            score += 30
        if black_bishops >= 2:
            score -= 30

        return score

    def _evaluate_rook_placement(self, board: chess.Board) -> float:
        """FIXED: Evaluate rook placement on open/semi-open files"""
        score = 0

        for color in [chess.WHITE, chess.BLACK]:
            rooks = board.pieces(chess.ROOK, color)
            for rook_square in rooks:
                file = chess.square_file(rook_square)
                file_mask = chess.BB_FILES[file]

                # Check if file is open or semi-open using proper bitboard operations
                own_pawns = board.pieces(chess.PAWN, color) & file_mask
                opp_pawns = board.pieces(chess.PAWN, not color) & file_mask

                if not own_pawns and not opp_pawns:
                    # Open file
                    bonus = 25
                elif not own_pawns:
                    # Semi-open file
                    bonus = 15
                else:
                    bonus = 0

                if color:
                    score += bonus
                else:
                    score -= bonus

        return score

    def _order_moves_advanced(self, board: chess.Board, moves: List[chess.Move]) -> List[chess.Move]:
        """Advanced move ordering with multiple heuristics"""
        def move_score(move):
            score = 0

            # Hash move gets highest priority
            pos_hash = self._position_hash(board)
            if pos_hash in self.transposition_table:
                tt_move = self.transposition_table[pos_hash].get('best_move')
                if tt_move == move:
                    return 10000

            # Captures with enhanced SEE
            if board.is_capture(move):
                see_score = self._see_capture_enhanced(board, move)
                if see_score >= 0:
                    captured_piece = board.piece_at(move.to_square)
                    attacking_piece = board.piece_at(move.from_square)
                    if captured_piece and attacking_piece:
                        mvv_lva = (self.piece_values[captured_piece.piece_type] * 10 -
                                 self.piece_values[attacking_piece.piece_type])
                        score += 8000 + mvv_lva + see_score
                else:
                    score += 2000 + see_score  # Bad captures still considered

            # Promotions
            if move.promotion:
                score += 7000 + self.piece_values.get(move.promotion, 0)

            # Checks
            board.push(move)
            if board.is_check():
                score += 5000
            board.pop()

            # Killer moves
            for ply_killers in self.killer_moves:
                if move in ply_killers:
                    score += 4000 - ply_killers.index(move) * 100
                    break

            # Castling
            if board.is_castling(move):
                score += 1000

            # History heuristic
            move_key = (move.from_square, move.to_square)
            score += self.history_table.get(move_key, 0) // 10

            # Piece development (early game)
            piece = board.piece_at(move.from_square)
            if piece and piece.piece_type in [chess.KNIGHT, chess.BISHOP]:
                if move.from_square in [chess.B1, chess.G1, chess.B8, chess.G8]:  # Starting squares
                    score += 50

            return score

        return sorted(moves, key=move_score, reverse=True)

    def _tactical_move_value(self, board: chess.Board, move: chess.Move) -> int:
        """Enhanced tactical move evaluation"""
        value = 0

        if board.is_capture(move):
            captured = board.piece_at(move.to_square)
            value += self.piece_values[captured.piece_type] if captured else 0

        if move.promotion:
            value += self.piece_values.get(move.promotion, 0)

        board.push(move)
        if board.is_check():
            value += 100
        if board.is_checkmate():
            value += 10000
        board.pop()

        return value

    def _see_capture_enhanced(self, board: chess.Board, move: chess.Move) -> int:
        """Enhanced Static Exchange Evaluation"""
        if not board.is_capture(move):
            return 0

        captured = board.piece_at(move.to_square)
        attacker = board.piece_at(move.from_square)

        if not captured or not attacker:
            return 0

        # Simple SEE: material gained - material potentially lost
        gain = self.piece_values[captured.piece_type]

        # Check if the capturing piece is defended
        board.push(move)
        defenders = board.attackers(not attacker.color, move.to_square)
        if defenders:
            # Find least valuable defender
            min_defender_value = min(
                self.piece_values[board.piece_at(sq).piece_type]
                for sq in defenders if board.piece_at(sq)
            )

            gain -= self.piece_values[attacker.piece_type]
            gain += min_defender_value  # Assume we can recapture

        board.pop()
        return gain

    def _extract_pv_enhanced(self, board: chess.Board, first_move: chess.Move, depth: int) -> List[str]:
        """Enhanced principal variation extraction"""
        pv = [str(first_move)]
        current_board = board.copy()

        for _ in range(min(depth, 6)):  # Slightly longer PV
            pos_hash = self._position_hash(current_board)
            if pos_hash in self.transposition_table:
                tt_entry = self.transposition_table[pos_hash]
                best_move = tt_entry.get('best_move')
                if best_move and best_move in current_board.legal_moves:
                    pv.append(str(best_move))
                    current_board.push(best_move)
                else:
                    break
            else:
                # If no TT entry, try to find a reasonable move
                legal_moves = list(current_board.legal_moves)
                if legal_moves:
                    # Pick the first capture or check, otherwise first move
                    next_move = None
                    for move in legal_moves:
                        if current_board.is_capture(move) or current_board.gives_check(move):
                            next_move = move
                            break
                    if not next_move:
                        next_move = legal_moves[0]

                    pv.append(str(next_move))
                    current_board.push(next_move)
                else:
                    break

        return pv

    def _position_hash(self, board: chess.Board) -> str:
        """Optimized position hashing"""
        return hashlib.md5(board.fen()[:60].encode()).hexdigest()[:16]


# Main API function
def analyze_chess_position(fen: str, depth: int = 6) -> str:
    """
    Complete chess position analysis with enhanced evaluation

    Args:
        fen: FEN string of position
        depth: Search depth (1-12, optimized for performance)

    Returns:
        JSON string with evaluation and top 3 best moves
    """
    engine = FastChessEngine()
    result = engine.analyze_position(fen, depth)
    return json.dumps(result, indent=2)


# Performance test
if __name__ == "__main__":
    test_positions = [
        ("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", 8),
        ("r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 0 4", 10),
        ("rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8", 12),
        ("8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1", 10),  # Endgame position
    ]

    print("Enhanced Chess Engine Performance Test")
    print("=" * 55)

    total_time = 0
    total_nodes = 0

    for i, (fen, depth) in enumerate(test_positions, 1):
        print(f"\nPosition {i} (Depth {depth}):")
        print(f"FEN: {fen}")

        start = time.time()
        result_json = analyze_chess_position(fen, depth)
        end = time.time()

        result = json.loads(result_json)

        if result['status'] == 'success':
            search_info = result['search_info']
            time_ms = search_info['time_ms']
            nodes = search_info['nodes']
            nps = search_info['nps']

            print(f"Time: {time_ms}ms")
            print(f"Nodes: {nodes:,}")
            print(f"NPS: {nps:,}")
            print(f"Evaluation: {result['evaluation']}")
            print(f"TT Hits: {search_info.get('tt_hits', 0)}")
            print(f"Beta Cutoffs: {search_info.get('beta_cutoffs', 0)}")

            print("Top 3 moves:")
            for j, move in enumerate(result['best_moves'], 1):
                pv_str = " ".join(move['principal_variation'][:4])
                print(f"  {j}. {move['move']} ({move['eval_score']}) - PV: {pv_str}")

            total_time += time_ms
            total_nodes += nodes

        else:
            print(f"Error: {result.get('error')}")

        print("-" * 40)

    print(f"\nTotal time: {total_time}ms")
    print(f"Total nodes: {total_nodes:,}")
    print(f"Average NPS: {int(total_nodes / (total_time / 1000)) if total_time > 0 else 0:,}")
