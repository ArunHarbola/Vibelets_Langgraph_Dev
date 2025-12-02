import React, { useEffect, useState } from 'react';

interface FacebookAuthProps {
    onLogin: (accessToken: string) => void;
}

export const FacebookAuth: React.FC<FacebookAuthProps> = ({ onLogin }) => {
    const [sdkLoaded, setSdkLoaded] = useState(false);

    useEffect(() => {
        // Load the SDK asynchronously
        const loadSdk = () => {
            if (document.getElementById('facebook-jssdk')) {
                setSdkLoaded(true);
                return;
            }
            const fjs = document.getElementsByTagName('script')[0];
            if (fjs.parentNode) {
                const js = document.createElement('script');
                js.id = 'facebook-jssdk';
                js.src = "https://connect.facebook.net/en_US/sdk.js";
                fjs.parentNode.insertBefore(js, fjs);
            }
        };

        (window as any).fbAsyncInit = function () {
            (window as any).FB.init({
                appId: '33211477898443534', // Use env var or fallback
                cookie: true,
                xfbml: true,
                version: 'v18.0'
            });
            setSdkLoaded(true);
        };

        loadSdk();
    }, []);

    const handleFacebookLogin = () => {
        if (!(window as any).FB) {
            alert("Facebook SDK not loaded yet. Please wait...");
            return;
        }
        (window as any).FB.login(function (response: any) {
            if (response.authResponse) {
                console.log('Welcome! Fetching your information.... ');
                const accessToken = response.authResponse.accessToken;
                onLogin(accessToken);
            } else {
                console.log('User cancelled login or did not fully authorize.');
                alert("Login cancelled or failed.");
            }
        }, { scope: 'ads_management,ads_read' });
    };

    return (
        <div className="bg-zinc-900 p-4 rounded-xl border border-zinc-800 w-full max-w-md">
            <h3 className="text-zinc-200 font-medium mb-2">Connect to Facebook</h3>
            <p className="text-zinc-400 text-sm mb-4">
                Log in with Facebook to authorize ad creation.
            </p>
            <button
                onClick={handleFacebookLogin}
                disabled={!sdkLoaded}
                className={`w-full py-2 text-white rounded-lg text-sm font-medium flex items-center justify-center gap-2 transition-colors ${sdkLoaded ? 'bg-[#1877F2] hover:bg-[#166fe5]' : 'bg-zinc-700 cursor-not-allowed'
                    }`}
            >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" />
                </svg>
                {sdkLoaded ? 'Login with Facebook' : 'Loading Facebook SDK...'}
            </button>
            <div className="mt-3 text-xs text-zinc-500 bg-zinc-950 p-2 rounded border border-zinc-800">
                Note: This will request `ads_management` and `ads_read` permissions.
            </div>
        </div>
    );
};
