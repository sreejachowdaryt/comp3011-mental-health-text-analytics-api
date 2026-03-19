/**
 * auth.js
 * Handles user registration, login, logout,
 * and toggling between the auth screen and main app.
 */

// ── SHOW / HIDE SCREENS ──

function showAuth() {
  document.getElementById('auth-page').style.display = 'flex';
  document.getElementById('sidebar').style.display = 'none';
  document.getElementById('main').style.display = 'none';
}

function showApp() {
  document.getElementById('auth-page').style.display = 'none';
  document.getElementById('sidebar').style.display = 'flex';
  document.getElementById('main').style.display = 'block';
  document.getElementById('user-email').textContent = currentUser || '—';
  navigate('dashboard');
}

// ── TAB SWITCH (login ↔ register) ──

function switchTab(tab) {
  document.getElementById('login-form').style.display    = tab === 'login'    ? 'block' : 'none';
  document.getElementById('register-form').style.display = tab === 'register' ? 'block' : 'none';
  document.getElementById('tab-login').classList.toggle('active',    tab === 'login');
  document.getElementById('tab-register').classList.toggle('active', tab === 'register');
}

// ── LOGIN ──

async function doLogin() {
  const email    = document.getElementById('login-email').value.trim();
  const password = document.getElementById('login-password').value;
  document.getElementById('login-error').textContent = '';

  try {
    const res = await api('POST', '/auth/login', { email, password }, false);
    token       = res.access_token;
    currentUser = email;
    localStorage.setItem('mp_token', token);
    localStorage.setItem('mp_email', email);
    showApp();
    toast('Signed in successfully', 'success');
  } catch (e) {
    document.getElementById('login-error').textContent = e.message || 'Invalid credentials';
  }
}

// ── REGISTER ──

async function doRegister() {
  const email    = document.getElementById('reg-email').value.trim();
  const password = document.getElementById('reg-password').value;
  document.getElementById('reg-error').textContent = '';

  try {
    await api('POST', '/auth/register', { email, password }, false);
    toast('Account created — sign in now', 'success');
    switchTab('login');
    document.getElementById('login-email').value = email;
  } catch (e) {
    document.getElementById('reg-error').textContent = e.message || 'Registration failed';
  }
}

// ── LOGOUT ──

function logout() {
  token       = null;
  currentUser = null;
  localStorage.removeItem('mp_token');
  localStorage.removeItem('mp_email');
  showAuth();
}