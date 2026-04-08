import { useState, useEffect, useCallback } from "react";
import { useNavigate, Link } from "react-router-dom";
import {
  LogOut,
  LayoutDashboard,
  Search,
  RefreshCw,
  AlertCircle,
  TrendingUp,
  Newspaper,
  LayoutGrid,
  Library
} from "lucide-react";
import api from "../utils/api";
import NewsCard from "../components/NewsCard";
import ChatSidebar from "../components/ChatSidebar";

const Dashboard = () => {
  const navigate = useNavigate();
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [activeChatArticle, setActiveChatArticle] = useState(null);
  const [user, setUser] = useState(null);

  const fetchNews = useCallback(async (query = "") => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.get("/api/news", {
        params: { q: query, limit: 150 }
      });

      if (response.data.success) {
        setArticles(response.data.data);
      } else {
        throw new Error("Failed to fetch news");
      }
    } catch (err) {
      console.error("News fetch error:", err);
      setError(err.response?.data?.detail || "Could not load news feed. Please try again later.");
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  }, []);

  // Initial fetch - RUNS ONLY ONCE ON MOUNT
  useEffect(() => {
    fetchNews(""); 
    api.get("/auth/me")
      .then(res => setUser(res.data))
      .catch(err => console.error("Failed to fetch user:", err));
  }, []); // <-- CRITICAL: MUST BE EMPTY

  // Safely grab the user's name, split by space to get the first name, fallback to 'there'
  const firstName = user?.username ? user.username.split(' ')[0] : 'there';

  // Handle Search
  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchNews(searchTerm);
  };

  const handleRefresh = () => {
    setIsRefreshing(true);
    fetchNews(searchTerm);
  };

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    navigate("/login", { replace: true });
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col font-sans selection:bg-blue-100 dark:selection:bg-blue-900/30">
      {/* Top Header Navigation */}
      <header className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-b border-slate-200 dark:border-slate-800 sticky top-0 z-50 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
                <LayoutDashboard className="w-6 h-6 text-white" />
              </div>
              <h1 className="text-xl font-black text-slate-900 dark:text-white tracking-tight uppercase">
                Pulse<span className="text-blue-600">News</span>
              </h1>
            </div>

            {/* Personalized Welcome inline */}
            <div className="hidden md:flex items-center text-base font-semibold text-slate-700 dark:text-slate-200">
              Welcome back, <span className="font-bold text-blue-600 dark:text-blue-400 ml-1.5 text-lg">{firstName}! </span>
            </div>

            <div className="flex items-center gap-2 sm:gap-4">
              <button
                onClick={handleRefresh}
                disabled={loading || isRefreshing}
                className="flex items-center gap-2 px-3 py-2 text-sm font-bold text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-xl transition-all disabled:opacity-50"
                title="Refresh News"
              >
                <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
                <span className="hidden sm:inline">Refresh</span>
              </button>

              <Link
                to="/vault"
                className="flex items-center gap-2 px-3 py-2 text-sm font-bold text-slate-600 dark:text-slate-400 hover:text-blue-600 dark:hover:text-blue-400 transition-all border border-transparent hover:border-slate-200 dark:hover:border-slate-800 rounded-xl"
              >
                <Library className="w-4 h-4" />
                <span className="hidden sm:inline">My Vault</span>
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

      <div className="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">

          <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
            <div>
              <div className="flex items-center gap-2 text-blue-600 font-bold text-sm uppercase tracking-widest mb-1">
                <TrendingUp className="w-4 h-4" />
                Live Headlines
              </div>
              <h2 className="text-3xl font-black text-slate-900 dark:text-white tracking-tight">
                Your Global Intelligence Feed
              </h2>
            </div>

            {/* Search Bar */}
            <form onSubmit={handleSearchSubmit} className="relative w-full max-w-md group">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 group-focus-within:text-blue-600 transition-colors" />
              <input
                type="text"
                placeholder="Search topics, news, or trends..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-12 pr-4 py-3.5 bg-slate-100 dark:bg-slate-800 border-none rounded-2xl text-slate-900 dark:text-white placeholder-slate-500 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 dark:focus:ring-offset-slate-900 transition-all shadow-inner"
              />
            </form>
          </div>
        </div>
      </div>

      {/* Main Content Feed */}
      <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 w-full">
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-2 text-slate-900 dark:text-white font-bold">
            <Newspaper className="w-5 h-5 text-blue-600" />
            <span>Latest Stories</span>
            <span className="ml-2 px-2 py-0.5 bg-slate-200 dark:bg-slate-800 rounded-full text-xs text-slate-500">
              {articles.length} found
            </span>
          </div>
        </div>

        {/* Loading State */}
        {loading && !isRefreshing ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 animate-pulse">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 overflow-hidden flex flex-col h-[450px]">
                <div className="h-48 bg-slate-200 dark:bg-slate-800 w-full" />
                <div className="p-5 flex-1 flex flex-col gap-4">
                  <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded w-3/4" />
                  <div className="space-y-2">
                    <div className="h-3 bg-slate-100 dark:bg-slate-800 rounded w-full" />
                    <div className="h-3 bg-slate-100 dark:bg-slate-800 rounded w-full" />
                    <div className="h-3 bg-slate-100 dark:bg-slate-800 rounded w-2/3" />
                  </div>
                  <div className="mt-auto pt-4 border-t border-slate-100 dark:border-slate-800 flex justify-between">
                    <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded w-20" />
                    <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded w-10" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : error ? (
          /* Error State */
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <div className="w-16 h-16 bg-rose-100 dark:bg-rose-900/30 text-rose-600 rounded-2xl flex items-center justify-center mb-4 shadow-lg">
              <AlertCircle className="w-8 h-8" />
            </div>
            <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-2">Something went wrong</h3>
            <p className="text-slate-500 dark:text-slate-400 max-w-md mx-auto mb-8">
              {error}
            </p>
            <button
              onClick={() => fetchNews(searchTerm)}
              className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl transition-all shadow-lg shadow-blue-600/30 active:scale-95"
            >
              Try Again
            </button>
          </div>
        ) : articles.length === 0 ? (
          /* Empty State */
          <div className="flex flex-col items-center justify-center py-24 text-center">
            <div className="w-20 h-20 bg-slate-100 dark:bg-slate-800 text-slate-300 rounded-full flex items-center justify-center mb-6">
              <LayoutGrid className="w-10 h-10" />
            </div>
            <h3 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">No Headlines Found</h3>
            <p className="text-slate-500 dark:text-slate-400">
              Your search for "{searchTerm}" didn't return any results. Try different keywords.
            </p>
          </div>
        ) : (
          /* Articles Grid (Responsive 1/2/3) */
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {articles.map((article) => (
              <NewsCard
                key={article.id}
                article={article}
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
          &copy; {new Date().getFullYear()} PulseNews AI. All intelligence grounded by VADER Sentiment.
        </div>
      </footer>
    </div>
  );
};

export default Dashboard;
