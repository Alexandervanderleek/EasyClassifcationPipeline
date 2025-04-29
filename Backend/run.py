#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Classifier API - Development Server Entry Point
"""

import os
from app import create_app, db

# Explicitly set development environment for local runs
os.environ.setdefault('FLASK_ENV', 'development')

# Create Flask application with explicit development environment
app = create_app('development')

# Create tables if they don't exist (development only)
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    # Run development server
    app.run(debug=True, host='0.0.0.0', port=int(os.getenv('PORT', 5000)))