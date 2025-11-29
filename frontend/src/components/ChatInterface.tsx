import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Loader2, Sparkles, Play, Video } from 'lucide-react';
import { api } from '@/lib/api';
import { AnalysisCard } from './AnalysisCard';
import { ScriptSelection } from './ScriptSelection';
import { ScriptRefinement } from './ScriptRefinement';

import { VideoGeneration } from './VideoGeneration';
import { ImageGeneration } from './ImageGeneration';
import { ImageSlideshow } from './ImageSlideshow';


type Step = 'URL' | 'PRODUCT_IMAGES' | 'ANALYSIS' | 'SCRIPTS' | 'REFINE' | 'IMAGES' | 'AUDIO' | 'VIDEO' | 'DONE';


interface Message {
    id: string;
    role: 'user' | 'agent';
    content?: string;
    component?: React.ReactNode;
}

export const ChatInterface = () => {
    const [messages, setMessages] = useState<Message[]>([
        {
            id: 'welcome',
            role: 'agent',
            content: "Hello! I'm your AI Ad Campaign Manager. Paste a product URL to get started."
        }
    ]);
    const [inputValue, setInputValue] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [step, setStep] = useState<Step>('URL');

    // Data Store
    const [data, setData] = useState<{
        productData?: any;
        analysis?: any;
        scripts?: string[];
        selectedScript?: string;
        audioUrl?: string;
        videoData?: any;
    }>({});

    const dataRef = useRef(data);
    useEffect(() => {
        dataRef.current = data;
    }, [data]);

    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const addMessage = (role: 'user' | 'agent', content?: string, component?: React.ReactNode) => {
        setMessages(prev => [...prev, {
            id: Math.random().toString(36).substring(7),
            role,
            content,
            component
        }]);
    };

    const handleContinueAnalysis = async () => {
        setIsLoading(true);
        addMessage('agent', "Great! Analyzing the product details now...");

        try {
            const analysis = await api.analyze(dataRef.current.productData);
            setData(prev => ({ ...prev, analysis }));

            setStep('ANALYSIS');
            addMessage('agent', undefined, (
                <AnalysisCard
                    analysis={analysis}
                    isRefining={false}
                    onConfirm={handleConfirmAnalysis}
                    onRefine={handleRefineAnalysis}
                />
            ));
        } catch (error) {
            addMessage('agent', "Failed to analyze product.");
        } finally {
            setIsLoading(false);
        }
    };

    const handleRefineAnalysis = async (feedback: string) => {
        setIsLoading(true);
        try {
            // Update the last message to show loading state if needed, or just replace the component
            // For simplicity, we'll just update the data and re-render the last component logic
            // But since components are in the message history, we need a way to update them.
            // A better way is to have the AnalysisCard handle its own loading state and just call us back with new data?
            // Actually, AnalysisCard calls onRefine, we do the API call, then we need to update the UI.

            // Let's replace the last message with a new AnalysisCard
            const newAnalysis = await api.analyze(dataRef.current.productData, feedback, dataRef.current.analysis);
            setData(prev => ({ ...prev, analysis: newAnalysis }));

            // Remove last agent message (the old card) and add new one
            setMessages(prev => {
                const newMsgs = [...prev];
                newMsgs.pop();
                return newMsgs;
            });

            addMessage('agent', "Here is the refined analysis:", (
                <AnalysisCard
                    analysis={newAnalysis}
                    isRefining={false}
                    onConfirm={handleConfirmAnalysis}
                    onRefine={handleRefineAnalysis}
                />
            ));
        } catch (error) {
            console.error(error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleConfirmAnalysis = async () => {
        setStep('SCRIPTS');
        addMessage('agent', "Analysis confirmed! Generating ad scripts...");
        setIsLoading(true);

        try {
            const res = await api.generateScripts(dataRef.current.productData, dataRef.current.analysis);
            setData(prev => ({ ...prev, scripts: res.scripts }));

            addMessage('agent', undefined, (
                <ScriptSelection
                    scripts={res.scripts}
                    isRefining={false}
                    onRefineAll={handleRefineAllScripts}
                    onSelect={handleSelectScript}
                />
            ));
        } catch (error) {
            addMessage('agent', "Failed to generate scripts.");
        } finally {
            setIsLoading(false);
        }
    };

    const handleRefineAllScripts = async (feedback: string) => {
        setIsLoading(true);
        try {
            const res = await api.generateScripts(dataRef.current.productData, dataRef.current.analysis, feedback, dataRef.current.scripts);
            setData(prev => ({ ...prev, scripts: res.scripts }));

            setMessages(prev => {
                const newMsgs = [...prev];
                newMsgs.pop();
                return newMsgs;
            });

            addMessage('agent', "Here are the refined scripts:", (
                <ScriptSelection
                    scripts={res.scripts}
                    isRefining={false}
                    onRefineAll={handleRefineAllScripts}
                    onSelect={handleSelectScript}
                />
            ));
        } catch (error) {
            console.error(error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleSelectScript = (script: string) => {
        setData(prev => ({ ...prev, selectedScript: script }));
        setStep('REFINE');
        addMessage('agent', "Great choice! Let's polish it.", (
            <ScriptRefinement
                script={script}
                isRefining={false}
                onTweak={handleTweakScript}
                onConfirm={handleConfirmScript}
            />
        ));
    };

    const handleTweakScript = async (feedback: string) => {
        if (!dataRef.current.selectedScript) return;
        setIsLoading(true);
        try {
            const res = await api.refineScript(dataRef.current.selectedScript, feedback);
            setData(prev => ({ ...prev, selectedScript: res.script }));

            setMessages(prev => {
                const newMsgs = [...prev];
                newMsgs.pop();
                return newMsgs;
            });

            addMessage('agent', "Updated script:", (
                <ScriptRefinement
                    script={res.script}
                    isRefining={false}
                    onTweak={handleTweakScript}
                    onConfirm={handleConfirmScript}
                />
            ));
        } catch (error) {
            console.error(error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleConfirmScript = async () => {
        if (!dataRef.current.selectedScript) return;
        setStep('IMAGES');
        addMessage('agent', "Script finalized. Let's generate some ad creatives.", (
            <ImageGeneration
                productUrl={dataRef.current.productData.url}
                script={dataRef.current.selectedScript}
                onImagesGenerated={handleImagesGenerated}
                onProceed={handleProceedToAudio}
                api={api}
            />
        ));
    };

    const handleImagesGenerated = (images: string[]) => {
        // Optional: store images in state if needed
        console.log("Generated images:", images);
    };

    const handleProceedToAudio = async () => {
        if (!dataRef.current.selectedScript) return;
        setStep('AUDIO');
        addMessage('agent', "Great! Now generating audio voiceover...");
        setIsLoading(true);

        try {
            const res = await api.generateAudio(dataRef.current.selectedScript);
            setData(prev => ({ ...prev, audioUrl: res.url }));

            addMessage('agent', "Audio generated!", (
                <div className="bg-zinc-900 p-4 rounded-xl border border-zinc-800 w-full max-w-md">
                    <div className="flex items-center gap-3 mb-3">
                        <div className="p-2 bg-indigo-500/20 rounded-full text-indigo-400">
                            <Play size={20} fill="currentColor" />
                        </div>
                        <span className="text-zinc-200 font-medium">Voiceover Preview</span>
                    </div>
                    <audio controls src={`http://localhost:8000${res.url}`} className="w-full" />
                    <button
                        onClick={() => handleGenerateVideo(res.url)}
                        className="mt-4 w-full py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-medium flex items-center justify-center gap-2"
                    >
                        <Video size={16} />
                        Generate Avatar Video
                    </button>
                </div>
            ));
        } catch (error) {
            addMessage('agent', "Failed to generate audio.");
        } finally {
            setIsLoading(false);
        }
    };

    const handleGenerateVideo = async (audioUrl: string) => {
        setStep('VIDEO');
        addMessage('agent', "Let's create a video! Select an avatar below to get started.", (
            <VideoGeneration
                audioUrl={audioUrl}
                onVideoGenerated={(videoUrl) => {
                    addMessage('agent', "Video Ready!", (
                        <div className="bg-zinc-900 p-4 rounded-xl border border-zinc-800 w-full max-w-md">
                            <video controls src={videoUrl} className="w-full rounded-lg" />
                            <a
                                href={videoUrl}
                                target="_blank"
                                rel="noreferrer"
                                className="mt-3 block text-center text-indigo-400 hover:text-indigo-300 text-sm"
                            >
                                Open in new tab
                            </a>
                        </div>
                    ));
                    setStep('DONE');
                }}
            />
        ));
    };

    const handleSend = async () => {
        if (!inputValue.trim()) return;

        const input = inputValue;
        setInputValue('');
        addMessage('user', input);

        if (step === 'URL') {
            setIsLoading(true);
            try {
                const productData = await api.scrape(input);
                setData(prev => ({ ...prev, productData }));

                addMessage('agent', "I've scraped the product data. Here are the images found:");

                setStep('PRODUCT_IMAGES');

                // Prefer downloaded images, fallback to scraped URLs
                const imagesToShow = productData.downloaded_images && productData.downloaded_images.length > 0
                    ? productData.downloaded_images
                    : productData.images;

                addMessage('agent', undefined, (
                    <ImageSlideshow
                        images={imagesToShow}
                        onContinue={handleContinueAnalysis}
                    />
                ));
            } catch (error) {
                addMessage('agent', "Sorry, I couldn't scrape that URL. Please try again.");
            } finally {
                setIsLoading(false);
            }
        } else if (step === 'ANALYSIS') {
            handleRefineAnalysis(input);
        } else if (step === 'SCRIPTS') {
            handleRefineAllScripts(input);
        } else if (step === 'REFINE') {
            handleTweakScript(input);
        }
    };

    return (
        <div className="flex flex-col h-screen bg-black text-zinc-100 font-sans selection:bg-indigo-500/30">
            {/* Header */}
            <header className="flex items-center justify-between px-6 py-4 border-b border-zinc-800 bg-zinc-950/50 backdrop-blur-md sticky top-0 z-10">
                <div className="flex items-center gap-2">
                    <div className="w-8 h-8 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center">
                        <Sparkles size={18} className="text-white" />
                    </div>
                    <h1 className="font-bold text-lg tracking-tight">Vibelets</h1>
                </div>
                <div className="text-xs text-zinc-500 font-mono">v1.0.0</div>
            </header>

            {/* Chat Area */}
            <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6 custom-scrollbar">
                {messages.map((msg) => (
                    <motion.div
                        key={msg.id}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                        <div className={`max-w-[90%] md:max-w-3xl ${msg.role === 'user' ? 'ml-auto' : ''}`}>
                            {msg.content && (
                                <div className={`p-4 rounded-2xl text-sm leading-relaxed shadow-sm ${msg.role === 'user'
                                    ? 'bg-zinc-800 text-white rounded-tr-sm'
                                    : 'bg-zinc-900 border border-zinc-800 text-zinc-300 rounded-tl-sm'
                                    }`}>
                                    {msg.content}
                                </div>
                            )}
                            {msg.component && (
                                <div className="mt-3">
                                    {msg.component}
                                </div>
                            )}
                        </div>
                    </motion.div>
                ))}
                {isLoading && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="flex justify-start"
                    >
                        <div className="bg-zinc-900 border border-zinc-800 p-4 rounded-2xl rounded-tl-sm flex items-center gap-2">
                            <Loader2 className="animate-spin text-indigo-500" size={16} />
                            <span className="text-xs text-zinc-400">Thinking...</span>
                        </div>
                    </motion.div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="p-4 border-t border-zinc-800 bg-zinc-950">
                <div className="max-w-3xl mx-auto relative">
                    <input
                        type="text"
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && !isLoading && handleSend()}
                        placeholder={
                            step === 'URL' ? "Paste product URL here..." :
                                step === 'ANALYSIS' ? "Type to refine analysis (e.g., 'Target audience should be younger')..." :
                                    step === 'SCRIPTS' ? "Type to regenerate all scripts (e.g., 'Make them funnier')..." :
                                        step === 'REFINE' ? "Type to tweak the script..." :
                                            "Type your feedback..."
                        }
                        disabled={isLoading || (step !== 'URL' && step !== 'ANALYSIS' && step !== 'SCRIPTS' && step !== 'REFINE')}
                        className="w-full bg-zinc-900 border border-zinc-800 rounded-xl pl-4 pr-12 py-4 text-zinc-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 disabled:opacity-50 disabled:cursor-not-allowed shadow-inner"
                    />
                    <button
                        onClick={handleSend}
                        disabled={isLoading || !inputValue.trim()}
                        className="absolute right-2 top-2 p-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg transition-colors disabled:opacity-0 disabled:scale-90"
                    >
                        <Send size={18} />
                    </button>
                </div>
            </div>
        </div>
    );
};
