import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

export const api = {
    scrape: async (url: string) => {
        const response = await axios.post(`${API_BASE_URL}/scrape`, { url });
        return response.data;
    },

    analyze: async (productData: any, feedback?: string, currentAnalysis?: any) => {
        const response = await axios.post(`${API_BASE_URL}/analyze`, {
            product_data: productData,
            feedback,
            current_analysis: currentAnalysis
        });
        return response.data;
    },

    generateScripts: async (productData: any, analysis: any, feedback?: string, currentScripts?: string[]) => {
        const response = await axios.post(`${API_BASE_URL}/scripts`, {
            product_data: productData,
            analysis,
            feedback,
            current_scripts: currentScripts
        });
        return response.data;
    },

    refineScript: async (script: string, feedback: string) => {
        const response = await axios.post(`${API_BASE_URL}/refine_script`, {
            script,
            feedback
        });
        return response.data;
    },

    generateAudio: async (script: string, filename?: string) => {
        const response = await axios.post(`${API_BASE_URL}/audio`, {
            script,
            filename
        });
        return response.data;
    },

    generateVideo: async (audioUrl: string) => {
        const response = await axios.post(`${API_BASE_URL}/video`, {
            audio_url: audioUrl
        });
        return response.data;
    },

    checkVideoStatus: async (videoId: string) => {
        const response = await axios.get(`${API_BASE_URL}/video_status/${videoId}`);
        return response.data;
    },

    getAvatars: async () => {
        const response = await axios.get(`${API_BASE_URL}/avatars`);
        return response.data;
    },

    uploadHeyGenAsset: async (filename: string) => {
        const response = await axios.post(`${API_BASE_URL}/heygen/upload`, {
            script: '', // Not needed for upload, but model might require it? No, we used AudioRequest which has script.
            // Wait, AudioRequest in server.py has script and filename. 
            // We should probably just send filename if we can, or send empty script.
            filename
        });
        return response.data;
    },

    generateHeyGenVideo: async (avatarId: string, audioAssetId: string) => {
        const response = await axios.post(`${API_BASE_URL}/heygen/generate`, {
            avatar_id: avatarId,
            audio_asset_id: audioAssetId
        });
        return response.data;
    },

    generateImages: async (productUrl: string, script: string) => {
        const response = await axios.post(`${API_BASE_URL}/generate_images`, {
            product_url: productUrl,
            script: script
        });
        return response.data;
    }
};
