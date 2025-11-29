import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronLeft, ChevronRight, Play } from 'lucide-react';

interface ImageSlideshowProps {
    images: string[];
    onContinue: () => void;
}

export const ImageSlideshow: React.FC<ImageSlideshowProps> = ({ images, onContinue }) => {
    const [currentIndex, setCurrentIndex] = useState(0);

    const nextSlide = () => {
        setCurrentIndex((prev) => (prev + 1) % images.length);
    };

    const prevSlide = () => {
        setCurrentIndex((prev) => (prev - 1 + images.length) % images.length);
    };

    if (!images || images.length === 0) {
        return (
            <div className="bg-zinc-900 p-4 rounded-xl border border-zinc-800 w-full max-w-md">
                <p className="text-zinc-400 text-sm mb-4">No product images found.</p>
                <button
                    onClick={onContinue}
                    className="w-full py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-medium flex items-center justify-center gap-2"
                >
                    <Play size={16} />
                    Continue to Analysis
                </button>
            </div>
        );
    }

    return (
        <div className="bg-zinc-900 p-4 rounded-xl border border-zinc-800 w-full max-w-md">
            <div className="relative aspect-square bg-zinc-950 rounded-lg overflow-hidden mb-4 group">
                <AnimatePresence mode="wait">
                    <motion.img
                        key={currentIndex}
                        src={images[currentIndex].startsWith('http') ? images[currentIndex] : `http://localhost:8000${images[currentIndex]}`}
                        alt={`Product Image ${currentIndex + 1}`}
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -20 }}
                        transition={{ duration: 0.3 }}
                        className="w-full h-full object-contain"
                    />
                </AnimatePresence>

                {/* Navigation Buttons */}
                {images.length > 1 && (
                    <>
                        <button
                            onClick={prevSlide}
                            className="absolute left-2 top-1/2 -translate-y-1/2 p-2 bg-black/50 hover:bg-black/70 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                            <ChevronLeft size={20} />
                        </button>
                        <button
                            onClick={nextSlide}
                            className="absolute right-2 top-1/2 -translate-y-1/2 p-2 bg-black/50 hover:bg-black/70 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                            <ChevronRight size={20} />
                        </button>
                    </>
                )}

                {/* Dots */}
                <div className="absolute bottom-2 left-1/2 -translate-x-1/2 flex gap-1.5">
                    {images.map((_, idx) => (
                        <div
                            key={idx}
                            className={`w-1.5 h-1.5 rounded-full transition-colors ${idx === currentIndex ? 'bg-white' : 'bg-white/30'
                                }`}
                        />
                    ))}
                </div>
            </div>

            <div className="flex justify-between items-center mb-4">
                <span className="text-xs text-zinc-500">
                    Image {currentIndex + 1} of {images.length}
                </span>
            </div>

            <button
                onClick={onContinue}
                className="w-full py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-medium flex items-center justify-center gap-2"
            >
                <Play size={16} />
                Continue to Analysis
            </button>
        </div>
    );
};
