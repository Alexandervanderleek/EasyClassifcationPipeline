"""
Classifier API - Development Server Entry Point
"""

import os
from app import create_app, db

os.environ.setdefault('FLASK_ENV', 'development')

app = create_app('development')

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.getenv('PORT', 5000)))