"use client";
import React from "react";
import { cn } from "@/lib/utils";
import { MessageSquare, Cpu, ShieldCheck, CheckCircle2 } from "lucide-react";

const steps = [
  {
    title: "1. Natural Conversation",
    description: "Discuss design choices where they happen — in Slack or GitHub pull requests. No extra documentation required.",
    icon: MessageSquare,
    color: "text-blue-600 bg-blue-100",
  },
  {
    title: "2. Autonomous Inference",
    description: "Memora’s AI Agents monitor established channels and automatically infer architectural decisions as they occur.",
    icon: Cpu,
    color: "text-purple-600 bg-purple-100",
  },
  {
    title: "3. Semantic Refinement",
    description: "Validate the AI’s findings or refine the metadata using our intuitive human-in-the-loop dashboard.",
    icon: ShieldCheck,
    color: "text-emerald-600 bg-emerald-100",
  },
  {
    title: "4. Living Documentation",
    description: "Inferred decisions become high-fidelity ADRs, automatically pushed to your repo and indexed for semantic search.",
    icon: CheckCircle2,
    color: "text-indigo-600 bg-indigo-100",
  },
];

export function HowItWorks() {
  return (
    <section className="py-24 bg-gray-50 border-y border-gray-200">
      <div className="container mx-auto px-4 max-w-6xl">
        <div className="text-center mb-20">
          <h2 className="text-3xl md:text-5xl font-bold tracking-tight text-gray-900 mb-4">
            How Memora Captures Decision Context
          </h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            A frictionless loop that turns developer conversations into enterprise-grade documentation.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {steps.map((step, i) => (
            <div key={i} className="relative flex flex-col items-center text-center">
              {/* Connector line for desktop */}
              {i < steps.length - 1 && (
                <div className="hidden md:block absolute top-12 left-1/2 w-full h-[2px] bg-gray-200 -z-10" />
              )}
              
              <div className={cn("w-20 h-20 rounded-3xl flex items-center justify-center mb-8 shadow-sm transition-transform hover:scale-110", step.color)}>
                <step.icon className="w-10 h-10" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-3">{step.title}</h3>
              <p className="text-sm text-gray-500 leading-relaxed max-w-[240px]">
                {step.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
