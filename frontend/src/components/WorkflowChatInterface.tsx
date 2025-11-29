'use client';

import React, { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
    Send, Loader2, Sparkles, Play, Video,
    CheckCircle2,
    Globe, Search, FileText, Image as ImageIcon,
    Music, User, Film, ArrowLeft, ArrowRight
} from 'lucide-react';
import { workflowApi, WorkflowState } from '@/lib/workflowApi';
import { AnalysisCard } from './AnalysisCard';
import { ScriptSelection } from './ScriptSelection';
import { ScriptRefinement } from './ScriptRefinement';
import { VideoGeneration } from './VideoGeneration';
import { ImageSlideshow } from './ImageSlideshow';

type WorkflowStep =
    | 'scrape'
    | 'analyze'
    | 'generate_scripts'
    | 'select_script'
    | 'refine_script'
    | 'generate_images'
    | 'refine_images'
    | 'generate_audio'
    | 'select_avatar'
    | 'generate_video'
    | 'complete';

interface StepInfo {
    id: WorkflowStep;
    label: string;
    icon: React.ReactNode;
    description: string;
}

const STEPS: StepInfo[] = [
    { id: 'scrape', label: 'Scrape', icon: <Globe size={16} />, description: 'Product URL' },
    { id: 'analyze', label: 'Analyze', icon: <Search size={16} />, description: 'Product Analysis' },
    { id: 'generate_scripts', label: 'Scripts', icon: <FileText size={16} />, description: 'Generate Scripts' },
    { id: 'select_script', label: 'Select', icon: <CheckCircle2 size={16} />, description: 'Choose Script' },
    { id: 'refine_script', label: 'Refine', icon: <FileText size={16} />, description: 'Refine Script' },
    { id: 'generate_images', label: 'Images', icon: <ImageIcon size={16} />, description: 'Generate Images' },
    { id: 'refine_images', label: 'Refine', icon: <ImageIcon size={16} />, description: 'Refine Images' },
    { id: 'generate_audio', label: 'Audio', icon: <Music size={16} />, description: 'Generate Audio' },
    { id: 'select_avatar', label: 'Avatar', icon: <User size={16} />, description: 'Select Avatar' },
    { id: 'generate_video', label: 'Video', icon: <Film size={16} />, description: 'Generate Video' },
];

interface Message {
    id: string;
    role: 'user' | 'agent';
    content?: string;
    component?: React.ReactNode;
}

export const WorkflowChatInterface = () => {
    const [messages, setMessages] = useState<Message[]>([
        {
            id: 'welcome',
            role: 'agent',
            content: "Hello! I'm your AI Ad Campaign Manager. Paste a product URL to get started."
        }
    ]);
    const [inputValue, setInputValue] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [currentStep, setCurrentStep] = useState<WorkflowStep>('scrape');
    const [workflowState, setWorkflowState] = useState<WorkflowState | null>(null);

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

    const updateStateFromResponse = (response: any) => {
        if (response.state) {
            setWorkflowState(response.state);
            if (response.state.current_step) {
                setCurrentStep(response.state.current_step as WorkflowStep);
            }
        }
        if (response.thread_id) {
            workflowApi.setThreadId(response.thread_id);
        }
    };

    const formatError = (error: any): string => {
        if (error.response?.data?.detail) {
            const detail = error.response.data.detail;
            if (typeof detail === 'string') return detail;
            if (Array.isArray(detail)) return detail.map((d: any) => d.msg || JSON.stringify(d)).join(', ');
            return JSON.stringify(detail);
        }
        return error.message || "An unexpected error occurred.";
    };

    const getStepIndex = (step: WorkflowStep): number => {
        return STEPS.findIndex(s => s.id === step);
    };

    const canGoBack = (): boolean => {
        const currentIndex = getStepIndex(currentStep);
        return currentIndex > 0;
    };

    const canGoForward = (): boolean => {
        const currentIndex = getStepIndex(currentStep);
        return currentIndex < STEPS.length - 1 && workflowState !== null;
    };

    const handleNavigate = async (direction: 'back' | 'forward' | 'to', step?: WorkflowStep) => {
        if (direction === 'to' && step) {
            const intent = `go to ${step}`;
            setIsLoading(true);
            try {
                const response = await workflowApi.navigate(intent);
                updateStateFromResponse(response);
                addMessage('agent', `Navigated to ${STEPS.find(s => s.id === step)?.label}`);
            } catch (error) {
                addMessage('agent', 'Failed to navigate. Please try again.');
            } finally {
                setIsLoading(false);
            }
        } else if (direction === 'back' && canGoBack()) {
            const currentIndex = getStepIndex(currentStep);
            const prevStep = STEPS[currentIndex - 1];
            await handleNavigate('to', prevStep.id);
        } else if (direction === 'forward' && canGoForward()) {
            const currentIndex = getStepIndex(currentStep);
            const nextStep = STEPS[currentIndex + 1];
            await handleNavigate('to', nextStep.id);
        }
    };

    const handleScrape = async (url: string) => {
        setIsLoading(true);
        addMessage('user', url);
        addMessage('agent', "Scraping product data...");

        try {
            const response = await workflowApi.scrape(url);
            updateStateFromResponse(response);

            const productData = response.state.product_data;
            if (productData) {
                addMessage('agent', "Product data scraped successfully! Here are the images found:");

                const imagesToShow = productData.downloaded_images && productData.downloaded_images.length > 0
                    ? productData.downloaded_images
                    : productData.images || [];

                addMessage('agent', undefined, (
                    <ImageSlideshow
                        images={imagesToShow}
                        onContinue={async () => {
                            await handleAnalyze();
                        }}
                    />
                ));
            }
        } catch (error: any) {
            addMessage('agent', formatError(error));
        } finally {
            setIsLoading(false);
        }
    };

    const handleAnalyze = async (feedback?: string) => {
        setIsLoading(true);
        if (feedback) {
            addMessage('user', feedback);
        }

        try {
            const response = await workflowApi.analyze(feedback);
            updateStateFromResponse(response);

            const analysis = response.state.analysis;
            if (analysis) {
                addMessage('agent', feedback ? "Here is the refined analysis:" : "Product analysis complete:", (
                    <AnalysisCard
                        analysis={analysis}
                        isRefining={false}
                        onConfirm={async () => {
                            await handleGenerateScripts();
                        }}
                        onRefine={async (fb: string) => {
                            await handleAnalyze(fb);
                        }}
                    />
                ));
            }
        } catch (error: any) {
            addMessage('agent', formatError(error));
        } finally {
            setIsLoading(false);
        }
    };

    const handleGenerateScripts = async (feedback?: string) => {
        setIsLoading(true);
        if (feedback) {
            addMessage('user', feedback);
        } else {
            addMessage('agent', "Generating ad scripts...");
        }

        try {
            const response = await workflowApi.generateScripts(feedback);
            updateStateFromResponse(response);

            const scripts = response.state.scripts;
            if (scripts) {
                addMessage('agent', feedback ? "Here are the refined scripts:" : "Generated 3 ad scripts:", (
                    <ScriptSelection
                        scripts={scripts}
                        isRefining={false}
                        onRefineAll={async (fb: string) => {
                            await handleGenerateScripts(fb);
                        }}
                        onSelect={async (script: string, index: number) => {
                            await handleSelectScript(index);
                        }}
                    />
                ));
            }
        } catch (error: any) {
            addMessage('agent', formatError(error));
        } finally {
            setIsLoading(false);
        }
    };

    const handleSelectScript = async (index: number) => {
        setIsLoading(true);
        try {
            const response = await workflowApi.selectScript(index);
            updateStateFromResponse(response);

            const selectedScript = response.state.selected_script;
            if (selectedScript) {
                addMessage('agent', "Great choice! Let's refine it:", (
                    <ScriptRefinement
                        script={selectedScript}
                        isRefining={false}
                        onTweak={async (fb: string) => {
                            await handleRefineScript(fb);
                        }}
                        onConfirm={async () => {
                            await handleGenerateImages();
                        }}
                    />
                ));
            }
        } catch (error: any) {
            addMessage('agent', formatError(error));
        } finally {
            setIsLoading(false);
        }
    };

    const handleRefineScript = async (feedback: string) => {
        setIsLoading(true);
        addMessage('user', feedback);

        try {
            const response = await workflowApi.refineScript(feedback);
            updateStateFromResponse(response);

            const refinedScript = response.state.selected_script;
            if (refinedScript) {
                setMessages(prev => {
                    const newMsgs = [...prev];
                    newMsgs.pop();
                    return newMsgs;
                });

                addMessage('agent', "Updated script:", (
                    <ScriptRefinement
                        script={refinedScript}
                        isRefining={false}
                        onTweak={async (fb: string) => {
                            await handleRefineScript(fb);
                        }}
                        onConfirm={async () => {
                            await handleGenerateImages();
                        }}
                    />
                ));
            }
        } catch (error: any) {
            addMessage('agent', formatError(error));
        } finally {
            setIsLoading(false);
        }
    };

    const handleGenerateImages = async (feedback?: string) => {
        setIsLoading(true);
        if (feedback) {
            addMessage('user', feedback);
        } else {
            addMessage('agent', "Generating ad creatives...");
        }

        try {
            const response = await workflowApi.generateImages(feedback);
            updateStateFromResponse(response);

            const images = response.state.generated_images;
            if (images && images.length > 0) {
                addMessage('agent', feedback ? "Here are the refined images:" : "Generated ad creatives:", (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 w-full max-w-2xl">
                        {images.map((img, idx) => (
                            <motion.div
                                key={idx}
                                initial={{ opacity: 0, scale: 0.9 }}
                                animate={{ opacity: 1, scale: 1 }}
                                className="relative aspect-square rounded-xl overflow-hidden border border-zinc-800 group"
                            >
                                <img
                                    src={`http://localhost:8000${img}`}
                                    alt={`Generated Ad ${idx + 1}`}
                                    className="w-full h-full object-cover"
                                />
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
                ));

                addMessage('agent', undefined, (
                    <div className="flex gap-2 mt-4">
                        <button
                            onClick={async () => await handleGenerateAudio()}
                            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-medium flex items-center gap-2"
                        >
                            <Music size={16} />
                            Proceed to Audio
                        </button>
                        <button
                            onClick={async () => {
                                const feedback = prompt("How would you like to refine the images?");
                                if (feedback) await handleRefineImages(feedback);
                            }}
                            className="px-4 py-2 bg-zinc-700 hover:bg-zinc-600 text-white rounded-lg text-sm font-medium"
                        >
                            Refine Images
                        </button>
                    </div>
                ));
            }
        } catch (error: any) {
            addMessage('agent', formatError(error));
        } finally {
            setIsLoading(false);
        }
    };

    const handleRefineImages = async (feedback: string) => {
        await handleGenerateImages(feedback);
    };

    const handleGenerateAudio = async () => {
        setIsLoading(true);
        addMessage('agent', "Generating audio voiceover...");

        try {
            const response = await workflowApi.generateAudio();
            updateStateFromResponse(response);

            const audioUrl = response.state.audio_url;
            if (audioUrl) {
                addMessage('agent', "Audio generated!", (
                    <div className="bg-zinc-900 p-4 rounded-xl border border-zinc-800 w-full max-w-md">
                        <div className="flex items-center gap-3 mb-3">
                            <div className="p-2 bg-indigo-500/20 rounded-full text-indigo-400">
                                <Play size={20} fill="currentColor" />
                            </div>
                            <span className="text-zinc-200 font-medium">Voiceover Preview</span>
                        </div>
                        <audio controls src={`http://localhost:8000${audioUrl}`} className="w-full" />
                        <button
                            onClick={async () => await handleSelectAvatar()}
                            className="mt-4 w-full py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-medium flex items-center justify-center gap-2"
                        >
                            <Video size={16} />
                            Select Avatar & Generate Video
                        </button>
                    </div>
                ));
            }
        } catch (error: any) {
            addMessage('agent', formatError(error));
        } finally {
            setIsLoading(false);
        }
    };

    const handleSelectAvatar = async () => {
        setIsLoading(true);
        try {
            const avatarsResponse = await workflowApi.getAvatars();
            const avatars = avatarsResponse.avatars;

            if (avatars && avatars.length > 0) {
                addMessage('agent', "Select an avatar:", (
                    <VideoGeneration
                        audioUrl={workflowState?.audio_url || ''}
                        onVideoGenerated={async (videoUrl) => {
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
                            setCurrentStep('complete');
                        }}
                    />
                ));
            }
        } catch (error: any) {
            addMessage('agent', formatError(error));
        } finally {
            setIsLoading(false);
        }
    };

    const renderStepComponent = (step: WorkflowStep, state: WorkflowState) => {
        switch (step) {
            case 'scrape':
                if (state.product_data) {
                    const imagesToShow = state.product_data.downloaded_images && state.product_data.downloaded_images.length > 0
                        ? state.product_data.downloaded_images
                        : state.product_data.images || [];
                    return (
                        <ImageSlideshow
                            images={imagesToShow}
                            onContinue={async () => await handleAnalyze()}
                        />
                    );
                }
                return null;
            case 'analyze':
                if (state.analysis) {
                    return (
                        <AnalysisCard
                            analysis={state.analysis}
                            isRefining={false}
                            onConfirm={async () => await handleGenerateScripts()}
                            onRefine={async (fb: string) => await handleAnalyze(fb)}
                        />
                    );
                }
                return null;
            case 'generate_scripts':
            case 'select_script':
                if (state.scripts) {
                    return (
                        <ScriptSelection
                            scripts={state.scripts}
                            isRefining={false}
                            onRefineAll={async (fb: string) => await handleGenerateScripts(fb)}
                            onSelect={async (script: string, index: number) => await handleSelectScript(index)}
                        />
                    );
                }
                return null;
            case 'refine_script':
                if (state.selected_script) {
                    return (
                        <ScriptRefinement
                            script={state.selected_script}
                            isRefining={false}
                            onTweak={async (fb: string) => await handleRefineScript(fb)}
                            onConfirm={async () => await handleGenerateImages()}
                        />
                    );
                }
                return null;
            case 'generate_images':
            case 'refine_images':
                if (state.generated_images && state.generated_images.length > 0) {
                    return (
                        <div>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 w-full max-w-2xl">
                                {state.generated_images.map((img, idx) => (
                                    <motion.div
                                        key={idx}
                                        initial={{ opacity: 0, scale: 0.9 }}
                                        animate={{ opacity: 1, scale: 1 }}
                                        className="relative aspect-square rounded-xl overflow-hidden border border-zinc-800 group"
                                    >
                                        <img
                                            src={`http://localhost:8000${img}`}
                                            alt={`Generated Ad ${idx + 1}`}
                                            className="w-full h-full object-cover"
                                        />
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
                            <div className="flex gap-2 mt-4">
                                <button
                                    onClick={async () => await handleGenerateAudio()}
                                    className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-medium flex items-center gap-2"
                                >
                                    <Music size={16} />
                                    Proceed to Audio
                                </button>
                                <button
                                    onClick={async () => {
                                        const feedback = prompt("How would you like to refine the images?");
                                        if (feedback) await handleRefineImages(feedback);
                                    }}
                                    className="px-4 py-2 bg-zinc-700 hover:bg-zinc-600 text-white rounded-lg text-sm font-medium"
                                >
                                    Refine Images
                                </button>
                            </div>
                        </div>
                    );
                }
                return null;
            case 'generate_audio':
                if (state.audio_url) {
                    return (
                        <div className="bg-zinc-900 p-4 rounded-xl border border-zinc-800 w-full max-w-md">
                            <div className="flex items-center gap-3 mb-3">
                                <div className="p-2 bg-indigo-500/20 rounded-full text-indigo-400">
                                    <Play size={20} fill="currentColor" />
                                </div>
                                <span className="text-zinc-200 font-medium">Voiceover Preview</span>
                            </div>
                            <audio controls src={`http://localhost:8000${state.audio_url}`} className="w-full" />
                            <button
                                onClick={async () => await handleSelectAvatar()}
                                className="mt-4 w-full py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-medium flex items-center justify-center gap-2"
                            >
                                <Video size={16} />
                                Select Avatar & Generate Video
                            </button>
                        </div>
                    );
                }
                return null;
            case 'select_avatar':
                // For select_avatar, we might need to fetch avatars if not in state, 
                // but usually the component handles it or we pass it.
                // For now, VideoGeneration component handles avatar selection if audioUrl is present.
                if (state.audio_url) {
                    return (
                        <VideoGeneration
                            audioUrl={state.audio_url}
                            onVideoGenerated={async (videoUrl) => {
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
                                setCurrentStep('complete');
                            }}
                        />
                    );
                }
                return null;
            case 'generate_video':
            case 'complete':
                if (state.video_url) {
                     return (
                        <div className="bg-zinc-900 p-4 rounded-xl border border-zinc-800 w-full max-w-md">
                            <video controls src={state.video_url} className="w-full rounded-lg" />
                            <a
                                href={state.video_url}
                                target="_blank"
                                rel="noreferrer"
                                className="mt-3 block text-center text-indigo-400 hover:text-indigo-300 text-sm"
                            >
                                Open in new tab
                            </a>
                        </div>
                    );
                }
                return null;
            default:
                return null;
        }
    };

    const handleSend = async () => {
        if (!inputValue.trim() || isLoading) return;

        const input = inputValue;
        setInputValue('');
        addMessage('user', input);
        setIsLoading(true);

        try {
            let response;
            
            // If we are in the initial scrape step and input looks like a URL, treat as scrape
            if (currentStep === 'scrape' && (input.startsWith('http') || input.startsWith('www'))) {
                response = await workflowApi.scrape(input);
            } else {
                // Otherwise, treat as chat/navigation/refinement
                response = await workflowApi.chat(input);
            }

            updateStateFromResponse(response);
            
            // Check if step changed or if we need to show a component for the current step
            const newStep = response.state.current_step as WorkflowStep;
            const component = renderStepComponent(newStep, response.state);
            
            if (component) {
                // Determine message based on step
                let msg = "Here is the result:";
                if (newStep === 'scrape') msg = "Product data scraped successfully!";
                else if (newStep === 'analyze') msg = "Here is the analysis:";
                else if (newStep === 'generate_scripts') msg = "Here are the generated scripts:";
                else if (newStep === 'generate_images') msg = "Here are the generated images:";
                else if (newStep === 'generate_audio') msg = "Audio generated!";
                else if (newStep === 'generate_video') msg = "Video generated!";
                
                addMessage('agent', msg, component);
            } else {
                // If no component, maybe just a text response or confirmation
                addMessage('agent', "Processed your request. What would you like to do next?");
            }

        } catch (error: any) {
            addMessage('agent', formatError(error));
        } finally {
            setIsLoading(false);
        }
    };

    const getCurrentStepInfo = () => {
        return STEPS.find(s => s.id === currentStep) || STEPS[0];
    };

    const getStepStatus = (step: WorkflowStep): 'completed' | 'current' | 'pending' => {
        if (!workflowState) return 'pending';

        const stepIndex = getStepIndex(step);
        const currentIndex = getStepIndex(currentStep);

        if (stepIndex < currentIndex) return 'completed';
        if (stepIndex === currentIndex) return 'current';
        return 'pending';
    };

    return (
        <div className="flex flex-col h-screen bg-black text-zinc-100 font-sans selection:bg-indigo-500/30">
            {/* Header with Step Indicators */}
            <header className="flex flex-col border-b border-zinc-800 bg-zinc-950/50 backdrop-blur-md sticky top-0 z-10">
                <div className="flex items-center justify-between px-6 py-4">
                    <div className="flex items-center gap-2">
                        <div className="w-8 h-8 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center">
                            <Sparkles size={18} className="text-white" />
                        </div>
                        <h1 className="font-bold text-lg tracking-tight">Vibelets</h1>
                    </div>
                    <div className="flex items-center gap-2">
                        <button
                            onClick={() => handleNavigate('back')}
                            disabled={!canGoBack() || isLoading}
                            className="p-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                            title="Go back"
                        >
                            <ArrowLeft size={18} />
                        </button>
                        <button
                            onClick={() => handleNavigate('forward')}
                            disabled={!canGoForward() || isLoading}
                            className="p-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                            title="Go forward"
                        >
                            <ArrowRight size={18} />
                        </button>
                    </div>
                </div>

                {/* Step Progress Bar */}
                <div className="px-6 pb-4 overflow-x-auto">
                    <div className="flex items-center gap-2 min-w-max">
                        {STEPS.map((step, index) => {
                            const status = getStepStatus(step.id);
                            return (
                                <React.Fragment key={step.id}>
                                    <button
                                        onClick={() => handleNavigate('to', step.id)}
                                        disabled={isLoading}
                                        className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium transition-all whitespace-nowrap ${status === 'completed'
                                                ? 'bg-green-500/20 text-green-400 hover:bg-green-500/30'
                                                : status === 'current'
                                                    ? 'bg-indigo-500/20 text-indigo-400 ring-2 ring-indigo-500/50'
                                                    : 'bg-zinc-800/50 text-zinc-500 hover:bg-zinc-800'
                                            } disabled:opacity-50 disabled:cursor-not-allowed`}
                                        title={step.description}
                                    >
                                        {step.icon}
                                        <span className="hidden sm:inline">{step.label}</span>
                                    </button>
                                    {index < STEPS.length - 1 && (
                                        <div className={`h-0.5 w-8 ${status === 'completed' ? 'bg-green-500' : 'bg-zinc-800'
                                            }`} />
                                    )}
                                </React.Fragment>
                            );
                        })}
                    </div>
                </div>
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
                            <span className="text-xs text-zinc-400">Processing...</span>
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
                            currentStep === 'scrape'
                                ? "Paste product URL here..."
                                : `Type to edit ${getCurrentStepInfo().label.toLowerCase()} (e.g., "Make it more energetic")...`
                        }
                        disabled={isLoading}
                        className="w-full bg-zinc-900 border border-zinc-800 rounded-xl pl-4 pr-12 py-4 text-zinc-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 disabled:opacity-50 disabled:cursor-not-allowed shadow-inner"
                    />
                    <button
                        onClick={handleSend}
                        disabled={isLoading || !inputValue.trim()}
                        className="absolute right-2 top-2 p-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg transition-colors disabled:opacity-50 disabled:scale-90"
                    >
                        <Send size={18} />
                    </button>
                </div>
                <div className="max-w-3xl mx-auto mt-2 text-xs text-zinc-500 text-center">
                    Current step: <span className="text-indigo-400 font-medium">{getCurrentStepInfo().description}</span>
                </div>
            </div>
        </div>
    );
};

