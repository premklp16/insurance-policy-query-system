import React from 'react';

/**
 * Navbar component that presents the query logo, title and dynamic system health.
 * 
 * @param {Object} props
 * @param {Object} props.health - The current health check state from API
 */
export default function Navbar({ health }) {
  let statusText = 'Connecting...';
  let statusColor = 'bg-amber-500 shadow-amber-500/50';
  let pulse = 'animate-pulse';

  if (health) {
    if (health.status === 'ok') {
      if (health.model_loaded) {
        statusText = 'System Ready';
        statusColor = 'bg-emerald-500 shadow-emerald-500/50';
        pulse = '';
      } else {
        statusText = 'Loading Model...';
        statusColor = 'bg-amber-500 shadow-amber-500/50';
        pulse = 'animate-pulse';
      }
    }
  } else if (health === null) {
    statusText = 'Server Offline';
    statusColor = 'bg-rose-500 shadow-rose-500/50';
    pulse = '';
  }

  return (
    <nav className="bg-slate-900 border-b border-slate-800 text-white py-4 px-6 md:px-12 flex justify-between items-center shadow-md sticky top-0 z-50">
      <div className="flex items-center gap-3">
        <div className="p-2.5 bg-indigo-600 rounded-xl shadow-md shadow-indigo-600/20 flex items-center justify-center">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-5.5 w-5.5 text-white"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
            width="22"
            height="22"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
        </div>
        <div className="flex flex-col md:flex-row md:items-center gap-1 md:gap-2">
          <span className="font-semibold text-lg tracking-wide bg-gradient-to-r from-white to-slate-300 bg-clip-text text-transparent">
            Insurance Policy Query System
          </span>
          <span className="w-fit text-[10px] font-mono text-indigo-400 bg-indigo-950/40 px-2 py-0.5 rounded border border-indigo-900/30">
            Semantic Search
          </span>
        </div>
      </div>

      <div className="flex items-center gap-2 bg-slate-800 border border-slate-800 px-3 py-1.5 rounded-full text-xs font-medium transition-all duration-300">
        <span className={`h-2.5 w-2.5 rounded-full ${statusColor} ${pulse} shadow-sm inline-block`}></span>
        <span className="text-slate-300">{statusText}</span>
      </div>
    </nav>
  );
}
