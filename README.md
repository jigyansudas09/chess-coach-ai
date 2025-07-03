# ♟️ Advanced Chess Analysis Platform

A comprehensive chess analysis application featuring AI-powered position evaluation, game database management, and intelligent move bookmarking with search capabilities.

## 📚 Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Database Schema](#database-schema)
- [Technologies Used](#technologies-used)
- [Major Development Challenges](#major-development-challenges)
- [Troubleshooting](#troubleshooting)
- [License](#license)
- [Project Structure](#project-structure)

## Features

### ♟️ Core Chess Features
- Interactive chess board with drag-and-drop piece movement
- Dual game modes: Play mode for active games, Analyze mode for position analysis
- Move validation powered by chess.js
- Complete game history with move navigation

###  AI-Powered Analysis
- python-chess engine integration
- HuggingFace NLP-powered AI coach
- Best move recommendations with eval scores
- Tactical motif recognition and strategic insight generation

### 🗂️ Database Management
- Full PGN game storage/retrieval
- Position bookmarking with embedded AI insights
- Advanced move search by tags, assessments, and notations
- Tag-based classification of positions

### Search Capabilities
- Fuzzy and partial text matching
- Multi-field filtering (notation, assessment, tags)
- Efficient pagination for large datasets
- PostgreSQL pg_trgm indexing for fast queries

## ⚙️ Installation

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- Git

### Backend Setup

```bash
git clone <repository-url>
cd chess-analysis-platform
pip install flask flask-cors python-chess psycopg2-binary requests
```

### PostgreSQL Setup

```bash
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo -u postgres psql
```

```sql
CREATE USER chess_user WITH PASSWORD 'your_secure_password';
CREATE DATABASE chess_coach OWNER chess_user;
GRANT ALL PRIVILEGES ON DATABASE chess_coach TO chess_user;
```

### Initialize Schema

```bash
psql -U chess_user -d chess_coach -f database/init.sql
```

##  Application Startup

### Configure Database (`chess_db.py`)

```python
self.connection = psycopg2.connect(
    host="localhost",
    database="chess_coach",
    user="chess_user",
    password="your_password"
)
```

### Run Flask Server

```bash
python python-server.py
```

Access at: http://192.168.29.161:8000

## 🔧 Configuration

### HuggingFace Key (`coach_review.py`)

```python
HUGGINGFACE_API_KEY = "your_api_key"
```

### Engine Parameters (`chess_engine.py`)

```python
DEFAULT_DEPTH = 8
DEFAULT_TIMEOUT = 30
CACHE_ENABLED = True
```

## Usage

### Operations

- **New Game** → Start fresh position
- **Play/Analyze** → Switch modes
- **Drag-and-drop** → Make moves
- **Save Games** → Store PGNs with labels

### Analysis

- AI eval and coach insights
- Bookmark analyzed positions
- Visual evaluation bar
- Tag positions by tactics/strategy

### Database

- Save/load/search games
- Bookmark and filter moves
- Tag-based fuzzy search

## API Documentation

### Game Endpoints

**POST /api/save-game**

```json
{
  "pgn": "1. e4 e5 2. Nf3 Nc6...",
  "final_fen": "rnbqkbnr/...",
  "game_name": "Game Name"
}
```

**GET /api/games?limit=20&offset=0**  
**GET /api/game/{game_id}**  
**DELETE /api/game/{game_id}**

### Move Endpoints

**POST /api/save-move**

```json
{
  "fen": "position_fen",
  "move_notation": "e4",
  "analysis_data": {
    "position_assessment": "analysis_text",
    "best_move_1": "recommended_move",
    "tags": ["opening", "center"]
  }
}
```

**GET /api/moves?limit=20&offset=0**  
**GET /api/search-moves?query=tactics**  
**DELETE /api/move/{move_id}**

###  Analysis Endpoints

**POST /analyze**

```json
{
  "fen": "board_position",
  "depth": 8
}
```

**POST /coach-review**

```json
{
  "fen": "position_fen",
  "turn": "White",
  "bestMoves": []
}
```

##  Database Schema

### `games` Table

```sql
CREATE TABLE games (
  id SERIAL PRIMARY KEY,
  pgn TEXT NOT NULL,
  final_fen TEXT NOT NULL,
  game_name VARCHAR(255),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### `moves` Table

```sql
CREATE TABLE moves (
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
```

### Indexes

```sql
CREATE EXTENSION pg_trgm;
CREATE INDEX idx_moves_tags ON moves USING GIN(tags);
CREATE INDEX idx_moves_notation_trgm ON moves USING GIN(move_notation gin_trgm_ops);
CREATE INDEX idx_moves_assessment_trgm ON moves USING GIN(position_assessment gin_trgm_ops);
```

##  Technologies Used

### Frontend
- HTML5 / CSS3 / JavaScript (ES6+)
- chess.js for logic
- chessboard.js for UI

### Backend
- Flask (Python)
- python-chess
- psycopg2 (PostgreSQL)
- HuggingFace API

## 🛠️ Major Development Challenges

###  chess.js Version Inconsistencies

**Problem**: `load()` returns vary by version  
**Fix**: Use exception-based validation

```js
// Instead of:
if (!game.load(fen)) throw Error();

// Use:
game.load(fen);
```

---

### Double Encoding in FEN Passing

**Problem**: HTML + JS encoding caused corrupted FEN  
**Fix**: Use `data-fen` attribute

```html
<!-- Old -->
onclick="loadPosition('${encodeURIComponent(fen)}')"

<!-- New -->
data-fen="${escapeHtml(fen)}"
```

---

###  PostgreSQL Search Bottlenecks

**Problem**: LIKE queries slow  
**Fix**: GIN + trigram indexes

```sql
CREATE EXTENSION pg_trgm;
CREATE INDEX idx_moves_trgm ON moves USING GIN(column gin_trgm_ops);
```

---

### Tab Switching Clears Board

**Problem**: Board resets before load completes  
**Fix**: Delay tab switch until after data load

## Troubleshooting

### 🧵 Database

```bash
sudo systemctl status postgresql
psql -U chess_user -d chess_coach -c "SELECT version();"
psql -U chess_user -d chess_coach -c "SELECT * FROM pg_extension WHERE extname = 'pg_trgm';"
```

### 🌐 API

```bash
curl http://192.168.29.161:8000/health
curl http://192.168.29.161:8000/api/games
curl "http://192.168.29.161:8000/api/search-moves?query=test"
```

###  Performance

```sql
EXPLAIN ANALYZE SELECT * FROM moves WHERE 'tactics' = ANY(tags);
REINDEX INDEX idx_moves_tags;
ANALYZE moves;
```

###  Frontend Debug

```js
console.log('loadPgn:', typeof game.loadPgn);
console.log('load:', typeof game.load);
```

## 📜 License

MIT License — see `LICENSE` file.

##  Project Structure

```
chess-analysis-platform/
├── index.html
├── python-server.py
├── chess_db.py
├── coach_review.py
├── chess_engine.py
├── enhanced-chess-analyzer.js
├── python-chess-bridge.js
├── updated-chess-ui-integration.js
├── database/
│   └── init.sql
└── static/
```
## Future Development 
```
|──Implement CPU-specific python engine
|──Reduce Database Query Latency
|──Vector Database System Implementation for move similarity search
|──Move Highlight and Arrows for calulation in UI
|──Stockfish Integration(optional)
|──Endgames move support DataTable integration
|──Mark blunder ,miss,great, best and excellent moves
|──Knight Move HeatMap("How does a knight move?")

```


<small> Once a Grandmaster was a beginner.</small>

