import api from './api';

export const profileService = {
  // Get all profiles
  async getProfiles() {
    try {
      const response = await api.get('/api/profiles/');
      return response.data;
    } catch (error) {
      throw new Error(error.userMessage || 'Failed to load profiles');
    }
  },

  // Create new profile
  async createProfile(profileData) {
    try {
      const response = await api.post('/api/profiles/', profileData);
      return response.data;
    } catch (error) {
      throw new Error(error.userMessage || 'Failed to create profile');
    }
  },

  // Get specific profile
  async getProfile(profileId) {
    try {
      const response = await api.get(`/api/profiles/${profileId}`);
      return response.data;
    } catch (error) {
      throw new Error(error.userMessage || 'Failed to load profile');
    }
  },

  // Update profile
  async updateProfile(profileId, updates) {
    try {
      const response = await api.put(`/api/profiles/${profileId}`, updates);
      return response.data;
    } catch (error) {
      throw new Error(error.userMessage || 'Failed to update profile');
    }
  },

  // Delete profile
  async deleteProfile(profileId) {
    try {
      const response = await api.delete(`/api/profiles/${profileId}`);
      return response.data;
    } catch (error) {
      throw new Error(error.userMessage || 'Failed to delete profile');
    }
  },

  // Duplicate profile
  async duplicateProfile(profileId, newName = null) {
    try {
      const response = await api.post(`/api/profiles/${profileId}/duplicate`, {
        new_name: newName
      });
      return response.data;
    } catch (error) {
      throw new Error(error.userMessage || 'Failed to duplicate profile');
    }
  },

  // Set default profile
  async setDefaultProfile(profileId) {
    try {
      const response = await api.post(`/api/profiles/${profileId}/set-default`);
      return response.data;
    } catch (error) {
      throw new Error(error.userMessage || 'Failed to set default profile');
    }
  },

  // Get preset profiles
  async getPresets() {
    try {
      const response = await api.get('/api/profiles/presets/list');
      return response.data;
    } catch (error) {
      throw new Error(error.userMessage || 'Failed to load presets');
    }
  },

  // Apply preset profile
  async applyPreset(presetId, profileName = null) {
    try {
      const response = await api.post(`/api/profiles/presets/${presetId}/apply`, {
        profile_name: profileName
      });
      return response.data;
    } catch (error) {
      throw new Error(error.userMessage || 'Failed to apply preset');
    }
  },

  // Get profile statistics
  async getStats() {
    try {
      const response = await api.get('/api/profiles/stats/summary');
      return response.data;
    } catch (error) {
      throw new Error(error.userMessage || 'Failed to get profile statistics');
    }
  },

  // Export profile
  async exportProfile(profileId) {
    try {
      const response = await api.post(`/api/profiles/export/${profileId}`);
      return response.data;
    } catch (error) {
      throw new Error(error.userMessage || 'Failed to export profile');
    }
  },

  // Import profile
  async importProfile(profileData, overwriteExisting = false) {
    try {
      const response = await api.post('/api/profiles/import', {
        profile_data: profileData,
        overwrite_existing: overwriteExisting
      });
      return response.data;
    } catch (error) {
      throw new Error(error.userMessage || 'Failed to import profile');
    }
  },

  // Search profiles
  async searchProfiles(query = null, tags = null) {
    try {
      const params = new URLSearchParams();
      if (query) params.append('q', query);
      if (tags) params.append('tags', tags);
      
      const response = await api.get(`/api/profiles/search?${params.toString()}`);
      return response.data;
    } catch (error) {
      throw new Error(error.userMessage || 'Failed to search profiles');
    }
  },

  // Backup profiles
  async backupProfiles() {
    try {
      const response = await api.post('/api/profiles/backup');
      return response.data;
    } catch (error) {
      throw new Error(error.userMessage || 'Failed to backup profiles');
    }
  },

  // Restore profiles
  async restoreProfiles(backupData, merge = false) {
    try {
      const response = await api.post('/api/profiles/restore', backupData, {
        params: { merge }
      });
      return response.data;
    } catch (error) {
      throw new Error(error.userMessage || 'Failed to restore profiles');
    }
  }
};