import logging
from app import app  # noqa: F401
from init_agents import create_default_agents

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Make sure we have a Project
try:
    with app.app_context():
        from models import Project, db
        default_project = Project.query.first()
        if not default_project:
            default_project = Project(name="Default Project", description="General conversations and fractal intelligence tasks")
            db.session.add(default_project)
            db.session.commit()
            logger.info(f"Created default project with ID {default_project.id}")
        else:
            logger.info(f"Using existing project with ID {default_project.id}")
        
        # Initialize agents on startup
        create_default_agents()
        logger.info("Agent initialization complete")
except Exception as e:
    logger.error(f"Error initializing: {str(e)}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
