import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import './App.css';

const API = 'http://127.0.0.1:8000';

// ─── API helpers ─────────────────────────────────────────────────────────────
const api = {
  get: (url, token) => axios.get(`${API}${url}`, token ? { headers: { Authorization: `Bearer ${token}` } } : {}),
  post: (url, data, token) => axios.post(`${API}${url}`, data, token ? { headers: { Authorization: `Bearer ${token}` } } : {}),
  put: (url, data, token) => axios.put(`${API}${url}`, data, { headers: { Authorization: `Bearer ${token}` } }),
};

// ─── Star Rating component ────────────────────────────────────────────────────
function StarRating({ value, onChange, readonly = false }) {
  const [hover, setHover] = useState(0);
  return (
    <div className="star-rating">
      {[1, 2, 3, 4, 5].map(star => (
        <span
          key={star}
          className={`star ${star <= (hover || value) ? 'active' : ''}`}
          onClick={() => !readonly && onChange && onChange(star)}
          onMouseEnter={() => !readonly && setHover(star)}
          onMouseLeave={() => !readonly && setHover(0)}
        >★</span>
      ))}
    </div>
  );
}

// ─── Product Card ─────────────────────────────────────────────────────────────
function ProductCard({ item, onClick }) {
  return (
    <div className="product-card" onClick={() => onClick(item)}>
      {item.score > 0 && (
        <div className="score-badge">{(item.score * 100).toFixed(1)}% match</div>
      )}
      <div className="product-img-wrapper">
        <img
          src={item.img_url || item.image_url || ''}
          alt={item.title}
          className="product-img"
          onError={e => { e.target.src = `https://placehold.co/300x300/1e293b/64748b?text=No+Image`; }}
        />
      </div>
      <div className="product-info">
        <div className="product-category">{item.category}</div>
        <div className="product-title" title={item.title}>{item.title}</div>
        <div className="product-meta">
          <div className="product-price">{item.price > 0 ? `$${Number(item.price).toFixed(2)}` : 'N/A'}</div>
          {item.rating > 0 && (
            <div className="product-rating">★ {Number(item.rating).toFixed(1)}</div>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── Auth Page ────────────────────────────────────────────────────────────────
function AuthPage({ onLogin }) {
  const [mode, setMode] = useState('login'); // login | register | forgot | reset
  const [form, setForm] = useState({ email: '', password: '', full_name: '', new_password: '', token: '' });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const handleSubmit = async e => {
    e.preventDefault();
    setError(''); setSuccess(''); setLoading(true);
    try {
      if (mode === 'login') {
        const res = await api.post('/auth/login', { email: form.email, password: form.password });
        onLogin(res.data.token, res.data.user);
      } else if (mode === 'register') {
        const res = await api.post('/auth/register', { email: form.email, password: form.password, full_name: form.full_name });
        onLogin(res.data.token, res.data.user);
      } else if (mode === 'forgot') {
        await api.post('/auth/forgot-password', { email: form.email });
        setSuccess('Link đặt lại mật khẩu đã được gửi tới email của bạn!');
      } else if (mode === 'reset') {
        await api.post('/auth/reset-password', { token: form.token, new_password: form.new_password });
        setSuccess('Đặt lại mật khẩu thành công!');
        setTimeout(() => setMode('login'), 2000);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Đã có lỗi xảy ra');
    } finally {
      setLoading(false);
    }
  };

  // Check URL for reset token
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const t = params.get('reset_token');
    if (t) { set('token', t); setMode('reset'); }
  }, []);

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-logo">⚡ SeqRec AI</div>
        <h2 className="auth-title">
          {mode === 'login' && 'Đăng nhập'}
          {mode === 'register' && 'Tạo tài khoản'}
          {mode === 'forgot' && 'Quên mật khẩu'}
          {mode === 'reset' && 'Đặt lại mật khẩu'}
        </h2>

        {error && <div className="alert error">{error}</div>}
        {success && <div className="alert success">{success}</div>}

        <form onSubmit={handleSubmit} className="auth-form">
          {mode === 'register' && (
            <input className="input" placeholder="Họ và tên" value={form.full_name}
              onChange={e => set('full_name', e.target.value)} required />
          )}
          {(mode === 'login' || mode === 'register' || mode === 'forgot') && (
            <input className="input" type="email" placeholder="Email" value={form.email}
              onChange={e => set('email', e.target.value)} required />
          )}
          {(mode === 'login' || mode === 'register') && (
            <input className="input" type="password" placeholder="Mật khẩu" value={form.password}
              onChange={e => set('password', e.target.value)} required />
          )}
          {mode === 'reset' && (
            <input className="input" type="password" placeholder="Mật khẩu mới" value={form.new_password}
              onChange={e => set('new_password', e.target.value)} required />
          )}
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? 'Đang xử lý...' : (
              mode === 'login' ? 'Đăng nhập' :
              mode === 'register' ? 'Tạo tài khoản' :
              mode === 'forgot' ? 'Gửi link đặt lại' : 'Đặt lại mật khẩu'
            )}
          </button>
        </form>

        <div className="auth-links">
          {mode === 'login' && <>
            <button className="link-btn" onClick={() => setMode('register')}>Chưa có tài khoản? Đăng ký</button>
            <button className="link-btn" onClick={() => setMode('forgot')}>Quên mật khẩu?</button>
          </>}
          {mode !== 'login' && <button className="link-btn" onClick={() => setMode('login')}>← Quay lại đăng nhập</button>}
        </div>
      </div>
    </div>
  );
}

// ─── Profile Page ─────────────────────────────────────────────────────────────
function ProfilePage({ user, token, onBack, onLogout }) {
  const [form, setForm] = useState({ full_name: user.full_name || '', old_password: '', new_password: '' });
  const [history, setHistory] = useState([]);
  const [msg, setMsg] = useState('');
  const [err, setErr] = useState('');
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  useEffect(() => {
    api.get(`/users/${user.user_id}/history`, token)
      .then(r => setHistory(r.data.history || []))
      .catch(() => {});
  }, [user, token]);

  const saveProfile = async e => {
    e.preventDefault(); setMsg(''); setErr('');
    try {
      await api.put('/auth/profile', { full_name: form.full_name }, token);
      setMsg('Cập nhật tên thành công!');
    } catch { setErr('Lỗi cập nhật'); }
  };

  const changePass = async e => {
    e.preventDefault(); setMsg(''); setErr('');
    try {
      await api.post('/auth/change-password', { old_password: form.old_password, new_password: form.new_password }, token);
      setMsg('Đổi mật khẩu thành công!');
      setForm(f => ({ ...f, old_password: '', new_password: '' }));
    } catch (er) { setErr(er.response?.data?.detail || 'Lỗi đổi mật khẩu'); }
  };

  return (
    <div className="profile-page">
      <div className="profile-header">
        <button className="back-btn" onClick={onBack}>← Quay lại</button>
        <h2>Hồ sơ cá nhân</h2>
        <button className="btn-danger" onClick={onLogout}>Đăng xuất</button>
      </div>

      {msg && <div className="alert success">{msg}</div>}
      {err && <div className="alert error">{err}</div>}

      <div className="profile-grid">
        <div className="profile-card">
          <div className="profile-avatar">{(user.full_name || user.email || 'U')[0].toUpperCase()}</div>
          <div className="profile-email">{user.email}</div>

          <form onSubmit={saveProfile} className="profile-form">
            <label>Họ và tên</label>
            <input className="input" value={form.full_name} onChange={e => set('full_name', e.target.value)} />
            <button type="submit" className="btn-primary">Lưu thông tin</button>
          </form>
        </div>

        <div className="profile-card">
          <h3>🔒 Đổi mật khẩu</h3>
          <form onSubmit={changePass} className="profile-form">
            <input className="input" type="password" placeholder="Mật khẩu hiện tại" value={form.old_password}
              onChange={e => set('old_password', e.target.value)} required />
            <input className="input" type="password" placeholder="Mật khẩu mới" value={form.new_password}
              onChange={e => set('new_password', e.target.value)} required />
            <button type="submit" className="btn-primary">Đổi mật khẩu</button>
          </form>
        </div>

        <div className="profile-card full-width">
          <h3>🕓 Lịch sử xem ({history.length})</h3>
          <div className="history-grid">
            {history.length === 0 && <p className="text-muted">Chưa có lịch sử</p>}
            {history.map((item, i) => (
              <div key={i} className="history-item" title={item.title}>
                <img src={item.img_url || ''} alt={item.title} className="history-img"
                  onError={e => { e.target.src = `https://placehold.co/100x100/1e293b/64748b?text=?`; }} />
                <div className="history-title">{item.title}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Product Detail Page ──────────────────────────────────────────────────────
function ProductPage({ product, token, userId, onBack, onRecsUpdate }) {
  const [rating, setRating] = useState(0);
  const [submitted, setSubmitted] = useState(false);
  const [similar, setSimilar] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleView = useCallback(async () => {
    if (!token || !userId) return;
    try {
      const res = await api.post('/interaction', { product_asin: product.asin, action_type: 'view' }, token);
      if (res.data.recommendations) onRecsUpdate(res.data.recommendations);
    } catch {}
  }, [product, token, userId, onRecsUpdate]);

  useEffect(() => {
    handleView();
    // Load similar items
    api.post('/recommend/sequence', { sequence: [product.item_id], top_k: 6 })
      .then(r => setSimilar(r.data.recommendations || []))
      .catch(() => {});
  }, [product.asin]);

  const submitRating = async () => {
    if (!token || !userId || rating === 0) return;
    setLoading(true);
    try {
      const res = await api.post('/interaction', { product_asin: product.asin, action_type: 'rate', rating }, token);
      if (res.data.recommendations) onRecsUpdate(res.data.recommendations);
      setSubmitted(true);
    } catch {} finally { setLoading(false); }
  };

  return (
    <div className="product-detail-page">
      <button className="back-btn" onClick={onBack}>← Quay lại</button>
      <div className="product-detail-grid">
        <div className="product-detail-img-wrap">
          <img src={product.img_url || ''} alt={product.title} className="product-detail-img"
            onError={e => { e.target.src = `https://placehold.co/400x400/1e293b/64748b?text=No+Image`; }} />
        </div>
        <div className="product-detail-info">
          <div className="product-category">{product.category}</div>
          <h1 className="product-detail-title">{product.title}</h1>
          <div className="product-detail-price">{product.price > 0 ? `$${Number(product.price).toFixed(2)}` : 'Liên hệ'}</div>
          <div className="detail-rating-row">
            <span className="text-muted">Đánh giá của bạn:</span>
            <StarRating value={rating} onChange={setRating} readonly={submitted} />
            {rating > 0 && !submitted && (
              <button className="btn-primary" onClick={submitRating} disabled={loading}>
                {loading ? '...' : 'Gửi đánh giá'}
              </button>
            )}
            {submitted && <span className="badge-success">✓ Đã đánh giá</span>}
          </div>
          {submitted && rating >= 4 && (
            <div className="alert success">⚡ Gợi ý đã được cập nhật dựa trên sở thích của bạn!</div>
          )}
        </div>
      </div>

      {similar.length > 0 && (
        <section className="similar-section">
          <h2 className="section-title">🔗 Sản phẩm tương tự</h2>
          <div className="rec-grid">
            {similar.map((item, i) => (
              <ProductCard key={i} item={item} onClick={() => {}} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

// ─── Realtime Demo Panel ──────────────────────────────────────────────────────
function DemoPanel({ itemToId }) {
  const [open, setOpen] = useState(false);
  const [inputId, setInputId] = useState('');
  const [sequence, setSequence] = useState([]);
  const [recs, setRecs] = useState([]);
  const [loading, setLoading] = useState(false);

  const addItem = () => {
    const id = parseInt(inputId);
    if (!id || sequence.includes(id)) return;
    setSequence(s => [...s, id]);
    setInputId('');
  };

  const removeItem = idx => setSequence(s => s.filter((_, i) => i !== idx));

  const predict = async () => {
    if (sequence.length === 0) return;
    setLoading(true);
    try {
      const res = await api.post('/recommend/sequence', { sequence, top_k: 6 });
      setRecs(res.data.recommendations || []);
    } catch {} finally { setLoading(false); }
  };

  if (!open) return (
    <button className="demo-fab" onClick={() => setOpen(true)} title="Mở Demo Realtime">
      🧪
    </button>
  );

  return (
    <div className="demo-panel">
      <div className="demo-header">
        <span>🧪 Demo Realtime</span>
        <button className="icon-btn" onClick={() => setOpen(false)}>✕</button>
      </div>
      <div className="demo-body">
        <div className="demo-input-row">
          <input className="input small" placeholder="Item ID..." value={inputId}
            onChange={e => setInputId(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && addItem()} />
          <button className="btn-sm" onClick={addItem}>+</button>
        </div>
        <div className="demo-sequence">
          {sequence.length === 0 && <span className="text-muted">Chưa có item nào</span>}
          {sequence.map((id, i) => (
            <span key={i} className="seq-tag">
              {id} <button className="remove-btn" onClick={() => removeItem(i)}>×</button>
            </span>
          ))}
        </div>
        <button className="btn-primary" onClick={predict} disabled={loading || sequence.length === 0}>
          {loading ? 'Đang dự đoán...' : '⚡ Predict'}
        </button>
        <div className="demo-recs">
          {recs.map((r, i) => (
            <div key={i} className="demo-rec-item">
              <img src={r.img_url || ''} alt={r.title}
                onError={e => { e.target.src = `https://placehold.co/48x48/1e293b/64748b?text=?`; }} />
              <div>
                <div className="demo-rec-title">{r.title?.substring(0, 40)}...</div>
                <div className="text-muted">{(r.score * 100).toFixed(1)}% match</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── Home Page ────────────────────────────────────────────────────────────────
function HomePage({ user, token, onProductClick, onProfile, onLogout }) {
  const [recs, setRecs] = useState([]);
  const [popular, setPopular] = useState([]);
  const [history, setHistory] = useState([]);
  const [recsSource, setRecsSource] = useState('');
  const [loading, setLoading] = useState(true);
  const [demoUser, setDemoUser] = useState('');
  const [demoUsers, setDemoUsers] = useState([]);

  const loadForUser = useCallback(async (uid, tkn) => {
    setLoading(true);
    try {
      const [recRes, popRes, histRes] = await Promise.all([
        api.get(`/recommend?user_id=${uid}&top_k=12`, tkn),
        api.get('/recommend/popular?top_k=12'),
        api.get(`/users/${uid}/history`, tkn),
      ]);
      setRecs(recRes.data.recommendations || []);
      setRecsSource(recRes.data.source || '');
      setPopular(popRes.data.recommendations || []);
      setHistory((histRes.data.history || []).slice(0, 10));
    } catch {} finally { setLoading(false); }
  }, []);

  useEffect(() => {
    const uid = user?.user_id || demoUser;
    if (uid) loadForUser(uid, token);
  }, [user, demoUser, token, loadForUser]);

  useEffect(() => {
    api.get('/').then(r => {
      const users = r.data.demo_users || [];
      setDemoUsers(users);
      if (!user && users.length > 0) setDemoUser(String(users[0]));
    }).catch(() => {});
  }, [user]);

  const handleRecsUpdate = useCallback(newRecs => {
    setRecs(newRecs);
    setRecsSource('personalized');
  }, []);

  const activeUid = user?.user_id || demoUser;

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="logo">⚡ SeqRec AI</div>
        <div className="header-right">
          {!user && (
            <div className="demo-selector">
              <span className="text-muted">Demo user:</span>
              <select value={demoUser} onChange={e => setDemoUser(e.target.value)} className="select-input">
                {demoUsers.map(u => <option key={u} value={u}>User #{u}</option>)}
              </select>
            </div>
          )}
          {user ? (
            <div className="user-menu">
              <div className="user-avatar" onClick={onProfile}>{(user.full_name || user.email || 'U')[0].toUpperCase()}</div>
              <span className="user-name">{user.full_name || user.email}</span>
              <button className="btn-ghost" onClick={onLogout}>Đăng xuất</button>
            </div>
          ) : (
            <button className="btn-primary" onClick={onProfile}>Đăng nhập</button>
          )}
        </div>
      </header>

      {loading ? (
        <div className="loading"><div className="spinner" /><span>Đang tải...</span></div>
      ) : (
        <main>
          {history.length > 0 && (
            <section className="section">
              <h2 className="section-title">🕓 Đã xem gần đây</h2>
              <div className="history-grid">
                {history.map((item, i) => (
                  <div key={i} className="history-item" onClick={() => onProductClick(item)} title={item.title}>
                    <img src={item.img_url || ''} alt={item.title} className="history-img"
                      onError={e => { e.target.src = `https://placehold.co/100x100/1e293b/64748b?text=?`; }} />
                    <div className="history-title">{item.title}</div>
                  </div>
                ))}
              </div>
            </section>
          )}

          <section className="section">
            <h2 className="section-title">
              {recsSource === 'popular' ? '🔥 Sản phẩm phổ biến' : '✨ Gợi ý cho bạn'}
              {recsSource === 'personalized' && <span className="badge-ai">AI Personalized</span>}
            </h2>
            <div className="rec-grid">
              {recs.map((item, i) => (
                <ProductCard key={i} item={item} onClick={p => onProductClick(p, handleRecsUpdate)} />
              ))}
            </div>
          </section>

          {popular.length > 0 && recsSource !== 'popular' && (
            <section className="section">
              <h2 className="section-title">📈 Trending Products</h2>
              <div className="rec-grid">
                {popular.map((item, i) => (
                  <ProductCard key={i} item={item} onClick={p => onProductClick(p, handleRecsUpdate)} />
                ))}
              </div>
            </section>
          )}
        </main>
      )}
      <DemoPanel />
    </div>
  );
}

// ─── Root App ─────────────────────────────────────────────────────────────────
export default function App() {
  const [page, setPage] = useState('home'); // home | auth | profile | product
  const [token, setToken] = useState(() => localStorage.getItem('seqrec_token'));
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem('seqrec_user')); } catch { return null; }
  });
  const [currentProduct, setCurrentProduct] = useState(null);
  const [recsCallback, setRecsCallback] = useState(null);

  const handleLogin = (tk, u) => {
    setToken(tk); setUser(u);
    localStorage.setItem('seqrec_token', tk);
    localStorage.setItem('seqrec_user', JSON.stringify(u));
    setPage('home');
  };

  const handleLogout = () => {
    if (token) api.post('/auth/logout', {}, token).catch(() => {});
    setToken(null); setUser(null);
    localStorage.removeItem('seqrec_token');
    localStorage.removeItem('seqrec_user');
    setPage('home');
  };

  const handleProductClick = (product, onRecsUpdate) => {
    setCurrentProduct(product);
    setRecsCallback(() => onRecsUpdate);
    setPage('product');
  };

  if (page === 'auth') return <AuthPage onLogin={handleLogin} />;

  if (page === 'profile') {
    if (!user) return <AuthPage onLogin={handleLogin} />;
    return <ProfilePage user={user} token={token} onBack={() => setPage('home')} onLogout={handleLogout} />;
  }

  if (page === 'product' && currentProduct) {
    return (
      <ProductPage
        product={currentProduct}
        token={token}
        userId={user?.user_id}
        onBack={() => setPage('home')}
        onRecsUpdate={recsCallback || (() => {})}
      />
    );
  }

  return (
    <HomePage
      user={user}
      token={token}
      onProductClick={handleProductClick}
      onProfile={() => user ? setPage('profile') : setPage('auth')}
      onLogout={handleLogout}
    />
  );
}
