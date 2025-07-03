import os
import requests
from typing import Dict, Any, List
import time
import hashlib

HF_TOKEN = os.getenv("HF_TOKEN")

API_URL = "https://router.huggingface.co/novita/v3/openai/chat/completions"

class ChessCoach:
    def __init__(self):
        self.hf_token = HF_TOKEN
        print("HF_TOKEN:", HF_TOKEN)
        self.timeout = 35
        # Add cache for storing responses
        self.position_cache = {}
    
    def _get_cache_key(self, fen: str, turn: str) -> str:
        """Generate unique cache key for FEN+turn combination"""
        combined = f"{fen}_{turn}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    def query(self, payload):
        """
        Sends a POST request to the Hugging Face API with the given payload.
        
        Args:
            payload (dict): The JSON payload to send in the POST request.
        
        Returns:
            dict: The JSON response from the API.
        """
        headers = {
            "Authorization": f"Bearer {self.hf_token}",
            #"Content-Type": "application/json"
        }
        
        try:
            response = requests.post(
                API_URL, 
                headers=headers, 
                json=payload, 
                timeout=self.timeout
            )
            #response.raise_for_status()  # Raises an HTTPError for bad responses
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return {"error": str(e)}

    def get_coach_review(self, fen: str, turn: str, best_moves: List[Dict] = None) -> Dict[str, Any]:
        """Get comprehensive coach review using API with fallback"""
        try:
            # Check cache first
            cache_key = self._get_cache_key(fen, turn)
            if cache_key in self.position_cache:
                print(f"✅ Cache hit for position: {fen[:20]}...")
                return self.position_cache[cache_key]
            
            if not self.hf_token:
                raise Exception("HF_TOKEN not available")

            # Create the optimized coaching prompt
            prompt = self._create_moves_coaching_prompt(fen, turn, best_moves or [])
            
            # Call the API with fallback mechanism
            review_data = self._call_inference_api_with_fallback(prompt)
            
            # Parse and validate the response
            result = self._intelligent_parse_and_validate(review_data, best_moves)
            
            # Store in cache
            self.position_cache[cache_key] = result
            print(f"💾 Cached response for position: {fen[:20]}...")
            
            return result

        except Exception as e:
            print(f"Error getting coach review: {e}")
            return self._get_enhanced_fallback_review(fen, turn, best_moves)

    def _call_inference_api_with_fallback(self, prompt: str) -> str:
        """
        Call API using meta-llama model only
        
        Args:
            prompt (str): The coaching prompt to send to the AI
            
        Returns:
            str: The AI response content
        """
        
        try:
            print(f"Trying meta-llama/Llama-3.1-8B-Instruct")
            
            # Create the payload for the API request
            payload = {
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a Grandmaster chess coach providing concise, tactical analysis."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 250,
                "temperature": 0.6,
                "top_p": 0.85,
                "model": "meta-llama/llama-3.1-8b-instruct"
            }
            
            # Make the API call using the query method
            response = self.query(payload)
            
            # Check if response contains an error
            if "error" in response:
                print(f"❌ API Error: {response['error']}")
                raise Exception(f"API Error: {response['error']}")
            
            # Extract response content from the API response
            try:
                response_content = response["choices"][0]["message"]["content"]
                
                if response_content and response_content.strip():
                    print(f"✅ Success with meta-llama/Llama-3.1-8B-Instruct")
                    return response_content
                else:
                    print(f"⚠️ Empty response from meta-llama/Llama-3.1-8B-Instruct")
                    raise Exception("Empty response from API")
                    
            except (KeyError, IndexError, TypeError) as e:
                print(f"❌ Response parsing error: {e}")
                print(f"Response format: {response}")
                raise Exception(f"Response parsing error: {e}")
                
        except Exception as e:
            print(f"❌ Failed meta-llama/Llama-3.1-8B-Instruct: {e}")
            raise Exception("API call failed")

    def _create_moves_coaching_prompt(self, fen: str, turn: str, best_moves: List[Dict]) -> str:
        """
        Create an optimized prompt with engine-provided best moves
        
        Args:
            fen (str): The FEN position string
            turn (str): Whose turn it is to move
            best_moves (List[Dict]): List of best moves from chess engine
            
        Returns:
            str: Formatted coaching prompt
        """
        moves_text = ""
        if best_moves and len(best_moves) > 0:
            moves_text = "\nEngine's top moves:\n"
            for i, move in enumerate(best_moves[:3]):
                move_notation = move.get('move', f'Move{i+1}')
                evaluation = move.get('evaluation', 'eval')
                moves_text += f"{i+1}. {move_notation} (eval: {evaluation})\n"
        else:
            moves_text = "\nNo engine moves provided - suggest your own best moves.\n"

        return f"""You are a master chess coach. Analyze this position with the engine's best moves.

Position: {fen}
Turn: {turn}{moves_text}

EXPLAIN WHY each of the top 3 moves works. Be concise and information-dense.

EXACT FORMAT REQUIRED:
Position Assessment: [Brief evaluation in 1-2 sentences]
Best Move 1: {best_moves[0].get('move', '[suggest move]') if best_moves else '[suggest move]'} - [explain WHY this move works tactically/strategically in 15-20 words]
Best Move 2: {best_moves[1].get('move', '[suggest move]') if len(best_moves) > 1 else '[suggest move]'} - [explain WHY this move works tactically/strategically in 15-20 words]
Best Move 3: {best_moves[2].get('move', '[suggest move]') if len(best_moves) > 2 else '[suggest move]'} - [explain WHY this move works tactically/strategically in 15-20 words]
Tactical Tags: [exactly 6 comma-separated tactical concepts like: pin, fork, discovery, sacrifice, initiative, development]
Strategic Focus: [1-2 sentence strategic advice]

Focus on explaining the MOTIFS and WHY each move is strong. Be educational and concise."""

    def _intelligent_parse_and_validate(self, raw_text: str, best_moves: List[Dict] = None) -> Dict[str, Any]:
        """
        Parse the AI response into structured format
        
        Args:
            raw_text (str): Raw response from the AI
            best_moves (List[Dict]): Original best moves for fallback
            
        Returns:
            Dict[str, Any]: Structured coaching analysis
        """
        import re
        
        try:
            # Extract position assessment using regex
            position_match = re.search(r'Position Assessment:\s*(.+?)(?=Best Move|$)', raw_text, re.IGNORECASE | re.DOTALL)
            position_assessment = position_match.group(1).strip() if position_match else "Position requires analysis."

            # Extract best moves with explanations using regex patterns
            move_patterns = [
                r'Best Move 1:\s*(.+?)(?=Best Move 2|Tactical Tags|$)',
                r'Best Move 2:\s*(.+?)(?=Best Move 3|Tactical Tags|$)',
                r'Best Move 3:\s*(.+?)(?=Tactical Tags|Strategic Focus|$)'
            ]

            best_moves_explanations = []
            for i, pattern in enumerate(move_patterns):
                match = re.search(pattern, raw_text, re.IGNORECASE | re.DOTALL)
                if match:
                    move_text = match.group(1).strip()
                    best_moves_explanations.append(move_text)
                else:
                    # Fallback to engine moves if available
                    if best_moves and i < len(best_moves):
                        move_notation = best_moves[i].get('move', f'Move {i+1}')
                        best_moves_explanations.append(f"{move_notation} - Strong candidate requiring analysis")
                    else:
                        best_moves_explanations.append(f"Move {i+1}: Analysis needed")

            # Extract tactical tags
            tags_match = re.search(r'Tactical Tags:\s*(.+?)(?=Strategic Focus|$)', raw_text, re.IGNORECASE)
            if tags_match:
                tags_text = tags_match.group(1).strip()
                tags = [tag.strip() for tag in tags_text.split(',')][:6]
            else:
                tags = ["tactics", "strategy", "development", "initiative", "calculation", "position"]

            # Extract strategic focus
            strategy_match = re.search(r'Strategic Focus:\s*(.+?)$', raw_text, re.IGNORECASE | re.DOTALL)
            strategic_advice = strategy_match.group(1).strip() if strategy_match else "Focus on piece coordination and pawn structure."

            # Return structured analysis
            return {
                "position_assessment": position_assessment,
                "best_move_1": best_moves_explanations[0],
                "best_move_2": best_moves_explanations[1],
                "best_move_3": best_moves_explanations[2],
                "tactical_opportunities": f"Key tactics: {', '.join(tags[:3])}",
                "strategic_advice": strategic_advice,
                "next_move_suggestions": f"Priority: {best_moves_explanations[0]}",
                "tags": tags,
                "timestamp": int(time.time()),
                "source": "ai_analysis_with_engine",
                "engine_moves_used": len(best_moves) if best_moves else 0
            }

        except Exception as e:
            print(f"Parsing error: {e}")
            return self._get_enhanced_fallback_review("", "", best_moves)

    def _get_enhanced_fallback_review(self, fen: str, turn: str, best_moves: List[Dict] = None) -> Dict[str, Any]:
        """
        Enhanced fallback with position-specific advice when API calls fail
        
        Args:
            fen (str): The FEN position string
            turn (str): Whose turn it is to move
            best_moves (List[Dict]): List of best moves from chess engine
            
        Returns:
            Dict[str, Any]: Fallback coaching analysis
        """
        return {
            "position_assessment": "Analysis unavailable - using fallback review",
            "best_move_1": "Move 1: Requires detailed analysis",
            "best_move_2": "Move 2: Consider alternatives",
            "best_move_3": "Move 3: Explore options",
            "tactical_opportunities": "Review position for tactical motifs",
            "strategic_advice": "Apply fundamental chess principles",
            "next_move_suggestions": "Priority: Analyze current position",
            "tags": ["analysis", "position", "tactics", "strategy", "development", "planning"],
            "timestamp": int(time.time()),
            "source": "enhanced_fallback"
        }

# Create global instance
chess_coach = ChessCoach()
