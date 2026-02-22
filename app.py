from flask import Flask, jsonify, request

app = Flask(__name__)

# Optimal data structure: dictionary for fast O(1) access by ID
books = {
    1: {
        "id": 1,
        "title": "The Great Gatsby",
        "author": "F. Scott Fitzgerald",
        "description": "A novel written by American author F. Scott Fitzgerald.",
        "year": 1925
    },
    2: {
        "id": 2,
        "title": "1984",
        "author": "George Orwell",
        "description": "A novel written by George Orwell.",
        "year": 1949
    },
    3: {
        "id": 3,
        "title": "Brave New World",
        "author": "Aldous Huxley",
        "description": "A novel written by Aldous Huxley.",
        "year": 1932
    }
}

next_id = 4

@app.route('/books', methods=['GET'])
def get_books():
    """Get a list of all books (Read - Collection)"""
    # Return a list of values from the dictionary
    return jsonify(list(books.values())), 200

@app.route('/books/<int:book_id>', methods=['GET'])
def get_book(book_id):
    """Get data for a specific book (Read - Single)"""
    book = books.get(book_id)
    if book:
        return jsonify(book), 200
    return jsonify({"error": "Book not found"}), 404

@app.route('/books', methods=['POST'])
def create_book():
    """Create a new book (Create)"""
    global next_id
    data = request.get_json()
    
    # Validation
    if not data:
        return jsonify({"error": "Request must be JSON"}), 400
    
    if 'title' not in data or not str(data['title']).strip():
        return jsonify({"error": "Title is required and cannot be empty"}), 422
        
    if 'author' not in data or not str(data['author']).strip():
        return jsonify({"error": "Author is required and cannot be empty"}), 422
        
    if 'year' in data:
        try:
            year = int(data['year'])
            if year < 0 or year > 2100:
                return jsonify({"error": "Year must be between 0 and 2100"}), 422
        except ValueError:
            return jsonify({"error": "Year must be an integer"}), 422
            
    if 'description' in data and len(str(data['description'])) > 1000:
        return jsonify({"error": "Description is too long (max 1000 chars)"}), 422
        
    new_book = {
        "id": next_id,
        "title": str(data['title']).strip(),
        "author": str(data['author']).strip(),
        "description": str(data.get('description', '')).strip(),
        "year": int(data['year']) if 'year' in data else None
    }
    
    books[next_id] = new_book
    next_id += 1
    
    return jsonify(new_book), 201

@app.route('/books/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    """Update an existing book (Update)"""
    book = books.get(book_id)
    if not book:
        return jsonify({"error": "Book not found"}), 404
        
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
        
    # Validation logic for updates
    if 'title' in data and not str(data['title']).strip():
        return jsonify({"error": "Title cannot be empty"}), 422
        
    if 'author' in data and not str(data['author']).strip():
        return jsonify({"error": "Author cannot be empty"}), 422
        
    if 'year' in data:
        try:
            year = int(data['year'])
            if year < 0 or year > 2100:
                return jsonify({"error": "Year must be between 0 and 2100"}), 422
        except ValueError:
            return jsonify({"error": "Year must be an integer"}), 422
            
    if 'description' in data and len(str(data['description'])) > 1000:
        return jsonify({"error": "Description is too long (max 1000 chars)"}), 422
        
    book['title'] = str(data['title']).strip() if 'title' in data else book['title']
    book['author'] = str(data['author']).strip() if 'author' in data else book['author']
    book['description'] = str(data['description']).strip() if 'description' in data else book['description']
    
    if 'year' in data:
        book['year'] = int(data['year'])
    
    return jsonify(book), 200

@app.route('/books/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    """Delete a book (Delete)"""
    if book_id in books:
        del books[book_id]
        return '', 204 # HTTP 204 No Content is best practice for successful deletion without return body
    return jsonify({"error": "Book not found"}), 404

if __name__ == '__main__':
    app.run()