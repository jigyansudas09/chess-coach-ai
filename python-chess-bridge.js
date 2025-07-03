// python-chess-bridge.js - Bridge to Python chess engine

// Configuration constants for the chess engine
const CHESS_ENGINE_CONFIG = {
    PYTHON_SERVER_URL: 'http://192.168.29.161:8000',
    TIMEOUT: 60000, // 60 seconds
    HEALTH_CHECK_TIMEOUT: 3000 // 3 seconds
};

class PythonChessBridge {
    constructor() {
        this.isInitialized = false;
        this.serverUrl = CHESS_ENGINE_CONFIG.PYTHON_SERVER_URL;
        this.requestTimeout = CHESS_ENGINE_CONFIG.TIMEOUT;
        console.log('🐍 PythonChessBridge constructor');
        console.log('🔧 Using PYTHON_SERVER_URL:', this.serverUrl);
    }

    async initialize() {
        try {
            // Test if Python server is running with a dedicated health check
            const isHealthy = await this.healthCheck();

            if (isHealthy) {
                this.isInitialized = true;
                console.log('✅ Python chess engine connected successfully.');
                return true;
            } else {
                throw new Error('Health check failed.');
            }
        } catch (error) {
            console.warn('🔴 Python server not available or not responding.', error.message);
            this.isInitialized = false; // Ensure it's marked as not initialized
            // In a real app, you might initialize a fallback engine here.
            // For now, we will just throw an error to make the problem clear.
            throw new Error('Could not connect to the Python chess engine.');
        }
    }

    async healthCheck() {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), CHESS_ENGINE_CONFIG.HEALTH_CHECK_TIMEOUT);

        try {
            const response = await fetch(`${this.serverUrl}/health`, {
                method: 'GET',
                signal: controller.signal
            });

            clearTimeout(timeoutId);
            if (controller.signal.aborted) {
                throw new Error(`Analysis timed out after ${timeout / 1000} seconds.`);
            }
            

            if (response.ok) {
                const data = await response.json();
                return data.status === 'ok';
            }
            return false;
        } catch (error) {
            clearTimeout(timeoutId);
            console.error('Health check request failed:', error.name);
            return false;
        }
    }

    async analyzePosition(fen, options = {}) {
        const { depth = 8, timeout = this.requestTimeout } = options;

        if (!this.isInitialized) {
            console.error('Engine not initialized. Call initialize() first.');
            // Attempt a quick health check before failing
            const isHealthy = await this.healthCheck();
            if (!isHealthy) {
                throw new Error('Engine not initialized and health check failed.');
            }
            this.isInitialized = true; // Health check passed, so we can proceed
            console.log('Engine re-initialized after health check.');
        }

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeout);

        try {
            const response = await fetch(`${this.serverUrl}/analyze`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    fen: fen,
                    depth: depth
                }),
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (response.ok) {
                const result = await response.json();
                if (result.status === 'error') {
                    throw new Error(result.error || 'Unknown engine error from server');
                }
                return this.formatPythonResult(result);
            } else {
                const errorText = await response.text();
                throw new Error(`Server responded with status ${response.status}: ${errorText}`);
            }

        } catch (error) {
            clearTimeout(timeoutId);
            console.error('Analysis request failed:', error.message);
            if (error.name === 'AbortError') {
                throw new Error(`Analysis timed out after ${timeout / 1000} seconds.`);
            }
            throw new Error('Failed to get analysis from the Python engine.');
        }
    }

    formatPythonResult(pythonResult) {
        // Convert Python engine result to our expected format
        if (pythonResult.status !== 'success') {
            throw new Error(pythonResult.error || 'Unknown engine error');
        }
        console.log('🔍 Raw Python result:', pythonResult);
        return {
            success: true,
            evaluation: pythonResult.evaluation || { value: 0 },  // Keep the full object
            bestMoves: pythonResult.bestMoves || [],              // Extract bestMoves
            searchInfo: pythonResult.searchInfo || {              // Extract searchInfo
                totalTime: 0,
                totalNodes: 0,
                nodesPerSecond: 0,
                depth: 0,
                source: 'python_engine'
            },
            timestamp: Date.now()
        };
    }

    formatEvaluation(value) {
        if (Math.abs(value) > 50) {
            const mateIn = Math.ceil(Math.abs(value) / 10);
            return value > 0 ? `M${mateIn}` : `M-${mateIn}`;
        }
        return value > 0 ? `+${value.toFixed(2)}` : value.toFixed(2);
    }

    getEngineInfo() {
        return {
            name: 'Python Chess Engine',
            version: '1.0',
            author: 'Custom Engine',
            isReady: this.isInitialized,
            serverUrl: this.serverUrl
        };
    }

    destroy() {
        this.isInitialized = false;
        console.log('PythonChessBridge destroyed.');
    }
}

// Make available globally or as a module
if (typeof window !== 'undefined') {
    window.PythonChessBridge = PythonChessBridge;
}
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PythonChessBridge;
}
