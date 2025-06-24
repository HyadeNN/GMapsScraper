import React, { useState, useEffect, memo, useCallback } from 'react';
import {
  Box,
  AppBar,
  Toolbar,
  Typography,
  Button,
  Chip,
  Grid,
  Paper,
  Divider
} from '@mui/material';
import {
  PlayArrow,
  Pause,
  Stop,
  Settings,
  Assessment
} from '@mui/icons-material';
import LocationTree from '../LocationTree/LocationTreeOptimized';
import ConfigPanel from '../ConfigPanel/ConfigPanel';
import ProgressPanel from '../ProgressPanel/ProgressPanel';
import ProfileManager from '../ProfileManager/ProfileManager';
import useWebSocket from '../../hooks/useWebSocket';
import useSettings from '../../hooks/useSettings';
import useLocations from '../../hooks/useLocations';
import useScraper from '../../hooks/useScraper';

const MainLayout = memo(() => {
  const [selectedProfile, setSelectedProfile] = useState(null);
  
  // Custom hooks for state management
  const { settings, updateSettings, loading: settingsLoading } = useSettings();
  const { locations, locationSelection, updateLocationSelection } = useLocations();
  const { 
    scraperStatus, 
    progress, 
    startScraping, 
    pauseScraping, 
    stopScraping,
    loading: scraperLoading 
  } = useScraper();
  
  // WebSocket connection for real-time updates
  const { connectionStatus, logs } = useWebSocket();

  const handleStartScraping = async () => {
    if (!settings.api_key) {
      alert('Please set your Google Places API key in settings');
      return;
    }
    
    if (!locationSelection || Object.keys(locationSelection.cities).length === 0) {
      alert('Please select at least one location to scrape');
      return;
    }

    try {
      await startScraping({
        settings,
        locations: locationSelection
      });
    } catch (error) {
      console.error('Failed to start scraping:', error);
      alert('Failed to start scraping: ' + error.message);
    }
  };

  const handlePauseScraping = async () => {
    try {
      await pauseScraping();
    } catch (error) {
      console.error('Failed to pause scraping:', error);
    }
  };

  const handleStopScraping = async () => {
    try {
      await stopScraping();
    } catch (error) {
      console.error('Failed to stop scraping:', error);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'running': return 'success';
      case 'paused': return 'warning';
      case 'error': return 'error';
      case 'completed': return 'info';
      default: return 'default';
    }
  };

  const canStart = !scraperLoading && scraperStatus?.can_start;
  const canPause = !scraperLoading && scraperStatus?.can_pause;
  const canStop = !scraperLoading && scraperStatus?.can_stop;

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <AppBar position="static" elevation={1}>
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Google Maps Scraper
          </Typography>
          
          {/* Connection Status */}
          <Chip
            label={`API: ${connectionStatus}`}
            color={connectionStatus === 'connected' ? 'success' : 'default'}
            size="small"
            sx={{ mr: 2 }}
          />
          
          {/* Scraper Status */}
          <Chip
            label={`Status: ${progress?.status || 'idle'}`}
            color={getStatusColor(progress?.status)}
            size="small"
            sx={{ mr: 2 }}
          />
          
          {/* Control Buttons */}
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button
              variant="contained"
              color="success"
              startIcon={<PlayArrow />}
              onClick={handleStartScraping}
              disabled={!canStart}
              size="small"
            >
              Start
            </Button>
            <Button
              variant="contained"
              color="warning"
              startIcon={<Pause />}
              onClick={handlePauseScraping}
              disabled={!canPause}
              size="small"
            >
              Pause
            </Button>
            <Button
              variant="contained"
              color="error"
              startIcon={<Stop />}
              onClick={handleStopScraping}
              disabled={!canStop}
              size="small"
            >
              Stop
            </Button>
          </Box>
        </Toolbar>
      </AppBar>

      {/* Main Content - 3 Panel Layout */}
      <Box sx={{ flex: 1, overflow: 'hidden' }}>
        <Box sx={{ display: 'flex', height: '100%', overflow: 'hidden' }}>
          {/* Left Panel - Location Tree */}
          <Box sx={{ width: '25%', borderRight: 1, borderColor: 'divider', overflow: 'hidden' }}>
            <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
              {/* Profile Manager */}
              <Box sx={{ flexShrink: 0, maxHeight: '30%', overflow: 'hidden' }}>
                <Paper sx={{ m: 1, p: 2, height: '100%', display: 'flex', flexDirection: 'column' }} elevation={1}>
                  <Typography variant="h6" gutterBottom sx={{ flexShrink: 0 }}>
                    Profiles
                  </Typography>
                  <Box sx={{ flex: 1, overflow: 'auto', minHeight: 0 }}>
                    <ProfileManager
                      selectedProfile={selectedProfile}
                      onProfileSelect={setSelectedProfile}
                    />
                  </Box>
                </Paper>
              </Box>
              
              <Divider />
              
              {/* Location Tree */}
              <Box sx={{ flex: 1, overflow: 'hidden', m: 1, minHeight: 0 }}>
                <Paper sx={{ height: '100%', p: 2, display: 'flex', flexDirection: 'column' }} elevation={1}>
                  <Typography variant="h6" gutterBottom sx={{ flexShrink: 0 }}>
                    Location Selection
                  </Typography>
                  <Box sx={{ flex: 1, overflow: 'hidden', minHeight: 0 }}>
                    <LocationTree
                      locations={locations}
                      selection={locationSelection}
                      onSelectionChange={updateLocationSelection}
                      disabled={progress?.status === 'running'}
                    />
                  </Box>
                </Paper>
              </Box>
            </Box>
          </Box>

          {/* Center Panel - Settings */}
          <Box sx={{ flex: 1, overflow: 'hidden' }}>
            <Box sx={{ height: '100%', overflow: 'auto', p: 2 }}>
              <Paper sx={{ p: 3, mb: 2 }} elevation={1}>
                <Typography variant="h5" gutterBottom>
                  <Settings sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Configuration
                </Typography>
                <ConfigPanel
                  settings={settings}
                  onSettingsChange={updateSettings}
                  loading={settingsLoading}
                  disabled={progress?.status === 'running'}
                />
              </Paper>
            </Box>
          </Box>

          {/* Right Panel - Progress Dashboard */}
          <Box sx={{ width: '30%', borderLeft: 1, borderColor: 'divider' }}>
            <Box sx={{ height: '100%', overflow: 'hidden', m: 1 }}>
              <Paper sx={{ height: '100%', p: 2 }} elevation={1}>
                <Typography variant="h6" gutterBottom>
                  <Assessment sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Progress Dashboard
                </Typography>
                <ProgressPanel
                  progress={progress}
                  logs={logs}
                  scraperStatus={scraperStatus}
                />
              </Paper>
            </Box>
          </Box>
        </Box>
      </Box>
    </Box>
  );
});

MainLayout.displayName = 'MainLayout';

export default MainLayout;