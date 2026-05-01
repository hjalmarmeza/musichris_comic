import React, { useState, useEffect } from 'react';
import './App.css';
import catalogData from '../data/catalog.json';

function App() {
  const [showSplash, setShowSplash] = useState(true);
  const [mode, setMode] = useState('manual'); // 'manual' or 'song'
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

  const handleForge = async () => {
    if (!GH_TOKEN) {
      const token = prompt('Introduce tu GitHub PAT (Master Access):');
      if (token) {
        localStorage.setItem('GH_TOKEN', token);
        window.location.reload();
      }
      return;
    }

    let payload = {};
    if (mode === 'manual') {
      if (!storyTitle || !storyIdea) {
        alert('Por favor, llena ambos campos.');
        return;
      }
      payload = { title: storyTitle, description: storyIdea };
    } else {
      if (!selectedSong) {
        alert('Por favor, selecciona una canción del catálogo.');
        return;
      }
      // Song to Story Mode: We pass the song details to the forge
      payload = { 
        title: selectedSong.title, 
        description: `Basado en la canción "${selectedSong.title}". Versículo: ${selectedSong.context?.verse || 'N/A'}. Enfoque: ${selectedSong.context?.focus || 'N/A'}`,
        song_url: selectedSong.audio_url,
        is_song_mode: true
      };
    }

    setIsForging(true);
    setStatus('🧠 SINCRONIZANDO ADN MINISTERIAL...');

    // Registrar en la memoria de forja si estamos en modo canción
    if (activeTab === 'song' && selectedSong) {
      const newForged = [...forgedSongs, selectedSong.id || selectedSong.title];
      setForgedSongs(newForged);
      localStorage.setItem('forged_songs_history', JSON.stringify(newForged));
    }
    
    try {
      const response = await fetch(`https://api.github.com/repos/${GH_REPO}/dispatches`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${GH_TOKEN.trim()}`,
          'Accept': 'application/vnd.github.v3+json',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          event_type: 'forge_comic',
          client_payload: payload
        })
      });

      if (response.ok) {
        setStatus('✨ ¡LA FORJA HA COMENZADO!');
        setTimeout(() => {
          setIsForging(false);
          setStoryTitle('');
          setStoryIdea('');
          setSelectedSong(null);
          setShowSplash(true);
        }, 4000);
      } else {
        const errorData = await response.json().catch(() => ({}));
        console.error('Error GitHub:', response.status, errorData);
        setStatus(`❌ ERROR ${response.status}: ${errorData.message || 'RECHAZADO'}`);
        if (response.status === 401) {
          localStorage.removeItem('GH_TOKEN');
          setTimeout(() => window.location.reload(), 3000);
        } else {
          setTimeout(() => setIsForging(false), 5000);
        }
      }
    } catch (err) {
      console.error('Error conexión:', err);
      setStatus('❌ ERROR DE CONEXIÓN (CORS/RED)');
      setTimeout(() => setIsForging(false), 5000);
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

  return (
    <div className="mobile-container fade-in">
      <header className="comic-header-mini">
        <img src="/musichris_comic/logo_v4.png" alt="Logo" style={{ width: '50px', cursor: 'pointer' }} onClick={() => setShowSplash(true)} />
      </header>

      <div className="mode-selector">
        <button className={mode === 'manual' ? 'active' : ''} onClick={() => setMode('manual')}>MANUAL</button>
        <button className={mode === 'song' ? 'active' : ''} onClick={() => setMode('song')}>SONG TO STORY</button>
      </div>

      <main className="glass-card" style={{ marginTop: '10px' }}>
        {!isForging ? (
          <>
            {mode === 'manual' ? (
              <div className="fade-in">
                <div className="input-group">
                  <div className="input-field">
                    <label className="label-comic">Título del Video</label>
                    <input 
                      type="text"
                      placeholder="Ej: La Fe de Abraham"
                      value={storyTitle}
                      onChange={(e) => setStoryTitle(e.target.value)}
                      className="input-comic"
                    />
                  </div>
                  <div className="input-field">
                    <label className="label-comic">Idea Central</label>
                    <textarea 
                      rows="3" 
                      placeholder="Describe la enseñanza o historia..."
                      value={storyIdea}
                      onChange={(e) => setStoryIdea(e.target.value)}
                      className="input-comic"
                    />
                  </div>
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
                      className="forge-button-glow"
                      onClick={handleForge}
                      disabled={isForging}
                    >
                      {status || '🚀 INICIAR FORJA DE CÓMIC'}
                    </button>
                  </div>
                )}
              </div>
            )}
          </>
        ) : (
          <div className="forge-status-overlay fade-in">
            <div className="ai-loader"></div>
            <p className="status-text">{status}</p>
          </div>
        )}
      </main>

      <div className="reset-container">
        <span onClick={resetToken} className="reset-link">⚙️ RECONFIGURAR ACCESO</span>
      </div>
    </div>
  );
}

export default App;
