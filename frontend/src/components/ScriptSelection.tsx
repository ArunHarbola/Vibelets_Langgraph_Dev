import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Check, RefreshCw, MessageSquare, ArrowRight } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ScriptSelectionProps {
    scripts: string[];
    onRefineAll: (feedback: string) => void;
    onSelect: (script: string, index: number) => void;
    isRefining: boolean;
}

export const ScriptSelection: React.FC<ScriptSelectionProps> = ({ scripts, onRefineAll, onSelect, isRefining }) => {
    const [activeTab, setActiveTab] = useState(0);
    // Removed internal state for context-aware chat flow


    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 w-full max-w-3xl shadow-lg"
        >
            <div className="flex justify-between items-center mb-6">
                <h3 className="text-xl font-semibold text-zinc-100">Select a Script</h3>
                <p className="text-xs text-zinc-500">
                    Type below to refine all scripts
                </p>
            </div>



            <div className="flex gap-2 mb-4 overflow-x-auto pb-2">
                {scripts.map((_, idx) => (
                    <button
                        key={idx}
                        onClick={() => setActiveTab(idx)}
                        className={cn(
                            "px-4 py-2 rounded-full text-sm font-medium transition-all whitespace-nowrap",
                            activeTab === idx
                                ? "bg-zinc-100 text-zinc-900"
                                : "bg-zinc-800 text-zinc-400 hover:bg-zinc-700 hover:text-zinc-200"
                        )}
                    >
                        Option {idx + 1}
                    </button>
                ))}
            </div>

            <div className="bg-zinc-950 p-6 rounded-xl border border-zinc-800 min-h-[200px] mb-6 relative">
                <div className="whitespace-pre-wrap text-zinc-300 leading-relaxed font-mono text-sm">
                    {scripts[activeTab]}
                </div>
            </div>

            <button
                onClick={() => onSelect(scripts[activeTab], activeTab)}
                className="w-full py-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg font-medium flex items-center justify-center gap-2 transition-all hover:shadow-[0_0_20px_rgba(99,102,241,0.3)] group"
            >
                Select This Script
                <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
            </button>
        </motion.div>
    );
};
