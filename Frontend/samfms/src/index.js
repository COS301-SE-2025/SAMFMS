import React from 'react';
import ReactDOM from 'react-dom/client';
import 'leaflet/dist/leaflet.css'; // Import Leaflet CSS
import 'leaflet-routing-machine/dist/leaflet-routing-machine.css'; // Import Leaflet Routing Machine CSS
import './index.css'; // Import the Tailwind CSS base file
import './styles/globals.css'; // Import our custom global styles
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
