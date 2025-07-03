// enhanced-chess-analyzer.js - Enhanced analyzer using Python engine

class EnhancedChessAnalyzer {
    constructor() {
        this.engine = null;
        this.isInitialized = false;
        this.cache = new Map();
        this.maxCacheSize = 500;
        this.analysisHistory = [];
        this.currentAnalysisId = null;
        console.log('🔧 EnhancedChessAnalyzer constructor called');
    }

    async initialize() {
        if (this.isInitialized) {
            console.log('Analyzer is already initialized.');
            return true;
        }

        try {
            this.engine = new PythonChessBridge();
            await this.engine.initialize();
            this.isInitialized = true;
            console.log('✅ Enhanced Chess Analyzer initialized successfully.');
            console.log('🔍 Engine details:', this.engine.getEngineInfo());
            return true;
        } catch (error) {
            console.error('❌ Enhanced Chess Analyzer initialization failed:', error.message);
            this.isInitialized = false;
            // We throw the error so the UI can catch it and display a message.
            throw new Error('Failed to initialize the chess analysis engine.');
        }
    }

    async getTopMoves(fen, options = {}) {
        const { depth = 8, useCache = true, timeout = 60000 } = options;


        if (!this.isInitialized) {
            console.warn('Analyzer not initialized. Attempting to re-initialize...');
            try {
                await this.initialize();
            } catch (error) {
                throw new Error('Analysis failed: Engine is not available.');
            }
        }

        // Validate FEN string
        if (!this.isValidFen(fen)) {
            throw new Error('Invalid FEN string provided');
        }

        const cacheKey = `${fen}_${depth}`;
        if (useCache && this.cache.has(cacheKey)) {
            console.log('📋 Using cached analysis for FEN:', fen);
            const cachedResult = this.cache.get(cacheKey);
            cachedResult.timestamp = Date.now();
            return cachedResult;
        }

        const currentId = this.generateAnalysisId();
        const localAnalysisId = currentId;
        const analysisId=currentId; // lock locally

        console.log(`🔍 Starting analysis (ID: ${localAnalysisId})`);

// no global assignment now

        console.log(`🔍 Starting analysis (ID: ${analysisId}, FEN: ${fen}, Depth: ${depth})`);

        try {
            console.log(`📡 getTopMoves() called with FEN=${fen}, depth=${depth}`);
            const result = await this.engine.analyzePosition(fen, { depth, timeout });

        
            if (localAnalysisId !== currentId) {
                console.warn(`⚠️ Analysis (ID: ${localAnalysisId}) is stale.`);
                return { cancelled: true };
            }

            if (result.success) {
                if (useCache) {
                    this.addToCache(cacheKey, result);
                }
                this.addToHistory(fen, result, options);
                console.log(`✅ Analysis (ID: ${analysisId}) completed successfully.`);
                return result;
            } else {
                // This case should ideally be handled by errors thrown from the bridge
                throw new Error('Analysis failed for an unknown reason.');
            }
        } catch (error) {
            console.error(`❌ Analysis (ID: ${analysisId}) error:`, error.message);
            // Re-throw the error to be handled by the caller
            throw error;
        } finally {
            if (this.currentAnalysisId == analysisId) {
                this.currentAnalysisId = null;
            }
        }
    }

    async quickEvaluation(fen) {
        return await this.getTopMoves(fen, { depth: 6, useCache: true, timeout: 60000 });
    }

    async deepAnalysis(fen) {
        return await this.getTopMoves(fen, { depth: 12, useCache: false, timeout: 180000 });
    }

    async tacticalAnalysis(fen) {
        return await this.getTopMoves(fen, { depth: 10, useCache: false, timeout: 90000 });
    }

    async multiDepthAnalysis(fen, maxDepth = 10) {
        const results = [];
        for (let depth = 4; depth <= maxDepth; depth += 2) {
            try {
                const result = await this.getTopMoves(fen, { depth, useCache: false, timeout: 60000 });
                results.push({ depth, result });
            } catch (error) {
                console.warn(`Analysis failed at depth ${depth}:`, error.message);
                break; // Stop if one level fails
            }
        }
        return results;
    }

    cancelCurrentAnalysis() {
        if (this.currentAnalysisId) {
            console.log(`🛑 Cancelling current analysis (ID: ${this.currentAnalysisId})`);
            this.currentAnalysisId = null;
        }
    }

    addToCache(key, value) {
        if (this.cache.size >= this.maxCacheSize) {
            const oldestKey = this.cache.keys().next().value;
            this.cache.delete(oldestKey);
        }
        const cachedValue = { ...value, cacheTime: Date.now(), expires: Date.now() + (60 * 60 * 1000) };
        this.cache.set(key, cachedValue);
    }

    addToHistory(fen, result, options) {
        this.analysisHistory.unshift({ fen, result, options, timestamp: Date.now() });
        if (this.analysisHistory.length > 50) {
            this.analysisHistory = this.analysisHistory.slice(0, 50);
        }
    }

    clearCache() {
        this.cache.clear();
        console.log('🗑️ Analysis cache cleared');
    }

    clearHistory() {
        this.analysisHistory = [];
        console.log('🗑️ Analysis history cleared');
    }

    getCacheStats() {
        const now = Date.now();
        const expired = Array.from(this.cache.values()).filter(v => v.expires && v.expires < now).length;
        return { size: this.cache.size, maxSize: this.maxCacheSize, expired };
    }

    cleanExpiredCache() {
        const now = Date.now();
        let cleaned = 0;
        for (const [key, value] of this.cache.entries()) {
            if (value.expires && value.expires < now) {
                this.cache.delete(key);
                cleaned++;
            }
        }
        if (cleaned > 0) {
            console.log(`🧹 Cleaned ${cleaned} expired cache entries`);
        }
        return cleaned;
    }

    getEngineStatus() {
        return this.engine ? this.engine.getEngineInfo() : { name: 'N/A', isReady: false };
    }

    getAnalysisHistory(limit = 10) {
        return this.analysisHistory.slice(0, limit);
    }

    isValidFen(fen) {
        if (!fen || typeof fen !== 'string') return false;
        const parts = fen.trim().split(/\s+/);
        if (parts.length !== 6) return false;
        const piecePlacement = parts[0];
        const ranks = piecePlacement.split('/');
        if (ranks.length !== 8) return false;
        for (const rank of ranks) {
            let fileCount = 0;
            for (const char of rank) {
                if (/[1-8]/.test(char)) fileCount += parseInt(char);
                else if (/[prnbqkPRNBQK]/.test(char)) fileCount += 1;
                else return false;
            }
            if (fileCount !== 8) return false;
        }
        if (!/^[wb]$/.test(parts[1])) return false;
        if (!/^[KQkq\-]+$/.test(parts[2])) return false;
        if (!/^([a-h][36]|\-)$/.test(parts[3])) return false;
        return true;
    }

    generateAnalysisId() {
        return Math.random().toString(36).substring(2, 15);
    }

    destroy() {
        this.cancelCurrentAnalysis();
        this.clearCache();
        this.clearHistory();
        if (this.engine) {
            this.engine.destroy();
        }
        this.isInitialized = false;
        console.log('🗑️ Enhanced Chess Analyzer destroyed');
    }
}

// Make available globally
if (typeof window !== 'undefined') {
    window.EnhancedChessAnalyzer = EnhancedChessAnalyzer;
}
