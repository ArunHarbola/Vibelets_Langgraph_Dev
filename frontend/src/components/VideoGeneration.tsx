import React, { useState, useEffect } from 'react';
import { workflowApi } from '@/lib/workflowApi';
import { Loader2, Play, Video, CheckCircle, User } from 'lucide-react';
import { motion } from 'framer-motion';
import axios from 'axios';

interface VideoGenerationProps {
    audioUrl: string;
    onVideoGenerated: (videoUrl: string) => void;
}

interface Avatar {
    avatar_id: string;
    avatar_name: string;
    preview_image_url?: string;
}

export const VideoGeneration: React.FC<VideoGenerationProps> = ({ audioUrl, onVideoGenerated }) => {
    const [avatars, setAvatars] = useState<Avatar[]>([]);
    const [selectedAvatar, setSelectedAvatar] = useState<string | null>(null);
    const [isLoadingAvatars, setIsLoadingAvatars] = useState(true);
    const [isGenerating, setIsGenerating] = useState(false);
    const [status, setStatus] = useState<string>('');
    const [error, setError] = useState<string | null>(null);
    const [videoUrl, setVideoUrl] = useState<string | null>(null);

    useEffect(() => {
        loadAvatars();
    }, []);

    const loadAvatars = async () => {
        try {
            const res = await workflowApi.getAvatars();
            setAvatars(res.avatars || []);
        } catch (err) {
            console.error("Failed to load avatars", err);
            setError("Failed to load avatars.");
        } finally {
            setIsLoadingAvatars(false);
        }
    };

    const handleGenerate = async () => {
        if (!selectedAvatar) return;
        setIsGenerating(true);
        setError(null);
        setVideoUrl(null);
        setStatus('Selecting avatar and generating video...');

        try {
            // 1. Select avatar via workflow
            await workflowApi.selectAvatar(selectedAvatar);

            // 2. Generate video via workflow
            setStatus('Initiating video generation...');
            const genRes = await workflowApi.generateVideo();
            const videoId = genRes.state.video_id;

            if (!videoId) {
                throw new Error("Failed to start video generation");
            }

            // 3. Poll Status
            setStatus('Generating video (this may take a few minutes)...');
            pollStatus(videoId);

        } catch (err: any) {
            console.error(err);
            setError(err.response?.data?.detail || err.message || "Video generation failed");
            setIsGenerating(false);
        }
    };

    const pollStatus = async (videoId: string) => {
        const interval = setInterval(async () => {
            try {
                // Use the old API endpoint for status checking (or add to workflow API)
                const res = await axios.get(`http://localhost:8000/api/video_status/${videoId}`);
                const statusData = res.data;

                // HeyGen API returns data in a 'data' wrapper
                const status = statusData.data?.status || statusData.status;
                const url = statusData.data?.video_url || statusData.video_url;

                if (status === 'completed') {
                    clearInterval(interval);
                    setStatus('Completed!');
                    setIsGenerating(false);
                    if (url) {
                        setVideoUrl(url);
                        onVideoGenerated(url);
                    } else {
                        setError("Video completed but no URL returned");
                    }
                } else if (status === 'failed') {
                    clearInterval(interval);
                    setError(statusData.error || "Video generation failed during processing");
                    setIsGenerating(false);
                } else {
                    setStatus(`Status: ${status}...`);
                }
            } catch (err) {
                clearInterval(interval);
                setError("Failed to check status");
                setIsGenerating(false);
            }
        }, 5000);
    };

    if (isLoadingAvatars) {
        return (
            <div className="flex items-center gap-2 text-zinc-400 p-4">
                <Loader2 className="animate-spin" size={16} />
                <span>Loading avatars...</span>
            </div>
        );
    }

    if (error) {
        return (
            <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm">
                {error}
                <button
                    onClick={() => setError(null)}
                    className="ml-2 underline hover:text-red-300"
                >
                    Try Again
                </button>
            </div>
        );
    }

    return (
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden w-full max-w-2xl">
            <div className="p-4 border-b border-zinc-800 bg-zinc-950/50">
                <h3 className="text-zinc-200 font-medium flex items-center gap-2">
                    <User size={18} className="text-indigo-400" />
                    Select an Avatar
                </h3>
            </div>

            <div className="p-4 grid grid-cols-2 sm:grid-cols-3 gap-3 max-h-60 overflow-y-auto custom-scrollbar">
                {avatars.map((avatar) => (
                    <button
                        key={avatar.avatar_id}
                        onClick={() => setSelectedAvatar(avatar.avatar_id)}
                        disabled={isGenerating}
                        className={`relative group rounded-lg overflow-hidden border transition-all ${selectedAvatar === avatar.avatar_id
                            ? 'border-indigo-500 ring-2 ring-indigo-500/20'
                            : 'border-zinc-800 hover:border-zinc-700'
                            }`}
                    >
                        <div className="aspect-[9/16] bg-zinc-800 relative">
                            {avatar.preview_image_url ? (
                                <img
                                    src={avatar.preview_image_url}
                                    alt={avatar.avatar_name}
                                    className="w-full h-full object-cover"
                                />
                            ) : (
                                <div className="w-full h-full flex items-center justify-center text-zinc-600">
                                    <User size={24} />
                                </div>
                            )}
                            <div className="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex items-end p-2">
                                <span className="text-xs text-white font-medium truncate w-full">
                                    {avatar.avatar_name}
                                </span>
                            </div>
                        </div>
                        {selectedAvatar === avatar.avatar_id && (
                            <div className="absolute top-2 right-2 bg-indigo-500 text-white p-1 rounded-full shadow-lg">
                                <CheckCircle size={12} fill="currentColor" className="text-white" />
                            </div>
                        )}
                    </button>
                ))}
            </div>

            <div className="p-4 border-t border-zinc-800 bg-zinc-950/30 flex items-center justify-between">
                <div className="text-sm text-zinc-400">
                    {isGenerating ? (
                        <div className="flex items-center gap-2 text-indigo-400">
                            <Loader2 className="animate-spin" size={14} />
                            {status}
                        </div>
                    ) : videoUrl ? (
                        <div className="flex items-center gap-2 text-green-400">
                            <CheckCircle size={14} />
                            Video Generated!
                        </div>
                    ) : (
                        selectedAvatar ? "Ready to generate" : "Select an avatar to continue"
                    )}
                </div>

                {videoUrl ? (
                    <div className="flex gap-2">
                        <a
                            href={videoUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-white rounded-lg text-sm font-medium flex items-center gap-2 transition-colors"
                        >
                            <Play size={16} />
                            Preview
                        </a>
                        <a
                            href={videoUrl}
                            download
                            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-medium flex items-center gap-2 transition-colors"
                        >
                            <Video size={16} />
                            Download
                        </a>
                    </div>
                ) : (
                    <button
                        onClick={handleGenerate}
                        disabled={!selectedAvatar || isGenerating}
                        className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg text-sm font-medium flex items-center gap-2 transition-colors"
                    >
                        {isGenerating ? (
                            <>Generating...</>
                        ) : (
                            <>
                                <Video size={16} />
                                Generate Video
                            </>
                        )}
                    </button>
                )}
            </div>

            {videoUrl && (
                <div className="p-4 border-t border-zinc-800 bg-black/20">
                    <video
                        src={videoUrl}
                        controls
                        className="w-full rounded-lg border border-zinc-800"
                        poster={avatars.find(a => a.avatar_id === selectedAvatar)?.preview_image_url}
                    />
                </div>
            )}
        </div>
    );
};
