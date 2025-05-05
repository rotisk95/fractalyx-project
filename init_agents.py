#!/usr/bin/env python3
# Initialize default agents in the database

from app import app, db
from models import Agent, AgentRole

def create_default_agents():
    """Create default agents if they don't exist in the database"""
    with app.app_context():
        # Check if we have any agents
        agent_count = Agent.query.count()
        if agent_count > 0:
            print(f"Found {agent_count} agents, skipping initialization")
            return
        
        # Create the default agents
        agents = [
            Agent(
                name="Coordinator",
                role=AgentRole.COORDINATOR,
                description="Coordinates the work of other agents and manages the overall project flow.",
                model="llama3:8b-vision"
            ),
            Agent(
                name="Planner",
                role=AgentRole.PLANNER,
                description="Plans the project structure and creates detailed specifications.",
                model="llama3:8b"
            ),
            Agent(
                name="Researcher",
                role=AgentRole.RESEARCHER,
                description="Researches information needed for the project.",
                model="llama3:8b"
            ),
            Agent(
                name="Developer",
                role=AgentRole.DEVELOPER,
                description="Develops code and technical solutions.",
                model="llama3:8b"
            ),
            Agent(
                name="Tester",
                role=AgentRole.TESTER,
                description="Tests code and solutions for quality and correctness.",
                model="llama3:8b"
            ),
            Agent(
                name="Reviewer",
                role=AgentRole.REVIEWER,
                description="Reviews work from other agents and provides feedback.",
                model="llama3:8b"
            )
        ]
        
        for agent in agents:
            db.session.add(agent)
        
        db.session.commit()
        print(f"Created {len(agents)} default agents")

if __name__ == "__main__":
    create_default_agents()
