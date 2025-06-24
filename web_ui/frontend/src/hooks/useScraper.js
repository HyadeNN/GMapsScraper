import { useState, useEffect, useCallback } from 'react';
import { scraperService } from '../services/scraperService';
import useWebSocket from './useWebSocket';

const useScraper = () => {
  const [scraperStatus, setScraperStatus] = useState(null);
  const [progress, setProgress] = useState({
    status: 'idle',
    current_city: null,
    current_district: null,
    current_search_method: null,
    completed_locations: 0,
    total_locations: 0,
    completion_percentage: 0.0,
    estimated_time_remaining: null,
    processing_speed: null,
    results_found: 0,
    errors_encountered: 0,
    last_save_time: null,
    start_time: null,
    elapsed_time: null
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [currentOperationId, setCurrentOperationId] = useState(null);

  const { 
    lastMessage, 
    sendStartScraping, 
    sendPauseScraping, 
    sendStopScraping,
    sendGetStatus,
    isConnected 
  } = useWebSocket();

  // Load initial status
  useEffect(() => {
    loadStatus();
  }, []);

  // Handle WebSocket messages
  useEffect(() => {
    if (lastMessage) {
      switch (lastMessage.type) {
        case 'progress_update':
          setProgress(prevProgress => ({
            ...prevProgress,
            ...lastMessage.data
          }));
          break;
          
        case 'initial_status':
          if (lastMessage.data) {
            setScraperStatus(lastMessage.data);
            if (lastMessage.data.progress) {
              setProgress(lastMessage.data.progress);
            }
          }
          break;
          
        case 'start_scraping_response':
          if (lastMessage.success) {
            setCurrentOperationId(lastMessage.operation_id);
          }
          break;
          
        case 'pause_scraping_response':
        case 'resume_scraping_response':
        case 'stop_scraping_response':
          // Status will be updated via progress_update messages
          break;
      }
    }
  }, [lastMessage]);

  const loadStatus = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const status = await scraperService.getStatus();
      setScraperStatus(status);
      setProgress(status.progress);
      setCurrentOperationId(status.operation_id);
    } catch (err) {
      console.error('Failed to load scraper status:', err);
      setError('Failed to load scraper status');
    } finally {
      setLoading(false);
    }
  }, []);

  const startScraping = useCallback(async ({ settings, locations, profileId = null }) => {
    setLoading(true);
    setError(null);
    
    try {
      // Generate operation ID
      const operationId = `scrape_${Date.now()}`;
      
      // Create scraping operation
      const operation = {
        operation_id: operationId,
        settings,
        locations,
        profile_id: profileId,
        created_at: new Date().toISOString()
      };

      // Try WebSocket first, fallback to HTTP
      if (isConnected) {
        const success = sendStartScraping(operationId, settings, locations);
        if (success) {
          setCurrentOperationId(operationId);
          return { success: true, operation_id: operationId };
        }
      }
      
      // Fallback to HTTP API
      const response = await scraperService.startScraping(operation);
      setCurrentOperationId(response.operation_id);
      return response;
      
    } catch (err) {
      console.error('Failed to start scraping:', err);
      setError('Failed to start scraping');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [isConnected, sendStartScraping]);

  const pauseScraping = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Try WebSocket first, fallback to HTTP
      if (isConnected) {
        const success = sendPauseScraping();
        if (success) {
          return { success: true };
        }
      }
      
      // Fallback to HTTP API
      const response = await scraperService.pauseScraping();
      return response;
      
    } catch (err) {
      console.error('Failed to pause scraping:', err);
      setError('Failed to pause scraping');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [isConnected, sendPauseScraping]);

  const resumeScraping = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await scraperService.resumeScraping();
      return response;
    } catch (err) {
      console.error('Failed to resume scraping:', err);
      setError('Failed to resume scraping');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const stopScraping = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Try WebSocket first, fallback to HTTP
      if (isConnected) {
        const success = sendStopScraping();
        if (success) {
          return { success: true };
        }
      }
      
      // Fallback to HTTP API
      const response = await scraperService.stopScraping();
      setCurrentOperationId(null);
      return response;
      
    } catch (err) {
      console.error('Failed to stop scraping:', err);
      setError('Failed to stop scraping');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [isConnected, sendStopScraping]);

  const getResults = useCallback(async (operationId = null) => {
    try {
      const results = await scraperService.getResults(operationId || currentOperationId);
      return results;
    } catch (err) {
      console.error('Failed to get results:', err);
      throw err;
    }
  }, [currentOperationId]);

  const validateApiKey = useCallback(async (apiKey) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await scraperService.validateApiKey(apiKey);
      return result;
    } catch (err) {
      console.error('API key validation failed:', err);
      setError('API key validation failed');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const getOperationHistory = useCallback(async () => {
    try {
      const history = await scraperService.getOperationHistory();
      return history;
    } catch (err) {
      console.error('Failed to get operation history:', err);
      throw err;
    }
  }, []);

  const cancelOperation = useCallback(async (operationId) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await scraperService.cancelOperation(operationId);
      if (operationId === currentOperationId) {
        setCurrentOperationId(null);
      }
      return response;
    } catch (err) {
      console.error('Failed to cancel operation:', err);
      setError('Failed to cancel operation');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [currentOperationId]);

  const checkHealth = useCallback(async () => {
    try {
      const health = await scraperService.checkHealth();
      return health;
    } catch (err) {
      console.error('Health check failed:', err);
      throw err;
    }
  }, []);

  // Auto-refresh status when not connected via WebSocket
  useEffect(() => {
    if (!isConnected && progress.status === 'running') {
      const interval = setInterval(() => {
        loadStatus();
      }, 10000); // Refresh every 10 seconds
      
      return () => clearInterval(interval);
    }
  }, [isConnected, progress.status, loadStatus]);

  // Request status via WebSocket when connected
  useEffect(() => {
    if (isConnected) {
      sendGetStatus();
    }
  }, [isConnected, sendGetStatus]);

  return {
    scraperStatus,
    progress,
    loading,
    error,
    currentOperationId,
    startScraping,
    pauseScraping,
    resumeScraping,
    stopScraping,
    getResults,
    validateApiKey,
    getOperationHistory,
    cancelOperation,
    checkHealth,
    loadStatus,
    clearError: () => setError(null),
    // Computed properties
    isIdle: progress.status === 'idle',
    isRunning: progress.status === 'running',
    isPaused: progress.status === 'paused',
    isCompleted: progress.status === 'completed',
    hasError: progress.status === 'error',
    canStart: scraperStatus?.can_start && !loading,
    canPause: scraperStatus?.can_pause && !loading,
    canStop: scraperStatus?.can_stop && !loading,
    canResume: scraperStatus?.can_resume && !loading
  };
};

export default useScraper;