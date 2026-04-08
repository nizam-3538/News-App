import React, { useState, useEffect } from "react";
import { X, Save, FileText, Tag, Plus } from "lucide-react";
import api from "../utils/api";

const NoteModal = ({ isOpen, onClose, articleId, articleTags = [], initialNote = "", onSave, onNoteSaved }) => {
  const [noteText, setNoteText] = useState(initialNote);
  const [localTags, setLocalTags] = useState(articleTags);
  const [tagInput, setTagInput] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setNoteText(initialNote || "");
      setLocalTags(articleTags || []);
      setTagInput("");
    }
  }, [initialNote, articleTags, isOpen]);

  if (!isOpen) return null;

  const handleSave = async () => {
    if (!articleId) return;
    setIsSaving(true);
    try {
      const promises = [
        api.patch(`/api/saved/${articleId}/note`, { note: noteText }),
        api.patch(`/api/saved/${articleId}/tags`, { tags: localTags })
      ];

      const [noteResponse, tagsResponse] = await Promise.all(promises);

      if (noteResponse.data.ok && tagsResponse.data.ok) {
        if (onSave) onSave(noteText, localTags);
        if (onNoteSaved) onNoteSaved();
        onClose();
      }
    } catch (err) {
      console.error("Failed to save note:", err);
      alert("Failed to save note. Please try again.");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[70] flex items-center justify-center p-4">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm"
        onClick={onClose}
      />
      
      {/* Modal Content */}
      <div className="relative w-full max-w-2xl bg-white dark:bg-slate-900 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-800 flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50">
          <div className="flex items-center gap-2 text-slate-800 dark:text-slate-200 font-semibold">
            <FileText className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            <h3>Personal Notes</h3>
          </div>
          <button 
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-4 flex-1 flex flex-col gap-4">
          
          {/* Tag Editor */}
          <div className="bg-slate-50 dark:bg-slate-950 p-3 rounded-xl border border-slate-200 dark:border-slate-800 shadow-inner">
            <div className="flex items-center gap-2 mb-2 text-xs font-bold text-slate-500 uppercase tracking-widest">
              <Tag className="w-3.5 h-3.5" />
              Categorize
            </div>
            <div className="flex flex-wrap gap-2 mb-3">
              {localTags.map((tag) => (
                <div key={tag} className="flex items-center gap-1 px-2.5 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 text-xs font-bold rounded-md border border-blue-200 dark:border-blue-800">
                  <span>#{tag}</span>
                  <button 
                    onClick={() => setLocalTags(prev => prev.filter(t => t !== tag))}
                    className="p-0.5 hover:bg-blue-200 dark:hover:bg-blue-800 rounded-sm transition-colors text-blue-500 hover:text-blue-700 dark:hover:text-blue-200"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </div>
              ))}
            </div>
            <div className="flex">
              <input
                type="text"
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ',') {
                    e.preventDefault();
                    const val = tagInput.trim().replace(/^#/, '');
                    if (val && !localTags.includes(val)) {
                      setLocalTags([...localTags, val]);
                    }
                    setTagInput("");
                  }
                }}
                placeholder="Add tags... (Press Enter or Comma)"
                className="flex-1 bg-transparent border-none focus:ring-0 text-sm text-slate-800 dark:text-slate-200 placeholder-slate-400 p-0"
              />
            </div>
          </div>
          <textarea
            value={noteText}
            onChange={(e) => setNoteText(e.target.value)}
            placeholder="Add your personal notes or AI summaries here..."
            className="w-full flex-1 min-h-[200px] resize-none p-4 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 text-slate-800 dark:text-slate-200 placeholder-slate-400 focus:outline-none transition-all shadow-inner"
          />
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-200 dark:border-slate-800 flex justify-end gap-3 bg-slate-50 dark:bg-slate-800/50 rounded-b-2xl">
          <button
            onClick={onClose}
            className="px-4 py-2 font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-lg transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="flex items-center gap-2 px-5 py-2 font-bold text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded-lg shadow-md shadow-blue-500/20 transition-all active:scale-95"
          >
            <Save className={`w-4 h-4 ${isSaving ? 'animate-pulse' : ''}`} />
            {isSaving ? 'Saving...' : 'Save Note'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default NoteModal;
