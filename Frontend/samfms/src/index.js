import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css'; // Import the Tailwind CSS base file
import './styles/globals.css'; // Import our custom global styles
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

