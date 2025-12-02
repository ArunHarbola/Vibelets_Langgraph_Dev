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
import { FacebookAuth } from './FacebookAuth';

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
    | 'facebook_auth'
    | 'select_ad_account'
    | 'select_media'
    | 'preview_campaign'
    | 'refine_campaign'
    | 'publish_campaign'
    | 'complete';

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

    // Helper functions for specific actions (kept for component callbacks)
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
                // Remove previous refinement card to avoid clutter
                setMessages(prev => {
                    const newMsgs = [...prev];
                    // Optional: remove logic if we want to keep history
                    // newMsgs.pop(); 
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
                            <div className="flex flex-wrap gap-2 mt-4">
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
                                <button
                                    onClick={() => handleSendWithInput("Create Facebook Campaign")}
                                    className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium flex items-center gap-2"
                                >
                                    <Globe size={16} />
                                    Create Facebook Campaign
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
            case 'facebook_auth':
                return (
                    <FacebookAuth
                        onLogin={(accessToken) => handleSendWithInput(accessToken)}
                    />
                );
            case 'select_ad_account':
                if (state.ad_accounts && state.ad_accounts.length > 0) {
                    return (
                        <div className="bg-zinc-900 p-4 rounded-xl border border-zinc-800 w-full max-w-md">
                            <h3 className="text-zinc-200 font-medium mb-3">Select Ad Account</h3>
                            <div className="space-y-2">
                                {state.ad_accounts.map((account: any) => (
                                    <button
                                        key={account.id}
                                        onClick={async () => {
                                            setIsLoading(true);
                                            // We can use the chat endpoint to select, as the agent will route it
                                            // Or we can add a specific API call if needed. 
                                            // For now, let's simulate a user message selecting the account
                                            // But ideally we should have a direct API call or use the generic chat.
                                            // Let's use a direct state update via chat for now to keep it simple
                                            // "Select account <id>"
                                            // But wait, the backend node checks state.selected_ad_account_id
                                            // We need to set that.
                                            // Let's assume the backend agent can parse "Select account X" or we send a hidden command.
                                            // Actually, the cleanest way is to just send the ID as a message and let the agent/node handle it,
                                            // OR update the state directly.
                                            // Since we don't have a specific "selectAdAccount" API method in workflowApi yet,
                                            // let's assume we can just send the ID.
                                            // However, the backend `_select_ad_account_node` checks `state.selected_ad_account_id`.
                                            // The `NavigationAgent` or `GuideAgent` doesn't automatically set that.
                                            // We might need to update the backend to handle this, OR just add a simple API method.
                                            // For this implementation, I'll assume we send a message "Select account {id}" and the backend *should* handle it,
                                            // but since I didn't implement an agent to parse that, I should probably add a specific API call or 
                                            // rely on the `_select_ad_account_node` to parse the message?
                                            // Looking at `_select_ad_account_node` in backend:
                                            // It just checks `state.get("selected_ad_account_id")`.
                                            // It does NOT parse messages.
                                            // So I need to update the backend node to parse messages OR add an API call.
                                            // I'll add an API call to `workflowApi` (I can't edit that file easily without seeing it, but I can assume it exists or I'll add it).
                                            // Wait, I can't edit `workflowApi.ts` easily if I haven't read it.
                                            // Let's check `workflowApi.ts` first? No, I'll just send a message and update the backend node to parse it.
                                            // Actually, I already wrote the backend node and it DOES NOT parse messages.
                                            // I should update the backend node `_select_ad_account_node` to parse the message.
                                            // I will do that in a separate step. For now, I'll implement the frontend to send the ID.

                                            // UPDATE: I will send a message with the ID.
                                            handleSendWithInput(`Select account ${account.id}`);
                                        }}
                                        className="w-full p-3 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-left transition-colors flex justify-between items-center"
                                    >
                                        <span className="font-medium text-zinc-200">{account.name}</span>
                                        <span className="text-xs text-zinc-500">{account.id}</span>
                                    </button>
                                ))}
                            </div>
                        </div>
                    );
                }
                return null;
            case 'select_media':
                // Show video and images
                const mediaItems = [];
                if (state.video_url) {
                    mediaItems.push({ type: 'video', url: state.video_url, id: 'generated_video' });
                }
                if (state.generated_images) {
                    state.generated_images.forEach((img: string, idx: number) => {
                        mediaItems.push({ type: 'image', url: img, id: `image_${idx}` });
                    });
                }

                if (mediaItems.length > 0) {
                    return (
                        <div className="w-full max-w-2xl">
                            <h3 className="text-zinc-200 font-medium mb-3">Select Creative for Ad</h3>
                            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                                {mediaItems.map((item, idx) => (
                                    <div
                                        key={idx}
                                        onClick={() => handleSendWithInput(`Select media ${item.url}`)}
                                        className="cursor-pointer group relative aspect-square rounded-xl overflow-hidden border border-zinc-800 hover:border-indigo-500 transition-all"
                                    >
                                        {item.type === 'video' ? (
                                            <video src={item.url} className="w-full h-full object-cover" />
                                        ) : (
                                            <img src={`http://localhost:8000${item.url}`} className="w-full h-full object-cover" alt="Ad Creative" />
                                        )}
                                        <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 flex items-center justify-center transition-opacity">
                                            <span className="px-3 py-1 bg-indigo-600 text-white text-xs rounded-full">Select</span>
                                        </div>
                                        {item.type === 'video' && (
                                            <div className="absolute top-2 right-2 bg-black/70 p-1 rounded-full">
                                                <Video size={12} className="text-white" />
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </div>
                    );
                }
                return null;
            case 'preview_campaign':
            case 'refine_campaign':
                if (state.campaign_preview) {
                    return (
                        <div className="bg-zinc-900 p-6 rounded-xl border border-zinc-800 w-full max-w-2xl">
                            <h3 className="text-zinc-200 font-medium mb-4 flex items-center gap-2">
                                <FileText size={18} className="text-indigo-400" />
                                Campaign Preview
                            </h3>
                            <div className="bg-zinc-950 p-4 rounded-lg border border-zinc-800 text-sm text-zinc-300 whitespace-pre-wrap font-mono mb-4 max-h-96 overflow-y-auto">
                                {state.campaign_preview}
                            </div>
                            <div className="flex justify-end gap-3">
                                <button
                                    onClick={() => {
                                        const feedback = prompt("What would you like to change?");
                                        if (feedback) handleSendWithInput(feedback);
                                    }}
                                    className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-white rounded-lg text-sm font-medium"
                                >
                                    Modify
                                </button>
                                <button
                                    onClick={() => handleSendWithInput("Publish Campaign")}
                                    className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-medium flex items-center gap-2"
                                >
                                    <Globe size={16} />
                                    Publish to Facebook
                                </button>
                            </div>
                        </div>
                    );
                }
                return null;
            case 'publish_campaign':
                if (state.publish_status === 'success') {
                    return (
                        <div className="bg-green-500/10 border border-green-500/20 p-6 rounded-xl w-full max-w-md text-center">
                            <div className="w-12 h-12 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                                <CheckCircle2 size={24} className="text-green-500" />
                            </div>
                            <h3 className="text-green-400 font-medium text-lg mb-2">Campaign Published!</h3>
                            <p className="text-zinc-400 text-sm">
                                Your ad campaign has been successfully published to Facebook.
                            </p>
                        </div>
                    );
                } else if (state.publish_status === 'failed') {
                    return (
                        <div className="bg-red-500/10 border border-red-500/20 p-6 rounded-xl w-full max-w-md text-center">
                            <h3 className="text-red-400 font-medium text-lg mb-2">Publishing Failed</h3>
                            <p className="text-zinc-400 text-sm mb-4">
                                {state.error || "An unknown error occurred."}
                            </p>
                            <button
                                onClick={() => handleSendWithInput("Retry Publish")}
                                className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-white rounded-lg text-sm font-medium"
                            >
                                Retry
                            </button>
                        </div>
                    );
                }
                return null;
        }
    };

    const handleSendWithInput = async (input: string) => {
        if (!input.trim() || isLoading) return;
        setInputValue('');
        addMessage('user', input);
        setIsLoading(true);

        // Create a placeholder message for the agent response
        const responseMsgId = Math.random().toString(36).substring(7);
        setMessages(prev => [...prev, {
            id: responseMsgId,
            role: 'agent',
            content: '', // Start empty
        }]);

        try {
            const threadId = workflowApi.getThreadId() || 'default';
            // Use the streaming endpoint
            const response = await fetch(`http://localhost:8000/api/workflow/stream?thread_id=${threadId}&message=${encodeURIComponent(input)}`);

            if (!response.body) throw new Error("No response body");

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            let accumulatedContent = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n\n');
                buffer = lines.pop() || ''; // Keep incomplete line

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));

                            if (data.type === 'token') {
                                accumulatedContent += data.content;
                                setMessages(prev => prev.map(msg =>
                                    msg.id === responseMsgId
                                        ? { ...msg, content: accumulatedContent }
                                        : msg
                                ));
                            } else if (data.type === 'complete') {
                                const state = data.state;
                                updateStateFromResponse({ state }); // Update global state

                                const newStep = state.current_step as WorkflowStep;
                                const component = renderStepComponent(newStep, state);

                                // Update the message with final content and component
                                setMessages(prev => prev.map(msg =>
                                    msg.id === responseMsgId
                                        ? {
                                            ...msg,
                                            content: state.agent_message || accumulatedContent || "Here is the result:",
                                            component
                                        }
                                        : msg
                                ));
                            } else if (data.type === 'error') {
                                console.error("Streaming error:", data.content);
                                setMessages(prev => prev.map(msg =>
                                    msg.id === responseMsgId
                                        ? { ...msg, content: `Error: ${data.content}` }
                                        : msg
                                ));
                            }
                        } catch (e) {
                            console.error("Error parsing SSE data:", e);
                        }
                    }
                }
            }

        } catch (error: any) {
            addMessage('agent', formatError(error));
        } finally {
            setIsLoading(false);
        }
    };


    const handleSend = async () => {
        await handleSendWithInput(inputValue);
    };

    return (
        <div className="flex flex-col h-screen bg-black text-zinc-100 font-sans selection:bg-indigo-500/30">
            {/* Header - Simplified */}
            <header className="flex flex-col border-b border-zinc-800 bg-zinc-950/50 backdrop-blur-md sticky top-0 z-10">
                <div className="flex items-center justify-between px-6 py-4">
                    <div className="flex items-center gap-2">
                        <div className="w-8 h-8 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center">
                            <Sparkles size={18} className="text-white" />
                        </div>
                        <h1 className="font-bold text-lg tracking-tight">Vibelets</h1>
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
            <div className="p-4 border-t border-zinc-800 bg-zinc-950/50 backdrop-blur-md">
                <div className="max-w-3xl mx-auto relative">
                    <input
                        type="text"
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                        placeholder="Type a message or paste a URL..."
                        className="w-full bg-zinc-900 border border-zinc-800 rounded-xl px-4 py-3 pr-12 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all placeholder:text-zinc-500"
                        disabled={isLoading}
                    />
                    <button
                        onClick={handleSend}
                        disabled={!inputValue.trim() || isLoading}
                        className="absolute right-2 top-1/2 -translate-y-1/2 p-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                    >
                        <Send size={16} />
                    </button>
                </div>
            </div>
        </div>
    );
};
