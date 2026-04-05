"use client";
import React from "react";
import { Github, Twitter, Linkedin, Brain } from "lucide-react";
import Link from "next/link";

export default function Footer() {
  return (
    <footer className="bg-white border-t border-gray-200 pt-16 pb-8">
      <div className="container mx-auto px-4 max-w-7xl">
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-8 mb-12">
          <div className="col-span-2 lg:col-span-2">
            <Link href="/" className="flex items-center gap-2 mb-6">
              <div className="w-8 h-8 rounded-lg bg-violet-600 flex items-center justify-center">
                <Brain className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold tracking-tight text-gray-900">Memora.dev</span>
            </Link>
            <p className="text-gray-500 max-w-xs mb-6">
              Capturing the architectural heartbeat of your engineering team. Built for the 2026 AWS Hackathon for Bharat.
            </p>
            <div className="flex gap-4">
              <Link href="#" className="text-gray-400 hover:text-violet-600 transition-colors">
                <Github className="w-5 h-5" />
              </Link>
              <Link href="#" className="text-gray-400 hover:text-violet-600 transition-colors">
                <Twitter className="w-5 h-5" />
              </Link>
              <Link href="#" className="text-gray-400 hover:text-violet-600 transition-colors">
                <Linkedin className="w-5 h-5" />
              </Link>
            </div>
          </div>
          
          <div>
            <h4 className="font-bold text-gray-900 mb-6">Product</h4>
            <ul className="space-y-4 text-sm text-gray-500">
              <li><Link href="/dashboard" className="hover:text-violet-600">Dashboard</Link></li>
              <li><Link href="/dashboard/chat" className="hover:text-violet-600">Memora Chat</Link></li>
              <li><Link href="/dashboard/adrs" className="hover:text-violet-600">ADR Builder</Link></li>
              <li><Link href="/dashboard/integrations" className="hover:text-violet-600">Integrations</Link></li>
            </ul>
          </div>

          <div>
            <h4 className="font-bold text-gray-900 mb-6">Resources</h4>
            <ul className="space-y-4 text-sm text-gray-500">
              <li><Link href="#" className="hover:text-violet-600">Documentation</Link></li>
              <li><Link href="#" className="hover:text-violet-600">Architecture Guide</Link></li>
              <li><Link href="#" className="hover:text-violet-600">API Reference</Link></li>
              <li><Link href="#" className="hover:text-violet-600">Community</Link></li>
            </ul>
          </div>

          <div>
            <h4 className="font-bold text-gray-900 mb-6">Company</h4>
            <ul className="space-y-4 text-sm text-gray-500">
              <li><Link href="#" className="hover:text-violet-600">About Us</Link></li>
              <li><Link href="#" className="hover:text-violet-600">Privacy Policy</Link></li>
              <li><Link href="#" className="hover:text-violet-600">Terms of Service</Link></li>
            </ul>
          </div>
        </div>
        
        <div className="border-t border-gray-100 pt-8 flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="text-sm text-gray-400">
            © 2026 Memora.dev. Built with ♥ on AWS Bedrock.
          </p>
          <div className="flex gap-8 text-sm text-gray-400">
            <Link href="#" className="hover:text-gray-900">Security</Link>
            <Link href="#" className="hover:text-gray-900">Status</Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
