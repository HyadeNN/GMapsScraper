import React, { useState, useMemo } from 'react';
import {
  Box,
  Typography,
  TextField,
  InputAdornment,
  FormControlLabel,
  Checkbox,
  Chip,
  IconButton,
  Menu,
  MenuItem,
  Tooltip,
  Collapse,
  Button
} from '@mui/material';
import {
  Search,
  ExpandMore,
  ChevronRight,
  LocationCity,
  LocationOn,
  MoreVert,
  CheckBox,
  CheckBoxOutlineBlank,
  IndeterminateCheckBox,
  Settings as SettingsIcon
} from '@mui/icons-material';
// TreeView implementation using manual expansion - more flexible for our use case

const SearchMethodIcon = ({ method }) => {
  const icons = {
    standard: '📍',
    grid: '🔧',
    skip: '⏭️'
  };
  return <span style={{ marginLeft: 4 }}>{icons[method] || '📍'}</span>;
};

const LocationTree = ({ locations, selection, onSelectionChange, disabled = false }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedNodes, setExpandedNodes] = useState(['root']);
  const [contextMenu, setContextMenu] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);

  // Filter locations based on search query
  const filteredLocations = useMemo(() => {
    if (!searchQuery.trim() || !locations?.cities) return locations?.cities || {};
    
    const query = searchQuery.toLowerCase();
    const filtered = {};
    
    Object.entries(locations.cities).forEach(([cityName, cityData]) => {
      const cityMatches = cityName.toLowerCase().includes(query);
      const matchingDistricts = {};
      
      // Check districts
      Object.entries(cityData.districts || {}).forEach(([districtName, districtData]) => {
        if (districtName.toLowerCase().includes(query)) {
          matchingDistricts[districtName] = districtData;
        }
      });
      
      // Include city if it matches or has matching districts
      if (cityMatches || Object.keys(matchingDistricts).length > 0) {
        filtered[cityName] = {
          ...cityData,
          districts: cityMatches ? cityData.districts : matchingDistricts
        };
      }
    });
    
    return filtered;
  }, [locations, searchQuery]);

  // Calculate checkbox states
  const getCheckboxState = (cityName, districtName = null) => {
    if (!selection?.cities) return 'unchecked';
    
    if (districtName) {
      // District checkbox
      const district = selection.cities[cityName]?.districts?.[districtName];
      return district?.selected ? 'checked' : 'unchecked';
    } else {
      // City checkbox
      const city = selection.cities[cityName];
      if (!city) return 'unchecked';
      
      const citySelected = city.selected;
      const districts = Object.values(city.districts || {});
      const selectedDistricts = districts.filter(d => d.selected).length;
      
      if (citySelected && selectedDistricts === districts.length) {
        return 'checked';
      } else if (citySelected || selectedDistricts > 0) {
        return 'indeterminate';
      } else {
        return 'unchecked';
      }
    }
  };

  // Handle checkbox changes
  const handleSelectionChange = (cityName, districtName = null, checked) => {
    if (disabled) return;
    
    const newSelection = { ...selection };
    
    if (!newSelection.cities) newSelection.cities = {};
    if (!newSelection.cities[cityName]) {
      const cityData = locations.cities[cityName];
      newSelection.cities[cityName] = {
        name: cityName,
        coordinates: [cityData?.lat || 0, cityData?.lng || 0],
        selected: false,
        search_method: 'standard',
        city_level_search: true,
        districts: {}
      };
    }
    
    if (districtName) {
      // District selection
      if (!newSelection.cities[cityName].districts[districtName]) {
        const districtData = locations.cities[cityName]?.districts?.[districtName];
        newSelection.cities[cityName].districts[districtName] = {
          name: districtName,
          coordinates: [districtData?.lat || 0, districtData?.lng || 0],
          selected: false,
          search_method: 'standard'
        };
      }
      newSelection.cities[cityName].districts[districtName].selected = checked;
    } else {
      // City selection
      newSelection.cities[cityName].selected = checked;
      
      // If selecting city, also select/deselect all districts
      Object.keys(newSelection.cities[cityName].districts || {}).forEach(district => {
        newSelection.cities[cityName].districts[district].selected = checked;
      });
      
      // If deselecting city, also deselect city-level search for clarity
      if (!checked) {
        Object.keys(locations.cities[cityName]?.districts || {}).forEach(districtName => {
          if (!newSelection.cities[cityName].districts[districtName]) {
            const districtData = locations.cities[cityName].districts[districtName];
            newSelection.cities[cityName].districts[districtName] = {
              name: districtName,
              coordinates: [districtData?.lat || 0, districtData?.lng || 0],
              selected: false,
              search_method: 'standard'
            };
          }
        });
      }
    }
    
    // Update totals
    newSelection.total_selected = Object.values(newSelection.cities).reduce((total, city) => {
      return total + (city.selected ? 1 : 0) + 
             Object.values(city.districts || {}).filter(d => d.selected).length;
    }, 0);
    
    newSelection.last_updated = new Date().toISOString();
    
    onSelectionChange(newSelection);
  };

  // Handle search method change
  const handleSearchMethodChange = (cityName, districtName, method) => {
    if (disabled) return;
    
    const newSelection = { ...selection };
    
    if (districtName) {
      if (newSelection.cities[cityName]?.districts?.[districtName]) {
        newSelection.cities[cityName].districts[districtName].search_method = method;
      }
    } else {
      if (newSelection.cities[cityName]) {
        newSelection.cities[cityName].search_method = method;
      }
    }
    
    onSelectionChange(newSelection);
  };

  // Context menu handlers
  const handleContextMenu = (event, cityName, districtName = null) => {
    event.preventDefault();
    if (disabled) return;
    
    setContextMenu({
      mouseX: event.clientX - 2,
      mouseY: event.clientY - 4,
      cityName,
      districtName
    });
    setSelectedNode({ cityName, districtName });
  };

  const handleContextMenuClose = () => {
    setContextMenu(null);
    setSelectedNode(null);
  };

  const handleBatchOperation = (operation) => {
    if (disabled || !selectedNode) return;
    
    const { cityName, districtName } = selectedNode;
    
    switch (operation) {
      case 'select_all':
        if (!districtName) {
          // Select city and all districts
          handleSelectionChange(cityName, null, true);
        }
        break;
        
      case 'deselect_all':
        if (!districtName) {
          // Deselect city and all districts  
          handleSelectionChange(cityName, null, false);
        }
        break;
        
      case 'set_standard':
        handleSearchMethodChange(cityName, districtName, 'standard');
        break;
        
      case 'set_grid':
        handleSearchMethodChange(cityName, districtName, 'grid');
        break;
        
      case 'set_skip':
        handleSearchMethodChange(cityName, districtName, 'skip');
        break;
    }
    
    handleContextMenuClose();
  };

  // Get selection statistics
  const getSelectionStats = () => {
    if (!selection?.cities) return { cities: 0, districts: 0 };
    
    const cities = Object.values(selection.cities).filter(c => c.selected).length;
    const districts = Object.values(selection.cities).reduce((total, city) => {
      return total + Object.values(city.districts || {}).filter(d => d.selected).length;
    }, 0);
    
    return { cities, districts };
  };

  const stats = getSelectionStats();

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Search and Stats */}
      <Box sx={{ mb: 2 }}>
        <TextField
          fullWidth
          size="small"
          placeholder="Search cities and districts..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <Search />
              </InputAdornment>
            ),
          }}
          disabled={disabled}
        />
        
        <Box sx={{ mt: 1, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          <Chip 
            label={`${stats.cities} cities`} 
            size="small" 
            color={stats.cities > 0 ? 'primary' : 'default'}
          />
          <Chip 
            label={`${stats.districts} districts`} 
            size="small" 
            color={stats.districts > 0 ? 'primary' : 'default'}
          />
        </Box>
      </Box>

      {/* Tree View */}
      <Box sx={{ flex: 1, overflow: 'auto' }}>
        {Object.keys(filteredLocations).length === 0 ? (
          <Typography variant="body2" color="text.secondary" align="center" sx={{ mt: 2 }}>
            {searchQuery ? 'No locations found' : 'No location data available'}
          </Typography>
        ) : (
          Object.entries(filteredLocations).map(([cityName, cityData]) => {
            const checkboxState = getCheckboxState(cityName);
            const isExpanded = expandedNodes.includes(cityName);
            const citySelection = selection?.cities?.[cityName];
            const searchMethod = citySelection?.search_method || 'standard';
            
            return (
              <Box key={cityName} sx={{ mb: 1 }}>
                {/* City Row */}
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    p: 0.5,
                    borderRadius: 1,
                    '&:hover': { bgcolor: 'action.hover' },
                    cursor: disabled ? 'not-allowed' : 'pointer'
                  }}
                  onContextMenu={(e) => handleContextMenu(e, cityName)}
                >
                  <IconButton
                    size="small"
                    onClick={() => {
                      if (isExpanded) {
                        setExpandedNodes(prev => prev.filter(n => n !== cityName));
                      } else {
                        setExpandedNodes(prev => [...prev, cityName]);
                      }
                    }}
                    disabled={disabled}
                  >
                    {isExpanded ? <ExpandMore /> : <ChevronRight />}
                  </IconButton>
                  
                  <Checkbox
                    checked={checkboxState === 'checked'}
                    indeterminate={checkboxState === 'indeterminate'}
                    onChange={(e) => handleSelectionChange(cityName, null, e.target.checked)}
                    disabled={disabled}
                    size="small"
                  />
                  
                  <LocationCity sx={{ mr: 1, color: 'primary.main' }} />
                  
                  <Typography variant="body2" sx={{ flex: 1, fontWeight: 'medium' }}>
                    {cityName}
                  </Typography>
                  
                  <SearchMethodIcon method={searchMethod} />
                  
                  <Tooltip title="Options">
                    <IconButton
                      size="small"
                      onClick={(e) => handleContextMenu(e, cityName)}
                      disabled={disabled}
                    >
                      <MoreVert fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </Box>
                
                {/* Districts */}
                <Collapse in={isExpanded}>
                  <Box sx={{ ml: 4 }}>
                    {Object.entries(cityData.districts || {}).map(([districtName, districtData]) => {
                      const districtCheckboxState = getCheckboxState(cityName, districtName);
                      const districtSelection = selection?.cities?.[cityName]?.districts?.[districtName];
                      const districtSearchMethod = districtSelection?.search_method || 'standard';
                      
                      return (
                        <Box
                          key={districtName}
                          sx={{
                            display: 'flex',
                            alignItems: 'center',
                            p: 0.5,
                            borderRadius: 1,
                            '&:hover': { bgcolor: 'action.hover' },
                            cursor: disabled ? 'not-allowed' : 'pointer'
                          }}
                          onContextMenu={(e) => handleContextMenu(e, cityName, districtName)}
                        >
                          <Box sx={{ width: 32 }} /> {/* Spacer for alignment */}
                          
                          <Checkbox
                            checked={districtCheckboxState === 'checked'}
                            onChange={(e) => handleSelectionChange(cityName, districtName, e.target.checked)}
                            disabled={disabled}
                            size="small"
                          />
                          
                          <LocationOn sx={{ mr: 1, color: 'secondary.main', fontSize: '1.1rem' }} />
                          
                          <Typography variant="body2" sx={{ flex: 1 }}>
                            {districtName}
                          </Typography>
                          
                          <SearchMethodIcon method={districtSearchMethod} />
                          
                          <Tooltip title="Options">
                            <IconButton
                              size="small"
                              onClick={(e) => handleContextMenu(e, cityName, districtName)}
                              disabled={disabled}
                            >
                              <MoreVert fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        </Box>
                      );
                    })}
                  </Box>
                </Collapse>
              </Box>
            );
          })
        )}
      </Box>

      {/* Context Menu */}
      <Menu
        open={contextMenu !== null}
        onClose={handleContextMenuClose}
        anchorReference="anchorPosition"
        anchorPosition={
          contextMenu !== null
            ? { top: contextMenu.mouseY, left: contextMenu.mouseX }
            : undefined
        }
      >
        {!selectedNode?.districtName && (
          [
            <MenuItem key="select-all" onClick={() => handleBatchOperation('select_all')}>
              <CheckBox sx={{ mr: 1 }} /> Select All Sublocations
            </MenuItem>,
            <MenuItem key="deselect-all" onClick={() => handleBatchOperation('deselect_all')}>
              <CheckBoxOutlineBlank sx={{ mr: 1 }} /> Deselect All Sublocations
            </MenuItem>
          ]
        )}
        <MenuItem onClick={() => handleBatchOperation('set_standard')}>
          📍 Set to Standard Search
        </MenuItem>
        <MenuItem onClick={() => handleBatchOperation('set_grid')}>
          🔧 Set to Grid Search
        </MenuItem>
        <MenuItem onClick={() => handleBatchOperation('set_skip')}>
          ⏭️ Set to Skip
        </MenuItem>
      </Menu>
    </Box>
  );
};

export default LocationTree;