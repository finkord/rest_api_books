const BACKEND_URL = window.BACKEND_URL || 'http://127.0.0.1:4010';

const ui = {
  authSection: document.getElementById('auth-section'),
  dashboardSection: document.getElementById('dashboard-section'),
  booksContainer: document.getElementById('books-container'),
  loader: document.getElementById('loader'),
  toast: document.getElementById('toast'),
  toastMessage: document.getElementById('toast-message')
};

let state = {
  accessToken: localStorage.getItem('access_token'),
  refreshToken: localStorage.getItem('refresh_token'),
  books: [],
  limit: 10,
  offset: 0
};

// Utils
function showToast(message, isError = false) {
  ui.toastMessage.textContent = message;
  ui.toast.style.display = 'block';
  setTimeout(() => ui.toast.style.display = 'none', 3000);
}

function updateView() {
  if (state.accessToken) {
    ui.authSection.style.display = 'none';
    ui.dashboardSection.style.display = 'block';
    fetchBooks();
  } else {
    ui.authSection.style.display = 'block';
    ui.dashboardSection.style.display = 'none';
  }
}

// API Fetch Wrapper (handles tokens)
async function fetchAPI(endpoint, options = {}) {
  if (!options.headers) options.headers = {};
  if (state.accessToken) {
    options.headers['Authorization'] = `Bearer ${state.accessToken}`;
  }
  let res = await fetch(`${BACKEND_URL}${endpoint}`, options);

  if (res.status === 401 && state.refreshToken) {
    const refreshRes = await fetch(`${BACKEND_URL}/api/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: state.refreshToken })
    });
    if (refreshRes.ok) {
      const data = await refreshRes.json();
      state.accessToken = data.access_token;
      state.refreshToken = data.refresh_token;
      localStorage.setItem('access_token', state.accessToken);
      localStorage.setItem('refresh_token', state.refreshToken);
      options.headers['Authorization'] = `Bearer ${state.accessToken}`;
      res = await fetch(`${BACKEND_URL}${endpoint}`, options);
    } else {
      logout();
    }
  }
  return res;
}

// Auth Actions
async function login(username, password) {
  const formData = new URLSearchParams();
  formData.append('username', username);
  formData.append('password', password);

  const res = await fetch(`${BACKEND_URL}/api/auth/login`, {
    method: 'POST',
    body: formData
  });
  if (res.ok) {
    const data = await res.json();
    state.accessToken = data.access_token;
    state.refreshToken = data.refresh_token;
    localStorage.setItem('access_token', state.accessToken);
    localStorage.setItem('refresh_token', state.refreshToken);
    showToast('Logged in successfully!');
    updateView();
  } else {
    showToast('Login failed', true);
  }
}

async function register(username, password) {
  const res = await fetch(`${BACKEND_URL}/api/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  });
  if (res.ok) {
    showToast('Registered successfully! Logging in...');
    await login(username, password);
  } else {
    const err = await res.json();
    showToast(err.detail || 'Registration failed', true);
  }
}

async function logout() {
  if (state.accessToken) {
    await fetchAPI('/api/auth/logout', { method: 'POST' });
  }
  state.accessToken = null;
  state.refreshToken = null;
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  updateView();
}

// Book Actions
async function fetchBooks() {
  ui.loader.style.display = 'block';
  ui.booksContainer.innerHTML = '';

  const author = document.getElementById('filter-author').value;
  const status = document.getElementById('filter-status').value;
  const sortBy = document.getElementById('filter-sort').value;
  const sortOrder = document.getElementById('filter-order').value;

  const params = new URLSearchParams({ limit: state.limit, offset: state.offset });
  if (author) params.append('author', author);
  if (status) params.append('status', status);
  if (sortBy) params.append('sort_by', sortBy);
  if (sortOrder) params.append('sort_order', sortOrder);

  const res = await fetchAPI(`/api/books?${params.toString()}`);
  ui.loader.style.display = 'none';

  if (res.ok) {
    const data = await res.json();
    state.books = data.items || [];
    renderBooks();
    document.getElementById('prev-btn').disabled = !data.prev_page;
    document.getElementById('next-btn').disabled = !data.next_page;
  } else {
    showToast('Failed to load books', true);
  }
}

function renderBooks() {
  ui.booksContainer.innerHTML = '';
  if (state.books.length === 0) {
    ui.booksContainer.innerHTML = '<p>No books found.</p>';
    return;
  }
  state.books.forEach((book) => {
    const el = document.createElement('div');
    el.className = 'window';
    el.innerHTML = `
      <div class="title-bar">
        <button aria-label="Close" class="close" onclick="deleteBook('${book.id}')">x</button>
        <h1 class="title">${book.title}</h1>
      </div>
      <div class="window-pane">
        <p><strong>Author:</strong> ${book.author}</p>
        <p><strong>Description:</strong> ${book.description}</p>
        <p><strong>Year:</strong> ${book.year_published}</p>
        <p><strong>Status:</strong> ${book.status}</p>
      </div>
    `;
    ui.booksContainer.appendChild(el);
  });
}

// Make deleteBook global so onclick works
window.deleteBook = async function (id) {
  if (!confirm("Delete this book?")) return;
  const res = await fetchAPI(`/api/books/${id}`, { method: 'DELETE' });
  if (res.ok) {
    showToast('Book deleted');
    fetchBooks();
  } else {
    showToast('Failed to delete', true);
  }
}

// Event Listeners
document.getElementById('auth-form').addEventListener('submit', (e) => {
  e.preventDefault();
  login(document.getElementById('username').value, document.getElementById('password').value);
});

document.getElementById('register-btn').addEventListener('click', () => {
  const u = document.getElementById('username').value;
  const p = document.getElementById('password').value;
  if (!u || !p) return showToast("Enter username and password", true);
  register(u, p);
});

document.getElementById('logout-btn').addEventListener('click', logout);

document.getElementById('add-book-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const btn = document.getElementById('submit-btn');
  btn.disabled = true;

  const payload = [{
    title: document.getElementById('title').value,
    author: document.getElementById('author').value,
    description: document.getElementById('description').value,
    status: document.getElementById('status').value,
    year_published: parseInt(document.getElementById('year').value, 10)
  }];

  const res = await fetchAPI('/api/books', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });

  btn.disabled = false;
  if (res.ok) {
    showToast('Book created!');
    document.getElementById('add-book-form').reset();
    fetchBooks();
  } else {
    showToast('Creation failed', true);
  }
});

document.getElementById('apply-filters-btn').addEventListener('click', () => {
  state.offset = 0;
  fetchBooks();
});

document.getElementById('prev-btn').addEventListener('click', () => {
  state.offset = Math.max(0, state.offset - state.limit);
  fetchBooks();
});

document.getElementById('next-btn').addEventListener('click', () => {
  state.offset += state.limit;
  fetchBooks();
});

// Initialize
updateView();
