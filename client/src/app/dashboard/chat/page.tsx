"use client";

import { useEffect, useState, useRef } from "react";
import { useWorkspace } from "@/context/WorkspaceContext";
import { useAuth } from "@/context/AuthContext";
import { getChatSessions, getChatSession, sendMessageStream } from "@/services/chat";
import { Brain, Search, PlusCircle, MessageSquare, Loader2, Send } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import ReactMarkdown from "react-markdown";

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
};

type Session = {
  session_id: string;
  title: string;
  updated_at: string;
};

export default function FullChatPage() {
  const { activeWorkspace } = useWorkspace();
  const { accessToken } = useAuth();
  
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const fetchSessions = async () => {
    if (!activeWorkspace) return;
    try {
      const data = await getChatSessions(activeWorkspace.workspace_id);
      setSessions(data || []);
    } catch (e) {
      console.error("Failed to fetch chat sessions:", e);
    }
  };

  useEffect(() => {
    fetchSessions();
  }, [activeWorkspace]);

  useEffect(() => {
    // If no active session, wait for user to select or start new
    if (!activeSessionId || !activeWorkspace) {
        setMessages([]);
        return;
    }

    const loadSession = async () => {
      try {
        const data = await getChatSession(activeWorkspace.workspace_id, activeSessionId);
        setMessages(data.messages || []);
      } catch (e) {
        console.error("Failed to load session:", e);
      }
    };
    loadSession();
  }, [activeSessionId, activeWorkspace]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading || !activeWorkspace) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await sendMessageStream(
        activeWorkspace.workspace_id, 
        userMsg.content, 
        activeSessionId, 
        accessToken
      );
      
      if (!res.body) throw new Error("No response body");
      
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let done = false;
      let buffer = "";
      
      const assistantId = (Date.now() + 1).toString();
      let extractedSessionId = activeSessionId;
      
      setMessages((prev) => [
        ...prev,
        {
          id: assistantId,
          role: "assistant",
          content: "",
        }
      ]);

      setLoading(false); 

      while (!done) {
        const { value, done: readerDone } = await reader.read();
        done = readerDone;
        if (value) {
          const chunk = decoder.decode(value, { stream: true });
          buffer += chunk;
          
          let displayContent = buffer;

          // Parse for __SESSION_ID__ injection logic from backend stream
          if (buffer.includes("__SESSION_ID__:_")) {
              continue; // don't render intermediate chunks
          }
          
          const sessionMatch = buffer.match(/__SESSION_ID__:([a-f0-9-]+)\n\n/);
          if (sessionMatch) {
              extractedSessionId = sessionMatch[1];
              if (!activeSessionId) {
                  setActiveSessionId(extractedSessionId);
              }
              displayContent = buffer.replace(/__SESSION_ID__:[a-f0-9-]+\n\n/, "");
          }

          setMessages((prev) => 
            prev.map((m) => {
              if (m.id === assistantId) {
                return { ...m, content: displayContent };
              }
              return m;
            })
          );
        }
      }
      
      // Refresh the session list in case it's a new chat, but delay to allow dynamo propagation
      setTimeout(fetchSessions, 500);

    } catch (e) {
      console.error(e);
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: "Sorry, I encountered an error while trying to answer that.",
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

  if (!activeWorkspace) {
    return <div className="p-8">Please select a workspace to use Memora Chat.</div>;
  }

  return (
    <div className="flex h-[calc(100vh-4rem)] max-w-full overflow-hidden">
      {/* Sidebar */}
      <div className="w-80 border-r bg-muted/20 flex flex-col hidden md:flex">
        <div className="p-4 border-b">
          <Button 
            className="w-full justify-start gap-2 cursor-pointer" 
            variant="outline"
            onClick={() => setActiveSessionId(null)}
          >
            <PlusCircle className="w-4 h-4" />
            New Architecture Chat
          </Button>
        </div>
        
        <div className="flex-1 overflow-y-auto p-3 space-y-1">
          {sessions.length === 0 ? (
            <div className="text-sm text-muted-foreground p-4 text-center">
              No recent chats
            </div>
          ) : (
            sessions.map((s) => (
              <button
                key={s.session_id}
                onClick={() => setActiveSessionId(s.session_id)}
                className={cn(
                  "w-full flex items-center gap-3 p-3 text-sm rounded-lg transition-colors text-left truncate cursor-pointer",
                  activeSessionId === s.session_id 
                    ? "bg-violet-100 text-violet-900 font-medium" 
                    : "hover:bg-muted/50 text-foreground"
                )}
              >
                <MessageSquare className="w-4 h-4 shrink-0 opacity-70" />
                <span className="truncate">{s.title}</span>
              </button>
            ))
          )}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col bg-background relative h-full">
        {/* Header */}
        <div className="h-14 border-b flex items-center px-6 gap-3 shrink-0">
          <Brain className="w-5 h-5 text-violet-600" />
          <h2 className="font-semibold text-lg text-foreground">
            {activeSessionId 
              ? sessions.find(s => s.session_id === activeSessionId)?.title || "Chat"
              : `New Chat in ${activeWorkspace.name}`
            }
          </h2>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 md:p-8 space-y-6">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center max-w-lg mx-auto text-center space-y-6">
              <div className="w-16 h-16 bg-violet-100 rounded-full flex items-center justify-center">
                <Brain className="w-8 h-8 text-violet-600" />
              </div>
              <h2 className="text-2xl font-bold">How can Memora help?</h2>
              <div className="grid grid-cols-2 gap-4 w-full">
                <div onClick={() => setInput("What was our reasoning for choosing DynamoDB?")} className="p-4 border rounded-xl hover:bg-muted/50 cursor-pointer text-sm text-left transition-colors">
                  <p className="font-medium">Why DynamoDB?</p>
                  <p className="text-muted-foreground mt-1">Review past decisions</p>
                </div>
                <div onClick={() => setInput("Summarize recent API design choices.")} className="p-4 border rounded-xl hover:bg-muted/50 cursor-pointer text-sm text-left transition-colors">
                  <p className="font-medium">Recent Design Choices</p>
                  <p className="text-muted-foreground mt-1">Catch up on API updates</p>
                </div>
              </div>
            </div>
          ) : (
            <div className="max-w-4xl mx-auto space-y-6">
              {messages.map((msg) => (
                <div key={msg.id} className={cn("flex gap-4", msg.role === "user" ? "justify-end" : "justify-start")}>
                  {msg.role === "assistant" && (
                     <div className="w-8 h-8 shrink-0 rounded-full bg-violet-100 flex items-center justify-center mt-1">
                       <Brain className="w-4 h-4 text-violet-600" />
                     </div>
                  )}
                  <div className={cn(
                    "px-5 py-4 rounded-2xl max-w-[85%]",
                    msg.role === "user" 
                      ? "bg-violet-600 text-white rounded-tr-sm" 
                      : "bg-muted/40 border text-foreground rounded-tl-sm"
                  )}>
                    {msg.role === "user" ? (
                      <div className="whitespace-pre-wrap">{msg.content}</div>
                    ) : (
                      <div className="prose prose-sm md:prose-base dark:prose-invert prose-p:leading-relaxed prose-pre:bg-zinc-900 prose-pre:text-zinc-50 max-w-none">
                        <ReactMarkdown>{msg.content}</ReactMarkdown>
                      </div>
                    )}
                  </div>
                </div>
              ))}
              {loading && (
                <div className="flex gap-4 items-center pl-2">
                  <div className="w-8 h-8 shrink-0 rounded-full bg-violet-100 flex items-center justify-center">
                    <Loader2 className="w-4 h-4 text-violet-600 animate-spin" />
                  </div>
                  <span className="text-sm text-muted-foreground">Memora is thinking...</span>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input Bar */}
        <div className="p-4 bg-background shrink-0">
          <div className="max-w-4xl mx-auto relative flex items-center shadow-sm">
             <Input
                placeholder="Ask about architectural decisions, PRs, or knowledge base context..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                className="pr-12 py-6 rounded-2xl border-gray-300 dark:border-gray-800 focus-visible:ring-violet-500 shadow-lg text-base"
                disabled={loading}
              />
              <Button
                size="icon"
                className="absolute right-2 w-10 h-10 rounded-xl bg-violet-600 hover:bg-violet-700 text-white disabled:opacity-50 cursor-pointer transition-all"
                onClick={handleSend}
                disabled={!input.trim() || loading}
              >
                <Send className="w-4 h-4" />
              </Button>
          </div>
          <div className="text-center mt-3">
              <span className="text-xs text-muted-foreground">
                AI responses are generated based on organizational context. Verify details with source PRs.
              </span>
          </div>
        </div>
      </div>
    </div>
  );
}
