import React from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { Store } from './store.jsx';
import { AuthProvider } from './auth.jsx';
import App from './App.jsx';
import './index.css';

createRoot(document.getElementById('root')).render(
  <BrowserRouter>
    <AuthProvider>
      <Store>
        <App />
      </Store>
    </AuthProvider>
  </BrowserRouter>
);