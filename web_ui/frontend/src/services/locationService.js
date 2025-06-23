import api from './api';

export const locationService = {
  // Get complete location hierarchy
  async getLocations() {
    try {
      const response = await api.get('/api/locations/');
      return response.data;
    } catch (error) {
      throw new Error(error.userMessage || 'Failed to load locations');
    }
  },

  // Estimate scraping duration for given selection
  async estimateDuration(locationSelection) {
    try {
      const response = await api.post('/api/locations/estimate', locationSelection);
      return response.data;
    } catch (error) {
      throw new Error(error.userMessage || 'Failed to estimate duration');
    }
  },

  // Update location selection
  async updateSelection(update) {
    try {
      const response = await api.post('/api/locations/update-selection', update);
      return response.data;
    } catch (error) {
      throw new Error(error.userMessage || 'Failed to update selection');
    }
  },

  // Perform batch operation on locations
  async applyBatchOperation(operation) {
    try {
      const response = await api.post('/api/locations/batch-operation', operation);
      return response.data;
    } catch (error) {
      throw new Error(error.userMessage || 'Failed to apply batch operation');
    }
  },

  // Get location presets
  async getPresets() {
    try {
      const response = await api.get('/api/locations/presets');
      return response.data;
    } catch (error) {
      throw new Error(error.userMessage || 'Failed to load presets');
    }
  },

  // Apply location preset
  async applyPreset(presetId) {
    try {
      const response = await api.post(`/api/locations/apply-preset/${presetId}`);
      return response.data;
    } catch (error) {
      throw new Error(error.userMessage || 'Failed to apply preset');
    }
  }
};