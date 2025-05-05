# Fractalyx

A collaborative intelligence platform leveraging a fractal network of AI agents designed to evolve, adapt, and accelerate users' vision.

## Overview

Fractalyx is a dynamic multiagent system that leverages advanced AI capabilities to create an interconnected network of intelligent nodes for collaborative project development. The platform enables intelligent ticket tracking, adaptive checkpoints, and flexible AI-driven workflows with enhanced interaction capabilities.

## Key Features

- **Intelligent Agent Network**: Six specialized fractal nodes (Coordinator, Planner, Researcher, Developer, Tester, and Reviewer) work together to handle different aspects of project development.
- **Project Management**: Create and track projects with a comprehensive ticket system and milestone checkpoints.
- **Secure Authentication**: User registration and login system with password protection.
- **SaaS Subscription Model**: Multiple pricing tiers processed through Stripe payment integration.
- **Interactive Chat Interface**: Communicate with the fractal intelligence network through a user-friendly chat interface.

## Technical Stack

- **Backend**: Flask with PostgreSQL database
- **Frontend**: Bootstrap CSS with custom styling
- **Authentication**: Flask-Login
- **Payment Processing**: Stripe Checkout
- **AI Integration**: Ollama for local LLM processing

## Installation

1. Clone this repository
2. Install dependencies with `pip install -r requirements.txt`
3. Set up environment variables
4. Initialize the database with `python init_agents.py`
5. Run the application with `gunicorn --bind 0.0.0.0:5000 main:app`

## Environment Variables

The following environment variables are required:

- `DATABASE_URL`: PostgreSQL database connection string
- `STRIPE_SECRET_KEY`: Stripe API key for payment processing
- `SESSION_SECRET`: Secret key for Flask sessions

## License

All rights reserved.
