import os
import logging
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort

from app import db
from models import Project, Agent, Ticket, Checkpoint, Conversation, Message, Customer, Subscription, TicketStatus
from agent_system.coordinator import AgentCoordinator
from routes.auth_routes import login_required

# Set up logging
logger = logging.getLogger(__name__)

# Create Blueprint
main_bp = Blueprint('main_bp', __name__)

@main_bp.route('/')
def index():
    """Home page route"""
    return render_template('index.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard route"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return redirect(url_for('auth_bp.login'))
        
        # Get user data
        customer = Customer.query.get_or_404(user_id)
        
        # Get user's projects
        projects = Project.query.order_by(Project.updated_at.desc()).all()
        project_count = len(projects)
        
        # Get subscription data
        subscription = Subscription.query.filter_by(customer_id=user_id, active=True).first()
        
        # Get ticket counts
        open_ticket_count = Ticket.query.filter_by(status=TicketStatus.OPEN).count()
        in_progress_ticket_count = Ticket.query.filter_by(status=TicketStatus.IN_PROGRESS).count()
        completed_ticket_count = Ticket.query.filter_by(status=TicketStatus.COMPLETED).count()
        total_tickets = open_ticket_count + in_progress_ticket_count + completed_ticket_count
        
        # Calculate completion percentage
        completed_percentage = 0
        if total_tickets > 0:
            completed_percentage = int((completed_ticket_count / total_tickets) * 100)
        
        # Get recent activities
        recent_activities = [
            # Placeholder for recent activities
        ]
        
        # For demo purposes, create some example activities
        if not recent_activities:
            # Get messages, projects and tickets and format them as activities
            messages = Message.query.filter_by(is_user=False).order_by(Message.timestamp.desc()).limit(3).all()
            recent_projects = Project.query.order_by(Project.created_at.desc()).limit(2).all()
            recent_tickets = Ticket.query.order_by(Ticket.updated_at.desc()).limit(2).all()
            
            for msg in messages:
                conversation = Conversation.query.get(msg.conversation_id)
                recent_activities.append({
                    'type': 'conversation',
                    'title': f"New message in '{conversation.title if conversation.title else 'Untitled'}'",
                    'description': msg.content[:100] + '...' if len(msg.content) > 100 else msg.content,
                    'time': msg.timestamp.strftime('%Y-%m-%d %H:%M')
                })
            
            for proj in recent_projects:
                recent_activities.append({
                    'type': 'project',
                    'title': f"Project created: {proj.name}",
                    'description': proj.description[:100] + '...' if proj.description and len(proj.description) > 100 else (proj.description or 'No description'),
                    'time': proj.created_at.strftime('%Y-%m-%d %H:%M')
                })
            
            for ticket in recent_tickets:
                recent_activities.append({
                    'type': 'ticket',
                    'title': f"Ticket updated: {ticket.title}",
                    'description': f"Status: {ticket.status.value}, Priority: {ticket.priority.value}",
                    'time': ticket.updated_at.strftime('%Y-%m-%d %H:%M')
                })
            
            # Sort by time
            recent_activities.sort(key=lambda x: datetime.strptime(x['time'], '%Y-%m-%d %H:%M'), reverse=True)
        
        return render_template(
            'dashboard.html',
            customer=customer,
            subscription=subscription,
            project_count=project_count,
            open_ticket_count=open_ticket_count,
            in_progress_ticket_count=in_progress_ticket_count,
            completed_ticket_count=completed_ticket_count,
            completed_percentage=completed_percentage,
            recent_activities=recent_activities
        )
    except Exception as e:
        logger.exception(f"Error in dashboard route: {str(e)}")
        flash(f"An error occurred: {str(e)}", "danger")
        return redirect(url_for('main_bp.index'))

@main_bp.route('/chat', defaults={'project_id': None})
@main_bp.route('/chat/<int:project_id>')
def chat(project_id):
    """Chat interface route"""
    try:
        # Get current conversation if exists in session
        current_conversation_id = session.get('current_conversation_id')
        
        # Get all conversations
        if project_id:
            conversations = Conversation.query.filter_by(project_id=project_id).order_by(Conversation.updated_at.desc()).all()
        else:
            conversations = Conversation.query.order_by(Conversation.updated_at.desc()).all()
        
        # If no current conversation but conversations exist, use the most recent one
        if not current_conversation_id and conversations:
            current_conversation_id = conversations[0].id
            session['current_conversation_id'] = current_conversation_id
            
        # Get messages for current conversation
        messages = []
        if current_conversation_id:
            messages = Message.query.filter_by(conversation_id=current_conversation_id).order_by(Message.timestamp).all()
        
        return render_template(
            'chat.html', 
            conversations=conversations, 
            messages=messages, 
            current_conversation_id=current_conversation_id,
            project_id=project_id
        )
    except Exception as e:
        logger.exception(f"Error in chat route: {str(e)}")
        flash(f"An error occurred while loading the chat: {str(e)}", "danger")
        return render_template('chat.html', conversations=[], messages=[], current_conversation_id=None)

@main_bp.route('/projects')
def projects():
    """Projects list route"""
    try:
        projects = Project.query.order_by(Project.updated_at.desc()).all()
        return render_template('projects.html', projects=projects)
    except Exception as e:
        logger.exception(f"Error in projects route: {str(e)}")
        flash(f"An error occurred while loading projects: {str(e)}", "danger")
        return render_template('projects.html', projects=[])

@main_bp.route('/project/<int:project_id>')
def project(project_id):
    """Single project view route"""
    try:
        project = Project.query.get_or_404(project_id)
        
        # Get all tickets for this project
        tickets = Ticket.query.filter_by(project_id=project_id).all()
        
        # Get all checkpoints for this project
        checkpoints = Checkpoint.query.filter_by(project_id=project_id).all()
        
        # Get all agents
        agents = Agent.query.all()
        
        return render_template(
            'project.html', 
            project=project, 
            tickets=tickets, 
            checkpoints=checkpoints, 
            agents=agents
        )
    except Exception as e:
        logger.exception(f"Error in project route: {str(e)}")
        flash(f"An error occurred while loading the project: {str(e)}", "danger")
        return redirect(url_for('main_bp.projects'))

@main_bp.route('/project/<int:project_id>/chat')
def project_chat(project_id):
    """Project-specific chat route"""
    try:
        # Check if project exists
        project = Project.query.get_or_404(project_id)
        
        # Create a new conversation for this project if none exists
        conversation = Conversation.query.filter_by(project_id=project_id).order_by(Conversation.updated_at.desc()).first()
        
        if not conversation:
            conversation = Conversation(
                title=f"Project: {project.name}",
                project_id=project_id
            )
            db.session.add(conversation)
            db.session.commit()
        
        # Store current conversation ID in session
        session['current_conversation_id'] = conversation.id
        
        # Redirect to the chat view with project ID
        return redirect(url_for('main_bp.chat', project_id=project_id))
    except Exception as e:
        logger.exception(f"Error in project_chat route: {str(e)}")
        flash(f"An error occurred while setting up the project chat: {str(e)}", "danger")
        return redirect(url_for('main_bp.projects'))

@main_bp.route('/agents')
def agents():
    """Agents management route"""
    try:
        agents = Agent.query.all()
        return render_template('agents.html', agents=agents)
    except Exception as e:
        logger.exception(f"Error in agents route: {str(e)}")
        flash(f"An error occurred while loading agents: {str(e)}", "danger")
        return redirect(url_for('main_bp.index'))

@main_bp.app_template_filter('format_date')
def format_date(value, format='%Y-%m-%d %H:%M'):
    """Format a datetime object into a string"""
    if value is None:
        return ""
    return value.strftime(format)
