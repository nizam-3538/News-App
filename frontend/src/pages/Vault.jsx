import React, { useState, useEffect, useRef } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, Sparkles, Send, Library, Search, Bot, User } from "lucide-react";
import api from "../utils/api";

const Vault = () => {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);

  // RAG Chat State
  const [chatHistory, setChatHistory] = useState([]);
  const [chatInput, setChatInput] = useState("");
  const [isChatLoading, setIsChatLoading] = useState(false);
  const chatEndRef = useRef(null);

  useEffect(() => {
    fetchVault();
  }, []);

  useEffect(() => {
    // Auto-scroll chat to bottom
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [chatHistory, isChatLoading]);

  const fetchVault = async () => {
    try {
      const response = await api.get("/api/saved?limit=50");
      setArticles(response.data);
    } catch (err) {
      console.error("Failed to load vault:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleVaultChat = async (e) => {
    e.preventDefault();
    if (!chatInput.trim() || isChatLoading) return;

    const userQuery = chatInput.trim();
    setChatInput("");
    setChatHistory((prev) => [...prev, { role: "user", content: userQuery }]);
    setIsChatLoading(true);

    try {
      const response = await api.post("/api/chat/vault", { query: userQuery });
      if (response.data.ok) {
        setChatHistory((prev) => [
          ...prev,
          { role: "ai", content: response.data.answer }
        ]);
      } else {
        throw new Error(response.data.answer);
      }
    } catch (err) {
      setChatHistory((prev) => [
        ...prev,
        { role: "ai", content: "Sorry, I encountered an error while searching your vault." }
      ]);
    } finally {
      setIsChatLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 font-sans flex flex-col">
      {/* Header */}
      <header className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-b border-slate-200 dark:border-slate-800 sticky top-0 z-50">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link to="/" className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg text-slate-500 transition-colors">
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <div className="flex items-center gap-2">
              <Library className="w-5 h-5 text-blue-600" />
              <h1 className="text-xl font-black text-slate-900 dark:text-white">My Vault</h1>
            </div>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-5xl mx-auto w-full px-4 sm:px-6 py-8 flex flex-col gap-8">

        {/* Vault AI RAG Chat */}
        <section className="bg-white dark:bg-slate-900 rounded-3xl shadow-sm border border-slate-200 dark:border-slate-800 overflow-hidden flex flex-col">
          <div className="bg-gradient-to-r from-blue-600 to-indigo-600 p-4 flex items-center gap-3 text-white">
            <Sparkles className="w-5 h-5" />
            <div>
              <h2 className="font-bold">Ask Your Vault</h2>
              <p className="text-xs text-blue-100 opacity-90">Powered by Groq Llama 3 • Instant Intelligence</p>
            </div>
          </div>

          <div className="p-4 sm:p-6 flex flex-col gap-4 max-h-[400px] overflow-y-auto bg-slate-50 dark:bg-slate-950/50">
            {chatHistory.length === 0 ? (
              <div className="text-center text-slate-500 py-8 text-sm">
                Ask a question to instantly synthesize information from all your saved articles.
              </div>
            ) : (
              chatHistory.map((msg, idx) => (
                <div key={idx} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                  <div className={`flex gap-3 max-w-[85%] ${msg.role === "user" ? "flex-row-reverse" : ""}`}>
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${msg.role === "user" ? "bg-blue-600 text-white" : "bg-indigo-100 dark:bg-indigo-900/50 text-indigo-600 dark:text-indigo-400"}`}>
                      {msg.role === "user" ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                    </div>
                    <div className={`p-4 rounded-2xl text-sm shadow-sm ${msg.role === "user" ? "bg-blue-600 text-white rounded-tr-none" : "bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-tl-none text-slate-800 dark:text-slate-200 whitespace-pre-wrap leading-relaxed"}`}>
                      {msg.content}
                    </div>
                  </div>
                </div>
              ))
            )}

            {isChatLoading && (
              <div className="flex justify-start">
                <div className="flex gap-3 max-w-[85%]">
                  <div className="w-8 h-8 rounded-full flex items-center justify-center bg-indigo-100 dark:bg-indigo-900/50 text-indigo-600 dark:text-indigo-400">
                    <Bot className="w-4 h-4" />
                  </div>
                  <div className="p-4 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl rounded-tl-none shadow-sm flex gap-1.5 items-center">
                    <div className="w-2 h-2 bg-indigo-400 rounded-full animate-pulse" />
                    <div className="w-2 h-2 bg-indigo-400 rounded-full animate-pulse delay-75" />
                    <div className="w-2 h-2 bg-indigo-400 rounded-full animate-pulse delay-150" />
                  </div>
                </div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          <form onSubmit={handleVaultChat} className="p-4 bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800 relative">
            <div className="relative flex items-center">
              <Search className="absolute left-4 w-5 h-5 text-slate-400" />
              <input
                type="text"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                placeholder="E.g. What did I save about quantum computing?"
                className="w-full pl-12 pr-14 py-3.5 bg-slate-100 dark:bg-slate-800 border-none rounded-xl text-sm text-slate-900 dark:text-white placeholder-slate-500 focus:ring-2 focus:ring-blue-500 transition-all"
                disabled={isChatLoading}
              />
              <button
                type="submit"
                disabled={isChatLoading || !chatInput.trim()}
                className="absolute right-2 p-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-300 dark:disabled:bg-slate-800 text-white rounded-lg transition-all"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </form>
        </section>

        {/* Saved Articles List */}
        <div>
          <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
            Saved Articles <span className="text-sm font-normal text-slate-500">({articles.length})</span>
          </h3>

          {loading ? (
            <div className="animate-pulse space-y-4">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="h-24 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800" />
              ))}
            </div>
          ) : articles.length === 0 ? (
            <div className="text-center py-12 text-slate-500 bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800">
              Your vault is empty. Save some articles to start building your knowledge base.
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4">
              {articles.map((article) => (
                <a key={article.article_id} href={article.url} target="_blank" rel="noopener noreferrer" className="p-4 bg-white dark:bg-slate-900 rounded-2xl shadow-sm hover:shadow-md border border-slate-200 dark:border-slate-800 transition-all flex flex-col sm:flex-row gap-4">
                  {article.image_url && (
                    <img src={article.image_url} alt={article.title} className="w-full sm:w-32 h-24 object-cover rounded-xl" />
                  )}
                  <div>
                    <h4 className="font-bold text-slate-900 dark:text-white line-clamp-1">{article.title}</h4>
                    <p className="text-sm text-slate-500 dark:text-slate-400 line-clamp-2 mt-1">{article.summary}</p>
                  </div>
                </a>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default Vault;