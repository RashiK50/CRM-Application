import AnalyticsDashboard from "./components/AnalyticsDashboard";
import React, { useState, useEffect } from "react";
import { 
  Inbox, 
  CheckCircle, 
  AlertTriangle, 
  ShieldAlert, 
  Search, 
  Bot, 
  Send, 
  RefreshCw, 
  TrendingUp, 
  User,
  UserCheck 
} from "lucide-react";

function App() {
  const [stats, setStats] = useState({ pending: 0, replied: 0, resolved: 0, escalated: 0, critical: 0, spam_filtered: 0 });
  const [threads, setThreads] = useState([]);
  const [selectedThread, setSelectedThread] = useState(null);
  const [searchEmail, setSearchEmail] = useState("info.seeking@generic-firm.com");
  const [draftReply, setDraftReply] = useState("");
  const [loading, setLoading] = useState(false);
  const [currentView, setCurrentView] = useState("inbox");
  const fetchStats = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/api/dashboard/stats");
      if (res.ok) {
        const data = await res.json();
        setStats({
          pending: data?.pending ?? 0,
          replied: data?.replied ?? 0,
          resolved: data?.resolved ?? 0,
          escalated: data?.escalated ?? 0,
          critical: data?.critical ?? 0,
          spam_filtered: data?.spam_filtered ?? 0
        });
      }
    } catch (err) {
      console.error("Metric sync fail:", err);
    }
  };

  const fetchCustomerThreads = async () => {
    if (!searchEmail.trim()) return;
    setLoading(true);
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/threads/${encodeURIComponent(searchEmail.trim())}`);
      if (res.ok) {
        const data = await res.json();
        const validatedThreads = Array.isArray(data) ? data : [];
        setThreads(validatedThreads);
        
        if (validatedThreads.length > 0) {
          setSelectedThread(validatedThreads[0]);
          const emailsArray = validatedThreads[0]?.emails || [];
          const latestEmail = emailsArray[emailsArray.length - 1];
          setDraftReply(latestEmail?.proposed_draft || "");
        } else {
          setSelectedThread(null);
          setDraftReply("");
        }
      } else {
        setThreads([]);
        setSelectedThread(null);
      }
    } catch (err) {
      console.error("Threads stream fail:", err);
      setThreads([]);
      setSelectedThread(null);
    } finally {
      setLoading(false);
    }
  };

  const fetchGlobalThreads = async () => {
    setLoading(true);
    try {
      const res = await fetch("http://127.0.0.1:8000/api/threads/global/recent");
      if (res.ok) {
        const data = await res.json();
        setThreads(data);
        // Automatically select the top thread if none is selected
        if (data.length > 0 && !selectedThread) {
          setSelectedThread(data[0]);
          const latestEmail = data[0]?.emails?.[data[0].emails.length - 1];
          setDraftReply(latestEmail?.proposed_draft || "");
        }
      }
    } catch (err) {
      console.error("Global threads fetch failed:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
    fetchGlobalThreads();
  }, []);

  const handleApproveDraft = async (emailId) => {
    if (!emailId) return;
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/respond/approve/${emailId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ final_reply: draftReply })
      });
      if (res.ok) {
        alert("Draft response approved!");
        fetchStats();
        fetchCustomerThreads();
      }
    } catch (err) {
      alert("Error transmitting approval handshake.");
    }
  };

  // Ultra-Defensive Parser: Safely unpacks strings, objects, or arrays containing 'thought' or 'trace' fields
  const renderAgentTrace = (trace) => {
    if (!trace) return "No reasoning trace available.";
    
    if (typeof trace === "object") {
      // Check for common backend variation keys explicitly
      if (trace.thought) return String(trace.thought);
      
      // THE FIX: Properly format the array of objects instead of forcing it to a String
      if (trace.trace) {
        return typeof trace.trace === "object" 
          ? JSON.stringify(trace.trace, null, 2) 
          : String(trace.trace);
      }
      
      if (trace.ai_raw) return typeof trace.ai_raw === "object" ? JSON.stringify(trace.ai_raw, null, 2) : String(trace.ai_raw);
      
      // Fallback: Serialize cleanly if it's an unrecognized plain object shape
      return JSON.stringify(trace, null, 2);
    }
    
    // If it's a string, double check if it's a raw JSON string that needs parsing
    if (typeof trace === "string" && (trace.startsWith("{") || trace.startsWith("["))) {
      try {
        const parsed = JSON.deserialize ? JSON.deserialize(trace) : JSON.parse(trace);
        if (parsed.thought) return String(parsed.thought);
        
        // THE FIX: Apply the same formatting logic to the parsed string payload
        if (parsed.trace) {
          return typeof parsed.trace === "object" 
            ? JSON.stringify(parsed.trace, null, 2) 
            : String(parsed.trace);
        }
        
        return JSON.stringify(parsed, null, 2);
      } catch (e) {
        // Fall back to the raw text if parsing fails
      }
    }
    
    return String(trace);
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col font-sans">
      
      <header className="bg-slate-800 border-b border-slate-700 px-6 py-4 flex items-center justify-between shadow-md">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-3">
            <Bot className="text-sky-400 w-8 h-8" />
            <div>
              <h1 className="text-lg font-bold tracking-tight text-white">Agentic CRM Core</h1>
              <p className="text-xs text-slate-400">Mission Control Operator Interface</p>
            </div>
          </div>
          
          {/* NEW VIEW SWITCHING TABS */}
          <nav className="flex gap-2 ml-4">
            <button 
              onClick={() => setCurrentView("inbox")}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition cursor-pointer ${currentView === "inbox" ? "bg-sky-400 text-slate-900" : "bg-slate-700 text-slate-300 hover:bg-slate-600"}`}
            >
              Inbox Console
            </button>
            <button 
              onClick={() => setCurrentView("analytics")}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition cursor-pointer ${currentView === "analytics" ? "bg-sky-400 text-slate-900" : "bg-slate-700 text-slate-300 hover:bg-slate-600"}`}
            >
              Analytics Hub
            </button>
          </nav>
        </div>
        
        <button 
          onClick={() => { fetchStats(); fetchGlobalThreads(); }} // <--- NEW
          className="flex items-center gap-2 text-xs bg-slate-700 hover:bg-slate-600 text-slate-300 px-3 py-2 rounded-lg transition cursor-pointer"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Sync Ledger
        </button>
      </header>

      <main className="flex-1 p-6 max-w-[1600px] w-full mx-auto flex flex-col gap-6">
        
        {/* Changed md:grid-cols-5 to lg:grid-cols-6 */}
        <section className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          <div className="bg-slate-800 p-4 rounded-xl border border-slate-700 flex items-center gap-4">
            <div className="p-3 bg-amber-500/10 text-amber-400 rounded-lg"><Inbox /></div>
            <div>
              <p className="text-xs text-slate-400 font-medium">Pending Queue</p>
              <h3 className="text-2xl font-bold text-white">{stats.pending}</h3>
            </div>
          </div>
          <div className="bg-slate-800 p-4 rounded-xl border border-slate-700 flex items-center gap-4">
            <div className="p-3 bg-emerald-500/10 text-emerald-400 rounded-lg"><CheckCircle /></div>
            <div>
              <p className="text-xs text-slate-400 font-medium">Auto Replied (AI)</p>
              <h3 className="text-2xl font-bold text-white">{stats.replied}</h3>
            </div>
          </div>
          
          {/* NEW: Human Resolved Card */}
          <div className="bg-slate-800 p-4 rounded-xl border border-slate-700 flex items-center gap-4">
            <div className="p-3 bg-sky-500/10 text-sky-400 rounded-lg"><UserCheck /></div>
            <div>
              <p className="text-xs text-slate-400 font-medium">Human Resolved</p>
              <h3 className="text-2xl font-bold text-white">{stats.resolved}</h3>
            </div>
          </div>

          <div className="bg-slate-800 p-4 rounded-xl border border-slate-700 flex items-center gap-4">
            <div className="p-3 bg-indigo-500/10 text-indigo-400 rounded-lg"><AlertTriangle /></div>
            <div>
              <p className="text-xs text-slate-400 font-medium">Escalated Logs</p>
              <h3 className="text-2xl font-bold text-white">{stats.escalated}</h3>
            </div>
          </div>
          <div className="bg-slate-800 p-4 rounded-xl border border-slate-700 flex items-center gap-4">
            <div className="p-3 bg-rose-500/10 text-rose-400 rounded-lg"><ShieldAlert /></div>
            <div>
              <p className="text-xs text-slate-400 font-medium">Critical Threats</p>
              <h3 className="text-2xl font-bold text-white">{stats.critical}</h3>
            </div>
          </div>
          <div className="bg-slate-800 p-4 rounded-xl border border-slate-700 flex items-center gap-4">
            <div className="p-3 bg-slate-500/10 text-slate-400 rounded-lg"><TrendingUp /></div>
            <div>
              <p className="text-xs text-slate-400 font-medium">Spam Intercepted</p>
              <h3 className="text-2xl font-bold text-white">{stats.spam_filtered}</h3>
            </div>
          </div>
        </section>


        {currentView ==="inbox" ? (
        <section className="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-6 min-h-[600px]">
          
          <div className="bg-slate-800 rounded-xl border border-slate-700 flex flex-col shadow-sm">
            <div className="p-4 border-b border-slate-700 flex flex-col gap-3">
              <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Search CRM Profile</label>
              <div className="relative">
                <input 
                  type="text" 
                  value={searchEmail}
                  onChange={(e) => setSearchEmail(e.target.value)}
                  placeholder="customer.email@domain.com"
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg pl-10 pr-4 py-2 text-sm text-white focus:outline-none focus:border-sky-400"
                />
                <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
              </div>
              <button 
                onClick={fetchCustomerThreads}
                className="w-full bg-sky-400 hover:bg-sky-500 text-slate-900 text-sm font-semibold py-2 rounded-lg transition shadow-md cursor-pointer"
              >
                Scan Conversation Path
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-2 space-y-2">
              {loading ? (
                <p className="text-sm text-slate-400 text-center py-8">Parsing vectors...</p>
              ) : threads.length === 0 ? (
                <p className="text-sm text-slate-500 text-center py-8">No conversation history loaded.</p>
              ) : (
                threads.map((t) => (
                  <div 
                    key={t?.thread_id || Math.random()}
                    onClick={() => {
                      setSelectedThread(t);
                      const latest = t?.emails?.[t?.emails?.length - 1];
                      setDraftReply(latest?.proposed_draft || "");
                    }}
                    className={`p-3 rounded-lg cursor-pointer border transition ${
                      selectedThread?.thread_id === t?.thread_id 
                        ? "bg-slate-700 border-sky-400" 
                        : "bg-transparent border-transparent hover:bg-slate-700/50"
                    }`}
                  >
                    <div className="flex justify-between items-start mb-1">
                      {/* NEW CONDITIONAL BADGE LOGIC */}
                      {t?.status === "Escalated" && t?.urgency === "Critical" ? (
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-rose-950 text-rose-400 border border-rose-800 font-bold uppercase shadow-sm">
                          CRITICAL THREAT
                        </span>
                      ) : (
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-900 text-sky-400 border border-slate-700 font-bold uppercase">
                          {t?.status || "UNKNOWN"}
                        </span>
                      )}
                    </div>
                    {/* NEW: Show the email address here */}
                    <h4 className="text-sm font-semibold text-white truncate">{t?.customer_email || "Unknown Sender"}</h4>
                    <p className="text-xs text-slate-400 truncate mt-0.5">{t?.subject || "No Subject"}</p>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="lg:col-span-2 bg-slate-800 rounded-xl border border-slate-700 flex flex-col overflow-hidden shadow-sm">
            {selectedThread ? (
              <div className="flex-1 flex flex-col h-full overflow-hidden">
                
                <div className="p-4 bg-slate-700/40 border-b border-slate-700 flex justify-between items-center">
                  <div>
                    <h2 className="text-base font-bold text-white">{selectedThread?.subject || "Active Thread"}</h2>
                    <p className="text-xs text-slate-400 flex items-center gap-1 mt-0.5">
                      <User className="w-3 h-3 text-sky-400" /> Thread Node: {selectedThread?.thread_id}
                    </p>
                  </div>
                </div>

                <div className="flex-1 overflow-y-auto p-4 space-y-4 max-h-[600px]">
                  {(selectedThread?.emails || []).map((email) => (
                    <div key={email?.id || Math.random()} className="space-y-4 border-b border-slate-700/30 pb-4 last:border-b-0">
                      
                      <div className="bg-slate-900 border border-slate-700 p-4 rounded-xl max-w-[90%]">
                        <div className="flex justify-between text-xs text-slate-400 border-b border-slate-700/30 pb-2 mb-2">
                          <span className="font-semibold text-slate-300">Inbound Customer Message ({email?.sender})</span>
                          <span>{email?.timestamp ? new Date(email.timestamp).toLocaleString() : ""}</span>
                        </div>
                        <p className="text-sm text-slate-200 leading-relaxed whitespace-pre-wrap">{email?.body || ""}</p>
                      </div>

                      {email?.agent_trace && (
                        <div className="bg-slate-900/60 border border-indigo-500/20 p-4 rounded-xl ml-auto max-w-[90%]">
                          <div className="flex items-center gap-2 text-xs text-indigo-400 font-semibold mb-2 border-b border-indigo-500/10 pb-2">
                            <Bot className="w-4 h-4" /> Layer 2 Autonomous Thinking Matrix Trace
                          </div>
                          <pre className="text-xs text-slate-300 font-mono overflow-x-auto bg-slate-900/50 p-3 rounded-lg border border-slate-700 leading-normal whitespace-pre-wrap">
                            {renderAgentTrace(email.agent_trace)}
                          </pre>
                        </div>
                      )}

                      {email?.proposed_draft && (
                        <div className="bg-slate-900/40 border border-sky-400/20 p-4 rounded-xl ml-auto max-w-[90%] space-y-3">
                          <div className="text-xs text-sky-400 font-semibold border-b border-sky-400/10 pb-2">
                            Generated Response Sandbox Draft (Awaiting Sign-off)
                          </div>
                          <textarea 
                            value={draftReply}
                            onChange={(e) => setDraftReply(e.target.value)}
                            className="w-full h-40 bg-slate-900 border border-slate-700 rounded-lg p-3 text-sm text-slate-200 font-sans focus:outline-none focus:border-sky-400 resize-none leading-relaxed"
                          />
                          <div className="flex justify-end">
                            <button 
                              onClick={() => handleApproveDraft(email?.id)}
                              className="flex items-center gap-2 bg-emerald-500 hover:bg-emerald-600 text-slate-900 text-xs font-bold px-4 py-2 rounded-lg transition shadow-md cursor-pointer"
                            >
                              <Send className="w-3.5 h-3.5" /> Commit & Transmit Response
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>

              </div>
            ) : (
              <div className="flex-1 flex flex-col items-center justify-center text-slate-500 p-8">
                <Bot className="w-12 h-12 text-slate-600 mb-3 stroke-[1.5]" />
                <p className="text-sm">Select an active context track thread from the navigation tree list panel.</p>
              </div>
            )}
          </div>

        </section>
        ):(
          
            <AnalyticsDashboard />)
        }
      </main>
    </div>
  );
}

export default App;