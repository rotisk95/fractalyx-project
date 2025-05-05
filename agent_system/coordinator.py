import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from models import AgentRole, TicketStatus, Ticket, Project, Agent, Checkpoint, Message, Conversation
from agent_system.agents import BaseAgent, CoordinatorAgent, PlannerAgent, ResearcherAgent, DeveloperAgent, TesterAgent, ReviewerAgent
from agent_system.ticket_system import TicketManager
from app import db

logger = logging.getLogger(__name__)


class AgentCoordinator:
    """Manages the coordination between multiple agents in the system."""
    
    def __init__(self, project_id: int):
        """
        Initialize the agent coordinator.
        
        Args:
            project_id (int): The ID of the project being worked on
        """
        self.project_id = project_id
        self.ticket_manager = TicketManager(project_id)
        self.agents = {}
        self.coordinator_agent = None
        self._load_agents()
        logger.debug(f"Initialized AgentCoordinator for project {project_id}")
    
    def _load_agents(self):
        """Load all agents from the database and initialize them."""
        project = Project.query.get(self.project_id)
        if not project:
            raise ValueError(f"Project with ID {self.project_id} not found")
        
        db_agents = Agent.query.all()
        if not db_agents:
            logger.info("No agents found in database. Creating default agents.")
            self._create_default_agents()
            db_agents = Agent.query.all()
        
        for db_agent in db_agents:
            agent_instance = self._create_agent_instance(db_agent)
            self.agents[db_agent.id] = agent_instance
            
            # Set the coordinator agent
            if db_agent.role == AgentRole.COORDINATOR:
                self.coordinator_agent = agent_instance
        
        logger.debug(f"Loaded {len(self.agents)} agents")
    
    def _create_default_agents(self):
        """Create default agents if none exist in the database."""
        default_agents = [
            {"name": "Alice", "role": AgentRole.COORDINATOR, "model": "llama3:8b-vision"},
            {"name": "Bob", "role": AgentRole.PLANNER, "model": "llama3:8b-vision"},
            {"name": "Charlie", "role": AgentRole.RESEARCHER, "model": "llama3:8b-vision"},
            {"name": "Diana", "role": AgentRole.DEVELOPER, "model": "llama3:8b-vision"},
            {"name": "Eve", "role": AgentRole.TESTER, "model": "llama3:8b-vision"},
            {"name": "Frank", "role": AgentRole.REVIEWER, "model": "llama3:8b-vision"}
        ]
        
        for agent_data in default_agents:
            agent = Agent(
                name=agent_data["name"],
                role=agent_data["role"],
                model=agent_data["model"],
                description=f"Default {agent_data['role'].value} agent"
            )
            db.session.add(agent)
        
        db.session.commit()
        logger.info("Created default agents")
    
    def _create_agent_instance(self, db_agent: Agent) -> BaseAgent:
        """
        Create an agent instance based on the agent's role.
        
        Args:
            db_agent (Agent): The database agent model
            
        Returns:
            BaseAgent: An instance of the appropriate agent class
        """
        agent_class_map = {
            AgentRole.COORDINATOR: CoordinatorAgent,
            AgentRole.PLANNER: PlannerAgent,
            AgentRole.RESEARCHER: ResearcherAgent,
            AgentRole.DEVELOPER: DeveloperAgent,
            AgentRole.TESTER: TesterAgent,
            AgentRole.REVIEWER: ReviewerAgent
        }
        
        agent_class = agent_class_map.get(db_agent.role)
        if not agent_class:
            raise ValueError(f"Unknown agent role: {db_agent.role}")
        
        return agent_class(
            agent_id=db_agent.id,
            name=db_agent.name,
            role=db_agent.role,
            model=db_agent.model
        )
    
    def get_agent_by_id(self, agent_id: int) -> Optional[BaseAgent]:
        """
        Get an agent by its ID.
        
        Args:
            agent_id (int): The agent ID
            
        Returns:
            Optional[BaseAgent]: The agent instance, or None if not found
        """
        return self.agents.get(agent_id)
    
    def get_agent_by_role(self, role: AgentRole) -> Optional[BaseAgent]:
        """
        Get the first agent with the specified role.
        
        Args:
            role (AgentRole): The agent role
            
        Returns:
            Optional[BaseAgent]: The agent instance, or None if not found
        """
        for agent in self.agents.values():
            if agent.role == role:
                return agent
        return None
    
    def process_user_message(self, message: str, conversation_id: int, image_path: Optional[str] = None) -> str:
        """
        Process a user message, directing it to the coordinator agent.
        
        Args:
            message (str): The user message
            conversation_id (int): The ID of the conversation
            image_path (Optional[str]): Path to an image file, if any
            
        Returns:
            str: The coordinator's response
        """
        if not self.coordinator_agent:
            raise ValueError("No coordinator agent found")
        
        # Create a message record
        db_message = Message(
            content=message,
            is_user=True,
            conversation_id=conversation_id,
            has_image=bool(image_path),
            image_path=image_path
        )
        db.session.add(db_message)
        db.session.commit()
        
        # Process the message with the coordinator agent
        response = self.coordinator_agent.process_message(message, image_path)
        
        # Create a response message record
        response_message = Message(
            content=response,
            is_user=False,
            agent_id=self.coordinator_agent.agent_id,
            conversation_id=conversation_id,
            has_image=False
        )
        db.session.add(response_message)
        db.session.commit()
        
        # Analyze message for potential project actions
        self._analyze_and_update_project(message, response)
        
        return response
    
    def _analyze_and_update_project(self, user_message: str, agent_response: str):
        """
        Analyze messages to identify project actions that need to be taken.
        
        Args:
            user_message (str): The user's message
            agent_response (str): The agent's response
        """
        # This is a simplified implementation; in a real system, this would use
        # more sophisticated NLP/LLM processing to identify actions
        
        # Check if this might be a new ticket request
        if "new task" in user_message.lower() or "create ticket" in user_message.lower():
            # Ask the planner to create a more detailed specification
            planner = self.get_agent_by_role(AgentRole.PLANNER)
            if planner:
                planning_prompt = (
                    f"Based on this user request, create a detailed ticket specification:\n\n"
                    f"User request: {user_message}\n\n"
                    f"Include a title, description, and priority level."
                )
                plan_response = planner.process_message(planning_prompt)
                
                # Extract ticket details (in a real system, would use more robust parsing)
                # For now, just create a simple ticket
                title = user_message[:100]  # Use first 100 chars as title
                self.ticket_manager.create_ticket(
                    title=title,
                    description=user_message,
                    priority="MEDIUM"
                )
                logger.info(f"Created new ticket from user message: {title}")
    
    def assign_ticket_to_agent(self, ticket_id: int, agent_id: int) -> bool:
        """
        Assign a ticket to an agent.
        
        Args:
            ticket_id (int): The ticket ID
            agent_id (int): The agent ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        agent = self.get_agent_by_id(agent_id)
        if not agent:
            logger.error(f"Agent with ID {agent_id} not found")
            return False
        
        return self.ticket_manager.assign_ticket(ticket_id, agent_id)
    
    def update_ticket_status(self, ticket_id: int, status: TicketStatus) -> bool:
        """
        Update the status of a ticket.
        
        Args:
            ticket_id (int): The ticket ID
            status (TicketStatus): The new status
            
        Returns:
            bool: True if successful, False otherwise
        """
        return self.ticket_manager.update_ticket_status(ticket_id, status)
    
    def create_checkpoint(self, name: str, description: str, milestone_date: Optional[datetime] = None) -> int:
        """
        Create a new checkpoint for the project.
        
        Args:
            name (str): The checkpoint name
            description (str): The checkpoint description
            milestone_date (Optional[datetime]): The target date for the checkpoint
            
        Returns:
            int: The ID of the created checkpoint
        """
        checkpoint = Checkpoint(
            name=name,
            description=description,
            milestone_date=milestone_date,
            project_id=self.project_id
        )
        db.session.add(checkpoint)
        db.session.commit()
        logger.info(f"Created new checkpoint: {name}")
        return checkpoint.id
    
    def add_ticket_to_checkpoint(self, checkpoint_id: int, ticket_id: int) -> bool:
        """
        Associate a ticket with a checkpoint.
        
        Args:
            checkpoint_id (int): The checkpoint ID
            ticket_id (int): The ticket ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        checkpoint = Checkpoint.query.get(checkpoint_id)
        ticket = Ticket.query.get(ticket_id)
        
        if not checkpoint or not ticket:
            logger.error(f"Checkpoint {checkpoint_id} or Ticket {ticket_id} not found")
            return False
        
        if ticket not in checkpoint.related_tickets:
            checkpoint.related_tickets.append(ticket)
            db.session.commit()
            logger.info(f"Added ticket {ticket_id} to checkpoint {checkpoint_id}")
            return True
        
        return False
    
    def create_conversation(self, title: Optional[str] = None) -> int:
        """
        Create a new conversation.
        
        Args:
            title (Optional[str]): The conversation title
            
        Returns:
            int: The ID of the created conversation
        """
        if not title:
            title = f"Conversation {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
        
        conversation = Conversation(
            title=title,
            project_id=self.project_id
        )
        db.session.add(conversation)
        db.session.commit()
        logger.info(f"Created new conversation: {title}")
        return conversation.id
