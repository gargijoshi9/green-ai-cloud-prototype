import React, { useState, useEffect } from 'react';

function App() {
  const [metrics, setMetrics] = useState(null);

  useEffect(() => {
    fetch('http://localhost:5000/api/sustainability-metrics')
      .then(res => res.json())
      .then(data => setMetrics(data))
      .catch(err => console.error("Error fetching metrics:", err));
  }, []);

  return (
    <div style={{ padding: '2rem', fontFamily: 'system-ui, sans-serif' }}>
      <header style={{ borderBottom: '2px solid #2ecc71', marginBottom: '2rem' }}>
        <h1 style={{ color: '#2c3e50' }}>Green AI Cloud Dashboard</h1>
        <p style={{ color: '#7f8c8d' }}>Prototype Skeleton - Monitoring Sustainable Computing</p>
      </header>

      {metrics ? (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
          <div style={{ padding: '1.5rem', background: '#f8f9fa', borderRadius: '8px', borderLeft: '4px solid #3498db' }}>
            <h3 style={{ margin: 0, color: '#34495e' }}>Active Instances</h3>
            <p style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>{metrics.active_instances}</p>
          </div>
          <div style={{ padding: '1.5rem', background: '#f8f9fa', borderRadius: '8px', borderLeft: '4px solid #e74c3c' }}>
            <h3 style={{ margin: 0, color: '#34495e' }}>Energy (kWh)</h3>
            <p style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>{metrics.energy_consumed_kwh}</p>
          </div>
          <div style={{ padding: '1.5rem', background: '#f8f9fa', borderRadius: '8px', borderLeft: '4px solid #9b59b6' }}>
            <h3 style={{ margin: 0, color: '#34495e' }}>Carbon (gCO2e)</h3>
            <p style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>{metrics.carbon_emission_grams}</p>
          </div>
          <div style={{ padding: '1.5rem', background: '#f8f9fa', borderRadius: '8px', borderLeft: '4px solid #2ecc71' }}>
            <h3 style={{ margin: 0, color: '#34495e' }}>Efficiency Score</h3>
            <p style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>{metrics.efficiency_score}/100</p>
          </div>
        </div>
      ) : (
        <p>Loading metrics from backend...</p>
      )}
    </div>
  );
}

export default App;