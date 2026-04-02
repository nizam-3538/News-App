import { useState, useEffect, useCallback } from "react";
import { useNavigate, Link } from "react-router-dom";
import { 
  LogOut, 
  LayoutDashboard, 
  Search, 
  AlertCircle,
  ShieldCheck,
  Library,
  ArrowLeft
} from "lucide-react";
import api from "../utils/api";
import NewsCard from "../components/NewsCard";
import ChatSidebar from "../components/ChatSidebar";

const Vault = () => {
  const navigate = useNavigate();
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeChatArticle, setActiveChatArticle] = useState(null);

  // Fetch saved articles
  const fetchSavedArticles = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.get("/api/saved/");
      // The backend returns a list of SavedArticleOut directly based on routers/saved.py
      setArticles(response.data);
    } catch (err) {
      console.error("Vault fetch error:", err);
      setError(err.response?.data?.detail || "Could not load your vault. Please try again later.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSavedArticles();
  }, [fetchSavedArticles]);

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    navigate("/login", { replace: true });
  };

  const handleDeleteSuccess = (articleId) => {
    setArticles(prev => prev.filter(a => (a.id || a.article_id) !== articleId));
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col font-sans selection:bg-blue-100 dark:selection:bg-blue-900/30">
      {/* Top Header Navigation */}
      <header className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-b border-slate-200 dark:border-slate-800 sticky top-0 z-50 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-3">
              <Link to="/dashboard" className="flex items-center gap-3 hover:opacity-80 transition-opacity">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
                  <LayoutDashboard className="w-6 h-6 text-white" />
                </div>
                <h1 className="text-xl font-black text-slate-900 dark:text-white tracking-tight uppercase">
                  Pulse<span className="text-blue-600">News</span>
                </h1>
              </Link>
            </div>

            <div className="flex items-center gap-2 sm:gap-4">
              <Link 
                to="/dashboard"
                className="flex items-center gap-2 px-3 py-2 text-sm font-bold text-slate-600 dark:text-slate-400 hover:text-blue-600 dark:hover:text-blue-400 transition-all"
              >
                <ArrowLeft className="w-4 h-4" />
                <span className="hidden sm:inline">Live Feed</span>
              </Link>
              <div className="h-6 w-px bg-slate-200 dark:bg-slate-800 mx-2" />
              <button
                onClick={handleLogout}
                className="flex items-center gap-2 px-4 py-2 text-sm font-bold text-slate-600 dark:text-slate-400 hover:text-rose-600 dark:hover:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/30 rounded-xl transition-all"
              >
                <LogOut className="w-4 h-4" />
                <span className="hidden sm:inline">Sign Out</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <div className="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-2xl bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center text-blue-600">
              <ShieldCheck className="w-7 h-7" />
            </div>
            <div>
              <div className="flex items-center gap-2 text-blue-600 font-bold text-sm uppercase tracking-widest mb-1">
                <Library className="w-4 h-4" />
                Intelligence Vault
              </div>
              <h2 className="text-3xl font-black text-slate-900 dark:text-white tracking-tight">
                Your Saved Knowledge
              </h2>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Feed */}
      <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 w-full">
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 animate-pulse">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 overflow-hidden flex flex-col h-[450px]">
                <div className="h-48 bg-slate-200 dark:bg-slate-800 w-full" />
                <div className="p-5 flex-1 flex flex-col gap-4">
                  <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded w-3/4" />
                  <div className="space-y-2">
                    <div className="h-3 bg-slate-100 dark:bg-slate-800 rounded w-full" />
                    <div className="h-3 bg-slate-100 dark:bg-slate-800 rounded w-full" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <div className="w-16 h-16 bg-rose-100 dark:bg-rose-900/30 text-rose-600 rounded-2xl flex items-center justify-center mb-4 shadow-lg">
              <AlertCircle className="w-8 h-8" />
            </div>
            <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-2">Error Loading Vault</h3>
            <p className="text-slate-500 dark:text-slate-400 max-w-md mx-auto mb-8">{error}</p>
            <button 
              onClick={fetchSavedArticles}
              className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl transition-all shadow-lg"
            >
              Try Again
            </button>
          </div>
        ) : articles.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-24 text-center">
            <div className="w-20 h-20 bg-slate-100 dark:bg-slate-800 text-slate-300 rounded-full flex items-center justify-center mb-6">
              <Library className="w-10 h-10" />
            </div>
            <h3 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">Your Vault is Empty</h3>
            <p className="text-slate-500 dark:text-slate-400 mb-8 max-w-sm mx-auto">
              Articles you bookmark will appear here for deep analysis and offline reference.
            </p>
            <Link 
              to="/dashboard"
              className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl transition-all shadow-lg"
            >
              Explore Feed
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {articles.map((article) => (
              <NewsCard 
                key={article.article_id} 
                article={article} 
                isVaultView={true}
                onDeleteSuccess={handleDeleteSuccess}
                onOpenChat={setActiveChatArticle}
              />
            ))}
          </div>
        )}
      </main>

      {/* Chat Sidebar Overlay */}
      {activeChatArticle && (
        <ChatSidebar 
          article={activeChatArticle} 
          onClose={() => setActiveChatArticle(null)} 
        />
      )}

      {/* Simple Footer */}
      <footer className="py-12 border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
        <div className="max-w-7xl mx-auto px-4 text-center text-slate-500 text-sm font-medium">
          &copy; {new Date().getFullYear()} PulseNews Vault. Secured by AES-256 Grounding.
        </div>
      </footer>
    </div>
  );
};

export default Vault;
