import React, { useState, useEffect } from 'react';
import './App.css';
import catalogData from '../data/catalog.json';

function App() {
  const [showSplash, setShowSplash] = useState(true);
  const [mode, setMode] = useState('verse'); // 'verse' as default
  const [storyTitle, setStoryTitle] = useState('');
  const [storyIdea, setStoryIdea] = useState('');
  const [selectedSong, setSelectedSong] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [isForging, setIsForging] = useState(false);
  const [status, setStatus] = useState('');
  const [historyData, setHistoryData] = useState([]);

  useEffect(() => {
    // Cargar historial global desde el repo si existe
    fetch('data/forged_history.json')
      .then(res => res.json())
      .then(data => setHistoryData(data))
      .catch(() => console.log('Sin historial global aún.'));
  }, []);

  const [forgedSongs, setForgedSongs] = useState(() => {
    const saved = localStorage.getItem('forged_songs_history');
    return saved ? JSON.parse(saved) : [];
  });

  const GH_TOKEN = localStorage.getItem('GH_TOKEN') || '';
  const GH_REPO = 'hjalmarmeza/musichris_comic';

  const allForged = [...new Set([...forgedSongs, ...historyData])];

  const filteredCatalog = catalogData.filter(song => 
    song.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (song.album && song.album.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const [logs, setLogs] = useState([]);

  const addLog = (msg) => {
    setLogs(prev => [...prev.slice(-3), `> ${msg}`]);
    setStatus(msg);
  };

  const handleForge = async () => {
    if (!GH_TOKEN) {
      const token = prompt('Introduce tu GitHub PAT (Master Access):');
      if (token) {
        localStorage.setItem('GH_TOKEN', token);
        window.location.reload();
      }
      return;
    }

    setIsForging(true);
    setLogs([]);
    addLog('Iniciando Motor...');

    let payload = {};
    if (mode === 'manual') {
      if (!storyTitle || !storyIdea) {
        addLog('Faltan datos manuales');
        setIsForging(false);
        return;
      }
      payload = { title: storyTitle, description: storyIdea };
    } else {
      if (!selectedSong) {
        addLog('Falta seleccionar canción');
        setIsForging(false);
        return;
      }
      payload = { 
        title: selectedSong.title, 
        description: `Basado en la canción "${selectedSong.title}". Versículo: ${selectedSong.context?.verse || 'N/A'}. Enfoque: ${selectedSong.context?.focus || 'N/A'}`,
        song_url: selectedSong.audio_url,
        is_song_mode: true
      };
    }

    addLog('Payload generado');

    // Registrar en la memoria de forja si estamos en modo canción
    if (mode === 'song' && selectedSong) {
      const newForged = [...forgedSongs, selectedSong.id || selectedSong.title];
      setForgedSongs(newForged);
      localStorage.setItem('forged_songs_history', JSON.stringify(newForged));
      addLog('Historial actualizado');
    }
    
    try {
      addLog('Llamando a GitHub...');
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 15000);

      const response = await fetch(`https://api.github.com/repos/${GH_REPO}/dispatches`, {
        method: 'POST',
        headers: {
          'Authorization': `token ${GH_TOKEN.trim()}`,
          'Accept': 'application/vnd.github.v3+json',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          event_type: 'verse_forge', // Siempre usamos verse_forge ahora
          client_payload: payload
        }),
        signal: controller.signal
      });

      clearTimeout(timeoutId);
      addLog(`Respuesta GH: ${response.status}`);

      if (response.ok) {
        addLog('✨ ¡ORDEN RECIBIDA POR GITHUB!');
        setTimeout(() => {
          setIsForging(false);
          setSelectedSong(null);
          setShowSplash(true);
        }, 3500);
      } else {
        const errorData = await response.json().catch(() => ({}));
        addLog(`❌ ERROR: ${errorData.message || 'RECHAZADO'}`);
        if (response.status === 401 || response.status === 403) {
          localStorage.removeItem('GH_TOKEN');
          setTimeout(() => window.location.reload(), 4000);
        } else {
          setTimeout(() => setIsForging(false), 6000);
        }
      }
    } catch (err) {
      console.error('Error:', err);
      const msg = err.name === 'AbortError' ? '⌛ TIEMPO EXCEDIDO' : '❌ FALLO DE RED';
      addLog(msg);
      setTimeout(() => setIsForging(false), 6000);
    }
  };

  const resetToken = () => {
    if (confirm('¿Quieres borrar el Token de acceso actual?')) {
      localStorage.removeItem('GH_TOKEN');
      window.location.reload();
    }
  };

  if (showSplash) {
    return (
      <div className="splash-screen" onClick={() => setShowSplash(false)}>
        <div className="splash-overlay"></div>
        <div className="splash-content fade-in">
          <img src="/musichris_comic/logo_v4.png" alt="Logo" className="pulse-logo" style={{ width: '180px' }} />
          <h1 className="splash-title" style={{ fontSize: '2.5rem' }}>MUSICHRIS</h1>
          <p style={{ letterSpacing: '8px', fontSize: '0.6rem', opacity: 0.6, marginTop: '-10px', marginBottom: '20px' }}>COMIC ENGINE</p>
          <div className="tap-to-start">TOCA PARA INICIAR PRODUCCIÓN</div>
        </div>
      </div>
    );
  }
  console.log('MusiChris Comic Forge v1.0.9 - Ready');

  return (
    <div className="mobile-container fade-in">
      <header className="comic-header-mini">
        <img src="/musichris_comic/logo_v4.png" alt="Logo" style={{ width: '50px', cursor: 'pointer' }} onClick={() => setShowSplash(true)} />
      </header>

      <div className="mode-selector">
        <button className={mode === 'verse' ? 'active verse-glow-btn' : ''} onClick={() => setMode('verse')}>VERSE MANUAL</button>
        <button className={mode === 'song' ? 'active verse-glow-btn' : ''} onClick={() => setMode('song')}>VERSE MUSICAL</button>
      </div>

      <main className="glass-card" style={{ marginTop: '10px' }}>
        {!isForging ? (
          <>
            {mode === 'manual' || mode === 'verse' ? (
              <div className="fade-in">
                <div className="input-group">
                  <div className="input-field">
                    <label className="label-comic">{mode === 'verse' ? 'Versículo / Referencia' : 'Título del Video'}</label>
                    <input 
                      type="text"
                      placeholder={mode === 'verse' ? "Ej: Salmos 23:1" : "Ej: La Fe de Abraham"}
                      value={storyTitle}
                      onChange={(e) => setStoryTitle(e.target.value)}
                      className="input-comic"
                    />
                  </div>
                  <div className="input-field">
                    <label className="label-comic">{mode === 'verse' ? 'Reflexión Profunda' : 'Idea Central o Enseñanza'}</label>
                    <textarea 
                      rows="4" 
                      placeholder={mode === 'verse' ? "Describe la escena o el mensaje que quieres visualizar en 4 actos..." : "Describe la enseñanza o historia bíblica que quieres convertir en cómic..."}
                      value={storyIdea}
                      onChange={(e) => setStoryIdea(e.target.value)}
                      className="input-comic"
                    />
                  </div>
                  
                  <button 
                    className="forge-button-glow verse-glow"
                    style={{ marginTop: '20px' }}
                    onClick={handleForge}
                    disabled={isForging || !storyTitle || !storyIdea}
                  >
                    {status || '✨ INICIAR FORJA VERSE'}
                  </button>
                </div>
              </div>
            ) : (
              <div className="catalog-mode fade-in">
                <div className="search-bar">
                  <input 
                    type="text" 
                    placeholder="Buscar canción o álbum..." 
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="input-comic-small"
                  />
                </div>
                <div className="song-grid">
                  {filteredCatalog.map((song, idx) => {
                    const isForged = allForged.includes(song.id || song.title);
                    return (
                      <div 
                        key={idx} 
                        className={`song-card ${selectedSong === song ? 'selected' : ''} ${isForged ? 'is-forged' : ''}`}
                        onClick={() => setSelectedSong(song)}
                      >
                        <img src={song.thumbnail || 'default_album.png'} alt={song.title} className="song-thumb" />
                        {isForged && <div className="forged-badge">✓ FORJADO</div>}
                        <div className="song-info">
                          <p className="song-title">{song.title}</p>
                          <p className="song-album">{song.album}</p>
                        </div>
                      </div>
                    );
                  })}
                </div>
                {selectedSong && !isForging && (
                  <div className="selection-preview fade-in">
                    <div className="preview-card">
                      <span className="preview-label">ADN MINISTERIAL:</span>
                      <p className="preview-verse">📖 {selectedSong.context?.verse || 'Cita no disponible'}</p>
                      <p className="preview-focus">🎯 {selectedSong.context?.focus}</p>
                    </div>
                    
                    <button 
                      className="forge-button-glow verse-glow"
                      onClick={handleForge}
                      disabled={isForging}
                    >
                      {status || '✨ INICIAR FORJA VERSE'}
                    </button>
                  </div>
                )}
              </div>
            )}
          </>
        ) : (
          <div className="forge-status-overlay fade-in">
            <div className="ai-loader"></div>
            <div className="status-logs">
              {logs.map((log, i) => (
                <p key={i} className="log-line">{log}</p>
              ))}
            </div>
          </div>
        )}
      </main>

      <div className="reset-container">
        <div className="build-info">BUILD v1.1.0</div>
        <span onClick={() => window.location.reload(true)} className="refresh-link">🔄 FORZAR ACTUALIZACIÓN</span>
        <br/><br/>
        <span onClick={resetToken} className="reset-link">⚙️ RECONFIGURAR ACCESO</span>
      </div>
    </div>
  );
}

export default App;
