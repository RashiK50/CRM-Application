import React, { useState, useEffect } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, Legend } from "recharts";
import { TrendingUp, BarChart3, Search, ShieldAlert, Calendar, User } from "lucide-react";

export default function AnalyticsDashboard() {
  const [sentimentData, setSentimentData] = useState([]);
  const [categoryData, setCategoryData] = useState([]);
  const [ragQuery, setRagQuery] = useState("");
  const [ragResults, setRagResults] = useState([]);
  const [ragLoading, setRagLoading] = useState(false);
  const [senderFilter, setSenderFilter] = useState("");

  // Fetch Sentiment Trends
  const fetchSentiment = async () => {
    try {
      const url = senderFilter 
        ? `http://127.0.0.1:8000/api/analytics/sentiment-trend?sender=${encodeURIComponent(senderFilter)}`
        : "http://127.0.0.1:8000/api/analytics/sentiment-trend";
      const res = await fetch(url);
      if (res.ok) setSentimentData(await res.json());
    } catch (err) {
      console.error("Failed fetching sentiment trends:", err);
    }
  };

  // Fetch Category Frequency
  const fetchCategories = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/api/analytics/category-breakdown");
      if (res.ok) setCategoryData(await res.json());
    } catch (err) {
      console.error("Failed fetching category breakdown:", err);
    }
  };

  // Execute RAG Search
  const handleRagSearch = async (e) => {
    e.preventDefault();
    if (!ragQuery.trim()) return;
    setRagLoading(true);
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/rag/search?q=${encodeURIComponent(ragQuery)}`);
      if (res.ok) setRagResults(await res.json());
    } catch (err) {
      console.error("RAG diagnostics failure:", err);
    } finally {
      setRagLoading(false);
    }
  };

  useEffect(() => {
    fetchSentiment();
    fetchCategories();
  }, [senderFilter]);

  return (
    <div className="space-y-6">
      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Sentiment Over Time Line Chart */}
        <div className="bg-slate-800 p-5 rounded-xl border border-slate-700 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sky-400 font-semibold">
              <TrendingUp className="w-5 h-5" /> Chronological Sentiment Stream
            </div>
            <input 
              type="text"
              placeholder="Filter by sender email..."
              value={senderFilter}
              onChange={(e) => setSenderFilter(e.target.value)}
              className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-sky-400 w-48"
            />
          </div>
          <div className="h-64 w-full">
            {sentimentData.length === 0 ? (
              <p className="text-sm text-slate-500 text-center pt-24">No stream nodes tracked.</p>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={sentimentData} margin={{ top: 10, right: 20, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="timestamp" stroke="#94a3b8" tickFormatter={(str) => new Date(str).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})} style={{ fontSize: '11px' }} />
                  <YAxis domain={[-1, 1]} stroke="#94a3b8" style={{ fontSize: '11px' }} />
                  <Tooltip contentStyle={{ backgroundColor: '#1e293b', borderColor: '#475569', color: '#f8fafc' }} />
                  <Line type="monotone" dataKey="sentiment_score" stroke="#38bdf8" strokeWidth={2.5} dot={{ r: 4 }} activeDot={{ r: 6 }} />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Category Breakdown Bar Chart */}
        <div className="bg-slate-800 p-5 rounded-xl border border-slate-700 space-y-4">
          <div className="flex items-center gap-2 text-indigo-400 font-semibold">
            <BarChart3 className="w-5 h-5" /> Distribution Frequency
          </div>
          <div className="h-64 w-full">
            {categoryData.length === 0 ? (
              <p className="text-sm text-slate-500 text-center pt-24">No classification logs available.</p>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={categoryData} margin={{ top: 10, right: 20, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="category" stroke="#94a3b8" style={{ fontSize: '11px' }} />
                  <YAxis stroke="#94a3b8" style={{ fontSize: '11px' }} />
                  <Tooltip contentStyle={{ backgroundColor: '#1e293b', borderColor: '#475569', color: '#f8fafc' }} />
                  <Bar dataKey="count" fill="#818cf8" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      </div>

      {/* RAG Diagnostics Panel */}
      <div className="bg-slate-800 p-5 rounded-xl border border-slate-700 space-y-4">
        <div className="flex items-center gap-2 text-emerald-400 font-semibold">
          <ShieldAlert className="w-5 h-5" /> Knowledge Base Vector Search Diagnostics
        </div>
        <form onSubmit={handleRagSearch} className="flex gap-2">
          <div className="relative flex-1">
            <input 
              type="text" 
              value={ragQuery}
              onChange={(e) => setRagQuery(e.target.value)}
              placeholder="Query corporate policies and similarity indices..."
              className="w-full bg-slate-900 border border-slate-700 rounded-lg pl-10 pr-4 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
            />
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
          </div>
          <button 
            type="submit"
            className="bg-emerald-500 hover:bg-emerald-600 text-slate-900 text-sm font-semibold px-5 py-2 rounded-lg transition cursor-pointer"
          >
            Query Vectors
          </button>
        </form>

        <div className="space-y-3">
          {ragLoading ? (
            <p className="text-sm text-slate-400 text-center py-4">Calculating mathematical distances...</p>
          ) : ragResults.length === 0 ? (
            <p className="text-sm text-slate-500 text-center py-4">No vector paths mapped yet.</p>
          ) : (
            ragResults.map((result, idx) => (
              <div key={idx} className="bg-slate-900 border border-slate-700/60 p-4 rounded-xl space-y-2">
                <div className="flex justify-between items-center text-xs border-b border-slate-700/40 pb-2">
                  <span className="text-emerald-400 font-mono font-semibold uppercase">Chunk similarity index</span>
                  <span className="bg-slate-800 border border-slate-700 text-slate-300 font-mono px-2 py-0.5 rounded">
                    Distance Metric: {result.score}
                  </span>
                </div>
                <p className="text-sm text-slate-300 leading-relaxed font-sans">{result.text}</p>
                {result.metadata && (
                  <div className="text-[11px] text-slate-500 font-mono">
                    Source File: {result.metadata.source || "Unknown Context"}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}