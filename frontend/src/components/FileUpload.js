import React, { useState } from 'react';
import { Box, Button, Typography, LinearProgress, Snackbar, Alert } from '@mui/material';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import axios from 'axios';

function FileUpload() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [notification, setNotification] = useState({ open: false, message: '', severity: 'success' });

  const handleFileChange = (event) => {
    setSelectedFile(event.target.files[0]);
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    const formData = new FormData();
    formData.append('file', selectedFile);

    setUploading(true);
    setUploadProgress(0);

    try {
      const response = await axios.post('http://localhost:8000/ingest', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setUploadProgress(percentCompleted);
        },
      });
      setNotification({ open: true, message: response.data.message, severity: 'success' });
    } catch (error) {
      setNotification({ open: true, message: 'File upload failed!', severity: 'error' });
    } finally {
      setUploading(false);
      setSelectedFile(null);
    }
  };

  const handleCloseNotification = () => {
    setNotification({ ...notification, open: false });
  };

  return (
    <Box sx={{ p: 2, borderBottom: '1px solid', borderColor: 'divider' }}>
      <Box sx={{ display: 'flex', alignItems: 'center' }}>
        <Button
          variant="contained"
          component="label"
          startIcon={<UploadFileIcon />}
        >
          Choose File
          <input type="file" hidden onChange={handleFileChange} />
        </Button>
        {selectedFile && (
          <Typography sx={{ ml: 2 }}>{selectedFile.name}</Typography>
        )}
        <Button
          variant="contained"
          onClick={handleUpload}
          disabled={!selectedFile || uploading}
          sx={{ ml: 'auto' }}
        >
          Upload
        </Button>
      </Box>
      {uploading && (
        <Box sx={{ width: '100%', mt: 2 }}>
          <LinearProgress variant="determinate" value={uploadProgress} />
        </Box>
      )}
      <Snackbar open={notification.open} autoHideDuration={6000} onClose={handleCloseNotification}>
        <Alert onClose={handleCloseNotification} severity={notification.severity} sx={{ width: '100%' }}>
          {notification.message}
        </Alert>
      </Snackbar>
    </Box>
  );
}

export default FileUpload;
