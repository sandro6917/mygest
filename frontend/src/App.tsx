import { RouterProvider } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useEffect } from 'react';
import { ToastContainer } from 'react-toastify';
import { router } from './routes';
import { apiClient } from './api/client';
import './styles/global.css';
import 'react-toastify/dist/ReactToastify.css';

// Create QueryClient instance
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 10 * 60 * 1000, // 10 minutes (formerly cacheTime)
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function App() {
  // Get CSRF token on app mount
  useEffect(() => {
    const fetchCsrfToken = async () => {
      try {
        console.log('[App] Fetching CSRF token...');
        await apiClient.get('/auth/csrf/');
        console.log('[App] CSRF token fetched successfully');
      } catch (error) {
        console.error('[App] Failed to fetch CSRF token:', error);
      }
    };
    
    fetchCsrfToken();
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
      <ToastContainer
        position="top-right"
        autoClose={3000}
        hideProgressBar={false}
        newestOnTop
        closeOnClick
        rtl={false}
        pauseOnFocusLoss
        draggable
        pauseOnHover
        theme="light"
      />
    </QueryClientProvider>
  );
}

export default App;
