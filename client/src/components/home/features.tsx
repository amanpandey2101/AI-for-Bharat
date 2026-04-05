"use client";
import React from "react";
import { Brain, Zap, Github, MessageSquare, ShieldCheck, Cpu } from "lucide-react";
import { cn } from "@/lib/utils";

const features = [
  {
    title: "Invisible Ingestion",
    description: "Capture decision evidence from Slack, WhatsApp, and GitHub threads without leaving your favorite tools.",
    icon: Github,
    color: "bg-blue-500/10 text-blue-600",
    className: "md:col-span-1",
  },
  {
    title: "Zero-Cost Heuristics",
    description: "Our Smart Heuristic Filter removes 95% of 'Hello' noise before it touches expensive LLM endpoints. Frugal engineering for the 2026 enterprise.",
    icon: Zap,
    color: "bg-amber-500/10 text-amber-600",
    className: "md:col-span-1",
  },
  {
    title: "Decision Memory Graph",
    description: "Built on Amazon Bedrock + OpenSearch Serverless. A living knowledge graph that maps human rationale to codebase evolution.",
    icon: Brain,
    color: "bg-violet-500/10 text-violet-600",
    className: "md:col-span-2",
  },
  {
    title: "Agentic PR Mentorship",
    description: "Automated peer reviews that prevent architectural drift by suggesting context from past engineering decisions.",
    icon: Cpu,
    color: "bg-emerald-500/10 text-emerald-600",
    className: "md:col-span-2",
  },
  {
    title: "Semantic Chat",
    description: "Ask 'Why did we use DynamoDB?' and get human-like answers with cited evidence from historical conversations.",
    icon: MessageSquare,
    color: "bg-rose-500/10 text-rose-600",
    className: "md:col-span-1",
  },
  {
    title: "High-Fidelity ADRs",
    description: "One-click conversion from informal chat to formal Architecture Decision Records. PRs auto-pushed to your repo.",
    icon: ShieldCheck,
    color: "bg-indigo-500/10 text-indigo-600",
    className: "md:col-span-1",
  },
];

export function Features() {
  return (
    <section className="py-24 bg-white">
      <div className="container mx-auto px-4 max-w-7xl">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-5xl font-bold tracking-tight text-gray-900 mb-4">
            The Context Engine for Engineering Teams
          </h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Stop losing vital architectural context in the noise of fast-paced development. 
            Memora captures every 'Why' as it happens.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {features.map((feature, i) => (
            <div
              key={i}
              className={cn(
                "group relative p-8 rounded-3xl border border-gray-100 bg-gray-50 flex flex-col justify-between transition-all duration-300 hover:shadow-xl hover:border-gray-200 hover:-translate-y-1",
                feature.className
              )}
            >
              <div>
                <div className={cn("w-12 h-12 rounded-2xl flex items-center justify-center mb-6", feature.color)}>
                  <feature.icon className="w-6 h-6" />
                </div>
                <h3 className="text-xl font-bold text-gray-900 mb-3">{feature.title}</h3>
                <p className="text-gray-600 leading-relaxed">{feature.description}</p>
              </div>
              <div className="mt-8 flex items-center text-sm font-semibold text-gray-900 opacity-0 group-hover:opacity-100 transition-opacity">
                Learn more →
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
