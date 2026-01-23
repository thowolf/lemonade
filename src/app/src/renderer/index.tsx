import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { ErrorBoundary } from './ErrorBoundary';

console.log('[Lemonade Renderer] index.tsx loaded');

const rootElement = document.getElementById('root');
console.log('[Lemonade Renderer] Root element found:', !!rootElement);

if (!rootElement) {
  console.error('[Lemonade Renderer] FATAL: Could not find root element');
  throw new Error('Root element not found - HTML did not load properly');
}

try {
  console.log('[Lemonade Renderer] Creating React root...');
  const root = ReactDOM.createRoot(rootElement);
  
  console.log('[Lemonade Renderer] Rendering App component...');
  root.render(
    <React.StrictMode>
      <ErrorBoundary>
        <App />
      </ErrorBoundary>
    </React.StrictMode>
  );
  
  console.log('[Lemonade Renderer] App rendered successfully');
} catch (error) {
  console.error('[Lemonade Renderer] FATAL ERROR during render:', error);
  console.error('[Lemonade Renderer] Stack trace:', (error as any)?.stack);
  throw error;
}

