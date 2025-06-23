import api from './api';

export const scraperService = {
  // Start scraping operation
  async startScraping(operation) {
    try {
      const response = await api.post('/api/scraper/start', operation);
      return response.data;
    } catch (error) {
      throw new Error(error.userMessage || 'Failed to start scraping');
    }
  },

  // Control scraper (pause, resume, stop)
  async controlScraper(action, operationId = null) {
    try {
      const response = await api.post('/api/scraper/control', {
        action,
        operation_id: operationId
      });
      return response.data;
    } catch (error) {
      throw new Error(error.userMessage || `Failed to ${action} scraping`);
    }
  },

  // Pause scraping
  async pauseScraping(operationId = null) {
    return this.controlScraper('pause', operationId);
  },

  // Resume scraping
  async resumeScraping(operationId = null) {
    return this.controlScraper('resume', operationId);
  },

  // Stop scraping
  async stopScraping(operationId = null) {
    return this.controlScraper('stop', operationId);
  },

  // Get scraper status
  async getStatus() {
    try {
      const response = await api.get('/api/scraper/status');
      return response.data;
    } catch (error) {
      throw new Error(error.userMessage || 'Failed to get scraper status');
    }
  },

  // Get scraping results
  async getResults(operationId = null) {
    try {
      const url = operationId 
        ? `/api/scraper/results?operation_id=${operationId}`
        : '/api/scraper/results';
      const response = await api.get(url);
      return response.data;
    } catch (error) {
      throw new Error(error.userMessage || 'Failed to get results');
    }
  },

  // Validate API key
  async validateApiKey(apiKey) {
    try {
      const response = await api.post('/api/scraper/validate-api-key', { api_key: apiKey });
      return response.data;
    } catch (error) {
      throw new Error(error.userMessage || 'API key validation failed');
    }
  },

  // Get operation history
  async getOperationHistory() {
    try {
      const response = await api.get('/api/scraper/operations/history');
      return response.data;
    } catch (error) {
      throw new Error(error.userMessage || 'Failed to get operation history');
    }
  },

  // Cancel operation
  async cancelOperation(operationId) {
    try {
      const response = await api.delete(`/api/scraper/operations/${operationId}`);
      return response.data;
    } catch (error) {
      throw new Error(error.userMessage || 'Failed to cancel operation');
    }
  },

  // Check scraper health
  async checkHealth() {
    try {
      const response = await api.get('/api/scraper/health');
      return response.data;
    } catch (error) {
      throw new Error(error.userMessage || 'Health check failed');
    }
  }
};