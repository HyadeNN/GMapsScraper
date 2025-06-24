import { useState, useEffect, useCallback, useRef } from 'react';
import { settingsService } from '../services/settingsService';

const useSettings = () => {
  const [settings, setSettings] = useState({
    api_key: '',
    search_terms: ['diş kliniği', 'dentist'],
    default_radius: 15000,
    request_delay: 1.0,
    max_retries: 3,
    batch_size: 20,
    storage_type: 'json',
    output_directory: 'data',
    language: 'tr',
    region: 'tr',
    grid_width_km: 5.0,
    grid_height_km: 5.0,
    grid_radius_meters: 800,
    mongodb_uri: null,
    mongodb_db: 'dental_clinics',
    mongodb_collection: 'places',
    log_level: 'INFO'
  });
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const savingRef = useRef(false);

  // Load settings on mount
  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const loadedSettings = await settingsService.getSettings();
      setSettings(loadedSettings);
    } catch (err) {
      console.error('Failed to load settings:', err);
      setError('Failed to load settings');
    } finally {
      setLoading(false);
    }
  }, []);

  const saveSettings = useCallback(async (newSettings) => {
    // Prevent concurrent save operations
    if (savingRef.current) {
      console.log('Save already in progress, skipping...');
      return settings;
    }
    
    savingRef.current = true;
    setLoading(true);
    setError(null);
    
    try {
      const savedSettings = await settingsService.updateSettings(newSettings);
      setSettings(savedSettings);
      return savedSettings;
    } catch (err) {
      console.error('Failed to save settings:', err);
      setError('Failed to save settings');
      throw err;
    } finally {
      savingRef.current = false;
      setLoading(false);
    }
  }, [settings]);

  const updateSettings = useCallback(async (updates) => {
    // If this is a complete settings object (manual save), save to backend
    if (Object.keys(updates).length > 5) {
      return await saveSettings(updates);
    }
    
    // Otherwise just update local state (no auto-save)
    setSettings(prevSettings => ({ ...prevSettings, ...updates }));
  }, [saveSettings]);

  const updatePartialSettings = useCallback(async (updates) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await settingsService.updatePartialSettings(updates);
      setSettings(response.settings);
      return response;
    } catch (err) {
      console.error('Failed to update partial settings:', err);
      setError('Failed to update settings');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const validateApiKey = useCallback(async (apiKey) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await settingsService.testApiKey(apiKey);
      return result;
    } catch (err) {
      console.error('API key validation failed:', err);
      setError('API key validation failed');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const resetToDefaults = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await settingsService.resetToDefaults();
      setSettings(response.settings);
      return response;
    } catch (err) {
      console.error('Failed to reset settings:', err);
      setError('Failed to reset settings');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const applyPreset = useCallback(async (presetName) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await settingsService.applyPreset(presetName);
      setSettings(response.settings);
      return response;
    } catch (err) {
      console.error('Failed to apply preset:', err);
      setError('Failed to apply preset');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const getEnvironmentInfo = useCallback(async () => {
    try {
      return await settingsService.getEnvironmentInfo();
    } catch (err) {
      console.error('Failed to get environment info:', err);
      throw err;
    }
  }, []);

  const getValidationRules = useCallback(async () => {
    try {
      return await settingsService.getValidationRules();
    } catch (err) {
      console.error('Failed to get validation rules:', err);
      throw err;
    }
  }, []);

  const getPresets = useCallback(async () => {
    try {
      return await settingsService.getPresets();
    } catch (err) {
      console.error('Failed to get presets:', err);
      throw err;
    }
  }, []);


  return {
    settings,
    loading,
    error,
    updateSettings,
    updatePartialSettings,
    saveSettings,
    loadSettings,
    validateApiKey,
    resetToDefaults,
    applyPreset,
    getEnvironmentInfo,
    getValidationRules,
    getPresets,
    clearError: () => setError(null)
  };
};

export default useSettings;