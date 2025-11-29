import React, { useState } from 'react';
import { Loader2, Image as ImageIcon, ArrowRight } from 'lucide-react';
import { motion } from 'framer-motion';

interface ImageGenerationProps {
    productUrl: string;
    script: string;
    onImagesGenerated: (images: string[]) => void;
    onProceed: () => void;
    api: any; // Pass api instance or function
}

export const ImageGeneration = ({ productUrl, script, onImagesGenerated, onProceed, api }: ImageGenerationProps) => {
    const [isLoading, setIsLoading] = useState(false);
    const [images, setImages] = useState<string[]>([]);
    const [error, setError] = useState<string | null>(null);

    const handleGenerate = async () => {
        setIsLoading(true);
        setError(null);
        try {
            const res = await api.generateImages(productUrl, script);
            setImages(res.images);
            onImagesGenerated(res.images);
        } catch (err) {
            setError("Failed to generate images. Please try again.");
        } finally {
            setIsLoading(false);
        }
    };

    if (images.length > 0) {
        return (
            <div className="w-full max-w-2xl space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {images.map((img, idx) => (
                        <motion.div
                            key={idx}
                            initial={{ opacity: 0, scale: 0.9 }}
                            animate={{ opacity: 1, scale: 1 }}
                            transition={{ delay: idx * 0.1 }}
                            className="relative aspect-square rounded-xl overflow-hidden border border-zinc-800 group"
                        >
                            <img src={`http://localhost:8000${img}`} alt={`Generated Ad ${idx + 1}`} className="w-full h-full object-cover" />
                            <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                                <a 
                                    href={`http://localhost:8000${img}`} 
                                    target="_blank" 
                                    rel="noreferrer"
                                    className="px-4 py-2 bg-white text-black rounded-full text-sm font-medium hover:bg-zinc-200 transition-colors"
                                >
                                    View Full
                                </a>
                            </div>
                        </motion.div>
                    ))}
                </div>
                <div className="flex justify-end">
                    <button
                        onClick={onProceed}
                        className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-medium transition-colors"
                    >
                        <span>Proceed to Audio</span>
                        <ArrowRight size={16} />
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="w-full max-w-md bg-zinc-900 border border-zinc-800 rounded-xl p-6">
            <div className="flex flex-col items-center text-center space-y-4">
                <div className="w-12 h-12 bg-indigo-500/20 rounded-full flex items-center justify-center text-indigo-400">
                    <ImageIcon size={24} />
                </div>
                <div>
                    <h3 className="text-lg font-medium text-zinc-200">Generate Ad Creatives</h3>
                    <p className="text-sm text-zinc-400 mt-1">
                        Create professional ad variations based on your script and product.
                    </p>
                </div>
                
                {error && (
                    <div className="text-red-400 text-xs bg-red-500/10 px-3 py-2 rounded-lg w-full">
                        {error}
                    </div>
                )}

                <button
                    onClick={handleGenerate}
                    disabled={isLoading}
                    className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-600/50 disabled:cursor-not-allowed text-white rounded-lg text-sm font-medium flex items-center justify-center gap-2 transition-colors"
                >
                    {isLoading ? (
                        <>
                            <Loader2 size={16} className="animate-spin" />
                            <span>Generating Creatives...</span>
                        </>
                    ) : (
                        <>
                            <ImageIcon size={16} />
                            <span>Generate Images</span>
                        </>
                    )}
                </button>
            </div>
        </div>
    );
};
