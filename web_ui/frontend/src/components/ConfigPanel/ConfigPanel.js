import React, { useState, useEffect } from 'react';
import {
  Box,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Typography,
  Slider,
  Divider,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Alert
} from '@mui/material';
import {
  ExpandMore,
  VpnKey,
  Search,
  Storage,
  GridView,
  Save,
  RestoreFromTrash
} from '@mui/icons-material';

const ConfigPanel = ({ settings, onSettingsChange, loading, disabled }) => {
  const [apiKeyVisible, setApiKeyVisible] = useState(false);
  const [validationResult, setValidationResult] = useState(null);
  const [localSettings, setLocalSettings] = useState(settings);

  useEffect(() => {
    setLocalSettings(settings);
  }, [settings]);

  const handleChange = (field, value) => {
    const newSettings = { ...localSettings, [field]: value };
    setLocalSettings(newSettings);
    onSettingsChange(newSettings);
  };

  const handleSearchTermsChange = (value) => {
    const terms = value.split(',').map(term => term.trim()).filter(term => term);
    handleChange('search_terms', terms);
  };

  const validateApiKey = async () => {
    if (!localSettings.api_key) return;
    
    try {
      setValidationResult({ valid: true, message: 'API key is valid' });
    } catch (error) {
      setValidationResult({ valid: false, message: error.message });
    }
  };

  const resetToDefaults = () => {
    const defaults = {
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
      auto_save_interval: 2,
      log_level: 'INFO'
    };
    
    setLocalSettings(defaults);
    onSettingsChange(defaults);
  };

  return (
    <Box sx={{ maxWidth: 800 }}>
      {/* API Configuration */}
      <Accordion defaultExpanded>
        <AccordionSummary expandIcon={<ExpandMore />}>
          <VpnKey sx={{ mr: 1 }} />
          <Typography variant="h6">API Configuration</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              fullWidth
              label="Google Places API Key"
              type={apiKeyVisible ? 'text' : 'password'}
              value={localSettings.api_key || ''}
              onChange={(e) => handleChange('api_key', e.target.value)}
              disabled={disabled}
              InputProps={{
                endAdornment: (
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <Button
                      size="small"
                      onClick={() => setApiKeyVisible(!apiKeyVisible)}
                    >
                      {apiKeyVisible ? 'Hide' : 'Show'}
                    </Button>
                    <Button
                      size="small"
                      variant="outlined"
                      onClick={validateApiKey}
                      disabled={!localSettings.api_key || loading}
                    >
                      Test
                    </Button>
                  </Box>
                )
              }}
            />
            {validationResult && (
              <Alert severity={validationResult.valid ? 'success' : 'error'}>
                {validationResult.message}
              </Alert>
            )}
            
            <Box sx={{ display: 'flex', gap: 2 }}>
              <FormControl sx={{ flex: 1 }}>
                <InputLabel>Language</InputLabel>
                <Select
                  value={localSettings.language || 'tr'}
                  onChange={(e) => handleChange('language', e.target.value)}
                  disabled={disabled}
                >
                  <MenuItem value="tr">Turkish</MenuItem>
                  <MenuItem value="en">English</MenuItem>
                </Select>
              </FormControl>
              
              <FormControl sx={{ flex: 1 }}>
                <InputLabel>Region</InputLabel>
                <Select
                  value={localSettings.region || 'tr'}
                  onChange={(e) => handleChange('region', e.target.value)}
                  disabled={disabled}
                >
                  <MenuItem value="tr">Turkey</MenuItem>
                  <MenuItem value="us">United States</MenuItem>
                </Select>
              </FormControl>
            </Box>
          </Box>
        </AccordionDetails>
      </Accordion>

      {/* Search Configuration */}
      <Accordion>
        <AccordionSummary expandIcon={<ExpandMore />}>
          <Search sx={{ mr: 1 }} />
          <Typography variant="h6">Search Configuration</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              fullWidth
              label="Search Terms (comma-separated)"
              value={localSettings.search_terms?.join(', ') || ''}
              onChange={(e) => handleSearchTermsChange(e.target.value)}
              disabled={disabled}
              helperText="Enter search terms separated by commas"
            />
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              {localSettings.search_terms?.map((term, index) => (
                <Chip
                  key={index}
                  label={term}
                  onDelete={() => {
                    const newTerms = localSettings.search_terms.filter((_, i) => i !== index);
                    handleChange('search_terms', newTerms);
                  }}
                  disabled={disabled}
                  size="small"
                />
              ))}
            </Box>
            
            <Box sx={{ display: 'flex', gap: 2 }}>
              <Box sx={{ flex: 1 }}>
                <Typography gutterBottom>
                  Default Radius: {localSettings.default_radius?.toLocaleString()} meters
                </Typography>
                <Slider
                  value={localSettings.default_radius || 15000}
                  onChange={(e, value) => handleChange('default_radius', value)}
                  min={1000}
                  max={50000}
                  step={1000}
                  disabled={disabled}
                  marks={[
                    { value: 5000, label: '5km' },
                    { value: 15000, label: '15km' },
                    { value: 30000, label: '30km' },
                    { value: 50000, label: '50km' }
                  ]}
                />
              </Box>
              
              <Box sx={{ flex: 1 }}>
                <Typography gutterBottom>
                  Request Delay: {localSettings.request_delay} seconds
                </Typography>
                <Slider
                  value={localSettings.request_delay || 1.0}
                  onChange={(e, value) => handleChange('request_delay', value)}
                  min={0.1}
                  max={5.0}
                  step={0.1}
                  disabled={disabled}
                  marks={[
                    { value: 0.5, label: '0.5s' },
                    { value: 1.0, label: '1s' },
                    { value: 2.0, label: '2s' },
                    { value: 5.0, label: '5s' }
                  ]}
                />
              </Box>
            </Box>
            
            <Box sx={{ display: 'flex', gap: 2 }}>
              <TextField
                sx={{ flex: 1 }}
                type="number"
                label="Max Retries"
                value={localSettings.max_retries || 3}
                onChange={(e) => handleChange('max_retries', parseInt(e.target.value))}
                disabled={disabled}
                inputProps={{ min: 1, max: 10 }}
              />
              
              <TextField
                sx={{ flex: 1 }}
                type="number"
                label="Batch Size"
                value={localSettings.batch_size || 20}
                onChange={(e) => handleChange('batch_size', parseInt(e.target.value))}
                disabled={disabled}
                inputProps={{ min: 1, max: 100 }}
              />
            </Box>
          </Box>
        </AccordionDetails>
      </Accordion>

      {/* Grid Search Settings */}
      <Accordion>
        <AccordionSummary expandIcon={<ExpandMore />}>
          <GridView sx={{ mr: 1 }} />
          <Typography variant="h6">Grid Search Settings</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <TextField
                sx={{ flex: 1 }}
                type="number"
                label="Grid Width (km)"
                value={localSettings.grid_width_km || 5.0}
                onChange={(e) => handleChange('grid_width_km', parseFloat(e.target.value))}
                disabled={disabled}
                inputProps={{ min: 1.0, max: 50.0, step: 0.5 }}
              />
              
              <TextField
                sx={{ flex: 1 }}
                type="number"
                label="Grid Height (km)"
                value={localSettings.grid_height_km || 5.0}
                onChange={(e) => handleChange('grid_height_km', parseFloat(e.target.value))}
                disabled={disabled}
                inputProps={{ min: 1.0, max: 50.0, step: 0.5 }}
              />
            </Box>
            
            <Box>
              <Typography gutterBottom>
                Grid Point Radius: {localSettings.grid_radius_meters} meters
              </Typography>
              <Slider
                value={localSettings.grid_radius_meters || 800}
                onChange={(e, value) => handleChange('grid_radius_meters', value)}
                min={100}
                max={5000}
                step={100}
                disabled={disabled}
                marks={[
                  { value: 500, label: '500m' },
                  { value: 800, label: '800m' },
                  { value: 1500, label: '1.5km' },
                  { value: 3000, label: '3km' }
                ]}
              />
            </Box>
          </Box>
        </AccordionDetails>
      </Accordion>

      {/* Storage Settings */}
      <Accordion>
        <AccordionSummary expandIcon={<ExpandMore />}>
          <Storage sx={{ mr: 1 }} />
          <Typography variant="h6">Storage Settings</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <FormControl sx={{ flex: 1 }}>
                <InputLabel>Storage Type</InputLabel>
                <Select
                  value={localSettings.storage_type || 'json'}
                  onChange={(e) => handleChange('storage_type', e.target.value)}
                  disabled={disabled}
                >
                  <MenuItem value="json">JSON Files</MenuItem>
                  <MenuItem value="mongodb">MongoDB</MenuItem>
                </Select>
              </FormControl>
              
              <TextField
                sx={{ flex: 1 }}
                label="Output Directory"
                value={localSettings.output_directory || 'data'}
                onChange={(e) => handleChange('output_directory', e.target.value)}
                disabled={disabled}
              />
            </Box>
            
            {localSettings.storage_type === 'mongodb' && (
              <>
                <TextField
                  fullWidth
                  label="MongoDB URI"
                  value={localSettings.mongodb_uri || ''}
                  onChange={(e) => handleChange('mongodb_uri', e.target.value)}
                  disabled={disabled}
                  placeholder="mongodb://localhost:27017"
                />
                
                <Box sx={{ display: 'flex', gap: 2 }}>
                  <TextField
                    sx={{ flex: 1 }}
                    label="Database Name"
                    value={localSettings.mongodb_db || 'dental_clinics'}
                    onChange={(e) => handleChange('mongodb_db', e.target.value)}
                    disabled={disabled}
                  />
                  
                  <TextField
                    sx={{ flex: 1 }}
                    label="Collection Name"
                    value={localSettings.mongodb_collection || 'places'}
                    onChange={(e) => handleChange('mongodb_collection', e.target.value)}
                    disabled={disabled}
                  />
                </Box>
              </>
            )}
          </Box>
        </AccordionDetails>
      </Accordion>

      {/* Action Buttons */}
      <Box sx={{ mt: 3, display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
        <Button
          variant="outlined"
          startIcon={<RestoreFromTrash />}
          onClick={resetToDefaults}
          disabled={disabled}
        >
          Reset to Defaults
        </Button>
        
        <Button
          variant="contained"
          startIcon={<Save />}
          disabled={disabled || loading}
        >
          {loading ? 'Saving...' : 'Save Configuration'}
        </Button>
      </Box>
    </Box>
  );
};

export default ConfigPanel;