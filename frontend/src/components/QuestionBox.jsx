import React, { useState } from 'react';

/**
 * QuestionBox provides the user input textbox and triggers query searches.
 * Handles loading status, validation, and Enter key submissions.
 */
export default function QuestionBox({
  isUploaded,
  onQuerySubmit,
  isProcessing,
}) {
  const [question, setQuestion] = useState('');
  const [warning, setWarning] = useState('');

  const handleSubmit = (e) => {
    if (e) e.preventDefault();
    
    if (!isUploaded || isProcessing) return;

    const queryStr = question.trim();
    if (!queryStr) {
      setWarning('Question cannot be empty. Please enter a search query.');
      return;
    }

    setWarning('');
    onQuerySubmit(queryStr);
  };

  const handleKeyDown = (e) => {
    // Submit on Enter without shift
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const disabledInput = !isUploaded || isProcessing;
  const disabledButton = disabledInput || !question.trim();

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 flex flex-col gap-4">
      <div className="flex flex-col gap-1.5">
        <h2 className="text-base font-semibold text-slate-900">Query Policy</h2>
        <p className="text-xs text-slate-500">
          Search and retrieve the most relevant clauses from the uploaded insurance policy using semantic search.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-3.5">
        <div className="flex flex-col md:flex-row gap-3 items-stretch">
          <div className="flex-1 relative">
            <textarea
              rows={3}
              value={question}
              onChange={(e) => {
                setQuestion(e.target.value);
                if (e.target.value.trim()) {
                  setWarning('');
                }
              }}
              onKeyDown={handleKeyDown}
              disabled={disabledInput}
              placeholder={
                isUploaded
                  ? "Search the policy (e.g., dental treatment, maternity, room rent, cancer treatment, waiting period)..."
                  : "Please upload an insurance policy PDF above to enable querying."
              }
              className={`w-full text-sm rounded-xl border p-4 outline-none transition-all duration-200 resize-none leading-relaxed h-full ${
                disabledInput
                  ? 'bg-slate-50/50 border-slate-200 text-slate-400 cursor-not-allowed placeholder-slate-400'
                  : 'border-slate-300 focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100/50 text-slate-800 placeholder-slate-400'
              }`}
            />
          </div>

          <button
            type="submit"
            disabled={disabledButton}
            className={`w-full md:w-44 rounded-xl text-sm font-semibold flex items-center justify-center gap-2 border transition-all duration-150 py-3 shrink-0 ${
              disabledButton
                ? 'bg-slate-50 border-slate-200 text-slate-400 cursor-not-allowed shadow-none'
                : 'bg-indigo-600 hover:bg-indigo-700 text-white border-indigo-600 hover:border-indigo-700 shadow-md shadow-indigo-600/10 active:scale-[0.98]'
            }`}
          >
            {isProcessing ? (
              <>
                <svg className="animate-spin h-4 w-4 text-indigo-200" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span>Searching...</span>
              </>
            ) : (
              <>
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4.5 w-4.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                <span>Ask Question</span>
              </>
            )}
          </button>
        </div>

        {warning && (
          <div className="flex items-center gap-2 text-rose-600 text-xs font-semibold">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <span>{warning}</span>
          </div>
        )}

        {isUploaded && (
          <div className="flex flex-wrap gap-2 items-center text-xs select-none">
            <span className="text-slate-400 font-medium">Try searching for:</span>
            {[
              "Dental treatment",
              "Cancer treatment",
              "Maternity",
              "Waiting period",
              "Room rent",
              "OPD",
              "Cataract",
              "Organ donor expenses",
            ].map((term) => (
              <button
                key={term}
                type="button"
                onClick={() => {
                  if (disabledInput) return;
                  setQuestion(term);
                  setWarning('');
                }}
                className="px-2.5 py-1 bg-slate-50 border border-slate-200 hover:bg-slate-100 active:bg-slate-150 text-slate-600 rounded-lg transition-colors cursor-pointer text-[11px] font-medium"
              >
                {term}
              </button>
            ))}
          </div>
        )}
      </form>
    </div>
  );
}
