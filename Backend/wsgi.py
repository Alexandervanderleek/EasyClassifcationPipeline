#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Classifier API - WSGI Entry Point
"""

import os
from app import create_app

# Create Flask application for WSGI server
app = create_app(os.getenv('FLASK_ENV', 'production'))

if __name__ == '__main__':
    app.run()