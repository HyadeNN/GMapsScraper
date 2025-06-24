import React, { useState, useEffect, memo, useCallback } from 'react';
import {
  Box,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Chip,
  Typography,
  Divider,
  Alert,
  Tooltip
} from '@mui/material';
import {
  Add,
  Save,
  Edit,
  Delete,
  FileCopy,
  GetApp,
  Publish,
  Star,
  StarBorder
} from '@mui/icons-material';
import { profileService } from '../../services/profileService';

const ProfileManager = memo(({ selectedProfile, onProfileSelect }) => {
  const [profiles, setProfiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [dialogMode, setDialogMode] = useState('create'); // create, edit, save
  const [dialogProfile, setDialogProfile] = useState({
    name: '',
    description: '',
    tags: []
  });
  const [presets, setPresets] = useState([]);

  useEffect(() => {
    loadProfiles();
    loadPresets();
  }, []);

  const loadProfiles = async () => {
    setLoading(true);
    try {
      const response = await profileService.getProfiles();
      setProfiles(response.profiles || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadPresets = async () => {
    try {
      const presetList = await profileService.getPresets();
      setPresets(presetList || []);
    } catch (err) {
      console.error('Failed to load presets:', err);
    }
  };

  const handleCreateProfile = () => {
    setDialogMode('create');
    setDialogProfile({
      name: '',
      description: '',
      tags: []
    });
    setDialogOpen(true);
  };

  const handleEditProfile = (profile) => {
    setDialogMode('edit');
    setDialogProfile({
      id: profile.id,
      name: profile.name,
      description: profile.description || '',
      tags: profile.tags || []
    });
    setDialogOpen(true);
  };

  const handleSaveCurrentAsProfile = () => {
    setDialogMode('save');
    setDialogProfile({
      name: `Profile ${new Date().toLocaleDateString()}`,
      description: 'Saved from current configuration',
      tags: ['default']
    });
    setDialogOpen(true);
  };

  const handleDialogSave = async () => {
    if (!dialogProfile.name.trim()) return;

    setLoading(true);
    try {
      if (dialogMode === 'create' || dialogMode === 'save') {
        // For now, we'll create with dummy data since we don't have access to current settings/locations
        const profileData = {
          name: dialogProfile.name,
          description: dialogProfile.description,
          settings: {
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
          },
          locations: {
            cities: {},
            total_selected: 0,
            estimated_duration: null,
            last_updated: new Date().toISOString()
          },
          tags: dialogProfile.tags
        };

        await profileService.createProfile(profileData);
      } else if (dialogMode === 'edit') {
        await profileService.updateProfile(dialogProfile.id, {
          name: dialogProfile.name,
          description: dialogProfile.description,
          tags: dialogProfile.tags
        });
      }

      await loadProfiles();
      setDialogOpen(false);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteProfile = async (profileId) => {
    if (!window.confirm('Are you sure you want to delete this profile?')) return;

    setLoading(true);
    try {
      await profileService.deleteProfile(profileId);
      await loadProfiles();
      if (selectedProfile?.id === profileId) {
        onProfileSelect(null);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDuplicateProfile = async (profile) => {
    setLoading(true);
    try {
      await profileService.duplicateProfile(profile.id, `${profile.name} (Copy)`);
      await loadProfiles();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSetDefaultProfile = async (profileId) => {
    setLoading(true);
    try {
      await profileService.setDefaultProfile(profileId);
      await loadProfiles();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleApplyPreset = async (presetId) => {
    setLoading(true);
    try {
      const newProfile = await profileService.applyPreset(presetId);
      await loadProfiles();
      onProfileSelect(newProfile);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString();
  };

  return (
    <Box>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Profile Selection */}
      <FormControl fullWidth sx={{ mb: 2 }}>
        <InputLabel>Active Profile</InputLabel>
        <Select
          value={selectedProfile?.id || ''}
          onChange={(e) => {
            const profile = profiles.find(p => p.id === e.target.value);
            onProfileSelect(profile);
          }}
          disabled={loading}
        >
          <MenuItem value="">
            <em>No profile selected</em>
          </MenuItem>
          {profiles.map((profile) => (
            <MenuItem key={profile.id} value={profile.id}>
              <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                <Typography>{profile.name}</Typography>
                {profile.is_default && (
                  <Star sx={{ ml: 1, fontSize: '1rem', color: 'warning.main' }} />
                )}
              </Box>
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      {/* Action Buttons */}
      <Box sx={{ display: 'flex', gap: 1, mb: 2, flexWrap: 'wrap' }}>
        <Button
          size="small"
          startIcon={<Add />}
          onClick={handleCreateProfile}
          disabled={loading}
        >
          New
        </Button>
        <Button
          size="small"
          startIcon={<Save />}
          onClick={handleSaveCurrentAsProfile}
          disabled={loading}
        >
          Save Current
        </Button>
      </Box>

      <Divider sx={{ mb: 2 }} />

      {/* Profile List */}
      <Typography variant="subtitle2" gutterBottom>
        Saved Profiles ({profiles.length})
      </Typography>
      
      <List dense sx={{ maxHeight: 200, overflow: 'auto' }}>
        {profiles.map((profile) => (
          <ListItem
            key={profile.id}
            button
            selected={selectedProfile?.id === profile.id}
            onClick={() => onProfileSelect(profile)}
          >
            <ListItemText
              primary={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Typography variant="body2">{profile.name}</Typography>
                  {profile.is_default && (
                    <Star sx={{ fontSize: '0.9rem', color: 'warning.main' }} />
                  )}
                </Box>
              }
              secondary={
                <Box>
                  {profile.description && (
                    <Typography variant="caption" display="block">
                      {profile.description}
                    </Typography>
                  )}
                  <Typography variant="caption" color="text.secondary">
                    Created: {formatDate(profile.created_at)}
                  </Typography>
                  {profile.tags && profile.tags.length > 0 && (
                    <Box sx={{ mt: 0.5 }}>
                      {profile.tags.map((tag, index) => (
                        <Chip
                          key={index}
                          label={tag}
                          size="small"
                          variant="outlined"
                          sx={{ mr: 0.5, height: 16, fontSize: '0.6rem' }}
                        />
                      ))}
                    </Box>
                  )}
                </Box>
              }
            />
            <ListItemSecondaryAction>
              <Box sx={{ display: 'flex' }}>
                <Tooltip title="Edit">
                  <IconButton
                    size="small"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleEditProfile(profile);
                    }}
                  >
                    <Edit fontSize="small" />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Duplicate">
                  <IconButton
                    size="small"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDuplicateProfile(profile);
                    }}
                  >
                    <FileCopy fontSize="small" />
                  </IconButton>
                </Tooltip>
                <Tooltip title={profile.is_default ? 'Default' : 'Set as default'}>
                  <IconButton
                    size="small"
                    onClick={(e) => {
                      e.stopPropagation();
                      if (!profile.is_default) {
                        handleSetDefaultProfile(profile.id);
                      }
                    }}
                    disabled={profile.is_default}
                  >
                    {profile.is_default ? <Star fontSize="small" /> : <StarBorder fontSize="small" />}
                  </IconButton>
                </Tooltip>
                <Tooltip title="Delete">
                  <IconButton
                    size="small"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteProfile(profile.id);
                    }}
                    color="error"
                  >
                    <Delete fontSize="small" />
                  </IconButton>
                </Tooltip>
              </Box>
            </ListItemSecondaryAction>
          </ListItem>
        ))}
      </List>

      {profiles.length === 0 && !loading && (
        <Typography variant="body2" color="text.secondary" align="center" sx={{ py: 2 }}>
          No profiles saved yet
        </Typography>
      )}

      {/* Preset Profiles */}
      {presets.length > 0 && (
        <>
          <Divider sx={{ my: 2 }} />
          <Typography variant="subtitle2" gutterBottom>
            Quick Start Presets
          </Typography>
          <List dense>
            {presets.map((preset) => (
              <ListItem
                key={preset.id}
                button
                onClick={() => handleApplyPreset(preset.id)}
              >
                <ListItemText
                  primary={preset.name}
                  secondary={
                    <Box>
                      <Typography variant="caption" display="block">
                        {preset.description}
                      </Typography>
                      <Typography variant="caption" color="primary">
                        {preset.estimated_duration} • {preset.locations_count} locations
                      </Typography>
                    </Box>
                  }
                />
              </ListItem>
            ))}
          </List>
        </>
      )}

      {/* Profile Dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          {dialogMode === 'create' ? 'Create New Profile' : 
           dialogMode === 'edit' ? 'Edit Profile' : 
           'Save Current Configuration'}
        </DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Profile Name"
            value={dialogProfile.name}
            onChange={(e) => setDialogProfile({ ...dialogProfile, name: e.target.value })}
            margin="normal"
            required
          />
          <TextField
            fullWidth
            label="Description"
            value={dialogProfile.description}
            onChange={(e) => setDialogProfile({ ...dialogProfile, description: e.target.value })}
            margin="normal"
            multiline
            rows={2}
          />
          <TextField
            fullWidth
            label="Tags (comma-separated)"
            value={dialogProfile.tags?.join(', ') || ''}
            onChange={(e) => {
              const tags = e.target.value.split(',').map(tag => tag.trim()).filter(tag => tag);
              setDialogProfile({ ...dialogProfile, tags });
            }}
            margin="normal"
            helperText="Add tags to categorize your profile"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={handleDialogSave} 
            variant="contained"
            disabled={!dialogProfile.name.trim() || loading}
          >
            {loading ? 'Saving...' : 'Save'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
});

ProfileManager.displayName = 'ProfileManager';

export default ProfileManager;