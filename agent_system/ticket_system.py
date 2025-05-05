import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from models import Ticket, TicketStatus, TicketPriority, Comment, Agent
from app import db

logger = logging.getLogger(__name__)


class TicketManager:
    """Manages ticket operations for a project."""
    
    def __init__(self, project_id: int):
        """
        Initialize the ticket manager.
        
        Args:
            project_id (int): The ID of the project
        """
        self.project_id = project_id
        logger.debug(f"Initialized TicketManager for project {project_id}")
    
    def create_ticket(self, title: str, description: str, priority: str, 
                     due_date: Optional[datetime] = None, 
                     parent_ticket_id: Optional[int] = None) -> int:
        """
        Create a new ticket.
        
        Args:
            title (str): The ticket title
            description (str): The ticket description
            priority (str): The priority level (HIGH, MEDIUM, LOW, CRITICAL)
            due_date (Optional[datetime]): The due date, if any
            parent_ticket_id (Optional[int]): The parent ticket ID, if this is a subtask
            
        Returns:
            int: The ID of the created ticket
        """
        try:
            # Convert priority string to enum
            priority_enum = getattr(TicketPriority, priority.upper())
            
            ticket = Ticket(
                title=title,
                description=description,
                status=TicketStatus.OPEN,
                priority=priority_enum,
                due_date=due_date,
                project_id=self.project_id,
                parent_ticket_id=parent_ticket_id
            )
            
            db.session.add(ticket)
            db.session.commit()
            logger.info(f"Created ticket: {ticket.id} - {title}")
            return ticket.id
            
        except Exception as e:
            db.session.rollback()
            logger.exception(f"Error creating ticket: {str(e)}")
            raise
    
    def get_ticket(self, ticket_id: int) -> Optional[Dict]:
        """
        Get a ticket by ID.
        
        Args:
            ticket_id (int): The ticket ID
            
        Returns:
            Optional[Dict]: The ticket data, or None if not found
        """
        ticket = Ticket.query.get(ticket_id)
        if not ticket:
            return None
            
        # Convert to dictionary
        result = {
            "id": ticket.id,
            "title": ticket.title,
            "description": ticket.description,
            "status": ticket.status.value,
            "priority": ticket.priority.value,
            "created_at": ticket.created_at,
            "updated_at": ticket.updated_at,
            "due_date": ticket.due_date,
            "project_id": ticket.project_id,
            "assigned_to": None
        }
        
        if ticket.assigned_agent_id:
            agent = Agent.query.get(ticket.assigned_agent_id)
            if agent:
                result["assigned_to"] = {
                    "id": agent.id,
                    "name": agent.name,
                    "role": agent.role.value
                }
        
        return result
    
    def get_all_tickets(self, status: Optional[str] = None) -> List[Dict]:
        """
        Get all tickets for the project.
        
        Args:
            status (Optional[str]): Filter by status, if provided
            
        Returns:
            List[Dict]: List of tickets
        """
        query = Ticket.query.filter_by(project_id=self.project_id)
        
        if status:
            status_enum = getattr(TicketStatus, status.upper())
            query = query.filter_by(status=status_enum)
        
        tickets = query.all()
        result = []
        
        for ticket in tickets:
            ticket_data = {
                "id": ticket.id,
                "title": ticket.title,
                "status": ticket.status.value,
                "priority": ticket.priority.value,
                "created_at": ticket.created_at,
                "due_date": ticket.due_date,
                "assigned_to": None
            }
            
            if ticket.assigned_agent_id:
                agent = Agent.query.get(ticket.assigned_agent_id)
                if agent:
                    ticket_data["assigned_to"] = {
                        "id": agent.id,
                        "name": agent.name,
                        "role": agent.role.value
                    }
            
            result.append(ticket_data)
        
        return result
    
    def update_ticket(self, ticket_id: int, **kwargs) -> bool:
        """
        Update a ticket.
        
        Args:
            ticket_id (int): The ticket ID
            **kwargs: Fields to update
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            ticket = Ticket.query.get(ticket_id)
            if not ticket:
                logger.error(f"Ticket {ticket_id} not found")
                return False
            
            # Update fields
            for key, value in kwargs.items():
                if hasattr(ticket, key):
                    # Handle enum fields
                    if key == "status" and isinstance(value, str):
                        value = getattr(TicketStatus, value.upper())
                    elif key == "priority" and isinstance(value, str):
                        value = getattr(TicketPriority, value.upper())
                    
                    setattr(ticket, key, value)
            
            db.session.commit()
            logger.info(f"Updated ticket: {ticket_id}")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.exception(f"Error updating ticket {ticket_id}: {str(e)}")
            return False
    
    def assign_ticket(self, ticket_id: int, agent_id: int) -> bool:
        """
        Assign a ticket to an agent.
        
        Args:
            ticket_id (int): The ticket ID
            agent_id (int): The agent ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            ticket = Ticket.query.get(ticket_id)
            agent = Agent.query.get(agent_id)
            
            if not ticket or not agent:
                logger.error(f"Ticket {ticket_id} or Agent {agent_id} not found")
                return False
            
            ticket.assigned_agent_id = agent_id
            ticket.status = TicketStatus.IN_PROGRESS
            db.session.commit()
            logger.info(f"Assigned ticket {ticket_id} to agent {agent_id}")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.exception(f"Error assigning ticket {ticket_id} to agent {agent_id}: {str(e)}")
            return False
    
    def add_comment(self, ticket_id: int, content: str, agent_id: Optional[int] = None, is_user: bool = False) -> int:
        """
        Add a comment to a ticket.
        
        Args:
            ticket_id (int): The ticket ID
            content (str): The comment content
            agent_id (Optional[int]): The agent ID, if comment is from an agent
            is_user (bool): True if comment is from the user
            
        Returns:
            int: The ID of the created comment
        """
        try:
            ticket = Ticket.query.get(ticket_id)
            if not ticket:
                logger.error(f"Ticket {ticket_id} not found")
                raise ValueError(f"Ticket {ticket_id} not found")
            
            comment = Comment(
                content=content,
                ticket_id=ticket_id,
                agent_id=agent_id,
                is_user=is_user
            )
            
            db.session.add(comment)
            db.session.commit()
            logger.info(f"Added comment to ticket {ticket_id}")
            return comment.id
            
        except Exception as e:
            db.session.rollback()
            logger.exception(f"Error adding comment to ticket {ticket_id}: {str(e)}")
            raise
    
    def update_ticket_status(self, ticket_id: int, status: TicketStatus) -> bool:
        """
        Update the status of a ticket.
        
        Args:
            ticket_id (int): The ticket ID
            status (TicketStatus): The new status
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            ticket = Ticket.query.get(ticket_id)
            if not ticket:
                logger.error(f"Ticket {ticket_id} not found")
                return False
            
            ticket.status = status
            db.session.commit()
            logger.info(f"Updated ticket {ticket_id} status to {status.value}")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.exception(f"Error updating ticket {ticket_id} status: {str(e)}")
            return False
    
    def get_ticket_comments(self, ticket_id: int) -> List[Dict]:
        """
        Get all comments for a ticket.
        
        Args:
            ticket_id (int): The ticket ID
            
        Returns:
            List[Dict]: List of comments
        """
        ticket = Ticket.query.get(ticket_id)
        if not ticket:
            logger.error(f"Ticket {ticket_id} not found")
            return []
        
        comments = Comment.query.filter_by(ticket_id=ticket_id).order_by(Comment.created_at).all()
        result = []
        
        for comment in comments:
            comment_data = {
                "id": comment.id,
                "content": comment.content,
                "created_at": comment.created_at,
                "is_user": comment.is_user,
                "agent": None
            }
            
            if comment.agent_id:
                agent = Agent.query.get(comment.agent_id)
                if agent:
                    comment_data["agent"] = {
                        "id": agent.id,
                        "name": agent.name,
                        "role": agent.role.value
                    }
            
            result.append(comment_data)
        
        return result
