import React, { useState } from "react";
import { Bookmark, ExternalLink, MessageCircle, Smile, Frown, Meh, Clock, User, Sparkles, Trash2, CheckCircle2, BookOpen } from "lucide-react";
import api from "../utils/api";
import NoteModal from "./NoteModal";

const NewsCard = ({ article, onOpenChat, isVaultView = false, onDeleteSuccess, onNoteSaved, onTagClick }) => {
  const {
    id,
    title,
    summary,
    link, // Original field from news fetcher
    url,  // Field used in Saved articles
    source,
    author,
    image_url,
    published_at,
    sentiment,
    tags = [],
  } = article;

  const [isSaving, setIsSaving] = useState(false);
  const [isSaved, setIsSaved] = useState(false);
  const [error, setError] = useState(null);
  const [isNoteModalOpen, setIsNoteModalOpen] = useState(false);
  const [currentNote, setCurrentNote] = useState(article.note || "");

  const finalUrl = url || link;
  const articleId = id || article.article_id;

  // Format date
  const formatDate = (dateStr) => {
    if (!dateStr) {
      return "Recently";
    }
    try {
      const date = new Date(dateStr);
      if (isNaN(date.getTime())) {
        return "Recently";
      }
      const datePart = date.toLocaleDateString("en-US", {
        month: "long",
        day: "numeric",
        year: "numeric",
      });
      const timePart = date.toLocaleTimeString("en-US", {
        hour: "2-digit",
        minute: "2-digit",
        hour12: true,
      });
      return `${datePart} at ${timePart}`;
    } catch (e) {
      return "Recently";
    }
  };

  const handleSave = async () => {
    if (isSaving || isSaved) return;
    setIsSaving(true);
    setError(null);
    try {
      await api.post("/api/saved/", {
        article_id: articleId,
        title,
        url: finalUrl,
        summary,
        source: source || "Unknown",
        author: author || "Unknown",
        image_url,
        published_at,
        sentiment: sentiment || "Neutral",
        categories: article.categories || []
      });
      setIsSaved(true);
    } catch (err) {
      let msg = "Failed to save article";
      if (err.response?.status === 400) {
        msg = err.response.data.detail || "Storage limit reached (500 articles).";
      } else if (err.response?.data?.detail) {
        msg = err.response.data.detail;
      }
      setError(msg);
      // We'll show the error for 3 seconds then clear it
      setTimeout(() => setError(null), 3000);
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm("Are you sure you want to remove this article from your vault?")) return;
    try {
      await api.delete(`/api/saved/${articleId}`);
      if (onDeleteSuccess) onDeleteSuccess(articleId);
    } catch (err) {
      alert("Failed to delete article");
    }
  };

  // Sentiment Helper
  const getSentimentStyles = (sent) => {
    switch (sent) {
      case "Positive":
        return {
          bg: "bg-emerald-100/80 dark:bg-emerald-900/30",
          text: "text-emerald-700 dark:text-emerald-400",
          border: "border-emerald-200 dark:border-emerald-800/50",
          icon: <Smile className="w-4 h-4" />,
        };
      case "Negative":
        return {
          bg: "bg-rose-100/80 dark:bg-rose-900/30",
          text: "text-rose-700 dark:text-rose-400",
          border: "border-rose-200 dark:border-rose-800/50",
          icon: <Frown className="w-4 h-4" />,
        };
      default:
        return {
          bg: "bg-slate-100/80 dark:bg-slate-800/30",
          text: "text-slate-600 dark:text-slate-400",
          border: "border-slate-200 dark:border-slate-700/50",
          icon: <Meh className="w-4 h-4" />,
        };
    }
  };

  const sentimentStyle = getSentimentStyles(sentiment);
  const isSavedArticle = isVaultView || isSaved;

  return (
    <>
      <div className="group relative bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm hover:shadow-xl transition-all duration-300 overflow-hidden flex flex-col h-full hover:-translate-y-1">
        {/* Article Image */}
        <div className="relative h-48 w-full overflow-hidden">
          {image_url ? (
            <img
              src={image_url}
              alt={title}
              className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
              onError={(e) => {
                e.target.style.display = 'none';
                e.target.nextSibling.style.display = 'flex';
              }}
            />
          ) : null}

          {/* Modern Fallback (Dark Slate Gradient + Sparkles) */}
          <div
            className={`w-full h-full bg-gradient-to-br from-slate-800 to-slate-900 flex flex-col items-center justify-center gap-3 transition-transform duration-500 group-hover:scale-105 ${image_url ? 'hidden' : 'flex'}`}
          >
            <div className="w-12 h-12 rounded-full bg-slate-700/50 flex items-center justify-center border border-slate-600/30">
              <Sparkles className="w-6 h-6 text-blue-400 animate-pulse" />
            </div>
            <span className="text-slate-400 text-xs font-bold uppercase tracking-widest">AI Enhanced Space</span>
          </div>

          {/* Sentiment Badge Overlay */}
          <div className={`absolute top-4 right-4 flex items-center gap-1.5 px-3 py-1.5 rounded-full border backdrop-blur-md font-semibold text-xs transition-opacity duration-300 ${sentimentStyle.bg} ${sentimentStyle.text} ${sentimentStyle.border}`}>
            {sentimentStyle.icon}
            {sentiment}
          </div>

          {/* Source Badge */}
          <div className="absolute bottom-4 left-4">
            <span className="px-2.5 py-1 rounded-md bg-white/90 dark:bg-slate-800/90 backdrop-blur-sm text-slate-800 dark:text-slate-200 text-xs font-bold shadow-sm border border-slate-200 dark:border-slate-700">
              {source}
            </span>
          </div>
        </div>

        {/* Card Content */}
        <div className="p-5 flex-1 flex flex-col">
          <div className="flex items-center gap-3 text-xs text-slate-500 dark:text-slate-400 mb-3">
            <div className="flex items-center gap-1">
              <Clock className="w-3.5 h-3.5" />
              {formatDate(published_at)}
            </div>
            <span className="w-1 h-1 rounded-full bg-slate-300" />
            <div className="flex items-center gap-1 font-semibold text-blue-600 dark:text-blue-400">
              <span>🕒 3 min read</span>
            </div>
            <span className="w-1 h-1 rounded-full bg-slate-300" />
            <div className="flex items-center gap-1 max-w-[100px] truncate">
              <User className="w-3.5 h-3.5" />
              {author}
            </div>
          </div>

          <h3 className="text-lg font-bold text-slate-900 dark:text-white leading-snug mb-3 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors line-clamp-2">
            {title}
          </h3>

          <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed mb-6 line-clamp-3">
            {summary || "No description available for this article."}
          </p>

          {/* Tags */}
          {tags.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-4">
              {tags.map((tag) => (
                <button
                  key={tag}
                  onClick={() => onTagClick && onTagClick(tag)}
                  className={`text-xs px-2.5 py-1 flex items-center gap-1 font-semibold rounded-full border transition-all ${onTagClick
                      ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 border-blue-200 dark:border-blue-800 hover:bg-blue-100 dark:hover:bg-blue-900/50 cursor-pointer hover:shadow-sm'
                      : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border-slate-200 dark:border-slate-700 cursor-default'
                    }`}
                >
                  <span className="opacity-60">#</span>{tag}
                </button>
              ))}
            </div>
          )}

          {/* Footer Actions */}
          <div className="mt-auto pt-4 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between">
            <a
              href={finalUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 text-sm font-bold text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 transition-colors"
            >
              Read Article
              <ExternalLink className="w-3.5 h-3.5" />
            </a>

            <div className="flex items-center gap-2">
              {isVaultView ? (
                <button
                  onClick={handleDelete}
                  className="p-2 text-slate-400 hover:text-rose-600 dark:hover:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-900/20 rounded-lg transition-all"
                  title="Remove from Vault"
                >
                  <Trash2 className="w-5 h-5" />
                </button>
              ) : (
                <button
                  onClick={handleSave}
                  disabled={isSaving || isSaved}
                  className={`p-2 rounded-lg transition-all ${isSaved
                    ? "text-blue-600 bg-blue-50 dark:bg-blue-900/20"
                    : "text-slate-400 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20"
                    }`}
                  title={isSaved ? "Saved to Vault" : "Save for Later"}
                >
                  {isSaved ? (
                    <CheckCircle2 className="w-5 h-5 fill-current" />
                  ) : (
                    <Bookmark className={`w-5 h-5 ${isSaving ? "animate-pulse" : ""}`} />
                  )}
                </button>
              )}

              {/* Notes Button - Conditionally Rendered */}
              {isSavedArticle && (
                <button
                  onClick={() => setIsNoteModalOpen(true)}
                  className="p-2 text-slate-400 hover:text-amber-600 dark:hover:text-amber-400 hover:bg-amber-50 dark:hover:bg-amber-900/20 rounded-lg transition-all"
                  title="Notes"
                >
                  <BookOpen className="w-5 h-5" />
                </button>
              )}

              <button
                onClick={() => onOpenChat(article)}
                className="p-2 text-slate-400 hover:text-indigo-600 dark:hover:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 rounded-lg transition-all"
                title="AI Discussion"
              >
                <MessageCircle className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Inline Error Toast */}
          {error && (
            <div className="absolute bottom-20 left-4 right-4 bg-rose-600 text-white p-2 rounded-lg text-[10px] font-bold text-center animate-bounce shadow-lg z-10">
              {error}
            </div>
          )}
        </div>
      </div>

      {isNoteModalOpen && (
        <NoteModal
          isOpen={isNoteModalOpen}
          onClose={() => setIsNoteModalOpen(false)}
          articleId={articleId}
          articleTags={tags}
          initialNote={currentNote}
          onSave={(newNote) => setCurrentNote(newNote)}
          onNoteSaved={onNoteSaved}
        />
      )}
    </>
  );
};

export default NewsCard;
