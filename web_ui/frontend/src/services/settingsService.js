import api from './api';

export const settingsService = {
  // Get current settings
  async getSettings() {
    try {
      const response = await api.get('/api/settings/');
      return response.data;
    } catch (error) {
      throw new Error(error.userMessage || 'Failed to load settings');
    }
  },

  // Update all settings
  async updateSettings(settings) {
    try {
      const response = await api.put('/api/settings/', settings);
      return response.data;
    } catch (error) {
      throw new Error(error.userMessage || 'Failed to update settings');
    }
  },

  // Update partial settings
  async updatePartialSettings(updates) {
    try {
      const response = await api.patch('/api/settings/', updates);
      return response.data;
    } catch (error) {
      throw new Error(error.userMessage || 'Failed to update settings');
    }
  },

  // Test API key
  async testApiKey(apiKey) {
    try {
      const response = await api.post('/api/settings/test-api-key', { api_key: apiKey });
      return response.data;
    } catch (error) {
      throw new Error(error.userMessage || 'API key validation failed');
    }
  },

  // Get default settings
  async getDefaults() {
    try {
      const response = await api.get('/api/settings/defaults');
      return response.data;
    } catch (error) {
      throw new Error(error.userMessage || 'Failed to get default settings');
    }
  },

  // Reset to defaults
  async resetToDefaults() {
    try {
      const response = await api.post('/api/settings/reset-to-defaults');
      return response.data;
    } catch (error) {
      throw new Error(error.userMessage || 'Failed to reset settings');
    }
  },

  // Get environment info
  async getEnvironmentInfo() {
    try {
      const response = await api.get('/api/settings/environment');
      return response.data;
    } catch (error) {
      throw new Error(error.userMessage || 'Failed to get environment info');
    }
  },

  // Get validation rules
  async getValidationRules() {
    try {
      const response = await api.get('/api/settings/validation-rules');
      return response.data;
    } catch (error) {
      throw new Error(error.userMessage || 'Failed to get validation rules');
    }
  },

  // Get settings presets
  async getPresets() {
    try {
      const response = await api.get('/api/settings/presets');
      return response.data;
    } catch (error) {
      throw new Error(error.userMessage || 'Failed to get settings presets');
    }
  },

  // Apply settings preset
  async applyPreset(presetName) {
    try {
      const response = await api.post(`/api/settings/presets/${presetName}/apply`);
      return response.data;
    } catch (error) {
      throw new Error(error.userMessage || 'Failed to apply preset');
    }
  }
};