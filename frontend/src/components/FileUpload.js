import React, { useState, useEffect } from 'react';
import { Box, Button, Typography, LinearProgress, Snackbar, Alert, List, ListItem, ListItemText, IconButton, Dialog, DialogTitle, DialogContent, Tooltip } from '@mui/material';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import PreviewIcon from '@mui/icons-material/Preview';
import axios from 'axios';

function FileUpload() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [notification, setNotification] = useState({ open: false, message: '', severity: 'success' });
  const [uploadHistory, setUploadHistory] = useState([]);
  const [previewFile, setPreviewFile] = useState(null);

  const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:8000';
  const MAX_SIZE_MB = 10;
  const ALLOWED_TYPES = ['application/pdf'];

  useEffect(() => {
    // Fetch upload history from backend
    async function fetchHistory() {
      try {
        const res = await axios.get(`${API_BASE}/files`);
        setUploadHistory(res.data.files || []);
      } catch (e) {
        // Ignore error for now
      }
    }
    fetchHistory();
  }, [notification]); // refresh on upload

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (!file) return;
    if (!ALLOWED_TYPES.includes(file.type)) {
      setNotification({ open: true, message: 'Only PDF files are allowed.', severity: 'error' });
      setSelectedFile(null);
      return;
    }
    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      setNotification({ open: true, message: `File size must be under ${MAX_SIZE_MB}MB.`, severity: 'error' });
      setSelectedFile(null);
      return;
    }
    setSelectedFile(file);
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    const formData = new FormData();
    formData.append('file', selectedFile);

    setUploading(true);
    setUploadProgress(0);

    try {
      const response = await axios.post(`${API_BASE}/ingest`, formData, {
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
      setNotification({ open: true, message: error?.response?.data?.message || 'File upload failed!', severity: 'error' });
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
        <Tooltip title="Choose a PDF file to upload">
          <Button
            variant="contained"
            component="label"
            startIcon={<UploadFileIcon />}
            aria-label="Choose file"
          >
            Choose File
            <input type="file" hidden onChange={handleFileChange} accept="application/pdf" />
          </Button>
        </Tooltip>
        {selectedFile && (
          <Typography sx={{ ml: 2 }}>{selectedFile.name}</Typography>
        )}
        <Tooltip title={selectedFile ? "Upload selected file" : "Select a file first"}>
          <span>
            <Button
              variant="contained"
              onClick={handleUpload}
              disabled={!selectedFile || uploading}
              sx={{ ml: 'auto' }}
              aria-label="Upload file"
            >
              Upload
            </Button>
          </span>
        </Tooltip>
      </Box>
      {uploading && (
        <Box sx={{ width: '100%', mt: 2 }}>
          <LinearProgress variant="determinate" value={uploadProgress} />
        </Box>
      )}
      <Snackbar open={notification.open} autoHideDuration={6000} onClose={handleCloseNotification} anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}>
        <Alert onClose={handleCloseNotification} severity={notification.severity} sx={{ width: '100%' }}>
          {notification.message}
        </Alert>
      </Snackbar>
      {/* Upload history */}
      <Box sx={{ mt: 2 }}>
        <Typography variant="subtitle2">Uploaded Documents</Typography>
        <List dense>
          {uploadHistory.length === 0 && <ListItem><ListItemText primary="No files uploaded yet." /></ListItem>}
          {uploadHistory.map((file, idx) => (
            <ListItem key={idx} secondaryAction={
              <Tooltip title="Preview document">
                <span>
                  <IconButton edge="end" aria-label="preview" onClick={() => setPreviewFile(file)}>
                    <PreviewIcon />
                  </IconButton>
                </span>
              </Tooltip>
            }>
              <ListItemText primary={file.name} />
            </ListItem>
          ))}
        </List>
      </Box>
      {/* Document preview dialog */}
      <Dialog open={!!previewFile} onClose={() => setPreviewFile(null)} maxWidth="md" fullWidth>
        <DialogTitle>Preview: {previewFile?.name}</DialogTitle>
        <DialogContent>
          {previewFile?.url && previewFile.name.endsWith('.pdf') ? (
            <iframe src={previewFile.url} title="PDF Preview" width="100%" height="600px" />
          ) : (
            <Typography>No preview available.</Typography>
          )}
        </DialogContent>
      </Dialog>
    </Box>
  );
}

export default FileUpload;
