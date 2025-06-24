import React, { useState, useMemo, useCallback, memo, startTransition } from 'react';
import {
  Box,
  Typography,
  TextField,
  InputAdornment,
  FormControlLabel,
  Checkbox,
  Chip,
  IconButton,
  Tooltip,
  Menu,
  MenuItem,
  Button,
  Divider,
  Collapse,
  ListItemIcon,
  ListItemText
} from '@mui/material';
import {
  Search,
  ExpandMore,
  ExpandLess,
  LocationOn,
  SelectAll,
  Clear,
  FilterList,
  GridView,
  MapOutlined,
  SkipNext,
  MoreVert,
  LocationCity
} from '@mui/icons-material';
import debounce from 'lodash.debounce';

// Memoized search method icon component
const SearchMethodIcon = memo(({ method }) => {
  const icons = {
    standard: '📍',
    grid: '🔧',
    skip: '⏭️'
  };
  return <span style={{ marginLeft: 4 }}>{icons[method] || '📍'}</span>;
});

SearchMethodIcon.displayName = 'SearchMethodIcon';

// Memoized district item component
const DistrictItem = memo(({ 
  cityName, 
  districtName, 
  districtData, 
  checkboxState, 
  onDistrictChange, 
  searchMethod,
  disabled 
}) => {
  const handleChange = useCallback((event) => {
    onDistrictChange(cityName, districtName, event.target.checked);
  }, [cityName, districtName, onDistrictChange]);

  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        pl: 4,
        py: 0.5,
        '&:hover': { backgroundColor: 'action.hover' },
      }}
    >
      <FormControlLabel
        sx={{ flex: 1 }}
        control={
          <Checkbox
            checked={checkboxState === 'checked'}
            indeterminate={checkboxState === 'indeterminate'}
            onChange={handleChange}
            disabled={disabled}
            size="small"
          />
        }
        label={
          <Typography variant="body2">
            {districtName}
            <SearchMethodIcon method={searchMethod} />
          </Typography>
        }
      />
      <Typography variant="caption" color="text.secondary">
        {districtData.location_count || 0} locations
      </Typography>
    </Box>
  );
});

DistrictItem.displayName = 'DistrictItem';

// Memoized city item component
const CityItem = memo(({ 
  cityName, 
  cityData, 
  checkboxState, 
  isExpanded, 
  onToggleExpand, 
  onCityChange, 
  onDistrictChange,
  searchMethod,
  selection,
  disabled,
  onContextMenu 
}) => {
  const handleCityChange = useCallback((event) => {
    onCityChange(cityName, event.target.checked);
  }, [cityName, onCityChange]);

  const handleToggle = useCallback(() => {
    onToggleExpand(cityName);
  }, [cityName, onToggleExpand]);

  const handleContextMenu = useCallback((event) => {
    onContextMenu(event, cityName);
  }, [cityName, onContextMenu]);

  const citySelection = selection?.cities?.[cityName];

  return (
    <Box sx={{ mb: 1 }}>
      {/* City Row */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          py: 0.5,
          px: 1,
          borderRadius: 1,
          '&:hover': { backgroundColor: 'action.hover' },
          backgroundColor: checkboxState !== 'unchecked' ? 'action.selected' : 'transparent',
        }}
        onContextMenu={handleContextMenu}
      >
        <IconButton size="small" onClick={handleToggle}>
          {isExpanded ? <ExpandLess /> : <ExpandMore />}
        </IconButton>
        
        <Checkbox
          checked={checkboxState === 'checked'}
          indeterminate={checkboxState === 'indeterminate'}
          onChange={handleCityChange}
          disabled={disabled}
          size="small"
        />
        
        <LocationCity sx={{ mr: 1, color: 'primary.main' }} />
        
        <Typography variant="body2" sx={{ flex: 1, fontWeight: 'medium' }}>
          {cityName}
        </Typography>
        
        <SearchMethodIcon method={searchMethod} />
        
        <Typography variant="caption" color="text.secondary" sx={{ mx: 1 }}>
          {cityData.district_count || 0} districts
        </Typography>
        
        <Tooltip title="Options">
          <IconButton
            size="small"
            onClick={handleContextMenu}
            disabled={disabled}
          >
            <MoreVert fontSize="small" />
          </IconButton>
        </Tooltip>
      </Box>

      {/* Districts */}
      <Collapse in={isExpanded} timeout="auto" unmountOnExit>
        {cityData.districts && Object.entries(cityData.districts).map(([districtName, districtData]) => {
          const districtCheckboxState = checkboxState === 'checked' ? 'checked' : 
            (citySelection?.districts?.[districtName] ? 'checked' : 'unchecked');
          const districtSearchMethod = citySelection?.districts?.[districtName]?.search_method || searchMethod;

          return (
            <DistrictItem
              key={districtName}
              cityName={cityName}
              districtName={districtName}
              districtData={districtData}
              checkboxState={districtCheckboxState}
              onDistrictChange={onDistrictChange}
              searchMethod={districtSearchMethod}
              disabled={disabled}
            />
          );
        })}
      </Collapse>
    </Box>
  );
});

CityItem.displayName = 'CityItem';

const LocationTree = memo(({ locations, selection, onSelectionChange, disabled = false }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedNodes, setExpandedNodes] = useState(['root']);
  const [contextMenu, setContextMenu] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);

  // Debounced search handler
  const debouncedSearch = useMemo(
    () => debounce((value) => {
      startTransition(() => {
        setSearchQuery(value);
      });
    }, 300),
    []
  );

  const handleSearchChange = useCallback((event) => {
    debouncedSearch(event.target.value);
  }, [debouncedSearch]);

  // Filter locations based on search query - with memoization
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

  // Calculate checkbox states - memoized
  const getCheckboxState = useCallback((cityName, districtName = null) => {
    if (!selection?.cities) return 'unchecked';
    
    const citySelection = selection.cities[cityName];
    if (!citySelection) return 'unchecked';
    
    if (districtName) {
      return citySelection.districts?.[districtName] ? 'checked' : 'unchecked';
    }
    
    // For city: check if all districts are selected
    const districtCount = locations?.cities?.[cityName]?.district_count || 0;
    const selectedDistrictCount = Object.keys(citySelection.districts || {}).length;
    
    if (selectedDistrictCount === 0) return 'unchecked';
    if (selectedDistrictCount === districtCount) return 'checked';
    return 'indeterminate';
  }, [selection, locations]);

  // Memoized handlers
  const handleCityChange = useCallback((cityName, checked) => {
    startTransition(() => {
      const newSelection = { ...selection };
      
      if (checked) {
        // Select city (without necessarily selecting all districts)
        if (!newSelection.cities[cityName]) {
          newSelection.cities[cityName] = {
            search_method: 'standard',
            districts: {}
          };
        }
      } else {
        // Deselect the city and all its districts
        delete newSelection.cities[cityName];
      }
      
      onSelectionChange(newSelection);
    });
  }, [selection, onSelectionChange]);

  const handleDistrictChange = useCallback((cityName, districtName, checked) => {
    startTransition(() => {
      const newSelection = { ...selection };
      
      if (checked) {
        // Ensure city exists in selection
        if (!newSelection.cities[cityName]) {
          newSelection.cities[cityName] = {
            search_method: 'standard',
            districts: {}
          };
        }
        
        // Add district
        newSelection.cities[cityName].districts[districtName] = {
          search_method: 'standard'
        };
      } else {
        // Remove district
        if (newSelection.cities[cityName]?.districts) {
          delete newSelection.cities[cityName].districts[districtName];
          
          // If no districts left, remove city
          if (Object.keys(newSelection.cities[cityName].districts).length === 0) {
            delete newSelection.cities[cityName];
          }
        }
      }
      
      onSelectionChange(newSelection);
    });
  }, [selection, onSelectionChange]);

  const toggleNode = useCallback((nodeId) => {
    setExpandedNodes(prev => 
      prev.includes(nodeId)
        ? prev.filter(id => id !== nodeId)
        : [...prev, nodeId]
    );
  }, []);

  const handleSelectAllCities = useCallback(() => {
    startTransition(() => {
      const newSelection = { cities: {} };
      
      Object.entries(locations.cities || {}).forEach(([cityName, cityData]) => {
        // Select only cities, not districts
        newSelection.cities[cityName] = {
          search_method: 'standard',
          districts: {}
        };
      });
      
      onSelectionChange(newSelection);
    });
  }, [locations, onSelectionChange]);

  const handleSelectAllWithDistricts = useCallback(() => {
    startTransition(() => {
      const newSelection = { cities: {} };
      
      Object.entries(locations.cities || {}).forEach(([cityName, cityData]) => {
        newSelection.cities[cityName] = {
          search_method: 'standard',
          districts: {}
        };
        
        Object.keys(cityData.districts || {}).forEach(districtName => {
          newSelection.cities[cityName].districts[districtName] = {
            search_method: 'standard'
          };
        });
      });
      
      onSelectionChange(newSelection);
    });
  }, [locations, onSelectionChange]);

  const handleClearAll = useCallback(() => {
    startTransition(() => {
      onSelectionChange({ cities: {} });
    });
  }, [onSelectionChange]);

  const handleContextMenu = useCallback((event, nodeId) => {
    event.preventDefault();
    setSelectedNode(nodeId);
    setContextMenu({
      mouseX: event.clientX - 2,
      mouseY: event.clientY - 4,
    });
  }, []);

  const handleCloseContextMenu = useCallback(() => {
    setContextMenu(null);
    setSelectedNode(null);
  }, []);

  const handleBatchOperation = useCallback((operation) => {
    if (!selectedNode || !selection) return;
    
    startTransition(() => {
      const newSelection = { ...selection };
      
      switch (operation) {
        case 'select_all':
          // Select all districts in the city
          if (selectedNode && locations.cities[selectedNode]) {
            const cityData = locations.cities[selectedNode];
            newSelection.cities[selectedNode] = {
              search_method: 'standard',
              districts: {}
            };
            
            if (cityData.districts) {
              Object.keys(cityData.districts).forEach(districtName => {
                newSelection.cities[selectedNode].districts[districtName] = {
                  search_method: 'standard'
                };
              });
            }
          }
          break;
          
        case 'deselect_all':
          // Deselect all districts in the city
          if (selectedNode && newSelection.cities[selectedNode]) {
            delete newSelection.cities[selectedNode];
          }
          break;
          
        case 'set_standard':
        case 'set_grid':
        case 'set_skip':
          const method = operation.replace('set_', '');
          if (newSelection.cities[selectedNode]) {
            newSelection.cities[selectedNode].search_method = method;
            // Apply to all districts
            Object.keys(newSelection.cities[selectedNode].districts || {}).forEach(districtName => {
              newSelection.cities[selectedNode].districts[districtName].search_method = method;
            });
          }
          break;
      }
      
      onSelectionChange(newSelection);
      handleCloseContextMenu();
    });
  }, [selectedNode, selection, locations, onSelectionChange, handleCloseContextMenu]);

  // Calculate stats - memoized
  const stats = useMemo(() => {
    let cities = 0;
    let districts = 0;
    
    if (selection?.cities) {
      cities = Object.keys(selection.cities).length;
      Object.values(selection.cities).forEach(city => {
        districts += Object.keys(city.districts || {}).length;
      });
    }
    
    return { cities, districts };
  }, [selection]);

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Search and Controls */}
      <Box sx={{ mb: 2 }}>
        <TextField
          fullWidth
          size="small"
          placeholder="Search locations..."
          onChange={handleSearchChange}
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
              <CityItem
                key={cityName}
                cityName={cityName}
                cityData={cityData}
                checkboxState={checkboxState}
                isExpanded={isExpanded}
                onToggleExpand={toggleNode}
                onCityChange={handleCityChange}
                onDistrictChange={handleDistrictChange}
                searchMethod={searchMethod}
                selection={selection}
                disabled={disabled}
                onContextMenu={handleContextMenu}
              />
            );
          })
        )}
      </Box>

      {/* Batch Actions */}
      <Box sx={{ mt: 2 }}>
        <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
          <Button
            size="small"
            startIcon={<LocationCity />}
            onClick={handleSelectAllCities}
            disabled={disabled}
            variant="outlined"
          >
            Cities Only
          </Button>
          <Button
            size="small"
            startIcon={<SelectAll />}
            onClick={handleSelectAllWithDistricts}
            disabled={disabled}
            variant="outlined"
          >
            All + Districts
          </Button>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            size="small"
            startIcon={<Clear />}
            onClick={handleClearAll}
            disabled={disabled || stats.cities === 0}
            color="secondary"
          >
            Clear All
          </Button>
        </Box>
      </Box>

      {/* Context Menu */}
      <Menu
        open={contextMenu !== null}
        onClose={handleCloseContextMenu}
        anchorReference="anchorPosition"
        anchorPosition={
          contextMenu !== null
            ? { top: contextMenu.mouseY, left: contextMenu.mouseX }
            : undefined
        }
      >
        {/* Selection Operations */}
        <MenuItem onClick={() => handleBatchOperation('select_all')}>
          <ListItemIcon>
            <SelectAll fontSize="small" />
          </ListItemIcon>
          <ListItemText>Select All Districts</ListItemText>
        </MenuItem>
        <MenuItem onClick={() => handleBatchOperation('deselect_all')}>
          <ListItemIcon>
            <Clear fontSize="small" />
          </ListItemIcon>
          <ListItemText>Deselect All Districts</ListItemText>
        </MenuItem>
        
        <Divider />
        
        {/* Search Method Operations */}
        <MenuItem onClick={() => handleBatchOperation('set_standard')}>
          <ListItemIcon>
            <LocationOn fontSize="small" />
          </ListItemIcon>
          <ListItemText>Set Standard Search</ListItemText>
        </MenuItem>
        <MenuItem onClick={() => handleBatchOperation('set_grid')}>
          <ListItemIcon>
            <GridView fontSize="small" />
          </ListItemIcon>
          <ListItemText>Set Grid Search</ListItemText>
        </MenuItem>
        <MenuItem onClick={() => handleBatchOperation('set_skip')}>
          <ListItemIcon>
            <SkipNext fontSize="small" />
          </ListItemIcon>
          <ListItemText>Skip Location</ListItemText>
        </MenuItem>
      </Menu>
    </Box>
  );
});

LocationTree.displayName = 'LocationTree';

export default LocationTree;