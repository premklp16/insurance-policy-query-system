import React, { useRef, useState } from 'react';

/**
 * UploadBox manages the PDF dropzone, client-side validation, 
 * upload progress rendering, and reset triggers.
 */
export default function UploadBox({
  isUploaded,
  uploadedFilename,
  onUploadSubmit,
  onResetSubmit,
  isProcessingGlobal,
}) {
  const [dragActive, setDragActive] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [feedback, setFeedback] = useState({ type: '', message: '' });
  
  const fileInputRef = useRef(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (isUploading || isProcessingGlobal || isUploaded) return;

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      processFile(e.target.files[0]);
    }
  };

  const processFile = (file) => {
    setFeedback({ type: '', message: '' });

    // 1. Validation: File type (PDF)
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setFeedback({
        type: 'error',
        message: 'Invalid file format. Please upload a standard PDF (.pdf) document.',
      });
      return;
    }

    // 2. Validation: Empty files
    if (file.size === 0) {
      setFeedback({
        type: 'error',
        message: 'The selected PDF file is empty (0 bytes).',
      });
      return;
    }

    // 3. Validation: Max size 20 MB
    const maxSizeLimit = 20 * 1024 * 1024;
    if (file.size > maxSizeLimit) {
      setFeedback({
        type: 'error',
        message: 'File size exceeds the 20 MB limit. Please upload a smaller document.',
      });
      return;
    }

    // Begin upload operation
    setIsUploading(true);
    setUploadProgress(0);

    onUploadSubmit(file, (progressPercent) => {
      setUploadProgress(progressPercent);
    })
      .then((res) => {
        setFeedback({
          type: 'success',
          message: 'Policy document processed successfully and ready for searching.',
        });
        setIsUploading(false);
      })
      .catch((err) => {
        const errorDetail = err.response?.data?.detail || 'Failed to process the PDF. Ensure it is not password-protected or corrupted.';
        setFeedback({
          type: 'error',
          message: errorDetail,
        });
        setIsUploading(false);
      });
  };

  const triggerFileSelect = () => {
    fileInputRef.current.click();
  };

  const handleReset = () => {
    setFeedback({ type: '', message: '' });
    setUploadProgress(0);
    setIsUploading(false);
    onResetSubmit()
      .then(() => {
        setFeedback({
          type: 'success',
          message: 'System reset successfully.',
        });
      })
      .catch((err) => {
        setFeedback({
          type: 'error',
          message: 'Failed to reset system. Please try again.',
        });
      });
  };

  const disabledState = isUploading || isProcessingGlobal;

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 flex flex-col gap-5">
      <div className="flex flex-col gap-1.5">
        <h2 className="text-base font-semibold text-slate-900">Upload Policy Document</h2>
        <p className="text-xs text-slate-500">
          Upload an insurance policy PDF to analyze and enable searching. (Max 20 MB)
        </p>
      </div>

      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf"
        className="hidden"
        onChange={handleFileChange}
        disabled={disabledState || isUploaded}
      />

      {/* Upload zone */}
      {!isUploaded ? (
        <div
          onDragEnter={handleDrag}
          onDragOver={handleDrag}
          onDragLeave={handleDrag}
          onDrop={handleDrop}
          onClick={disabledState ? undefined : triggerFileSelect}
          className={`border-2 border-dashed rounded-xl p-8 flex flex-col items-center justify-center gap-3 transition-all duration-200 ${
            disabledState ? 'cursor-not-allowed opacity-60 bg-slate-50 border-slate-200' : 'cursor-pointer hover:bg-slate-50/50'
          } ${
            dragActive ? 'border-indigo-500 bg-indigo-50/20' : 'border-slate-300'
          }`}
        >
          <div className={`p-3 rounded-full ${dragActive ? 'bg-indigo-100 text-indigo-600' : 'bg-slate-100 text-slate-600'}`}>
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
          </div>
          <div className="text-center">
            <span className="text-sm font-semibold text-indigo-600">Click to upload</span>
            <span className="text-sm text-slate-500"> or drag & drop</span>
            <p className="text-[11px] text-slate-400 mt-1">PDF documents only</p>
          </div>
        </div>
      ) : (
        <div className="border border-emerald-100 bg-emerald-50/30 rounded-xl p-5 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3 min-w-0">
            <div className="p-2.5 bg-emerald-100 text-emerald-700 rounded-lg shrink-0">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="min-w-0">
              <p className="text-xs text-slate-500">Active Policy</p>
              <p className="text-sm font-semibold text-slate-800 truncate">{uploadedFilename}</p>
            </div>
          </div>
          <button
            onClick={handleReset}
            disabled={disabledState}
            className="px-3.5 py-1.5 text-xs font-semibold text-rose-600 bg-rose-50 border border-rose-100 rounded-lg hover:bg-rose-100 hover:text-rose-700 transition-colors disabled:opacity-50 shrink-0"
          >
            Reset
          </button>
        </div>
      )}

      {/* Progress Bar */}
      {isUploading && (
        <div className="flex flex-col gap-2">
          <div className="flex justify-between text-xs font-semibold text-slate-600">
            <span>{uploadProgress === 100 ? 'Processing policy document...' : 'Uploading policy document...'}</span>
            <span>{uploadProgress}%</span>
          </div>
          <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
            <div
              className="bg-indigo-600 h-full transition-all duration-300 rounded-full"
              style={{ width: `${uploadProgress}%` }}
            ></div>
          </div>
        </div>
      )}

      {/* Feedback Alert banners */}
      {feedback.message && (
        <div
          className={`flex items-start gap-2.5 p-3.5 rounded-xl border text-xs font-medium ${
            feedback.type === 'success'
              ? 'bg-emerald-50/40 border-emerald-100 text-emerald-800'
              : 'bg-rose-50/40 border-rose-100 text-rose-800'
          }`}
        >
          {feedback.type === 'success' ? (
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4.5 w-4.5 text-emerald-600 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          ) : (
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4.5 w-4.5 text-rose-600 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          )}
          <span className="leading-normal">{feedback.message}</span>
        </div>
      )}
    </div>
  );
}
