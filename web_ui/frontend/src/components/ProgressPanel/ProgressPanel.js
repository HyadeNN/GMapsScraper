import React, { useState, useEffect, useRef, memo, useMemo } from 'react';
import {
  Box,
  Typography,
  LinearProgress,
  Chip,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  IconButton,
  Tooltip,
  Divider,
  Paper,
} from '@mui/material';
import {
  LocationOn,
  Timer,
  Speed,
  CheckCircle,
  Error,
  Clear,
  Refresh,
  Info,
  Warning,
  BugReport,
  CheckCircleOutline
} from '@mui/icons-material';

const LogMessage = memo(({ log }) => {
  const getLogIcon = (level) => {
    switch (level.toLowerCase()) {
      case 'success': return <CheckCircleOutline sx={{ color: 'success.main' }} />;
      case 'error': return <Error sx={{ color: 'error.main' }} />;
      case 'warning': return <Warning sx={{ color: 'warning.main' }} />;
      case 'debug': return <BugReport sx={{ color: 'info.main' }} />;
      default: return <Info sx={{ color: 'info.main' }} />;
    }
  };

  const getLogColor = (level) => {
    switch (level.toLowerCase()) {
      case 'success': return 'success.main';
      case 'error': return 'error.main';
      case 'warning': return 'warning.main';
      case 'debug': return 'info.main';
      default: return 'text.primary';
    }
  };

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  return (
    <ListItem dense sx={{ py: 0.5 }}>
      <ListItemIcon sx={{ minWidth: 32 }}>
        {getLogIcon(log.level)}
      </ListItemIcon>
      <ListItemText
        primary={
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography variant="caption" sx={{ color: 'text.secondary' }}>
              [{formatTime(log.timestamp)}]
            </Typography>
            {log.location && (
              <Chip label={log.location} size="small" variant="outlined" />
            )}
          </Box>
        }
        secondary={
          <Typography variant="body2" sx={{ color: getLogColor(log.level) }}>
            {log.message}
          </Typography>
        }
      />
    </ListItem>
  );
});

LogMessage.displayName = 'LogMessage';

const ProgressPanel = memo(({ progress, logs, scraperStatus }) => {
  const [autoScroll, setAutoScroll] = useState(true);
  const logListRef = useRef(null);
  const [filteredLogs, setFilteredLogs] = useState(logs || []);
  const [logFilter, setLogFilter] = useState('all');

  useEffect(() => {
    setFilteredLogs(logs || []);
  }, [logs]);

  useEffect(() => {
    if (autoScroll && logListRef.current) {
      logListRef.current.scrollTop = logListRef.current.scrollHeight;
    }
  }, [filteredLogs, autoScroll]);

  const clearLogs = () => {
    setFilteredLogs([]);
  };

  const formatDuration = (seconds) => {
    if (!seconds) return 'N/A';
    
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
      return `${hours}h ${minutes}m ${secs}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${secs}s`;
    } else {
      return `${secs}s`;
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

  const getElapsedTime = () => {
    if (!progress?.start_time) return 'N/A';
    
    const start = new Date(progress.start_time);
    const now = new Date();
    const elapsed = Math.floor((now - start) / 1000);
    
    return formatDuration(elapsed);
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Current Status */}
      <Card sx={{ mb: 2 }} elevation={2}>
        <CardContent sx={{ pb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
            <Typography variant="h6">Current Status</Typography>
            <Chip 
              label={progress?.status || 'idle'} 
              color={getStatusColor(progress?.status)}
              size="small"
            />
          </Box>
          
          {progress?.status === 'running' || progress?.status === 'paused' ? (
            <>
              <Box sx={{ mb: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2">Progress</Typography>
                  <Typography variant="body2">
                    {progress.completed_locations || 0}/{progress.total_locations || 0} 
                    ({(progress.completion_percentage || 0).toFixed(1)}%)
                  </Typography>
                </Box>
                <LinearProgress 
                  variant="determinate" 
                  value={progress.completion_percentage || 0}
                  sx={{ height: 8, borderRadius: 4 }}
                />
              </Box>
              
              {progress.current_city && (
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <LocationOn sx={{ mr: 1, fontSize: '1rem', color: 'primary.main' }} />
                  <Typography variant="body2">
                    {progress.current_city}
                    {progress.current_district && ` / ${progress.current_district}`}
                  </Typography>
                  {progress.current_search_method && (
                    <Chip 
                      label={progress.current_search_method} 
                      size="small" 
                      variant="outlined"
                      sx={{ ml: 1 }}
                    />
                  )}
                </Box>
              )}
            </>
          ) : (
            <Typography variant="body2" color="text.secondary">
              {progress?.status === 'completed' ? 'Scraping completed successfully' : 'No active scraping operation'}
            </Typography>
          )}
        </CardContent>
      </Card>

      {/* Statistics */}
      <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1, mb: 2 }}>
        <Paper sx={{ p: 1.5, textAlign: 'center' }}>
          <Timer sx={{ color: 'primary.main', mb: 0.5 }} />
          <Typography variant="caption" display="block">Elapsed</Typography>
          <Typography variant="body2" fontWeight="bold">
            {getElapsedTime()}
          </Typography>
        </Paper>
        
        <Paper sx={{ p: 1.5, textAlign: 'center' }}>
          <Speed sx={{ color: 'secondary.main', mb: 0.5 }} />
          <Typography variant="caption" display="block">Speed</Typography>
          <Typography variant="body2" fontWeight="bold">
            {progress?.processing_speed || 'N/A'}
          </Typography>
        </Paper>
        
        <Paper sx={{ p: 1.5, textAlign: 'center' }}>
          <CheckCircle sx={{ color: 'success.main', mb: 0.5 }} />
          <Typography variant="caption" display="block">Results</Typography>
          <Typography variant="body2" fontWeight="bold">
            {(progress?.results_found || 0).toLocaleString()}
          </Typography>
        </Paper>
        
        <Paper sx={{ p: 1.5, textAlign: 'center' }}>
          <Error sx={{ color: 'error.main', mb: 0.5 }} />
          <Typography variant="caption" display="block">Errors</Typography>
          <Typography variant="body2" fontWeight="bold">
            {progress?.errors_encountered || 0}
          </Typography>
        </Paper>
      </Box>

      {/* Time Estimates */}
      {(progress?.estimated_time_remaining || progress?.processing_speed) && (
        <Card sx={{ mb: 2 }}>
          <CardContent sx={{ py: 1.5 }}>
            <Typography variant="subtitle2" gutterBottom>Time Estimates</Typography>
            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <Typography variant="body2">Remaining:</Typography>
              <Typography variant="body2" fontWeight="bold">
                {progress?.estimated_time_remaining || 'Calculating...'}
              </Typography>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Live Logs */}
      <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
          <Typography variant="h6">Live Logs</Typography>
          <Box>
            <Tooltip title="Auto-scroll">
              <IconButton
                size="small"
                color={autoScroll ? 'primary' : 'default'}
                onClick={() => setAutoScroll(!autoScroll)}
              >
                <Refresh />
              </IconButton>
            </Tooltip>
            <Tooltip title="Clear logs">
              <IconButton size="small" onClick={clearLogs}>
                <Clear />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>
        
        <Paper 
          ref={logListRef}
          sx={{ 
            flex: 1, 
            overflow: 'auto',
            minHeight: 200,
            maxHeight: 400,
            bgcolor: 'grey.50'
          }}
        >
          {filteredLogs.length === 0 ? (
            <Box sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="body2" color="text.secondary">
                No log messages yet
              </Typography>
            </Box>
          ) : (
            <List dense sx={{ py: 0 }}>
              {filteredLogs.map((log, index) => (
                <React.Fragment key={index}>
                  <LogMessage log={log} />
                  {index < filteredLogs.length - 1 && <Divider />}
                </React.Fragment>
              ))}
            </List>
          )}
        </Paper>
        
        {filteredLogs.length > 0 && (
          <Typography variant="caption" sx={{ mt: 0.5, textAlign: 'center', color: 'text.secondary' }}>
            {filteredLogs.length} log entries
          </Typography>
        )}
      </Box>
    </Box>
  );
});

ProgressPanel.displayName = 'ProgressPanel';

export default ProgressPanel;