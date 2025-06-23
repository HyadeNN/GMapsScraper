import { useState, useEffect, useCallback } from 'react';
import { locationService } from '../services/locationService';

const useLocations = () => {
  const [locations, setLocations] = useState(null);
  const [locationSelection, setLocationSelection] = useState({
    cities: {},
    total_selected: 0,
    estimated_duration: null,
    last_updated: new Date().toISOString()
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Load locations on mount
  useEffect(() => {
    loadLocations();
  }, []);

  const loadLocations = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const locationsData = await locationService.getLocations();
      setLocations(locationsData);
    } catch (err) {
      console.error('Failed to load locations:', err);
      setError('Failed to load locations');
    } finally {
      setLoading(false);
    }
  }, []);

  const updateLocationSelection = useCallback((newSelection) => {
    setLocationSelection(newSelection);
  }, []);

  const estimateDuration = useCallback(async (selection = null) => {
    const selectionToEstimate = selection || locationSelection;
    
    try {
      const estimate = await locationService.estimateDuration(selectionToEstimate);
      return estimate;
    } catch (err) {
      console.error('Failed to estimate duration:', err);
      throw err;
    }
  }, [locationSelection]);

  const applyBatchOperation = useCallback(async (operation) => {
    try {
      const response = await locationService.applyBatchOperation(operation);
      return response;
    } catch (err) {
      console.error('Failed to apply batch operation:', err);
      throw err;
    }
  }, []);

  const applyPreset = useCallback(async (presetId) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await locationService.applyPreset(presetId);
      
      // Convert the preset response to our location selection format
      const newSelection = {
        cities: {},
        total_selected: 0,
        estimated_duration: response.estimated_duration,
        last_updated: new Date().toISOString()
      };
      
      // Initialize cities from preset
      response.cities_selected.forEach(cityName => {
        if (locations?.cities?.[cityName]) {
          const cityData = locations.cities[cityName];
          newSelection.cities[cityName] = {
            name: cityName,
            coordinates: [cityData.lat || 0, cityData.lng || 0],
            selected: true,
            search_method: response.settings_applied?.default_method || 'standard',
            city_level_search: response.settings_applied?.city_level_only !== false,
            districts: {}
          };
          
          // Add districts if not city-level only
          if (!response.settings_applied?.city_level_only) {
            Object.entries(cityData.districts || {}).forEach(([districtName, districtData]) => {
              newSelection.cities[cityName].districts[districtName] = {
                name: districtName,
                coordinates: [districtData.lat || 0, districtData.lng || 0],
                selected: true,
                search_method: response.settings_applied?.default_method || 'standard'
              };
            });
          }
        }
      });
      
      // Calculate total selected
      newSelection.total_selected = Object.values(newSelection.cities).reduce((total, city) => {
        return total + (city.selected ? 1 : 0) + 
               Object.values(city.districts || {}).filter(d => d.selected).length;
      }, 0);
      
      setLocationSelection(newSelection);
      return response;
    } catch (err) {
      console.error('Failed to apply preset:', err);
      setError('Failed to apply preset');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [locations]);

  const getPresets = useCallback(async () => {
    try {
      return await locationService.getPresets();
    } catch (err) {
      console.error('Failed to get presets:', err);
      throw err;
    }
  }, []);

  const selectAllCities = useCallback(() => {
    if (!locations?.cities) return;
    
    const newSelection = { ...locationSelection };
    
    Object.entries(locations.cities).forEach(([cityName, cityData]) => {
      newSelection.cities[cityName] = {
        name: cityName,
        coordinates: [cityData.lat || 0, cityData.lng || 0],
        selected: true,
        search_method: 'standard',
        city_level_search: true,
        districts: {}
      };
      
      // Also select all districts
      Object.entries(cityData.districts || {}).forEach(([districtName, districtData]) => {
        newSelection.cities[cityName].districts[districtName] = {
          name: districtName,
          coordinates: [districtData.lat || 0, districtData.lng || 0],
          selected: true,
          search_method: 'standard'
        };
      });
    });
    
    // Update totals
    newSelection.total_selected = Object.values(newSelection.cities).reduce((total, city) => {
      return total + (city.selected ? 1 : 0) + 
             Object.values(city.districts || {}).filter(d => d.selected).length;
    }, 0);
    
    newSelection.last_updated = new Date().toISOString();
    setLocationSelection(newSelection);
  }, [locations, locationSelection]);

  const deselectAll = useCallback(() => {
    const newSelection = {
      cities: {},
      total_selected: 0,
      estimated_duration: null,
      last_updated: new Date().toISOString()
    };
    setLocationSelection(newSelection);
  }, []);

  const selectMajorCities = useCallback(() => {
    if (!locations?.cities) return;
    
    const majorCities = [
      'İstanbul', 'Ankara', 'İzmir', 'Bursa', 'Antalya', 
      'Adana', 'Konya', 'Gaziantep', 'Kayseri', 'Mersin',
      'Eskişehir', 'Diyarbakır', 'Samsun', 'Denizli', 'Şanlıurfa'
    ];
    
    const newSelection = { ...locationSelection };
    
    // Clear existing selection
    newSelection.cities = {};
    
    majorCities.forEach(cityName => {
      if (locations.cities[cityName]) {
        const cityData = locations.cities[cityName];
        newSelection.cities[cityName] = {
          name: cityName,
          coordinates: [cityData.lat || 0, cityData.lng || 0],
          selected: true,
          search_method: 'standard',
          city_level_search: true,
          districts: {}
        };
      }
    });
    
    // Update totals
    newSelection.total_selected = Object.values(newSelection.cities).filter(c => c.selected).length;
    newSelection.last_updated = new Date().toISOString();
    setLocationSelection(newSelection);
  }, [locations, locationSelection]);

  const getSelectionStats = useCallback(() => {
    if (!locationSelection?.cities) return { cities: 0, districts: 0, total: 0 };
    
    const cities = Object.values(locationSelection.cities).filter(c => c.selected).length;
    const districts = Object.values(locationSelection.cities).reduce((total, city) => {
      return total + Object.values(city.districts || {}).filter(d => d.selected).length;
    }, 0);
    
    return { cities, districts, total: cities + districts };
  }, [locationSelection]);

  return {
    locations,
    locationSelection,
    loading,
    error,
    updateLocationSelection,
    loadLocations,
    estimateDuration,
    applyBatchOperation,
    applyPreset,
    getPresets,
    selectAllCities,
    deselectAll,
    selectMajorCities,
    getSelectionStats,
    clearError: () => setError(null)
  };
};

export default useLocations;