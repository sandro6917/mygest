// Environment variables
const getDefaultApiBaseUrl = () => {
	if (typeof window !== 'undefined' && window.location.origin) {
		return `${window.location.origin}/api/v1`;
	}
	return '/api/v1';
};

const getDefaultWsBaseUrl = () => {
	if (typeof window !== 'undefined' && window.location.origin) {
		const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
		return `${protocol}//${window.location.host}/ws`;
	}
	return 'ws://localhost:8001/ws';
};

export const API_BASE_URL = import.meta.env.VITE_API_URL || getDefaultApiBaseUrl();
export const WS_BASE_URL = import.meta.env.VITE_WS_URL || getDefaultWsBaseUrl();
export const APP_NAME = 'MyGest';
export const APP_VERSION = '1.5.0';

// Backend URL (senza il prefisso /api/v1) per chiamate dirette come PDF, etichette, etc.
export const getBackendBaseUrl = () => {
	// In development con Vite proxy, usa l'origin corrente
	if (import.meta.env.DEV) {
		return window.location.origin;
	}
	// In production, estrai il backend URL rimuovendo /api/v1
	if (import.meta.env.VITE_API_URL) {
		return import.meta.env.VITE_API_URL.replace('/api/v1', '');
	}
	// Fallback: usa l'origin corrente
	return window.location.origin;
};
