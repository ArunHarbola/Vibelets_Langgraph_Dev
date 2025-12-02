/**
 * Workflow API - LangGraph-based endpoints
 * Supports context-aware state management with thread_id
 */
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/workflow';

export interface WorkflowState {
    current_step: string;
    navigation_intent?: string;
    agent_message?: string;
    messages: Array<{ role: string; content: string }>;
    url?: string;
    product_data?: any;
    selected_product?: any;
    analysis?: any;
    analysis_feedback: string[];
    scripts?: string[];
    script_feedback: string[];
    selected_script_index?: number;
    selected_script?: string;
    script_refinement_feedback: string[];
    generated_images?: string[];
    image_feedback: string[];
    image_generation_prompt?: string;
    audio_file?: string;
    audio_url?: string;
    available_avatars?: Array<{ avatar_id: string; avatar_name: string }>;
    selected_avatar_id?: string;
    video_id?: string;
    video_url?: string;
    video_status?: string;
    error?: string;
    iteration_count: Record<string, number>;
    facebook_access_token?: string;
    facebook_user_id?: string;
    ad_accounts?: Array<any>;
    selected_ad_account_id?: string;
    selected_media?: { type: string; url: string; filename?: string };
    campaign_config?: any;
    campaign_preview?: string;
    publish_status?: string;
}

export interface WorkflowResponse {
    thread_id: string;
    state: WorkflowState;
    current_step?: string;
    [key: string]: any;
}

class WorkflowAPI {
    private threadId: string | null = null;

    setThreadId(threadId: string | null) {
        this.threadId = threadId;
    }

    getThreadId(): string | null {
        return this.threadId;
    }

    async scrape(url: string): Promise<WorkflowResponse> {
        const response = await axios.post(`${API_BASE_URL}/scrape`, {
            url,
            thread_id: this.threadId
        });
        if (response.data.thread_id) {
            this.threadId = response.data.thread_id;
        }
        return response.data;
    }

    async analyze(feedback?: string): Promise<WorkflowResponse> {
        if (!this.threadId) throw new Error('No thread_id available');
        const response = await axios.post(`${API_BASE_URL}/analyze`, {
            thread_id: this.threadId,
            feedback
        });
        return response.data;
    }

    async generateScripts(feedback?: string): Promise<WorkflowResponse> {
        if (!this.threadId) throw new Error('No thread_id available');
        const response = await axios.post(`${API_BASE_URL}/generate_scripts`, {
            thread_id: this.threadId,
            feedback
        });
        return response.data;
    }

    async selectScript(scriptIndex: number): Promise<WorkflowResponse> {
        if (!this.threadId) throw new Error('No thread_id available');
        const response = await axios.post(`${API_BASE_URL}/select_script`, {
            thread_id: this.threadId,
            script_index: scriptIndex
        });
        return response.data;
    }

    async refineScript(feedback: string): Promise<WorkflowResponse> {
        if (!this.threadId) throw new Error('No thread_id available');
        const response = await axios.post(`${API_BASE_URL}/refine_script`, {
            thread_id: this.threadId,
            feedback
        });
        return response.data;
    }

    async generateImages(feedback?: string, numImages: number = 2): Promise<WorkflowResponse> {
        if (!this.threadId) throw new Error('No thread_id available');
        const response = await axios.post(`${API_BASE_URL}/generate_images`, {
            thread_id: this.threadId,
            feedback,
            num_images: numImages
        });
        return response.data;
    }

    async refineImages(feedback: string): Promise<WorkflowResponse> {
        if (!this.threadId) throw new Error('No thread_id available');
        const response = await axios.post(`${API_BASE_URL}/refine_images`, {
            thread_id: this.threadId,
            feedback
        });
        return response.data;
    }

    async generateAudio(): Promise<WorkflowResponse> {
        if (!this.threadId) throw new Error('No thread_id available');
        const response = await axios.post(`${API_BASE_URL}/generate_audio`, {
            thread_id: this.threadId
        });
        return response.data;
    }

    async getAvatars(): Promise<{ avatars: Array<{ avatar_id: string; avatar_name: string }> }> {
        if (!this.threadId) throw new Error('No thread_id available');
        const response = await axios.get(`${API_BASE_URL}/avatars`, {
            params: { thread_id: this.threadId }
        });
        return response.data;
    }

    async selectAvatar(avatarId: string): Promise<WorkflowResponse> {
        if (!this.threadId) throw new Error('No thread_id available');
        const response = await axios.post(`${API_BASE_URL}/select_avatar`, {
            thread_id: this.threadId,
            avatar_id: avatarId
        });
        return response.data;
    }

    async generateVideo(): Promise<WorkflowResponse> {
        if (!this.threadId) throw new Error('No thread_id available');
        const response = await axios.post(`${API_BASE_URL}/generate_video`, {
            thread_id: this.threadId
        });
        return response.data;
    }

    async navigate(navigationIntent: string): Promise<WorkflowResponse> {
        if (!this.threadId) throw new Error('No thread_id available');
        const response = await axios.post(`${API_BASE_URL}/navigate`, {
            thread_id: this.threadId,
            navigation_intent: navigationIntent
        });
        return response.data;
    }

    async chat(message: string): Promise<WorkflowResponse> {
        // Allow chat without thread_id to start new session
        const response = await axios.post(`${API_BASE_URL}/chat`, {
            thread_id: this.threadId,
            message
        });

        // Update thread_id if returned
        if (response.data.thread_id) {
            this.threadId = response.data.thread_id;
        }

        return response.data;
    }

    async getState(): Promise<WorkflowResponse> {
        if (!this.threadId) throw new Error('No thread_id available');
        const response = await axios.get(`${API_BASE_URL}/state/${this.threadId}`);
        return response.data;
    }
}

export const workflowApi = new WorkflowAPI();

