const API_URL = 'http://127.0.0.1:4010/books';

const booksContainer = document.getElementById('books-container');
const loader = document.getElementById('loader');
const form = document.getElementById('add-book-form');
const submitBtn = document.getElementById('submit-btn');
const toast = document.getElementById('toast');

// State
let books = [];

// Show toast notification
function showToast(message, isError = false) {
  toast.textContent = message;
  toast.style.background = isError ? '#ef4444' : '#10b981';
  toast.classList.add('show');
  setTimeout(() => {
    toast.classList.remove('show');
  }, 3000);
}

// Fetch books from Mock API
async function fetchBooks() {
  booksContainer.innerHTML = '';
  loader.style.display = 'block';
  
  try {
    const response = await fetch(API_URL);
    if (!response.ok) throw new Error('Failed to fetch');
    const data = await response.json();
    books = data;
    renderBooks();
  } catch (error) {
    console.error('Error fetching books:', error);
    booksContainer.innerHTML = '<div class="empty-state">Failed to load books. Is the mock server running?</div>';
    showToast('Connection Error', true);
  } finally {
    loader.style.display = 'none';
  }
}

// Render books to DOM
function renderBooks() {
  booksContainer.innerHTML = '';
  
  if (books.length === 0) {
    booksContainer.innerHTML = '<div class="empty-state">No books available. Add one!</div>';
    return;
  }

  books.forEach((book, index) => {
    const el = document.createElement('div');
    el.className = 'book-item';
    // Stagger animation delay
    el.style.animation = `slideUp 0.4s ease forwards ${index * 0.1}s`;
    el.style.opacity = '0';
    el.style.transform = 'translateY(20px)';
    
    el.innerHTML = `
      <div class="book-title">${book.title}</div>
      <div class="book-author">by ${book.author}</div>
      <div class="book-year">${book.published_year}</div>
    `;
    booksContainer.appendChild(el);
  });
}

// Add animation keyframes via JS
const style = document.createElement('style');
style.textContent = `
  @keyframes slideUp {
    to { opacity: 1; transform: translateY(0); }
  }
`;
document.head.appendChild(style);

// Handle form submission
form.addEventListener('submit', async (e) => {
  e.preventDefault();
  
  const title = document.getElementById('title').value;
  const author = document.getElementById('author').value;
  const year = parseInt(document.getElementById('year').value, 10);
  
  const newBook = { title, author, published_year: year };
  
  submitBtn.disabled = true;
  submitBtn.textContent = 'Creating...';
  
  try {
    const response = await fetch(API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(newBook)
    });
    
    if (!response.ok) throw new Error('Failed to create');
    
    const createdBook = await response.json();
    
    // Add the newly created book (from mock response) to the UI
    books.push(createdBook);
    renderBooks();
    
    showToast('Book created successfully!');
    form.reset();
  } catch (error) {
    console.error('Error creating book:', error);
    showToast('Failed to create book', true);
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = 'Create Book';
  }
});

// Initial load
fetchBooks();
