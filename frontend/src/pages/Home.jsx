import React, { useState, useEffect } from 'react';
import Navbar from '../components/Navbar';
import UploadBox from '../components/UploadBox';
import QuestionBox from '../components/QuestionBox';
import AnswerCard from '../components/AnswerCard';
import { uploadPdf, queryPolicy, resetSystem, checkHealth } from '../services/api';

/**
 * Main dashboard container that coordinates states between 
 * Navbar, Upload, Question, and Answer panels.
 */
export default function Home() {
  const [health, setHealth] = useState(null);
  const [isUploaded, setIsUploaded] = useState(false);
  const [uploadedFilename, setUploadedFilename] = useState('');
  const [queryResult, setQueryResult] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [globalError, setGlobalError] = useState('');

  // Retrieves health statistics from backend
  const fetchHealthState = () => {
    checkHealth()
      .then((res) => {
        setHealth(res.data);
        setIsUploaded(res.data.document_uploaded);
        
        // Recover state name on reload if a doc is cached
        if (res.data.document_uploaded && !uploadedFilename) {
          setUploadedFilename('Active Policy');
        } else if (!res.data.document_uploaded) {
          setUploadedFilename('');
        }
      })
      .catch(() => {
        setHealth(null);
        setIsUploaded(false);
        setUploadedFilename('');
      });
  };

  // Perform check on mount
  useEffect(() => {
    fetchHealthState();
    
    // Poll health status every 5 seconds to detect server state changes
    const interval = setInterval(fetchHealthState, 5000);
    return () => clearInterval(interval);
  }, [uploadedFilename]);

  const handleUploadSubmit = async (file, onProgress) => {
    setGlobalError('');
    try {
      const response = await uploadPdf(file, onProgress);
      setIsUploaded(true);
      setUploadedFilename(file.name);
      setQueryResult(null); // Clear previous results
      fetchHealthState();
      return response;
    } catch (err) {
      setIsUploaded(false);
      setUploadedFilename('');
      throw err;
    }
  };

  const handleResetSubmit = async () => {
    setGlobalError('');
    try {
      const response = await resetSystem();
      setIsUploaded(false);
      setUploadedFilename('');
      setQueryResult(null);
      fetchHealthState();
      return response;
    } catch (err) {
      throw err;
    }
  };

  const handleQuerySubmit = async (question) => {
    setIsProcessing(true);
    setGlobalError('');
    try {
      const response = await queryPolicy(question);
      setQueryResult(response.data);
    } catch (err) {
      const errorText = err.response?.data?.detail || 'An error occurred while processing your search query.';
      setGlobalError(errorText);
      setQueryResult(null);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-800">
      <Navbar health={health} />

      <main className="flex-1 max-w-4xl w-full mx-auto px-4 py-8 md:py-12 flex flex-col gap-6">
        
        {/* Connection status warning */}
        {health === null && (
          <div className="flex items-center gap-3 p-4 bg-rose-50 border border-rose-100 rounded-2xl text-rose-800 text-xs font-semibold animate-pulse">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-rose-600 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <div>
              <p className="font-bold">Backend Connection Failed</p>
              <p className="font-normal text-rose-650 mt-0.5">Please ensure the FastAPI server is running locally on port 8000.</p>
            </div>
          </div>
        )}

        {/* Global backend query/processing error alert */}
        {globalError && (
          <div className="flex items-center gap-3 p-4 bg-rose-50 border border-rose-100 rounded-2xl text-rose-800 text-xs font-semibold">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-rose-650 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div className="leading-relaxed">
              <span className="font-bold">Query Error: </span>
              <span className="font-normal text-rose-700">{globalError}</span>
            </div>
          </div>
        )}

        {/* Form Layout Split */}
        <div className="flex flex-col gap-6">
          <UploadBox
            isUploaded={isUploaded}
            uploadedFilename={uploadedFilename}
            onUploadSubmit={handleUploadSubmit}
            onResetSubmit={handleResetSubmit}
            isProcessingGlobal={isProcessing}
          />

          <QuestionBox
            isUploaded={isUploaded}
            onQuerySubmit={handleQuerySubmit}
            isProcessing={isProcessing}
          />

          <AnswerCard result={queryResult} />
        </div>
      </main>
    </div>
  );
}
