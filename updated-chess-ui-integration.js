// updated-chess-ui-integration.js - Complete UI integration with all features

class UpdatedChessUIIntegration {
    constructor() {
        this.analyzer = null;
        this.isAnalyzing = false;
        this.currentAnalysisId = null;
        this.evaluationHistory = [];
        this.autoAnalyze = false;
        this.lastPosition = null;
        this.serverUrl = 'http://192.168.29.161:8000'; // Set the Python server URL
    }

    async initialize() {
        try {
            const response = await fetch(`${this.serverUrl}/health`);
        if (!response.ok) throw new Error('Python server unreachable');
            this.analyzer = new EnhancedChessAnalyzer();
            await this.analyzer.initialize();
            this.updateEngineStatus('Python Engine Ready', true);
            this.showNotification('Enhanced chess engine ready!', 'success');
            
            // Set up event listeners
            this.setupEventListeners();
            
            console.log('🚀 Chess UI Integration initialized');
            return true;
        } catch (error) {
            console.error('UI Integration failed:', error);
            this.updateEngineStatus('Engine Failed', false);
            this.showNotification('Engine initialization failed!', 'error');
            return false;
        }
    }

    setupEventListeners() {
        // Add button event listeners
        const analyzeBtn = document.getElementById('analyzeBtn');
        const quickBtn = document.getElementById('quickAnalysisBtn');
        const tacticalBtn = document.getElementById('tacticalAnalysisBtn');
        const deepBtn = document.getElementById('deepAnalysisBtn');
        const testBtn = document.getElementById('testPythonEngineBtn');
        const flipBtn = document.getElementById('flipBtn');
        const resetBtn = document.getElementById('resetBtn');

        if (analyzeBtn) {
            analyzeBtn.addEventListener('click', () => this.analyzeCurrentPosition());
        }
        if (quickBtn) {
            quickBtn.addEventListener('click', () => this.quickAnalysis());
        }
        if (tacticalBtn) {
            tacticalBtn.addEventListener('click', () => this.tacticalAnalysis());
        }
        if (deepBtn) {
            deepBtn.addEventListener('click', () => this.deepAnalysis());
        }
        if (testBtn) {
            testBtn.addEventListener('click', () => this.testPythonEngine());
        }
        if (flipBtn) {
            flipBtn.addEventListener('click', () => this.flipBoard());
        }
        if (resetBtn) {
            resetBtn.addEventListener('click', () => this.resetPosition());
        }

        // Auto-analyze toggle
        const autoAnalyzeCheckbox = document.getElementById('autoAnalyzeToggle');
        if (autoAnalyzeCheckbox) {
            autoAnalyzeCheckbox.addEventListener('change', (e) => {
                this.autoAnalyze = e.target.checked;
                this.showNotification(`Auto-analyze ${this.autoAnalyze ? 'enabled' : 'disabled'}`, 'info');
            });
        }

        // Position monitoring for auto-analyze
        this.startPositionMonitoring();
    }

    startPositionMonitoring() {
        setInterval(() => {
            if (this.autoAnalyze && !this.isAnalyzing) {
                const currentGame = this.getCurrentGame();
                if (currentGame) {
                    const currentFen = currentGame.fen();
                    if (currentFen !== this.lastPosition) {
                        this.lastPosition = currentFen;
                        setTimeout(() => this.quickAnalysis(), 500); // Small delay
                    }
                }
            }
        }, 1000);
    }
    async testServerConnection() {
        try {
            const response = await fetch(`${this.serverUrl}/health`, { 
                method: 'GET',
                signal: AbortSignal.timeout(30000)
            });
            console.log('Server response:', await response.json());
            return true;
        } catch (error) {
            console.error('Server connection failed:', error);
            return false;
        }
    }
    

    async analyzeCurrentPosition() {
        this.autoAnalyze = false;
        
        if (!this.analyzer || !this.analyzer.isInitialized) {
            this.showNotification('Engine not ready!', 'error');
            return;
        }

        if (this.isAnalyzing) {
            this.stopAnalysis();
            return;
        }

        try {
            this.isAnalyzing = true;
            this.updateAnalyzeButton('stop');
            this.updateEngineStatus('Analyzing with Python Engine...', true);

            const currentGame = this.getCurrentGame();
            if (!currentGame) {
                throw new Error('No game available');
            }

            const fen = currentGame.fen();
            const analysis = await this.analyzer.getTopMoves(fen, {
                depth: 6,
                timeout: 60000
            });
            if (analysis.cancelled) {
                this.showNotification('Analysis was cancelled.', 'warning');
                return;
            }

            if (analysis.success) {
                this.displayAnalysisResults(analysis);
                this.updateEngineStatus('Python Analysis Complete', true);
                this.showNotification('Deep analysis complete!', 'success');
                
                // Add to evaluation history
                this.addToEvaluationHistory(fen, analysis);
            }

        } catch (error) {
            console.error('Analysis failed:', error);
            this.updateEngineStatus('Analysis Failed', false);
            this.showNotification(`Analysis failed: ${error.message}`, 'error');
        } finally {
            this.isAnalyzing = false;
            this.updateAnalyzeButton('analyze');
        }
    }

    async quickAnalysis() {
        this.autoAnalyze = false;
        
        const isConnected = await this.testServerConnection();
        if (!isConnected) {
            this.showNotification('Cannot connect to Python engine!', 'error');
            return;
        }
        
        if (!this.analyzer) return;

        try {
            this.updateEngineStatus('Quick Analysis...', true);
            const currentGame = this.getCurrentGame();
            if (!currentGame) return;

            const fen = currentGame.fen();
            const analysis = await this.analyzer.quickEvaluation(fen);
            if (analysis.cancelled) {
                this.showNotification('Analysis was cancelled.', 'warning');
                return;
            }
            
            this.displayAnalysisResults(analysis);
            this.updateEngineStatus('Quick Analysis Complete', true);
            this.showNotification('Quick analysis complete!', 'info');
        } catch (error) {
            console.error('Quick analysis failed:', error);
            this.showNotification('Quick analysis failed!', 'error');
        }
    }

    async tacticalAnalysis() {
        this.autoAnalyze = false;
        if (!this.analyzer) return;

        try {
            this.updateEngineStatus('Tactical Analysis...', true);
            const currentGame = this.getCurrentGame();
            if (!currentGame) return;

            const fen = currentGame.fen();
            const analysis = await this.analyzer.tacticalAnalysis(fen);
            if (analysis.cancelled) {
                this.showNotification('Analysis was cancelled.', 'warning');
                return;
            }
            
            this.displayAnalysisResults(analysis);
            this.updateEngineStatus('Tactical Analysis Complete', true);
            this.showNotification('Tactical analysis complete!', 'success');
        } catch (error) {
            console.error('Tactical analysis failed:', error);
            this.showNotification('Tactical analysis failed!', 'error');
        }
    }

    async deepAnalysis() {
        this.autoAnalyze = false; 
        if (!this.analyzer) return;

        try {
            this.updateEngineStatus('Deep Analysis...', true);
            const currentGame = this.getCurrentGame();
            if (!currentGame) return;

            const fen = currentGame.fen();
            const analysis = await this.analyzer.deepAnalysis(fen);
            
            this.displayAnalysisResults(analysis);
            this.updateEngineStatus('Deep Analysis Complete', true);
            this.showNotification('Deep analysis complete!', 'success');
        } catch (error) {
            console.error('Deep analysis failed:', error);
            this.showNotification('Deep analysis failed!', 'error');
        }
    }

    async testPythonEngine() {
        this.autoAnalyze = false;
        if (!this.analyzer) {
            this.showNotification('Engine not initialized!', 'error');
            return;
        }

        try {
            this.updateEngineStatus('Testing Python Engine...', true);
            
            // Test with starting position
            const startFen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";
            const analysis = await this.analyzer.getTopMoves(startFen, {
                depth: 6,
                timeout: 100000
            });
            if (analysis.cancelled) {
                this.showNotification('Analysis was cancelled.', 'warning');
                return;
            }

            if (analysis.success) {
                this.showNotification('Python engine test successful!', 'success');
                console.log('🐍 Python Engine Test Result:', analysis);
                
                // Display test results
                this.displayAnalysisResults(analysis);
            } else {
                this.showNotification('Python engine test failed!', 'error');
            }

        } catch (error) {
            console.error('Python engine test failed:', error);
            this.showNotification(`Engine test failed: ${error.message}`, 'error');
        } finally {
            this.updateEngineStatus('Engine Test Complete', true);
        }
    }

    stopAnalysis() {
        if (this.analyzer) {
            this.analyzer.cancelCurrentAnalysis();
        }
        this.isAnalyzing = false;
        this.updateAnalyzeButton('analyze');
        this.updateEngineStatus('Analysis Stopped', false);
        this.showNotification('Analysis stopped', 'info');
    }

    displayAnalysisResults(analysis) {
        console.log('🔍 Raw analysis result:', analysis);
        console.log('🔍 Raw analysis result:', analysis);
    
    // Safe extraction with defaults
        const evaluation = analysis.evaluation || { value: 0 };
        const bestMoves = analysis.bestMoves || [];
        const searchInfo = analysis.searchInfo || {
            totalTime: 0,
            totalNodes: 0,
            nodesPerSecond: 0,
            depth: 0,
            source: 'python_engine'
        };

        
        let evalValue = 0;
        if (typeof evaluation === 'object' && evaluation.value !== undefined) {
            evalValue = analysis?.evaluation?.value;
        } else if (typeof evaluation === 'number') {
            evalValue = evaluation;
        }
        // Update evaluation bar
        if (window.updateEvalBar) {
            const rawValue = evaluation?.value;
            if (typeof rawValue === 'number' && !isNaN(rawValue)) {
                window.updateEvalBar(rawValue);
            } else {
                window.updateEvalBar(0); // fallback to 0 or skip update
            }
        }
        // Update engine info display with safe checks
    if (evaluation) {
        const displayValue = evaluation.display || evalValue.toFixed(2);
        this.updateElement('engineEval', displayValue);
    }

        // Update engine info display
        if (searchInfo) {
            this.updateElement('engineDepth', searchInfo.depth?.toString() || '0');
            this.updateElement('engineNodes', this.formatNumber(searchInfo.totalNodes || 0));
            this.updateElement('engineTime', ((searchInfo.totalTime || 0) / 1000).toFixed(1) + 's');
            this.updateElement('engineNPS', this.formatNumber(searchInfo.nodesPerSecond || 0) + ' nps');
            
            // Show engine source
            const sourceText = this.getSourceDisplayText(searchInfo.source);
            this.updateElement('engineSource', sourceText);
        }

        // Update best moves
        if (bestMoves && bestMoves.length > 0) {
            this.updateElement('bestMove', bestMoves[0].san || bestMoves[0].move || 'N/A');
            this.displayTopMoves(bestMoves);
        }

        // Show engine source
        const sourceText = this.getSourceDisplayText(searchInfo.source);
        this.updateElement('engineSource', sourceText);
        console.log('✅ Analysis display updated successfully');

        // Update additional stats if available
        

        // Update position evaluation chart if it exists
        this.updateEvaluationChart(evaluation.value);
        this.displayTopMoves(bestMoves);

        // Log detailed analysis
        console.log('🐍 Python Engine Analysis/Updated:', {
            evaluation: evaluation,
            topMoves: bestMoves.slice(0, 3),
            searchStats: searchInfo,
            source: searchInfo.source
        });
    }
    updateElement(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = value;
        } else {
            console.warn(`Element with ID '${elementId}' not found`);
        }
    }
    formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toString();
    }
    
updateEngineStatus(status, isReady) {
    const statusElement = document.getElementById('engineStatus');
    if (statusElement) {
        statusElement.textContent = status;
        statusElement.style.color = isReady ? '#28a745' : '#dc3545';
    }
}

getSourceDisplayText(source) {
    switch (source) {
        case 'opening_book':
            return 'Opening Book';
        case 'engine_search':
            return 'Python Engine';
        case 'python_engine':
            return 'Python Engine';
        default:
            return 'Python Engine';
    }
}


getEvalClass(evalValue) {
    if (Math.abs(evalValue) > 5) return 'mate';
    if (evalValue > 2) return 'winning';
    if (evalValue > 0.5) return 'advantage';
    if (evalValue > -0.5) return 'equal';
    if (evalValue > -2) return 'disadvantage';
    return 'losing';
}

displayTopMoves(moves) {
    let movesContainer = document.getElementById('topMovesContainer');
    if (!movesContainer) {
        const engineInfo = document.querySelector('.engine-info');
        if (engineInfo) {
            movesContainer = document.createElement('div');
            movesContainer.id = 'topMovesContainer';
            movesContainer.className = 'top-moves-container';
            engineInfo.appendChild(movesContainer);
        }
    }

    if (movesContainer && moves && moves.length > 0) {
        let movesHtml = '<div class="top-moves-header">Top Moves</div>';
        
        moves.slice(0, 3).forEach((move, index) => {
            const evalClass = this.getEvalClass(move.evaluationRaw || 0);
            movesHtml += `
                <div class="move-line" onclick="makeMove('${move.move || ''}')">
                    <div class="move-info">
                        <span class="move-rank">${index + 1}.</span>
                        <span class="move-notation">${move.san || move.move || 'N/A'}</span>
                        <span class="move-eval ${evalClass}">${move.evaluation || '0.0'}</span>
                    </div>
                    <div class="move-pv">${(move.principalVariation || []).slice(0, 4).join(' ')}</div>
                    <div class="move-stats">Depth: ${move.depth || 0} | Nodes: ${this.formatNumber(move.nodes || 0)}</div>
                </div>
            `;
        });
        
        movesContainer.innerHTML = movesHtml;
    }
}

    playMove(move) {
        const currentGame = this.getCurrentGame();
        if (currentGame && window.makeMove) {
            try {
                window.makeMove(move);
                this.showNotification(`Played: ${move}`, 'info');
            } catch (error) {
                console.error('Failed to play move:', error);
                this.showNotification('Failed to play move', 'error');
            }
        }
    }

    flipBoard() {
        if (window.flipBoard) {
            window.flipBoard();
        } else if (window.board && window.board.flip) {
            window.board.flip();
        }
        this.showNotification('Board flipped', 'info');
    }

    resetPosition() {
        const currentGame = this.getCurrentGame();
        if (currentGame && currentGame.reset) {
            currentGame.reset();
            this.showNotification('Position reset to starting position', 'info');
            
            // Update the board display
            if (window.updateBoard) {
                window.updateBoard();
            }
            
            // Clear analysis
            this.clearAnalysisDisplay();
        }
    }

    clearAnalysisDisplay() {
        this.updateElement('engineEval', '0.00');
        this.updateElement('engineDepth', '-');
        this.updateElement('engineNodes', '-');
        this.updateElement('engineTime', '-');
        this.updateElement('bestMove', '-');
        
        const movesContainer = document.getElementById('topMovesContainer');
        if (movesContainer) {
            movesContainer.innerHTML = '';
        }
        
        if (window.updateEvalBar) {
            window.updateEvalBar(0);
        }
    }

    updateAnalyzeButton(state) {
        const analyzeBtn = document.getElementById('analyzeBtn');
        if (analyzeBtn) {
            if (state === 'stop') {
                analyzeBtn.textContent = 'Stop Analysis';
                analyzeBtn.classList.add('analyzing', 'btn-danger');
                analyzeBtn.classList.remove('btn-primary');
            } else {
                analyzeBtn.textContent = 'Analyze Position';
                analyzeBtn.classList.remove('analyzing', 'btn-danger');
                analyzeBtn.classList.add('btn-primary');
            }
        }
    }

    updateEngineStatus(status, isActive) {
        this.updateElement('engineStatus', status);
        
        const statusElement = document.getElementById('engineStatus');
        if (statusElement) {
            statusElement.className = `engine-status ${isActive ? 'engine-active' : 'engine-inactive'}`;
        }
    }

    

    getCurrentGame() {
        // Try to get the global game object from the window
        if (typeof window !== 'undefined' && window.getCurrentGame) {
            return window.getCurrentGame();
        }
        
        // Fallback: try to access global game variables directly
        if (typeof window !== 'undefined') {
            const currentTab = window.currentTab || 'play';
            if (currentTab === 'analyze' && window.analyzeGame) {
                return window.analyzeGame;
            } else if (window.game) {
                return window.game;
            }
        }
        
        // Last resort: create a new game with starting position
        if (typeof Chess !== 'undefined') {
            console.warn('Creating new Chess game as fallback');
            return new Chess();
        }
        
        throw new Error('No chess game instance available');
    }
    

    addToEvaluationHistory(fen, analysis) {
        this.evaluationHistory.unshift({
            fen,
            evaluation: analysis.evaluation.value,
            timestamp: Date.now(),
            depth: analysis.searchInfo.depth
        });

        // Keep only last 50 evaluations
        if (this.evaluationHistory.length > 50) {
            this.evaluationHistory = this.evaluationHistory.slice(0, 50);
        }
    }

    updateEvaluationChart(evaluation) {
        // Update evaluation history chart if it exists
        const chartElement = document.getElementById('evaluationChart');
        if (chartElement && this.evaluationHistory.length > 1) {
            this.renderEvaluationChart();
        }
    }

    renderEvaluationChart() {
        // Simple evaluation chart rendering
        const chartElement = document.getElementById('evaluationChart');
        if (!chartElement) return;

        const history = this.evaluationHistory.slice(0, 20).reverse();
        const maxVal = Math.max(...history.map(h => Math.abs(h.evaluation)));
        const scale = maxVal > 0 ? 100 / maxVal : 1;

        let chartHtml = '<div class="eval-chart">';
        history.forEach((entry, index) => {
            const height = Math.abs(entry.evaluation) * scale;
            const color = entry.evaluation > 0 ? 'white-advantage' : 'black-advantage';
            chartHtml += `<div class="eval-bar ${color}" style="height: ${height}%" title="Move ${index + 1}: ${entry.evaluation.toFixed(2)}"></div>`;
        });
        chartHtml += '</div>';

        chartElement.innerHTML = chartHtml;
    }

    getEvalClass(value) {
        if (Math.abs(value) > 50) return 'mate';
        if (value > 2) return 'winning';
        if (value > 0.5) return 'advantage';
        if (value > -0.5) return 'equal';
        if (value > -2) return 'disadvantage';
        return 'losing';
    }

    getSourceDisplayText(source) {
        switch (source) {
            case 'engine_search': return 'Python Engine';
            case 'opening_book': return 'Opening Book';
            case 'basic_fallback': return 'Basic Fallback';
            default: return source || 'Unknown';
        }
    }

    formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        }
        if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toString();
    }

    showNotification(message, type = 'info') {
        // Try to use existing notification system
        if (window.showNotification) {
            window.showNotification(message, type);
            return;
        }

        // Fallback notification system
        console.log(`${type.toUpperCase()}: ${message}`);
        
        // Create simple notification if possible
        if (document.body) {
            const notification = document.createElement('div');
            notification.className = `notification notification-${type}`;
            notification.textContent = message;
            notification.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 12px 16px;
                border-radius: 6px;
                color: white;
                font-weight: 500;
                z-index: 10000;
                max-width: 300px;
                box-shadow: 0 4px 12pxrgb(1, 5, 23);
                background-color: ${type === 'error' ? '#dc3545' : 
                                 type === 'success' ? '#272f54' : 
                                 type === 'warning' ? '#ffc107' : '#17a2b8'};
                animation: slideIn 0.3s ease-out;
            `;

            document.body.appendChild(notification);

            // Auto remove after 5 seconds
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.style.animation = 'slideOut 0.3s ease-in';
                    setTimeout(() => {
                        if (notification.parentNode) {
                            notification.parentNode.removeChild(notification);
                        }
                    }, 300);
                }
            }, 5000);
        }
    }

    toggleAutoAnalyze() {
        this.autoAnalyze = !this.autoAnalyze;
        const checkbox = document.getElementById('autoAnalyzeToggle');
        if (checkbox) {
            checkbox.checked = this.autoAnalyze;
        }
        
        if (this.autoAnalyze) {
            this.showNotification('Auto-analyze enabled', 'info');
        } else {
            this.showNotification('Auto-analyze disabled', 'info');
        }
    }

    getEngineStats() {
        if (!this.analyzer) return null;

        return {
            cacheStats: this.analyzer.getCacheStats(),
            historyCount: this.evaluationHistory.length,
            isAnalyzing: this.isAnalyzing,
            engineInfo: this.analyzer.getEngineStatus()
        };
    }

    clearEngineCache() {
        if (this.analyzer) {
            this.analyzer.clearCache();
            this.showNotification('Engine cache cleared', 'info');
        }
    }

    exportAnalysis() {
        if (this.evaluationHistory.length === 0) {
            this.showNotification('No analysis history to export', 'warning');
            return;
        }

        const exportData = {
            timestamp: new Date().toISOString(),
            engineInfo: this.getEngineStats(),
            evaluationHistory: this.evaluationHistory
        };

        const dataStr = JSON.stringify(exportData, null, 2);
        const blob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(blob);

        const a = document.createElement('a');
        a.href = url;
        a.download = `chess_analysis_${Date.now()}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        this.showNotification('Analysis exported successfully', 'success');
    }

    destroy() {
        this.stopAnalysis();
        
        if (this.analyzer) {
            this.analyzer.destroy();
        }

        this.evaluationHistory = [];
        console.log('🗑️ Chess UI Integration destroyed');
    }
}

// Utility functions for global access
function showNotification(message, type = 'info') {
    console.log(`${type.toUpperCase()}: ${message}`);
}

function updateEvalBar(value) {
    const evalBar = document.getElementById('evalBar');
    const evalFill = document.getElementById('evalFill');
    
    if (evalBar && evalFill) {
        // Convert evaluation to percentage (capped at +/-5)
        const cappedValue = Math.max(-5, Math.min(5, value));
        const percentage = ((cappedValue + 5) / 10) * 100;
        
        evalFill.style.height = `${percentage}%`;
        
        // Update color based on evaluation
        if (value > 2) {
            evalFill.style.backgroundColor = '#28a745'; // Green
        } else if (value > 0.5) {
            evalFill.style.backgroundColor = '#90EE90'; // Light green
        } else if (value > -0.5) {
            evalFill.style.backgroundColor = '#808080'; // Gray
        } else if (value > -2) {
            evalFill.style.backgroundColor = '#FFB6C1'; // Light red
        } else {
            evalFill.style.backgroundColor = '#dc3545'; // Red
        }
    }
}

// Make classes available globally
window.UpdatedChessUIIntegration = UpdatedChessUIIntegration;
window.showNotification = showNotification;
window.updateEvalBar = updateEvalBar;

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
    
    .top-moves-container {
        margin-top: 15px;
        border: 1px solid #dee2e6;
        border-radius: 6px;
        overflow: hidden;
    }
    
    .top-moves-header {
        background: #f8f9fa;
        padding: 8px 12px;
        border-bottom: 1px solid #dee2e6;
        font-weight: 600;
    }
    
    .move-line {
        padding: 8px 12px;
        border-bottom: 1px solid #eee;
        cursor: pointer;
        transition: background-color 0.2s;
    }
    
    .move-line:hover {
        background-color: #f8f9fa;
    }
    
    .move-line:last-child {
        border-bottom: none;
    }
    
    .move-info {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 4px;
    }
    
    .move-rank {
        font-weight: 600;
        min-width: 20px;
    }
    
    .move-notation {
        font-family: monospace;
        font-weight: 600;
        min-width: 60px;
    }
    
    .move-eval {
        font-weight: 600;
        padding: 2px 6px;
        border-radius: 3px;
        font-size: 0.85em;
    }
    
    .move-eval.winning { background: #d4edda; color: #155724; }
    .move-eval.advantage { background: #d1ecf1; color: #0c5460; }
    .move-eval.equal { background: #f8f9fa; color: #6c757d; }
    .move-eval.disadvantage { background: #f8d7da; color: #721c24; }
    .move-eval.losing { background: #f5c6cb; color: #721c24; }
    .move-eval.mate { background: #721c24; color: white; }
    
    .move-pv {
        font-family: monospace;
        font-size: 0.85em;
        color: #6c757d;
        margin-bottom: 2px;
    }
    
    .move-stats {
        font-size: 0.75em;
        color: #868e96;
    }
    
    .eval-chart {
        display: flex;
        align-items: end;
        height: 60px;
        gap: 2px;
        padding: 5px;
        background: #f8f9fa;
        border-radius: 4px;
    }
    
    .eval-bar {
        flex: 1;
        min-height: 2px;
        border-radius: 1px;
        transition: height 0.3s;
    }
    
    .eval-bar.white-advantage { background:rgb(255, 255, 255); }
    .eval-bar.black-advantage { background:rgb(0, 0, 0); }
    
    .engine-status.engine-active {
        color:rgb(255, 255, 255);
        font-weight: 300;
    }
    
    .engine-status.engine-inactive {
        color:rgb(57, 63, 69);
    }
    
    .btn.analyzing {
        position: relative;
        overflow: hidden;
    }
    
    .btn.analyzing::after {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
        animation: shimmer 1.5s infinite;
    }
    
    @keyframes shimmer {
        0% { left: -100%; }
        100% { left: 100%; }
    }
`;
document.head.appendChild(style);
