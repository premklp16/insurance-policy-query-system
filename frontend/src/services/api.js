import axios from 'axios';

// Create an Axios instance pointing to the FastAPI local server
const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 60000, // Large timeout for loading sentence transformers initially
});

/**
 * Uploads an insurance policy PDF file to the backend.
 * Provides progress event callbacks for the UI.
 * 
 * @param {File} file - The PDF file object
 * @param {Function} onProgress - Callback function for upload progress tracking
 */
export const uploadPdf = (file, onProgress) => {
  const formData = new FormData();
  formData.append('file', file);

  return api.post('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (onProgress && progressEvent.total) {
        const percentCompleted = Math.round(
          (progressEvent.loaded * 100) / progressEvent.total
        );
        onProgress(percentCompleted);
      }
    },
  });
};

/**
 * Submits a query question against the currently cached PDF.
 * 
 * @param {string} question - The query string
 */
export const queryPolicy = (question) => {
  return api.post('/query', { question });
};

/**
 * Requests the backend to clear in-memory caches and delete any cached policy info.
 */
export const resetSystem = () => {
  return api.delete('/reset');
};

/**
 * Checks system operational health and model status.
 */
export const checkHealth = () => {
  return api.get('/health');
};

export default api;
