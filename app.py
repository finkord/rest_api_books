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
    return jsonify({"error": "404, Book not found"}), 404

@app.route('/books', methods=['POST'])
def create_book():
    """Create a new book (Create)"""
    global next_id
    data = request.get_json()
    
    if not data or not 'title' in data or not 'author' in data:
        return jsonify({"error": "Title and author are required"}), 400
        
    new_book = {
        "id": next_id,
        "title": data['title'],
        "author": data['author'],
        "description": data.get('description', ''),
        "year": data.get('year')
    }
    
    books[next_id] = new_book
    next_id += 1
    
    return jsonify(new_book), 201

@app.route('/books/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    """Update an existing book (Update)"""
    book = books.get(book_id)
    if not book:
        return jsonify({"error": "404, Book not found"}), 404
        
    data = request.get_json()
    if not data:
        return jsonify({"error": "400, No data provided"}), 400
        
    book['title'] = data.get('title', book['title'])
    book['author'] = data.get('author', book['author'])
    book['description'] = data.get('description', book['description'])
    book['year'] = data.get('year', book['year'])
    
    return jsonify(book), 200

@app.route('/books/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    """Delete a book (Delete)"""
    if book_id in books:
        del books[book_id]
        return jsonify({"message": "200, Book deleted successfully"}), 200
    return jsonify({"error": "404, Book not found"}), 404

if __name__ == '__main__':
    app.run()