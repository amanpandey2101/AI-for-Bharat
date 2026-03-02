"use client";

import { useState, useRef, useEffect } from "react";
import { useWorkspace } from "@/context/WorkspaceContext";
import { sendMessageStream } from "@/services/chat";
import { Brain, X, Send, Loader2, Minimize2, Maximize2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import ReactMarkdown from "react-markdown";

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
};

export function ChatWidget() {
  const { activeWorkspace } = useWorkspace();
  const [isOpen, setIsOpen] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom of messages
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
    }
  }, [messages, isOpen]);

  // Initial greeting if opened for the first time
  useEffect(() => {
    if (isOpen && messages.length === 0 && activeWorkspace) {
      setMessages([
        {
          id: "greeting",
          role: "assistant",
          content: `Hi! I'm your Memora AI assistant for the **${activeWorkspace.name}** workspace. You can ask me about past decisions, pull requests, Slack discussions, or Jira tasks.`,
        },
      ]);
    }
  }, [isOpen, messages.length, activeWorkspace]);

  // Hide widget entirely if no workspace is active
  if (!activeWorkspace) {
    return null;
  }

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await sendMessageStream(activeWorkspace.workspace_id, userMsg.content);
      
      if (!res.body) throw new Error("No response body");
      
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let done = false;
      
      const assistantId = (Date.now() + 1).toString();
      
      setMessages((prev) => [
        ...prev,
        {
          id: assistantId,
          role: "assistant",
          content: "",
        }
      ]);

      setLoading(false); // Stop thinking spinner, we're typing now

      while (!done) {
        const { value, done: readerDone } = await reader.read();
        done = readerDone;
        if (value) {
          const chunk = decoder.decode(value, { stream: true });
          
          setMessages((prev) => 
            prev.map((m) => {
              if (m.id === assistantId) {
                return { ...m, content: m.content + chunk };
              }
              return m;
            })
          );
        }
      }
      
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: "Sorry, I encountered an error while trying to answer that. Please make sure the Knowledge Base is configured and try again.",
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <>
      {/* Floating Toggle Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 w-14 h-14 bg-violet-600 hover:bg-violet-700 text-white rounded-full shadow-lg shadow-violet-500/30 flex items-center justify-center transition-transform hover:scale-105 active:scale-95 z-50"
          aria-label="Open AI Assistant"
        >
          <Brain className="w-6 h-6" />
        </button>
      )}

      {/* Chat Window */}
      {isOpen && (
        <div
          className={cn(
            "fixed bottom-6 right-6 bg-background border shadow-2xl rounded-2xl flex flex-col z-50 transition-all duration-300 ease-in-out overflow-hidden",
            isExpanded ? "w-[450px] h-[700px] max-h-[90vh]" : "w-[360px] h-[550px] max-h-[80vh]"
          )}
        >
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b bg-gradient-to-r from-violet-600 to-indigo-600 text-white">
            <div className="flex items-center gap-2">
              <div className="bg-white/20 p-1.5 rounded-lg">
                <Brain className="w-4 h-4" />
              </div>
              <div>
                <h3 className="font-semibold text-sm">Memora AI</h3>
                <p className="text-[10px] text-white/80 opacity-90 truncate max-w-[150px]">
                  {activeWorkspace.name}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-1">
              <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="p-1.5 hover:bg-white/20 rounded-md transition-colors text-white"
              >
                {isExpanded ? (
                  <Minimize2 className="w-4 h-4" />
                ) : (
                  <Maximize2 className="w-4 h-4" />
                )}
              </button>
              <button
                onClick={() => setIsOpen(false)}
                className="p-1.5 hover:bg-white/20 rounded-md transition-colors text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-muted/30">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={cn(
                  "flex flex-col max-w-[85%]",
                  msg.role === "user" ? "ml-auto items-end" : "mr-auto items-start"
                )}
              >
                <div
                  className={cn(
                    "px-4 py-2.5 rounded-2xl text-sm leading-relaxed",
                    msg.role === "user"
                      ? "bg-violet-600 text-white rounded-br-sm"
                      : "bg-background border shadow-sm rounded-bl-sm"
                  )}
                >
                  {msg.role === "user" ? (
                    msg.content
                  ) : (
                    <div className="prose prose-sm prose-p:leading-relaxed prose-pre:bg-muted prose-pre:text-muted-foreground prose-a:text-violet-600 dark:prose-invert max-w-none">
                      <ReactMarkdown>{msg.content}</ReactMarkdown>
                    </div>
                  )}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex items-center gap-2 text-muted-foreground text-sm pl-2">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Thinking...</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="p-3 border-t bg-background">
            <div className="relative flex items-center">
              <Input
                placeholder="Ask about workspace decisions..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                className="pr-12 rounded-full border-muted-foreground/20 focus-visible:ring-violet-500"
                disabled={loading}
              />
              <Button
                size="icon"
                variant="ghost"
                className="absolute right-1 w-8 h-8 rounded-full text-violet-600 hover:text-violet-700 hover:bg-violet-100 disabled:opacity-50"
                onClick={handleSend}
                disabled={!input.trim() || loading}
              >
                <Send className="w-4 h-4" />
              </Button>
            </div>
            <div className="text-center mt-2">
              <span className="text-[10px] text-muted-foreground">
                AI can make mistakes. Verify important decisions.
              </span>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
