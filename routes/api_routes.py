import os
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify
import requests
from werkzeug.utils import secure_filename

from app import db
from models import Project, Agent, Ticket, Checkpoint, Conversation, Message, Comment, AgentRole, TicketStatus, TicketPriority
from agent_system.coordinator import AgentCoordinator

# Set up logging
logger = logging.getLogger(__name__)

# Create Blueprint
api_bp = Blueprint('api_bp', __name__)

# Ensure upload directory exists
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@api_bp.route('/projects', methods=['GET'])
def get_projects():
    """Get all projects"""
    try:
        projects = Project.query.order_by(Project.updated_at.desc()).all()
        
        result = []
        for project in projects:
            ticket_count = Ticket.query.filter_by(project_id=project.id).count()
            open_ticket_count = Ticket.query.filter_by(project_id=project.id, status=TicketStatus.OPEN).count()
            completed_ticket_count = Ticket.query.filter_by(project_id=project.id, status=TicketStatus.COMPLETED).count()
            
            result.append({
                'id': project.id,
                'name': project.name,
                'description': project.description,
                'created_at': project.created_at,
                'updated_at': project.updated_at,
                'ticket_count': ticket_count,
                'open_ticket_count': open_ticket_count,
                'completed_ticket_count': completed_ticket_count
            })
            
        return jsonify({'projects': result})
    except Exception as e:
        logger.exception(f"Error getting projects: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/projects', methods=['POST'])
def create_project():
    """Create a new project"""
    try:
        data = request.json or {}
        
        if not data.get('name'):
            return jsonify({'error': 'Project name is required'}), 400
        
        project = Project(
            name=data.get('name'),
            description=data.get('description', '')
        )
        
        db.session.add(project)
        db.session.commit()
        
        logger.info(f"Created new project: {project.name} (ID: {project.id})")
        
        return jsonify({
            'id': project.id,
            'name': project.name,
            'project_id': project.id,  # Added for consistency with other responses'
            'description': project.description,
            'created_at': project.created_at,
            'updated_at': project.updated_at
        })
    except Exception as e:
        db.session.rollback()
        logger.exception(f"Error creating project: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/projects/<int:project_id>', methods=['GET'])
def get_project(project_id):
    """Get a specific project"""
    try:
        project = Project.query.get_or_404(project_id)
        
        return jsonify({
            'id': project.id,
            'name': project.name,
            'description': project.description,
            'created_at': project.created_at,
            'updated_at': project.updated_at
        })
    except Exception as e:
        logger.exception(f"Error getting project {project_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/projects/<int:project_id>/tickets', methods=['GET'])
def get_project_tickets(project_id):
    """Get all tickets for a project"""
    try:
        status_filter = request.args.get('status')
        
        query = Ticket.query.filter_by(project_id=project_id)
        
        if status_filter and hasattr(TicketStatus, status_filter.upper()):
            status_enum = getattr(TicketStatus, status_filter.upper())
            query = query.filter_by(status=status_enum)
        
        tickets = query.all()
        
        result = []
        for ticket in tickets:
            agent_info = None
            if ticket.assigned_agent_id:
                agent = Agent.query.get(ticket.assigned_agent_id)
                if agent:
                    agent_info = {
                        'id': agent.id,
                        'name': agent.name,
                        'role': agent.role.value
                    }
            
            result.append({
                'id': ticket.id,
                'title': ticket.title,
                'description': ticket.description,
                'status': ticket.status.value,
                'priority': ticket.priority.value,
                'created_at': ticket.created_at,
                'updated_at': ticket.updated_at,
                'due_date': ticket.due_date,
                'assigned_to': agent_info
            })
            
        return jsonify({'tickets': result})
    except Exception as e:
        logger.exception(f"Error getting tickets for project {project_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/projects/<int:project_id>/tickets', methods=['POST'])
def create_project_ticket(project_id):
    """Create a new ticket for a project"""
    try:
        # Verify project exists
        Project.query.get_or_404(project_id)  # Check existence without assignment

        data = request.json or {}

        if not data.get('title'):
            return jsonify({'error': 'Ticket title is required'}), 400

        # Parse priority
        priority_str = data.get('priority', 'MEDIUM')
        priority = getattr(TicketPriority, priority_str.upper())

        # Parse due date
        due_date = None
        if data.get('due_date'):
            try:
                due_date_str = data.get('due_date')
                if due_date_str:
                    # Replace 'Z' with '+00:00' for valid timezone format
                    due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
                else:
                    due_date = None
            except ValueError as ve:
                logger.error(f"Invalid date format for due_date: {str(ve)}")
                return jsonify({'error': 'Invalid date format for due_date'}), 400

        ticket = Ticket(
            title=data.get('title'),
            description=data.get('description', ''),
            status=TicketStatus.OPEN,
            priority=priority,
            due_date=due_date,
            project_id=project_id,
            parent_ticket_id=data.get('parent_ticket_id')
        )

        db.session.add(ticket)
        db.session.commit()

        logger.info(f"Created new ticket: {ticket.title} (ID: {ticket.id}) for project {project_id}")

        return jsonify({
            'id': ticket.id,
            'title': ticket.title,
            'description': ticket.description,
            'status': ticket.status.value,
            'priority': ticket.priority.value,
            'created_at': ticket.created_at,
            'updated_at': ticket.updated_at,
            'due_date': ticket.due_date
        })
    except Exception as e:
        db.session.rollback()
        logger.exception(f"Error creating ticket for project {project_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/projects/<int:project_id>/checkpoints', methods=['GET'])
def get_project_checkpoints(project_id):
    """Get all checkpoints for a project"""
    try:
        checkpoints = Checkpoint.query.filter_by(project_id=project_id).all()
        
        result = []
        for checkpoint in checkpoints:
            related_tickets = []
            for ticket in checkpoint.related_tickets:
                related_tickets.append({
                    'id': ticket.id,
                    'title': ticket.title,
                    'status': ticket.status.value,
                    'priority': ticket.priority.value
                })
            
            result.append({
                'id': checkpoint.id,
                'name': checkpoint.name,
                'description': checkpoint.description,
                'created_at': checkpoint.created_at,
                'milestone_date': checkpoint.milestone_date,
                'completed': checkpoint.completed,
                'related_tickets': related_tickets
            })
            
        return jsonify({'checkpoints': result})
    except Exception as e:
        logger.exception(f"Error getting checkpoints for project {project_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/projects/<int:project_id>/checkpoints', methods=['POST'])
def create_project_checkpoint(project_id):
    """Create a new checkpoint for a project"""
    try:
        # Verify project exists
        Project.query.get_or_404(project_id)  # Keep the line but remove assignment
        
        data = request.json or {}
        
        if not data.get('name'):
            return jsonify({'error': 'Checkpoint name is required'}), 400
        
        # Parse milestone date
        milestone_date_str = data.get('milestone_date', '')
        milestone_date = None
        if milestone_date_str:
            milestone_date = datetime.fromisoformat(milestone_date_str.replace('Z', '+00:00'))
        
        checkpoint = Checkpoint()  # Instantiate without arguments
# Set attributes individually if setters or similar methods are used instead of constructor parameters
        checkpoint.name = data.get('name')
        checkpoint.description = data.get('description', '')
        checkpoint.milestone_date = milestone_date
        checkpoint.completed = False
        checkpoint.project_id = project_id
        
        # Add related tickets if provided
        related_ticket_ids = data.get('related_ticket_ids', [])
        for ticket_id in related_ticket_ids:
            # Retrieve ticket and ensure it belongs to the current project before association
            ticket = Ticket.query.get(ticket_id)
            if ticket and ticket.project_id == project_id:
                checkpoint.related_tickets.append(ticket)
        
        db.session.add(checkpoint)
        db.session.commit()
        
        logger.info(f"Created new checkpoint: {checkpoint.name} (ID: {checkpoint.id}) for project {project_id}")
        
        return jsonify({
            'id': checkpoint.id,
            'name': checkpoint.name,
            'description': checkpoint.description,
            'created_at': checkpoint.created_at,
            'milestone_date': checkpoint.milestone_date,
            'completed': checkpoint.completed
        })
    except Exception as e:
        db.session.rollback()
        logger.exception(f"Error creating checkpoint for project {project_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/tickets/<int:ticket_id>', methods=['GET'])
def get_ticket(ticket_id):
    """Get a specific ticket"""
    try:
        ticket = Ticket.query.get_or_404(ticket_id)
        
        agent_info = None
        if ticket.assigned_agent_id:
            agent = Agent.query.get(ticket.assigned_agent_id)
            if agent:
                agent_info = {
                    'id': agent.id,
                    'name': agent.name,
                    'role': agent.role.value
                }
        
        result = {
            'id': ticket.id,
            'title': ticket.title,
            'description': ticket.description,
            'status': ticket.status.value,
            'priority': ticket.priority.value,
            'created_at': ticket.created_at,
            'updated_at': ticket.updated_at,
            'due_date': ticket.due_date,
            'project_id': ticket.project_id,
            'assigned_to': agent_info
        }
        
        return jsonify({'ticket': result})
    except Exception as e:
        logger.exception(f"Error getting ticket {ticket_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/tickets/<int:ticket_id>/comments', methods=['GET'])
def get_ticket_comments(ticket_id):
    """Get all comments for a ticket"""
    try:
        ticket = Ticket.query.get_or_404(ticket_id)
        
        comments = Comment.query.filter_by(ticket_id=ticket_id).order_by(Comment.created_at).all()
        
        result = []
        for comment in comments:
            agent_info = None
            if comment.agent_id:
                agent = Agent.query.get(comment.agent_id)
                if agent:
                    agent_info = {
                        'id': agent.id,
                        'name': agent.name,
                        'role': agent.role.value
                    }
            
            result.append({
                'id': comment.id,
                'content': comment.content,
                'created_at': comment.created_at,
                'is_user': comment.is_user,
                'agent': agent_info
            })
            
        return jsonify({'comments': result})
    except Exception as e:
        logger.exception(f"Error getting comments for ticket {ticket_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/tickets/<int:ticket_id>/comments', methods=['POST'])
def add_ticket_comment(ticket_id):
    """Add a comment to a ticket"""
    try:
        ticket = Ticket.query.get_or_404(ticket_id)
        
        data = request.json
        
        if not data.get('content'):
            return jsonify({'error': 'Comment content is required'}), 400
        
        comment = Comment(
            content=data.get('content'),
            ticket_id=ticket_id,
            agent_id=data.get('agent_id'),
            is_user=data.get('is_user', True)
        )
        
        db.session.add(comment)
        db.session.commit()
        
        logger.info(f"Added comment to ticket {ticket_id}")
        
        return jsonify({
            'id': comment.id,
            'content': comment.content,
            'created_at': comment.created_at,
            'is_user': comment.is_user
        })
    except Exception as e:
        db.session.rollback()
        logger.exception(f"Error adding comment to ticket {ticket_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/tickets/<int:ticket_id>/assign', methods=['POST'])
def assign_ticket(ticket_id):
    """Assign a ticket to an agent"""
    try:
        ticket = Ticket.query.get_or_404(ticket_id)
        
        data = request.json
        
        if not data.get('agent_id'):
            return jsonify({'error': 'Agent ID is required'}), 400
        
        agent = Agent.query.get_or_404(data.get('agent_id'))
        
        ticket.assigned_agent_id = agent.id
        
        # If ticket is open, change status to in progress
        if ticket.status == TicketStatus.OPEN:
            ticket.status = TicketStatus.IN_PROGRESS
        
        db.session.commit()
        
        logger.info(f"Assigned ticket {ticket_id} to agent {agent.id} ({agent.name})")
        
        return jsonify({
            'success': True,
            'ticket_id': ticket.id,
            'agent_id': agent.id,
            'agent_name': agent.name,
            'status': ticket.status.value
        })
    except Exception as e:
        db.session.rollback()
        logger.exception(f"Error assigning ticket {ticket_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/tickets/<int:ticket_id>/status', methods=['POST'])
def update_ticket_status(ticket_id):
    """Update the status of a ticket"""
    try:
        ticket = Ticket.query.get_or_404(ticket_id)
        
        data = request.json
        
        if not data.get('status'):
            return jsonify({'error': 'Status is required'}), 400
        
        status = data.get('status').upper()
        
        if not hasattr(TicketStatus, status):
            return jsonify({'error': f'Invalid status: {status}'}), 400
        
        ticket.status = getattr(TicketStatus, status)
        db.session.commit()
        
        logger.info(f"Updated ticket {ticket_id} status to {status}")
        
        return jsonify({
            'success': True,
            'ticket_id': ticket.id,
            'status': ticket.status.value
        })
    except Exception as e:
        db.session.rollback()
        logger.exception(f"Error updating ticket {ticket_id} status: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/conversations', methods=['GET'])
def get_conversations():
    """Get all conversations"""
    try:
        conversations = Conversation.query.order_by(Conversation.updated_at.desc()).all()
        
        result = []
        for conversation in conversations:
            result.append({
                'id': conversation.id,
                'title': conversation.title,
                'created_at': conversation.created_at,
                'updated_at': conversation.updated_at,
                'project_id': conversation.project_id
            })
            
        return jsonify({'conversations': result})
    except Exception as e:
        logger.exception(f"Error getting conversations: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/conversations/recent', methods=['GET'])
def get_recent_conversation():
    """Get the most recent conversation"""
    try:
        conversation = Conversation.query.order_by(Conversation.updated_at.desc()).first()
        
        if not conversation:
            return jsonify({'message': 'No conversations found'})
        
        return jsonify({
            'id': conversation.id,
            'title': conversation.title,
            'created_at': conversation.created_at,
            'updated_at': conversation.updated_at,
            'project_id': conversation.project_id
        })
    except Exception as e:
        logger.exception(f"Error getting recent conversation: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/conversations', methods=['POST'])
def create_conversation():
    """Create a new conversation"""
    try:
        data = request.json or {}
        
        # Ensure there's a default project (1) if none is provided
        project_id = data.get('project_id')
        if not project_id:
            # Find the first project or create a default one
            default_project = Project.query.first()
            if not default_project:
                default_project = Project(name="Default Project", description="Automatically created default project")
                db.session.add(default_project)
                db.session.flush()
            project_id = default_project.id
            
        conversation = Conversation(
            title=data.get('title', f"Conversation {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"),
            project_id=project_id
        )
        
        db.session.add(conversation)
        db.session.commit()
        
        logger.info(f"Created new conversation: {conversation.id}")
        
        return jsonify({
            'id': conversation.id,
            'title': conversation.title,
            'created_at': conversation.created_at,
            'updated_at': conversation.updated_at,
            'project_id': conversation.project_id
        })
    except Exception as e:
        db.session.rollback()
        logger.exception(f"Error creating conversation: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/conversations/<int:conversation_id>/messages', methods=['GET'])
def get_conversation_messages(conversation_id):
    """Get all messages for a conversation"""
    try:
        conversation = Conversation.query.get_or_404(conversation_id)
        
        messages = Message.query.filter_by(conversation_id=conversation_id).order_by(Message.timestamp).all()
        
        result = []
        for message in messages:
            agent_info = None
            if message.agent_id:
                agent = Agent.query.get(message.agent_id)
                if agent:
                    agent_info = {
                        'id': agent.id,
                        'name': agent.name,
                        'role': agent.role.value
                    }
            
            result.append({
                'id': message.id,
                'content': message.content,
                'timestamp': message.timestamp,
                'is_user': message.is_user,
                'agent_name': agent_info['name'] if agent_info else None,
                'has_image': message.has_image,
                'image_path': message.image_path
            })
            
        return jsonify({'messages': result})
    except Exception as e:
        logger.exception(f"Error getting messages for conversation {conversation_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/conversations/<int:conversation_id>/messages', methods=['POST'])
def add_conversation_message(conversation_id):
    """Add a message to a conversation"""
    try:
        logger.info(f"Adding message to conversation {conversation_id}")
        conversation = Conversation.query.get_or_404(conversation_id)
        logger.info(f"Found conversation: {conversation.id}, title: {conversation.title}, project_id: {conversation.project_id}")
        
        # Check if this is a form submission with an image
        image_path = None
        if request.files and 'image' in request.files:
            image_file = request.files['image']
            if image_file.filename:
                filename = secure_filename(image_file.filename)
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                image_file.save(filepath)
                image_path = filepath
                logger.info(f"Saved image to {filepath}")
        
        # Get message content
        message_content = ''
        if request.form and 'message' in request.form:
            message_content = request.form['message']
            logger.info(f"Got message from form: {message_content[:50]}...")
        elif request.json and 'message' in request.json:
            message_content = request.json['message']
            logger.info(f"Got message from JSON: {message_content[:50]}...")
        
        if not message_content and not image_path:
            logger.warning("No message or image provided")
            return jsonify({'error': 'Message content or image is required'}), 400
        
        # Initialize or get agent coordinator
        project_id = conversation.project_id
        project = None
        
        if project_id:
            logger.info(f"Using existing project_id: {project_id}")
            agent_coordinator = AgentCoordinator(project_id)
        else:
            # Use first project or create one if none exists
            project = Project.query.first()
            if not project:
                logger.info("No project found, creating a new one")
                project = Project(name="General", description="General conversations")
                db.session.add(project)
                db.session.commit()
                logger.info(f"Created new project with ID {project.id}")
            else:
                logger.info(f"Using first project with ID {project.id}")
            
            agent_coordinator = AgentCoordinator(project.id)
            
            # Update conversation with project ID
            conversation.project_id = project.id
            db.session.commit()
            logger.info(f"Updated conversation {conversation_id} to have project_id {project.id}")
        
        # Process message with agent coordinator - this will handle creating both the user message and agent response
        response = agent_coordinator.process_user_message(message_content, conversation_id, image_path)
        logger.info(f"Got response from agent: {response[:50]}...")
        
        # Find the agent information
        coordinator_agent = agent_coordinator.coordinator_agent
        agent_id = coordinator_agent.agent_id if coordinator_agent else None
        agent_name = "Coordinator"
        
        if agent_id:
            agent = Agent.query.get(agent_id)
            if agent:
                agent_name = agent.name
                logger.info(f"Using agent name: {agent_name}")
        
        # Verify the messages were created (debugging)
        user_messages = Message.query.filter_by(conversation_id=conversation_id, is_user=True).order_by(Message.id.desc()).limit(1).all()
        agent_messages = Message.query.filter_by(conversation_id=conversation_id, is_user=False).order_by(Message.id.desc()).limit(1).all()
        
        if user_messages:
            logger.info(f"Found user message with ID {user_messages[0].id}, content: {user_messages[0].content[:30]}...")
        else:
            logger.warning("No user message found for this conversation")
            
        if agent_messages:
            logger.info(f"Found agent message with ID {agent_messages[0].id}, content: {agent_messages[0].content[:30]}...")
        else:
            logger.warning("No agent message found for this conversation")
        
        # Double-check that conversation has a project_id
        if conversation.project_id is None and project:
            conversation.project_id = project.id
            db.session.commit()
            logger.info(f"Updated conversation {conversation_id} to have project_id {project.id}")
        
        # Update conversation timestamp and title if needed
        conversation.updated_at = datetime.utcnow()
        if not conversation.title or conversation.title.startswith("Conversation"):
            # Use the first 30 chars of the message as the title
            new_title = message_content[:30]
            if len(message_content) > 30:
                new_title += "..."
            conversation.title = new_title
            logger.info(f"Updated conversation title to: {new_title}")
        
        db.session.commit()
        
        logger.info("Successfully processed message and created response")
        return jsonify({
            'success': True,
            'response': response,
            'agent_name': agent_name,
            'conversation_updated': True
        })
    except Exception as e:
        db.session.rollback()
        logger.exception(f"Error adding message to conversation {conversation_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/agents', methods=['GET'])
def get_agents():
    """Get all agents"""
    try:
        agents = Agent.query.all()
        
        result = []
        for agent in agents:
            result.append({
                'id': agent.id,
                'name': agent.name,
                'role': agent.role.value,
                'model': agent.model,
                'description': agent.description
            })
            
        return jsonify({'agents': result})
    except Exception as e:
        logger.exception(f"Error getting agents: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/agents', methods=['POST'])
def create_agent():
    """Create a new agent"""
    try:
        data = request.json
        
        if not data.get('name') or not data.get('role'):
            return jsonify({'error': 'Agent name and role are required'}), 400
        
        # Validate role
        role_str = data.get('role').upper()
        if not hasattr(AgentRole, role_str):
            return jsonify({'error': f'Invalid role: {role_str}'}), 400
        
        agent = Agent(
            name=data.get('name'),
            role=getattr(AgentRole, role_str),
            model=data.get('model', 'llama3:8b-vision'),
            description=data.get('description', '')
        )
        
        db.session.add(agent)
        db.session.commit()
        
        logger.info(f"Created new agent: {agent.name} ({agent.role.value})")
        
        return jsonify({
            'id': agent.id,
            'name': agent.name,
            'role': agent.role.value,
            'model': agent.model,
            'description': agent.description
        })
    except Exception as e:
        db.session.rollback()
        logger.exception(f"Error creating agent: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/checkpoints/<int:checkpoint_id>', methods=['GET'])
def get_checkpoint(checkpoint_id):
    """Get a specific checkpoint"""
    try:
        checkpoint = Checkpoint.query.get_or_404(checkpoint_id)
        
        related_tickets = []
        for ticket in checkpoint.related_tickets:
            related_tickets.append({
                'id': ticket.id,
                'title': ticket.title,
                'status': ticket.status.value,
                'priority': ticket.priority.value
            })
        
        result = {
            'id': checkpoint.id,
            'name': checkpoint.name,
            'description': checkpoint.description,
            'created_at': checkpoint.created_at,
            'milestone_date': checkpoint.milestone_date,
            'completed': checkpoint.completed,
            'related_tickets': related_tickets
        }
        
        return jsonify({'checkpoint': result})
    except Exception as e:
        logger.exception(f"Error getting checkpoint {checkpoint_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/checkpoints/<int:checkpoint_id>/status', methods=['POST'])
def update_checkpoint_status(checkpoint_id):
    """Update the status of a checkpoint"""
    try:
        checkpoint = Checkpoint.query.get_or_404(checkpoint_id)
        
        data = request.json
        
        if 'completed' not in data:
            return jsonify({'error': 'Completed status is required'}), 400
        
        checkpoint.completed = data.get('completed')
        db.session.commit()
        
        logger.info(f"Updated checkpoint {checkpoint_id} completed status to {checkpoint.completed}")
        
        return jsonify({
            'success': True,
            'checkpoint_id': checkpoint.id,
            'completed': checkpoint.completed
        })
    except Exception as e:
        db.session.rollback()
        logger.exception(f"Error updating checkpoint {checkpoint_id} status: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/ollama/status', methods=['GET'])
def check_ollama_status():
    """Check if Ollama is running"""
    try:
        response = requests.get('http://localhost:11434/api/tags', timeout=2)
        
        if response.status_code == 200:
            # Check if llama3:8b-vision is available
            models = response.json().get('models', [])
            has_vision_model = any(model.get('name') == 'llama3:8b-vision' for model in models)
            
            return jsonify({
                'running': True,
                'has_vision_model': has_vision_model
            })
        else:
            return jsonify({'running': False})
    except Exception as e:
        logger.exception(f"Error checking Ollama status: {str(e)}")
        return jsonify({'running': False, 'error': str(e)})
