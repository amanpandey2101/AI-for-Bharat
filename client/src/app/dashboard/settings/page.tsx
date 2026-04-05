"use client";

import React from "react";
import { 
  User, 
  Github, 
  Slack, 
  ShieldCheck, 
  LayoutDashboard,
  ExternalLink,
  RefreshCcw,
  CheckCircle2,
  AlertCircle
} from "lucide-react";
import { useWorkspace } from "@/context/WorkspaceContext";
import { Button } from "@/components/ui/button";

export default function SettingsPage() {
  const { activeWorkspace } = useWorkspace();

  const integrations = [
    { 
      name: "GitHub", 
      icon: <Github className="w-5 h-5" />, 
      status: "Connected", 
      details: "4 repositories tracked",
      lastSync: "2 mins ago"
    },
    { 
      name: "Slack", 
      icon: <Slack className="w-5 h-5" />, 
      status: "Connected", 
      details: "#engineering, #architecture",
      lastSync: "10 mins ago"
    },
    { 
      name: "Jira", 
      icon: <LayoutDashboard className="w-5 h-5" />, 
      status: "Setup Required", 
      details: "Connect to track tickets",
      lastSync: "N/A"
    }
  ];

  return (
    <div className="max-w-5xl mx-auto space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-700">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 tracking-tight">Settings</h1>
        <p className="text-gray-500 mt-1">Manage your engineering memory, workspace preferences, and AI integrations.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {/* Left Column: Profile & Account */}
        <div className="md:col-span-1 space-y-6">
          <div className="p-6 bg-white rounded-3xl border border-gray-100 shadow-sm">
            <div className="flex flex-col items-center text-center">
              <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center text-white mb-4 shadow-lg">
                <User className="w-10 h-10" />
              </div>
              <h2 className="text-lg font-bold text-gray-900">Engineering Lead</h2>
              <p className="text-xs text-gray-500">memora-dev-team@internal.com</p>
              <Button variant="outline" size="sm" className="mt-4 rounded-xl border-gray-200">
                Edit Profile
              </Button>
            </div>
          </div>

          <div className="p-6 bg-gray-900 rounded-3xl text-white shadow-xl overflow-hidden relative">
            <div className="relative z-10">
               <div className="flex items-center gap-2 mb-4">
                  <ShieldCheck className="w-5 h-5 text-emerald-400" />
                  <span className="text-sm font-bold uppercase tracking-wider text-emerald-400">Pro Account</span>
               </div>
               <p className="text-sm text-gray-300 mb-6">You&rsquo;re currently monitoring 12,000 architectural vectors across 3 environments.</p>
               <Button className="w-full bg-white text-black hover:bg-gray-100 rounded-xl font-bold h-10 transition-all">
                 Upgrade Plan
               </Button>
            </div>
            <div className="absolute -bottom-10 -right-10 w-40 h-40 bg-blue-500/10 rounded-full blur-3xl" />
          </div>
        </div>

        {/* Right Column: Main Settings */}
        <div className="md:col-span-2 space-y-8">
          {/* Workspace Status */}
          <section>
            <div className="flex items-center justify-between mb-4">
               <h3 className="text-sm font-bold uppercase tracking-widest text-gray-400">Workspace Status</h3>
               <span className="px-2 py-0.5 bg-emerald-50 text-emerald-600 rounded-full text-[10px] font-bold border border-emerald-100">AI ACTIVE</span>
            </div>
            <div className="p-6 bg-white rounded-3xl border border-gray-100 shadow-sm space-y-4">
               <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs font-bold text-gray-400 uppercase tracking-tight">Active Context</p>
                    <p className="text-lg font-bold text-gray-900">{activeWorkspace?.name || "No Active Workspace"}</p>
                  </div>
                  <Button variant="ghost" size="icon" className="rounded-full hover:bg-gray-50">
                    <RefreshCcw className="w-4 h-4 text-gray-400" />
                  </Button>
               </div>
               <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-50">
                  <div className="space-y-1">
                    <p className="text-[10px] font-bold text-gray-400 uppercase tracking-tight">Inference Model</p>
                    <p className="text-sm font-semibold text-gray-700 italic">Amazon Bedrock • Nova Lite</p>
                  </div>
                  <div className="space-y-1 text-right">
                    <p className="text-[10px] font-bold text-gray-400 uppercase tracking-tight">Knowledge Base</p>
                    <p className="text-sm font-semibold text-gray-700">KB-AF89...4D2B</p>
                  </div>
               </div>
            </div>
          </section>

          {/* Integrations Health */}
          <section>
            <h3 className="text-sm font-bold uppercase tracking-widest text-gray-400 mb-4">Integration Health</h3>
            <div className="space-y-3">
              {integrations.map((item) => (
                <div key={item.name} className="flex items-center justify-between p-4 bg-white rounded-2xl border border-gray-100 shadow-sm group hover:border-blue-100 transition-all">
                  <div className="flex items-center gap-4">
                    <div className={`p-3 rounded-xl ${item.status === "Connected" ? "bg-gray-50 text-gray-900" : "bg-gray-50 text-gray-300"}`}>
                      {item.icon}
                    </div>
                    <div>
                      <p className="text-sm font-bold text-gray-900">{item.name}</p>
                      <p className="text-xs text-gray-500">{item.details}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    {item.status === "Connected" ? (
                      <div className="flex items-center gap-1">
                        <CheckCircle2 className="w-3 h-3 text-emerald-500" />
                        <span className="text-[10px] font-bold text-emerald-600 uppercase tracking-widest">Live</span>
                      </div>
                    ) : (
                      <div className="flex items-center gap-1">
                        <AlertCircle className="w-3 h-3 text-amber-500" />
                        <span className="text-[10px] font-bold text-amber-600 uppercase tracking-widest">Setup</span>
                      </div>
                    )}
                    <Button variant="ghost" size="icon" className="rounded-full text-gray-300 hover:text-blue-600 opacity-0 group-hover:opacity-100 transition-all">
                      <ExternalLink className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
