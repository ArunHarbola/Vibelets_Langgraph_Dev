import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Check, RefreshCw, Edit2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface AnalysisCardProps {
    analysis: any;
    onConfirm: () => void;
    onRefine: (feedback: string) => void;
    isRefining: boolean;
}

export const AnalysisCard: React.FC<AnalysisCardProps> = ({ analysis, onConfirm, onRefine, isRefining }) => {
    // Removed internal state for context-aware chat flow


    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 w-full max-w-2xl shadow-lg"
        >
            <div className="flex justify-between items-center mb-4">
                <h3 className="text-xl font-semibold text-zinc-100">Product Analysis</h3>
            </div>

            <div className="space-y-4 text-zinc-300 text-sm max-h-[400px] overflow-y-auto pr-2 custom-scrollbar">
                {Object.entries(analysis).map(([key, value]) => (
                    <div key={key} className="bg-zinc-950/50 p-3 rounded-lg">
                        <span className="text-xs font-bold text-indigo-400 uppercase tracking-wider block mb-1">
                            {key.replace(/_/g, ' ')}
                        </span>
                        <div className="whitespace-pre-wrap">
                            {typeof value === 'string' ? value : JSON.stringify(value, null, 2)}
                        </div>
                    </div>
                ))}
            </div>

            <div className="mt-6 flex flex-col gap-3">
                {/* <button
                    onClick={onConfirm}
                    className="w-full py-3 bg-green-600 hover:bg-green-500 text-white rounded-lg font-medium flex items-center justify-center gap-2 transition-all hover:shadow-[0_0_20px_rgba(34,197,94,0.3)]"
                >
                    <Check size={18} />
                    Confirm Analysis
                </button> */}
                <p className="text-xs text-center text-zinc-500">
                    Type below to refine the analysis...
                </p>
            </div>
        </motion.div>
    );
};
