import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import interactionPlugin from '@fullcalendar/interaction';
import itLocale from '@fullcalendar/core/locales/it';
import type { EventClickArg } from '@fullcalendar/core';
import { apiClient } from '../api/client';

interface CalendarEvent {
  id: string;
  title: string;
  start: string;
  end?: string;
  url?: string;
  backgroundColor?: string;
  borderColor?: string;
  extendedProps?: Record<string, unknown>;
}

const priorityColors = {
  low: '#10b981',
  medium: '#f59e0b',
  high: '#ef4444',
  critical: '#dc2626'
};

export const CalendarioPage: React.FC = () => {
  const navigate = useNavigate();
  const calendarRef = useRef<FullCalendar | null>(null);
  const [filters, setFilters] = useState({
    stato: '',
    priorita: ''
  });
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [loading, setLoading] = useState(false);

  const loadEvents = useCallback(async (start?: string, end?: string) => {
    try {
      setLoading(true);
      
      // Se non vengono passate date, usa il mese corrente
      const now = new Date();
      const startDate = start || new Date(now.getFullYear(), now.getMonth(), 1).toISOString().split('T')[0];
      const endDate = end || new Date(now.getFullYear(), now.getMonth() + 1, 0).toISOString().split('T')[0];
      
      const params: Record<string, string> = {
        start: startDate,
        end: endDate
      };

      if (filters.stato) params.stato = filters.stato;
      if (filters.priorita) params.priorita = filters.priorita;

      console.log('Caricamento eventi calendario con parametri:', params);

      const response = await apiClient.get<CalendarEvent[]>('/scadenze/occorrenze/calendar_events/', { params });

      console.log('Risposta API calendario:', response.data);
      
      setEvents(response.data);
    } catch (error) {
      console.error('Errore nel caricamento degli eventi:', error);
      setEvents([]);
    } finally {
      setLoading(false);
    }
  }, [filters.priorita, filters.stato]);

  // Carica eventi al mount e quando cambiano i filtri
  useEffect(() => {
    void loadEvents();
  }, [loadEvents]);

  const handleEventClick = (info: EventClickArg) => {
    info.jsEvent.preventDefault();
    // Naviga alla pagina dettaglio scadenza usando React Router
    const eventId = info.event.id;
    if (eventId) {
      // Estrai l'ID della scadenza dall'URL se presente
      const url = info.event.url;
      if (url) {
        const match = url.match(/\/scadenze\/(\d+)/);
        if (match) {
          navigate(`/scadenze/${match[1]}`);
        }
      }
    }
  };

  return (
    <div style={{ padding: '20px' }}>
      {/* Header */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: '20px'
      }}>
        <h1 style={{ margin: 0 }}>📅 Calendario Scadenze</h1>
        <div style={{ display: 'flex', gap: '10px' }}>
          <Link to="/scadenze/scadenziario" className="btn btn-secondary">
            📋 Scadenziario
          </Link>
          <Link to="/scadenze/statistiche" className="btn btn-secondary">
            📊 Statistiche
          </Link>
        </div>
      </div>

      {/* Filtri */}
      <div style={{
        background: 'white',
        padding: '15px',
        borderRadius: '8px',
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
        marginBottom: '20px',
        display: 'flex',
        gap: '15px',
        alignItems: 'end',
        flexWrap: 'wrap'
      }}>
        <div style={{ flex: '1 1 200px' }}>
          <label style={{ display: 'block', marginBottom: '5px', fontWeight: 500 }}>
            Stato
          </label>
          <select
            value={filters.stato}
            onChange={(e) => setFilters({ ...filters, stato: e.target.value })}
            className="form-select"
            style={{ width: '100%' }}
          >
            <option value="">Tutti</option>
            <option value="pending">In attesa</option>
            <option value="in_progress">In corso</option>
            <option value="completed">Completata</option>
            <option value="cancelled">Annullata</option>
          </select>
        </div>

        <div style={{ flex: '1 1 200px' }}>
          <label style={{ display: 'block', marginBottom: '5px', fontWeight: 500 }}>
            Priorità
          </label>
          <select
            value={filters.priorita}
            onChange={(e) => setFilters({ ...filters, priorita: e.target.value })}
            className="form-select"
            style={{ width: '100%' }}
          >
            <option value="">Tutte</option>
            <option value="low">Bassa</option>
            <option value="medium">Media</option>
            <option value="high">Alta</option>
            <option value="critical">Critica</option>
          </select>
        </div>

        <button
          onClick={() => setFilters({ stato: '', priorita: '' })}
          className="btn btn-sm btn-secondary"
        >
          🔄 Reset
        </button>
      </div>

      {/* Legenda */}
      <div style={{
        background: 'white',
        padding: '15px',
        borderRadius: '8px',
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
        marginBottom: '20px'
      }}>
        <strong style={{ marginRight: '15px' }}>Legenda Priorità:</strong>
        {Object.entries(priorityColors).map(([key, color]) => (
          <span 
            key={key} 
            style={{
              display: 'inline-block',
              marginRight: '15px',
              fontSize: '14px'
            }}
          >
            <span style={{
              display: 'inline-block',
              width: '16px',
              height: '16px',
              background: color,
              borderRadius: '3px',
              marginRight: '5px',
              verticalAlign: 'middle'
            }}></span>
            {key === 'low' && 'Bassa'}
            {key === 'medium' && 'Media'}
            {key === 'high' && 'Alta'}
            {key === 'critical' && 'Critica'}
          </span>
        ))}
      </div>

      {/* Calendario */}
      <div style={{
        background: 'white',
        padding: '20px',
        borderRadius: '8px',
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
      }}>
        {loading && (
          <div style={{ textAlign: 'center', padding: '20px', color: '#6b7280' }}>
            Caricamento eventi...
          </div>
        )}
        <FullCalendar
          ref={calendarRef}
          plugins={[dayGridPlugin, interactionPlugin]}
          initialView="dayGridMonth"
          locale={itLocale}
          headerToolbar={{
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,dayGridWeek'
          }}
          events={events}
          eventClick={handleEventClick}
          eventDidMount={(info) => {
            info.el.title = info.event.title;
          }}
          datesSet={(dateInfo) => {
            // Ricarica eventi quando cambia la vista del calendario
            loadEvents(
              dateInfo.startStr.split('T')[0],
              dateInfo.endStr.split('T')[0]
            );
          }}
          height="auto"
          contentHeight={600}
        />
      </div>
    </div>
  );
};

export default CalendarioPage;
