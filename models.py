from datetime import datetime
from enum import Enum
from app import db
from werkzeug.security import generate_password_hash, check_password_hash


class AgentRole(Enum):
    COORDINATOR = "coordinator"
    PLANNER = "planner"
    RESEARCHER = "researcher"
    DEVELOPER = "developer"
    TESTER = "tester"
    REVIEWER = "reviewer"


class TicketStatus(Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class TicketPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SubscriptionTier(Enum):
    BASIC = "basic"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class Project(db.Model):
    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime,
                           default=datetime.utcnow,
                           nullable=False)
    updated_at = db.Column(db.DateTime,
                           default=datetime.utcnow,
                           onupdate=datetime.utcnow,
                           nullable=False)

    # Relationships
    tickets = db.relationship('Ticket',
                              backref='project',
                              lazy='dynamic',
                              cascade='all, delete-orphan')
    checkpoints = db.relationship('Checkpoint',
                                  backref='project',
                                  lazy='dynamic',
                                  cascade='all, delete-orphan')

    def __init__(self, name, description=None):
        self.name = name
        self.description = description

    def __repr__(self):
        return f"<Project {self.name}>"


class Agent(db.Model):
    __tablename__ = 'agents'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.Enum(AgentRole), nullable=False)
    model = db.Column(db.String(100), default="llama3:8b-vision")
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    assigned_tickets = db.relationship('Ticket',
                                       backref='assigned_agent',
                                       lazy='dynamic')
    messages = db.relationship('Message',
                               backref='agent',
                               lazy='dynamic',
                               foreign_keys='Message.agent_id')

    def __repr__(self):
        return f"<Agent {self.name} ({self.role.value})>"


class Ticket(db.Model):
    __tablename__ = 'tickets'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.Enum(TicketStatus),
                       default=TicketStatus.OPEN,
                       nullable=False)
    priority = db.Column(db.Enum(TicketPriority),
                         default=TicketPriority.MEDIUM,
                         nullable=False)
    created_at = db.Column(db.DateTime,
                           default=datetime.utcnow,
                           nullable=False)
    updated_at = db.Column(db.DateTime,
                           default=datetime.utcnow,
                           onupdate=datetime.utcnow,
                           nullable=False)
    due_date = db.Column(db.DateTime, nullable=True)

    # Foreign keys
    project_id = db.Column(db.Integer,
                           db.ForeignKey('projects.id'),
                           nullable=False)
    assigned_agent_id = db.Column(db.Integer,
                                  db.ForeignKey('agents.id'),
                                  nullable=True)
    parent_ticket_id = db.Column(db.Integer,
                                 db.ForeignKey('tickets.id'),
                                 nullable=True)

    # Relationships
    subtasks = db.relationship('Ticket',
                               backref=db.backref('parent', remote_side=[id]),
                               lazy='dynamic')
    comments = db.relationship('Comment',
                               backref='ticket',
                               lazy='dynamic',
                               cascade='all, delete-orphan')

    def __init__(self,
                 title,
                 project_id,
                 description=None,
                 status=None,
                 priority=None,
                 due_date=None,
                 assigned_agent_id=None,
                 parent_ticket_id=None):
        self.title = title
        self.description = description
        self.status = status or TicketStatus.OPEN
        self.priority = priority or TicketPriority.MEDIUM
        self.due_date = due_date
        self.project_id = project_id
        self.assigned_agent_id = assigned_agent_id
        self.parent_ticket_id = parent_ticket_id

    def __repr__(self):
        return f"<Ticket {self.id}: {self.title} ({self.status.value})>"


class Checkpoint(db.Model):
    __tablename__ = 'checkpoints'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    milestone_date = db.Column(db.DateTime, nullable=True)
    completed = db.Column(db.Boolean, default=False)

    # Foreign keys
    project_id = db.Column(db.Integer,
                           db.ForeignKey('projects.id'),
                           nullable=False)

    # Relationships
    related_tickets = db.relationship('Ticket',
                                      secondary='checkpoint_ticket',
                                      backref='checkpoints')

    def __repr__(self):
        return f"<Checkpoint {self.name}>"


# Association table for checkpoints and tickets
checkpoint_ticket = db.Table(
    'checkpoint_ticket',
    db.Column('checkpoint_id',
              db.Integer,
              db.ForeignKey('checkpoints.id'),
              primary_key=True),
    db.Column('ticket_id',
              db.Integer,
              db.ForeignKey('tickets.id'),
              primary_key=True))


class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_user = db.Column(db.Boolean, default=False)
    has_image = db.Column(db.Boolean, default=False)
    image_path = db.Column(db.String(255), nullable=True)

    # Foreign keys
    agent_id = db.Column(db.Integer, db.ForeignKey('agents.id'), nullable=True)
    conversation_id = db.Column(db.Integer,
                                db.ForeignKey('conversations.id'),
                                nullable=False)

    def __repr__(self):
        return f"<Message {self.id} from {'User' if self.is_user else 'Agent'}>"


class Conversation(db.Model):
    __tablename__ = 'conversations'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime,
                           default=datetime.utcnow,
                           onupdate=datetime.utcnow)

    # Foreign keys
    project_id = db.Column(db.Integer,
                           db.ForeignKey('projects.id'),
                           nullable=True)

    # Relationships
    messages = db.relationship('Message',
                               backref='conversation',
                               lazy='dynamic',
                               cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Conversation {self.id}: {self.title}>"


class Comment(db.Model):
    __tablename__ = 'comments'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_user = db.Column(db.Boolean, default=False)

    # Foreign keys
    ticket_id = db.Column(db.Integer,
                          db.ForeignKey('tickets.id'),
                          nullable=False)
    agent_id = db.Column(db.Integer, db.ForeignKey('agents.id'), nullable=True)

    def __repr__(self):
        return f"<Comment {self.id} on Ticket {self.ticket_id}>"


class Customer(db.Model):
    __tablename__ = 'customers'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    company_name = db.Column(db.String(100), nullable=True)
    stripe_customer_id = db.Column(db.String(100), unique=True, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    subscriptions = db.relationship('Subscription',
                                    backref='customer',
                                    lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<Customer {self.username}>"


class Subscription(db.Model):
    __tablename__ = 'subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    stripe_subscription_id = db.Column(db.String(100),
                                       unique=True,
                                       nullable=True)
    tier = db.Column(db.Enum(SubscriptionTier), default=SubscriptionTier.BASIC)
    active = db.Column(db.Boolean, default=True)
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime, nullable=True)
    auto_renew = db.Column(db.Boolean, default=True)

    # Foreign keys
    customer_id = db.Column(db.Integer,
                            db.ForeignKey('customers.id'),
                            nullable=False)

    def __repr__(self):
        return f"<Subscription {self.id} - {self.tier.value}>"

    @property
    def is_active(self):
        if not self.active:
            return False
        if self.end_date and self.end_date < datetime.utcnow():
            return False
        return True
