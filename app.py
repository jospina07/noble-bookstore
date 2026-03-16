from flask import Flask
from routes.main_routes import main
from routes.book_routes import books_bp

app = Flask(__name__)
app.register_blueprint(main)
app.register_blueprint(books_bp)

if __name__ == "__main__":
    app.run(debug=True)