import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Chart as ChartJS,
  ArcElement,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';
import type { ChartData } from 'chart.js';
import { Doughnut, Pie, Bar } from 'react-chartjs-2';
import { apiClient } from '../api/client';

ChartJS.register(
  ArcElement,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  Title,
  Tooltip,
  Legend
);

interface StatsData {
  priorita: { [key: string]: number };
  stato: { [key: string]: number };
  andamento_mensile: { labels: string[]; scadenze: number[]; completate: number[] };
  top_scadenze: Array<{ titolo: string; occorrenze: number; critiche: number }>;
  totali: {
    totale_scadenze: number;
    scadenze_attive: number;
    completate: number;
    in_scadenza: number;
  };
}

export const StatistichePage: React.FC = () => {
  const [data, setData] = useState<StatsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/scadenze/statistiche/');
      setData(response.data);
    } catch (error) {
      console.error('Errore caricamento statistiche:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={{ padding: '20px', textAlign: 'center' }}>
        <p>Caricamento statistiche...</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div style={{ padding: '20px', textAlign: 'center' }}>
        <p>Errore nel caricamento delle statistiche</p>
      </div>
    );
  }

  const prioritaData = {
    labels: Object.keys(data.priorita).map(k => {
      const labels: { [key: string]: string } = {
        low: 'Bassa',
        medium: 'Media',
        high: 'Alta',
        critical: 'Critica'
      };
      return labels[k] || k;
    }),
    datasets: [{
      data: Object.values(data.priorita),
      backgroundColor: ['#10b981', '#f59e0b', '#ef4444', '#dc2626']
    }]
  };

  const statoData = {
    labels: Object.keys(data.stato).map(k => {
      const labels: { [key: string]: string } = {
        pending: 'In attesa',
        in_progress: 'In corso',
        completed: 'Completata',
        cancelled: 'Annullata'
      };
      return labels[k] || k;
    }),
    datasets: [{
      data: Object.values(data.stato),
      backgroundColor: ['#f59e0b', '#3b82f6', '#10b981', '#6b7280']
    }]
  };

  const andamentoData = {
    labels: data.andamento_mensile.labels,
    datasets: [
      {
        type: 'bar' as const,
        label: 'Scadenze totali',
        data: data.andamento_mensile.scadenze,
        backgroundColor: 'rgba(59, 130, 246, 0.5)',
        borderColor: 'rgb(59, 130, 246)',
        borderWidth: 1
      },
      {
        type: 'line' as const,
        label: 'Completate',
        data: data.andamento_mensile.completate,
        borderColor: 'rgb(16, 185, 129)',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        tension: 0.4
      }
    ]
  } as unknown as ChartData<'bar', number[], string>;

  return (
    <div style={{ padding: '20px' }}>
      {/* Header */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: '20px'
      }}>
        <h1 style={{ margin: 0 }}>📊 Statistiche Scadenze</h1>
        <div style={{ display: 'flex', gap: '10px' }}>
          <Link to="/scadenze/scadenziario" className="btn btn-secondary">
            📋 Scadenziario
          </Link>
          <Link to="/scadenze/calendario" className="btn btn-primary">
            📅 Calendario
          </Link>
        </div>
      </div>

      {/* Cards Statistiche */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '15px',
        marginBottom: '30px'
      }}>
        <div style={{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
          padding: '20px',
          borderRadius: '8px',
          boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
        }}>
          <div style={{ fontSize: '14px', opacity: 0.9 }}>Totale Scadenze</div>
          <div style={{ fontSize: '32px', fontWeight: 700, marginTop: '8px' }}>
            {data.totali.totale_scadenze}
          </div>
        </div>

        <div style={{
          background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
          color: 'white',
          padding: '20px',
          borderRadius: '8px',
          boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
        }}>
          <div style={{ fontSize: '14px', opacity: 0.9 }}>Scadenze Attive</div>
          <div style={{ fontSize: '32px', fontWeight: 700, marginTop: '8px' }}>
            {data.totali.scadenze_attive}
          </div>
        </div>

        <div style={{
          background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
          color: 'white',
          padding: '20px',
          borderRadius: '8px',
          boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
        }}>
          <div style={{ fontSize: '14px', opacity: 0.9 }}>Completate</div>
          <div style={{ fontSize: '32px', fontWeight: 700, marginTop: '8px' }}>
            {data.totali.completate}
          </div>
        </div>

        <div style={{
          background: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
          color: 'white',
          padding: '20px',
          borderRadius: '8px',
          boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
        }}>
          <div style={{ fontSize: '14px', opacity: 0.9 }}>In Scadenza (7gg)</div>
          <div style={{ fontSize: '32px', fontWeight: 700, marginTop: '8px' }}>
            {data.totali.in_scadenza}
          </div>
        </div>
      </div>

      {/* Grafici */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
        gap: '20px',
        marginBottom: '30px'
      }}>
        <div style={{
          background: 'white',
          padding: '20px',
          borderRadius: '8px',
          boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
        }}>
          <h3 style={{ marginTop: 0 }}>Distribuzione per Priorità</h3>
          <Doughnut data={prioritaData} options={{ maintainAspectRatio: true }} />
        </div>

        <div style={{
          background: 'white',
          padding: '20px',
          borderRadius: '8px',
          boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
        }}>
          <h3 style={{ marginTop: 0 }}>Distribuzione per Stato</h3>
          <Pie data={statoData} options={{ maintainAspectRatio: true }} />
        </div>
      </div>

      {/* Andamento Mensile */}
      <div style={{
        background: 'white',
        padding: '20px',
        borderRadius: '8px',
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
        marginBottom: '30px'
      }}>
        <h3 style={{ marginTop: 0 }}>Andamento Ultimi 12 Mesi</h3>
        <Bar data={andamentoData} options={{ 
          maintainAspectRatio: true,
          scales: {
            y: {
              beginAtZero: true
            }
          }
        }} />
      </div>

      {/* Top 5 Scadenze */}
      <div style={{
        background: 'white',
        padding: '20px',
        borderRadius: '8px',
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
      }}>
        <h3 style={{ marginTop: 0 }}>🏆 Top 5 Scadenze per Occorrenze</h3>
        <ol style={{ paddingLeft: '20px' }}>
          {data.top_scadenze.map((item, idx) => (
            <li key={idx} style={{
              marginBottom: '12px',
              fontSize: '15px'
            }}>
              <strong>{item.titolo}</strong>
              <div style={{ fontSize: '13px', color: '#6b7280', marginTop: '4px' }}>
                📅 {item.occorrenze} occorrenze
                {item.critiche > 0 && (
                  <span style={{ marginLeft: '10px', color: '#dc2626' }}>
                    🔥 {item.critiche} critiche
                  </span>
                )}
              </div>
            </li>
          ))}
        </ol>
      </div>
    </div>
  );
};

export default StatistichePage;
