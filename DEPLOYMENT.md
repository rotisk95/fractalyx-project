# Deployment Guide for Fractalyx

## Prerequisites

1. Python 3.11 or higher
2. PostgreSQL database
3. Stripe account (for payment processing)

## Environment Setup

### Environment Variables

Create a `.env` file in the root directory with the following variables:

```
DATABASE_URL=postgresql://username:password@localhost:5432/fractalyx
STRIPE_SECRET_KEY=your_stripe_secret_key
SESSION_SECRET=your_secure_random_string
FLASK_SECRET_KEY=another_secure_random_string
```

### Database Setup

1. Create a PostgreSQL database:
   ```
   createdb fractalyx
   ```

2. The application will automatically create the required tables on startup.

## Installation Steps

1. Clone the repository:
   ```
   git clone https://github.com/rotisk95/fractalyx-project.git
   cd fractalyx-project
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Initialize the default agents:
   ```
   python init_agents.py
   ```

5. Start the application:
   ```
   gunicorn --bind 0.0.0.0:5000 main:app
   ```

## Deployment Options

### Production Deployment

For production deployment, consider using:

1. **Docker**: Containerize the application for consistent deployment.
2. **NGINX**: As a reverse proxy in front of Gunicorn.
3. **Supervisor**: To manage the Gunicorn process.

### Cloud Deployment

The application can be deployed to various cloud platforms:

1. **Heroku**: Easy deployment with PostgreSQL add-on.
2. **AWS**: Using EC2, RDS for PostgreSQL, and Elastic Beanstalk.
3. **Google Cloud Platform**: Using App Engine or Compute Engine.

## Post-Deployment Tasks

1. Set up a proper domain name and SSL certificate.
2. Configure email sending for notifications.
3. Set up monitoring and logging.
4. Create regular database backups.
