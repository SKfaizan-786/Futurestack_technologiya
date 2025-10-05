import { useCallback, useEffect, useRef, useState } from 'react';

interface NaturalLanguageInputProps {
  onSubmit: (text: string) => Promise<void>;
  isProcessing: boolean;
}

const exampleInputs = [
  "67 year old female with stage 3 non-small cell lung cancer, EGFR positive, previously treated with erlotinib",
  "52 year old male with metastatic colorectal cancer, failed FOLFOX chemotherapy, lives in Boston MA",
  "Stage 4 breast cancer patient, triple negative, age 45, completed radiation therapy 3 months ago",
];

type Message = { id: string; role: 'user' | 'assistant' | 'system'; text: string };

export function NaturalLanguageInput({ onSubmit, isProcessing }: NaturalLanguageInputProps) {
  const [text, setText] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const listRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight;
    }
  }, [messages]);

  const addMessage = useCallback((m: Message) => {
    setMessages((prev) => [...prev, m]);
  }, []);

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!text.trim()) return;

    const userMsg: Message = { id: String(Date.now()), role: 'user', text: text.trim() };
    addMessage(userMsg);
    setText('');

    try {
      const placeholder: Message = { id: `assistant-${Date.now()}`, role: 'assistant', text: isProcessing ? 'Processing...' : '' };
      addMessage(placeholder);

      await onSubmit(userMsg.text);

      setMessages((prev) => prev.map((m) => (m.id === placeholder.id ? { ...m, text: 'Search completed — showing results.' } : m)));
    } catch (err: any) {
      setMessages((prev) => prev.map((m) => (m.role === 'assistant' && m.text === 'Processing...' ? { ...m, text: 'Failed to process. Please try again.' } : m)));
      console.error(err);
      alert(err?.message || 'Failed to find matching trials.');
    }
  };

  const handleExample = (example: string) => {
    setText(example);
  };

  return (
    <div className="w-full">
      <div className="border border-gray-200 rounded-lg overflow-hidden">
        <div ref={listRef} className="h-48 overflow-y-auto p-4 bg-gray-50">
          {messages.length === 0 && (
            <div className="text-sm text-gray-500">No messages yet — start by typing a patient description.</div>
          )}
          {messages.map((m) => (
            <div key={m.id} className={`max-w-3/4 ${m.role === 'user' ? 'ml-auto text-right' : 'mr-auto text-left'}`}>
              <div
                className={`inline-block px-4 py-2 rounded-lg text-sm ${
                  m.role === 'user' ? 'bg-[#1e68d1] text-white' : 'bg-white border border-gray-200 text-gray-800'
                }`}
              >
                {m.text}
              </div>
            </div>
          ))}
        </div>

        <div className="p-4 border-t border-gray-100">
          <form onSubmit={(e) => void handleSubmit(e)} className="space-y-4">
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="e.g., 65 year old female with stage 3 lung cancer, EGFR positive..."
              rows={4}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#1e68d1] focus:border-transparent resize-none"
              disabled={isProcessing}
            />

            <div className="flex flex-col gap-2">
              {exampleInputs.map((ex, i) => (
                <button
                  key={i}
                  type="button"
                  onClick={() => handleExample(ex)}
                  className="text-left text-xs px-3 py-1 rounded-md bg-gray-100 hover:bg-gray-200 text-gray-700 w-full truncate"
                  disabled={isProcessing}
                >
                  {ex}
                </button>
              ))}
            </div>

            <div className="flex items-center justify-between flex-wrap gap-2">
              <button
                type="button"
                onClick={() => setText('')}
                className="px-3 py-2 rounded-md text-sm text-gray-700 border border-gray-300 hover:bg-gray-100 hover:shadow-sm transition"
                disabled={isProcessing}
              >
                Clear
              </button>
              <button
                type="submit"
                disabled={!text.trim() || isProcessing}
                className="inline-flex items-center gap-2 px-6 py-2 bg-gradient-to-br from-[#1e68d1] to-[#0b4fa1] text-white rounded-lg text-sm font-medium disabled:opacity-50"
              >
                {isProcessing ? (
                  <>
                    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    Finding...
                  </>
                ) : (
                  'Find My Matching Trials'
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}