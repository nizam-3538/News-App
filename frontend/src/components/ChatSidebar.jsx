import React, { useState, useEffect, useRef } from "react";
import { X, Send, Bot, User, Sparkles, MessageCircle, Volume2, Square, Save, BookOpen } from "lucide-react";
import api from "../utils/api";
import NoteModal from "./NoteModal";

const LANGUAGES = [
  { code: "English", label: "English" },
  { code: "Spanish", label: "Español" },
  { code: "French", label: "Français" },
  { code: "German", label: "Deutsch" },
  { code: "Hindi", label: "हिन्दी" },
  { code: "Tamil", label: "தமிழ்" },
  { code: "Telugu", label: "తెలుగు" },
  { code: "Kannada", label: "ಕನ್ನಡ" },
  { code: "Malayalam", label: "മലയാളം" },
  { code: "Japanese", label: "日本語" },
  { code: "Chinese", label: "中文" },
  { code: "Korean", label: "한국어" },
  { code: "Thai", label: "ไทย" },
  { code: "Vietnamese", label: "Tiếng Việt" },
  { code: "Indonesian", label: "Bahasa Indonesia" },
  { code: "Arabic", label: "العربية" },
  { code: "Turkish", label: "Türkçe" },
];

const ChatSidebar = ({ article, onClose, onNoteSaved }) => {
  const [messages, setMessages] = useState([
    {
      role: "ai",
      text: `Hello! I'm your AI News assistant. I've analyzed "${article?.title}". Ask me anything about it!`,
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [selectedLanguage, setSelectedLanguage] = useState("English");
  const [isSpeaking, setIsSpeaking] = useState(null); // stores the index of message being spoken
  const scrollRef = useRef(null);
  const [isNoteModalOpen, setIsNoteModalOpen] = useState(false);
  const [summaryNote, setSummaryNote] = useState("");
  const [isSummarizing, setIsSummarizing] = useState(false);

  // 🛡️ TTS SAFEGUARD: Immediate cleanup on unmount or when sidebar closes
  useEffect(() => {
    return () => {
      window.speechSynthesis.cancel();
    };
  }, []);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, loading]);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", text: userMessage }]);
    setLoading(true);

    try {
      const response = await api.post("/api/chat", {
        article_text: article.summary || article.content || article.title,
        question: userMessage,
        language: selectedLanguage
      });

      if (response.data.ok) {
        setMessages((prev) => [
          ...prev,
          { role: "ai", text: response.data.answer },
        ]);
      } else {
        throw new Error("Failed to get AI response");
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "ai", text: "Sorry, I encountered an error. Please try again." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleSpeech = (text, index) => {
    if (isSpeaking === index) {
      window.speechSynthesis.cancel();
      setIsSpeaking(null);
    } else {
      window.speechSynthesis.cancel(); // cancel any previous
      const utterance = new SpeechSynthesisUtterance(text);

      // Attempt to find a voice matching the language if possible
      utterance.onend = () => setIsSpeaking(null);
      utterance.onerror = () => setIsSpeaking(null);

      setIsSpeaking(index);
      window.speechSynthesis.speak(utterance);
    }
  };

  const handleLanguageChange = async (newLang) => {
    const oldLang = selectedLanguage;
    const previousMessages = [...messages]; // 🛡️ BACKUP STATE: Prevent blank UI on failure
    setSelectedLanguage(newLang);

    if (messages.length <= 1 || loading) return;

    setLoading(true);
    try {
      const response = await api.post("/api/chat", {
        article_text: article.summary || article.content || article.title,
        question: `Translate the previous chat history into ${newLang}. YOU MUST RETURN ONLY THE JSON ARRAY. DON'T ADD ANY EXTRA TEXT.`,
        language: newLang,
        history: messages.map(m => ({ role: m.role, content: m.text }))
      });

      if (!response.data.ok) {
        throw new Error(response.data.answer);
      }

      const rawText = response.data.answer.trim();

      try {
        // 🛡️ BULLETPROOF EXTRACTION: Use regex to find the array even if AI adds conversational text
        const jsonMatch = rawText.match(/\[[\s\S]*\]/);
        if (!jsonMatch) throw new Error("No JSON array found in response");

        const translatedHistory = JSON.parse(jsonMatch[0]);

        if (!Array.isArray(translatedHistory)) throw new Error("AI did not return an array");

        // 🛡️ DISAPPEARING CHAT FIX: Strict length validation
        if (translatedHistory.length < messages.length) {
          throw new Error("AI returned incomplete history (summarized)");
        }

        // Overwrite messages with the batch-translated version
        setMessages(translatedHistory.map(m => ({
          // 🛡️ ROLE NORMALIZATION: Force bad roles to "ai"
          role: (m.role === "model" || m.role === "assistant") ? "ai" : m.role,
          text: m.content
        })));
      } catch (error) {
        console.error("🚨 PARSE ERROR DETAILS:", error);
        alert("The AI returned a malformed response during translation. Please try again or stick to the current language.");
        setMessages(previousMessages); // 🛡️ RESTORE STATE
        setSelectedLanguage(oldLang); // Revert dropdown
      }
    } catch (err) {
      console.error("Batch Translation error:", err);
      // Append the error message directly to chat history instead of alert()
      alert(`Translation failed: ${err.message || "Please try again."}`);
      setMessages(previousMessages); // 🛡️ RESTORE STATE
      setSelectedLanguage(oldLang);
    } finally {
      setLoading(false);
    }
  };

  const handleSummarizeAndSave = async () => {
    if (messages.length <= 1 || isSummarizing) return;
    setIsSummarizing(true);
    try {
      const response = await api.post("/api/chat/summary", {
        history: messages.map(m => ({ role: m.role, content: m.text })),
        language: selectedLanguage
      });

      if (response.data.ok) {
        const existingNote = article.note || "";
        const newText = existingNote
          ? `${existingNote}\n\n--- AI Chat Summary ---\n${response.data.summary}`
          : `--- AI Chat Summary ---\n${response.data.summary}`;
        setSummaryNote(newText);
        setIsNoteModalOpen(true);
      } else {
        alert("Failed to generate summary: " + response.data.summary);
      }
    } catch (err) {
      console.error("Summary error:", err);
      alert("Error generating summary.");
    } finally {
      setIsSummarizing(false);
    }
  };

  if (!article) return null;

  // Check if article is saved (typically indicated by having a saved_id or a populated note field)
  const isSavedArticle = !!(article.saved_id || article.note !== undefined);

  return (
    <div className="fixed inset-0 z-[60] flex justify-end overflow-hidden">
      {/* Semi-transparent Backdrop */}
      <div
        className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />

      {/* Sidebar Drawer */}
      <aside className="relative w-full sm:w-96 bg-white dark:bg-slate-900 shadow-2xl flex flex-col h-full transform transition-transform duration-300 ease-in-out translate-x-0">
        {/* Header */}
        <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-white dark:bg-slate-900">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center">
              <MessageCircle className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-slate-900 dark:text-white line-clamp-1">
                AI Discussion
              </h2>
              <div className="flex items-center gap-2">
                <p className="text-[10px] text-slate-500 uppercase tracking-widest font-black">
                  Grounded by Gemini
                </p>
                <select
                  value={selectedLanguage}
                  onChange={(e) => handleLanguageChange(e.target.value)}
                  className="text-[10px] bg-slate-100 dark:bg-slate-800 border-none rounded py-0 px-1 font-bold text-blue-600 outline-none focus:ring-0"
                >
                  {LANGUAGES.map(lang => (
                    <option key={lang.code} value={lang.code}>{lang.label}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-1">
            {isSavedArticle && (
              <button
                onClick={handleSummarizeAndSave}
                disabled={isSummarizing || messages.length <= 1}
                title="Summarize Chat to Notes"
                className="p-2 hover:bg-blue-50 dark:hover:bg-slate-800 rounded-lg text-blue-600 dark:text-blue-400 transition-colors disabled:opacity-50"
              >
                {isSummarizing ? <Bot className="w-5 h-5 animate-pulse" /> : <BookOpen className="w-5 h-5" />}
              </button>
            )}
            <button
              onClick={onClose}
              className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg text-slate-500 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Selected Article Meta */}
        <div className="px-4 py-3 bg-slate-50 dark:bg-slate-800/50 border-b border-slate-200 dark:border-slate-800">
          <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 mb-1 uppercase tracking-tighter">
            Talking about:
          </p>
          <p className="text-sm font-bold text-slate-900 dark:text-white line-clamp-2 leading-tight">
            {article.title}
          </p>
        </div>

        {/* Chat History */}
        <div
          ref={scrollRef}
          className="flex-1 overflow-y-auto p-4 space-y-4 bg-white dark:bg-slate-900"
        >
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div className="flex flex-col gap-1 max-w-[85%]">
                <div
                  className={`p-3 rounded-2xl text-sm shadow-sm relative group ${msg.role === "user"
                    ? "bg-blue-600 text-white rounded-tr-none"
                    : "bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200 rounded-tl-none border border-slate-200 dark:border-slate-700"
                    }`}
                >
                  {msg.text}

                  {(msg.role === "ai" || msg.role === "model" || msg.role === "assistant") && (
                    <button
                      onClick={() => handleToggleSpeech(msg.text, idx)}
                      className="absolute -right-8 top-0 p-1.5 text-slate-400 hover:text-blue-600 transition-colors"
                      title={isSpeaking === idx ? "Stop speaking" : "Read aloud"}
                    >
                      {isSpeaking === idx ? (
                        <Square className="w-4 h-4 fill-current" />
                      ) : (
                        <Volume2 className="w-4 h-4" />
                      )}
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="bg-slate-100 dark:bg-slate-800 p-3 rounded-2xl rounded-tl-none border border-slate-200 dark:border-slate-700">
                <div className="flex gap-1">
                  <div className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                  <div className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                  <div className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="p-4 border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
          <form
            onSubmit={handleSendMessage}
            className="relative flex items-center gap-2"
          >
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about this article..."
              className="w-full pl-4 pr-12 py-3 bg-slate-100 dark:bg-slate-800 border-none rounded-xl text-sm text-slate-900 dark:text-white placeholder-slate-500 focus:ring-2 focus:ring-blue-500 transition-all"
              disabled={loading}
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="absolute right-2 p-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-300 dark:disabled:bg-slate-800 text-white rounded-lg transition-all shadow-lg shadow-blue-500/20"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
          <p className="mt-3 text-[10px] text-center text-slate-400">
            Powered by Gemini AI. Answers are grounded by article content.
          </p>
        </div>
      </aside>

      {/* Note Modal for AI Summary */}
      {isNoteModalOpen && (
        <NoteModal
          isOpen={isNoteModalOpen}
          onClose={() => setIsNoteModalOpen(false)}
          articleId={article.article_id || article.id}
          articleTags={article.tags || []}
          initialNote={summaryNote}
          onSave={(newNote) => {
            // Safe fallback if parent state updater isn't wired yet.
            if (!article.note) article.note = newNote;
          }}
          onNoteSaved={onNoteSaved}
        />
      )}
    </div>
  );
};

export default ChatSidebar;
