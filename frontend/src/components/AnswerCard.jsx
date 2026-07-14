import React from 'react';

/**
 * AnswerCard presents the matching policy text, source page numbers, 
 * and similarity match scores.
 */
export default function AnswerCard({ result }) {
  if (!result) {
    return (
      <div className="bg-slate-50 border border-slate-200 border-dashed rounded-2xl p-8 flex flex-col items-center justify-center text-center">
        <div className="p-3 bg-white border border-slate-150 rounded-xl text-slate-400 mb-2 shadow-sm">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
        </div>
        <p className="text-sm font-semibold text-slate-700">No query results yet</p>
        <p className="text-xs text-slate-500 mt-1 max-w-xs leading-normal">
          Upload a policy and submit a question above to find matching policy clauses.
        </p>
      </div>
    );
  }

  const { status, answer, page, similarity, message, highlighted_sentence, heading } = result;

  if (status === 'error' || !answer) {
    return (
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 flex flex-col gap-4 animate-fadeIn">
        <div className="flex items-center justify-between border-b border-slate-100 pb-4 flex-wrap gap-3">
          <div className="flex items-center gap-2">
            <div className="p-2 bg-amber-50 rounded-lg text-amber-600">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <h2 className="text-base font-semibold text-slate-900">No Related Policy Clause Found</h2>
          </div>
        </div>

        {/* Fallback Message */}
        <div className="bg-amber-50/20 border border-amber-100/50 rounded-xl p-4 md:p-5 text-sm text-slate-600 leading-relaxed font-normal select-text">
          {message || "The uploaded policy does not appear to contain a clause closely related to your question."}
        </div>
      </div>
    );
  }

  // Determine badge colors based on percentage
  let matchBadgeColor = 'text-indigo-700 bg-indigo-50 border-indigo-100';
  if (similarity >= 80) {
    matchBadgeColor = 'text-emerald-700 bg-emerald-50 border-emerald-100';
  } else if (similarity >= 55) {
    matchBadgeColor = 'text-amber-700 bg-amber-50 border-amber-100';
  } else {
    matchBadgeColor = 'text-rose-700 bg-rose-50 border-rose-100';
  }

  const isLowSimilarity = similarity < 50.0;

  const renderAnswerText = () => {
    if (!answer) return null;
    if (!highlighted_sentence) return answer;

    const idx = answer.indexOf(highlighted_sentence);
    if (idx === -1) {
      return answer;
    }

    const before = answer.substring(0, idx);
    const match = answer.substring(idx, idx + highlighted_sentence.length);
    const after = answer.substring(idx + highlighted_sentence.length);

    return (
      <>
        {before}
        <mark className="bg-indigo-200/95 text-indigo-950 font-bold px-1 py-0.5 rounded transition-colors duration-200 shadow-sm">
          {match}
        </mark>
        {after}
      </>
    );
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 flex flex-col gap-4 animate-fadeIn">
      <div className="flex items-center justify-between border-b border-slate-100 pb-4 flex-wrap gap-3">
        <div className="flex items-center gap-2">
          <div className="p-2 bg-indigo-50 rounded-lg text-indigo-600">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
          </div>
          <h2 className="text-base font-semibold text-slate-900">Most Relevant Policy Clause</h2>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {isLowSimilarity && (
            <div className="px-2.5 py-1 text-xs font-mono font-semibold rounded-lg border text-rose-700 bg-rose-50 border-rose-100">
              Low Similarity Match
            </div>
          )}
          {heading && (
            <div className="px-2.5 py-1 text-xs font-mono font-medium rounded-lg bg-slate-50 border border-slate-150 text-slate-600 flex items-center gap-1">
              <span>Section</span>
              <span className="font-bold text-slate-800">{heading}</span>
            </div>
          )}
          <div className="px-2.5 py-1 text-xs font-mono font-medium rounded-lg bg-slate-50 border border-slate-150 text-slate-600 flex items-center gap-1">
            <span>Page</span>
            <span className="font-bold text-slate-800">{page}</span>
          </div>
          <div className={`px-2.5 py-1 text-xs font-mono font-semibold rounded-lg border flex items-center gap-1 ${matchBadgeColor}`}>
            <span>Semantic Match</span>
            <span>{similarity}%</span>
          </div>
        </div>
      </div>

      {/* Extracted Clause */}
      <div className="bg-slate-50/50 border border-slate-100 rounded-xl p-4 md:p-5 text-sm text-slate-700 leading-relaxed font-normal whitespace-pre-wrap select-text">
        {renderAnswerText()}
      </div>

      {/* Explanatory Note */}
      <div className="bg-slate-50 border border-slate-150 rounded-xl p-3 text-xs text-slate-500 leading-relaxed flex items-start gap-2 select-none">
        <svg xmlns="http://www.w3.org/2000/svg" className="h-4.5 w-4.5 text-slate-400 shrink-0 mt-0.5" viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zm-1 9a1 1 0 100-2v-3a1 1 0 00-1-1H9a1 1 0 100 2v3a1 1 0 001 1h1z" clipRule="evenodd" />
        </svg>
        <div>
          This system retrieves the most relevant clause from the uploaded policy using semantic search. Please review the retrieved clause carefully, as the system does not determine whether a claim is covered or excluded.
        </div>
      </div>

      <div className="flex items-center gap-1.5 text-[10px] text-slate-400 select-none">
        <svg xmlns="http://www.w3.org/2000/svg" className="h-3.5 w-3.5" viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zm-1 9a1 1 0 100-2v-3a1 1 0 00-1-1H9a1 1 0 100 2v3a1 1 0 001 1h1z" clipRule="evenodd" />
        </svg>
        <span>Retrieved text is displayed directly from the uploaded policy document.</span>
      </div>
    </div>
  );
}
