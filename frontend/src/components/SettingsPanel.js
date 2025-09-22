import React, { useState, useEffect } from 'react';
import { Dialog, DialogTitle, DialogContent, DialogActions, Button, FormControl, InputLabel, Select, MenuItem, Slider, Box, FormControlLabel, Switch } from '@mui/material';

function SettingsPanel({ open, onClose, settings, onChange }) {
  const [localSettings, setLocalSettings] = useState(settings);
  const [darkMode, setDarkMode] = useState(() => {
    const stored = localStorage.getItem('darkMode');
    return stored ? JSON.parse(stored) : false;
  });

  useEffect(() => {
    setLocalSettings(settings);
    if (typeof settings.darkMode !== 'undefined') setDarkMode(settings.darkMode);
  }, [settings]);

  const handleSlider = (e, value) => {
    setLocalSettings({ ...localSettings, numDocs: value });
  };

  const handleModel = (e) => {
    setLocalSettings({ ...localSettings, model: e.target.value });
  };

  const handleDarkMode = (e) => {
    setDarkMode(e.target.checked);
    localStorage.setItem('darkMode', JSON.stringify(e.target.checked));
  };

  const handleSave = () => {
    onChange({ ...localSettings, darkMode });
    onClose();
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="xs" fullWidth>
      <DialogTitle>Settings</DialogTitle>
      <DialogContent>
        <Box sx={{ mt: 2 }}>
          <FormControl fullWidth sx={{ mb: 3 }}>
            <InputLabel id="model-select-label">Model</InputLabel>
            <Select
              labelId="model-select-label"
              value={localSettings.model}
              label="Model"
              onChange={handleModel}
            >
              <MenuItem value="all-MiniLM-L6-v2">MiniLM-L6-v2</MenuItem>
              <MenuItem value="gpt-3.5-turbo">GPT-3.5 Turbo</MenuItem>
              <MenuItem value="gpt-4">GPT-4</MenuItem>
            </Select>
          </FormControl>
          <Box sx={{ mb: 2 }}>
            Number of retrieved docs: {localSettings.numDocs}
            <Slider
              value={localSettings.numDocs}
              min={1}
              max={10}
              step={1}
              onChange={handleSlider}
              valueLabelDisplay="auto"
            />
          </Box>
          <FormControlLabel
            control={<Switch checked={darkMode} onChange={handleDarkMode} name="darkMode" color="primary" />}
            label="Dark Mode"
          />
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button onClick={handleSave} variant="contained">Save</Button>
      </DialogActions>
    </Dialog>
  );
}

export default SettingsPanel;
