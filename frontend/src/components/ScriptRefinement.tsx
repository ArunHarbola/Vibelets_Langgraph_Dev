import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Check, RefreshCw, Wand2 } from 'lucide-react';

interface ScriptRefinementProps {
    script: string;
    onConfirm: () => void;
    onTweak: (feedback: string) => void;
    isRefining: boolean;
}

export const ScriptRefinement: React.FC<ScriptRefinementProps> = ({ script, onConfirm, onTweak, isRefining }) => {
    // Removed internal state for context-aware chat flow


    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 w-full max-w-3xl shadow-lg"
        >
            <div className="flex items-center gap-2 mb-4">
                <Wand2 className="text-purple-400" size={20} />
                <h3 className="text-xl font-semibold text-zinc-100">Final Polish</h3>
            </div>

            <div className="bg-zinc-950 p-6 rounded-xl border border-zinc-800 mb-6">
                <div className="whitespace-pre-wrap text-zinc-300 leading-relaxed font-mono text-sm">
                    {script}
                </div>
            </div>

            <div className="flex flex-col gap-4">
                <p className="text-xs text-center text-zinc-500">
                    Type below to tweak the script...
                </p>

                <button
                    onClick={onConfirm}
                    className="w-full py-3 bg-purple-600 hover:bg-purple-500 text-white rounded-lg font-medium flex items-center justify-center gap-2 transition-all hover:shadow-[0_0_20px_rgba(168,85,247,0.3)]"
                >
                    <Check size={18} />
                    Finalize & Generate Creatives
                </button>
            </div>
        </motion.div>
    );
};
