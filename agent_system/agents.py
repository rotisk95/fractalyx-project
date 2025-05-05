import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple

from agent_system.ollama_client import OllamaClient
from models import AgentRole

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Base class for all agents in the system."""
    
    def __init__(self, agent_id: int, name: str, role: AgentRole, model: str = "llama3:8b-vision"):
        """
        Initialize a base agent.
        
        Args:
            agent_id (int): The database ID of the agent
            name (str): The name of the agent
            role (AgentRole): The role of the agent
            model (str): The Ollama model to use
        """
        self.agent_id = agent_id
        self.name = name
        self.role = role
        self.model = model
        self.ollama_client = OllamaClient(model)
        self.system_prompt = self._get_system_prompt()
        self.context = []
        logger.debug(f"Initialized {self.role.value} agent: {self.name}")
        
    def _get_system_prompt(self) -> str:
        """Get the system prompt for this agent type."""
        base_prompt = (
            f"You are {self.name}, a {self.role.value} agent in a multi-agent system. "
            f"You are working with other agents to complete projects through a ticket system. "
        )
        role_specific_prompt = self._get_role_specific_prompt()
        return base_prompt + role_specific_prompt
    
    @abstractmethod
    def _get_role_specific_prompt(self) -> str:
        """Get the role-specific part of the system prompt."""
        pass
        
    def process_message(self, message: str, image_path: Optional[str] = None) -> str:
        """
        Process a message, optionally with an image.
        
        Args:
            message (str): The message to process
            image_path (Optional[str]): Path to an image file, if any
            
        Returns:
            str: The agent's response
        """
        # Add to context
        self.context.append({"role": "user", "content": message})
        
        # Process with Ollama
        if image_path:
            response = self.ollama_client.generate_with_image(
                system_prompt=self.system_prompt,
                messages=self.context,
                image_path=image_path
            )
        else:
            response = self.ollama_client.generate(
                system_prompt=self.system_prompt,
                messages=self.context
            )
        
        # Add response to context
        self.context.append({"role": "assistant", "content": response})
        
        return response
    
    def reset_context(self):
        """Reset the conversation context."""
        self.context = []
        logger.debug(f"Reset context for {self.name}")


class CoordinatorAgent(BaseAgent):
    """Coordinates the work of other agents and manages the overall project flow."""
    
    def _get_role_specific_prompt(self) -> str:
        return (
            "Your role is to coordinate the work of all other agents. You assign tasks, monitor progress, "
            "and ensure that the project is moving forward. You should:\n"
            "1. Break down user requirements into manageable tasks\n"
            "2. Assign tickets to appropriate agents based on their roles\n"
            "3. Monitor the status of all tickets and update checkpoints\n"
            "4. Identify blockers and help resolve them\n"
            "5. Provide progress updates to the user\n"
            "When communicating with the user, be clear about the project status, next steps, and any issues."
        )


class PlannerAgent(BaseAgent):
    """Plans the project structure and creates detailed specifications."""
    
    def _get_role_specific_prompt(self) -> str:
        return (
            "Your role is to create detailed plans and specifications for the project. You should:\n"
            "1. Analyze user requirements and create a project roadmap\n"
            "2. Break down large tasks into smaller, manageable tickets\n"
            "3. Define checkpoints and milestones for the project\n"
            "4. Estimate effort and complexity for tasks\n"
            "5. Identify dependencies between tasks\n"
            "Your plans should be detailed, clear, and actionable. Focus on creating a structured approach to completing the project."
        )


class ResearcherAgent(BaseAgent):
    """Researches information needed for the project."""
    
    def _get_role_specific_prompt(self) -> str:
        return (
            "Your role is to research information needed for the project. You should:\n"
            "1. Gather information about technologies, tools, and best practices relevant to the project\n"
            "2. Analyze technical feasibility of approaches\n"
            "3. Research solutions to technical challenges\n"
            "4. Provide detailed research reports with recommendations\n"
            "5. Support other agents with specific information they need\n"
            "Your research should be thorough, accurate, and directly applicable to the project at hand."
        )


class DeveloperAgent(BaseAgent):
    """Develops code and technical solutions."""
    
    def _get_role_specific_prompt(self) -> str:
        return (
            "Your role is to develop code and technical solutions for the project. You should:\n"
            "1. Write clean, maintainable code that meets requirements\n"
            "2. Implement features according to specifications\n"
            "3. Refactor code as needed to improve quality\n"
            "4. Solve technical problems encountered during development\n"
            "5. Document your code and implementation decisions\n"
            "Your code should follow best practices and be well-structured. Consider security, performance, and maintainability."
        )


class TesterAgent(BaseAgent):
    """Tests code and solutions for quality and correctness."""
    
    def _get_role_specific_prompt(self) -> str:
        return (
            "Your role is to test code and solutions for quality and correctness. You should:\n"
            "1. Create test plans for features and components\n"
            "2. Identify edge cases and potential issues\n"
            "3. Report bugs and issues in a clear, reproducible manner\n"
            "4. Verify that implementations meet requirements\n"
            "5. Suggest improvements to quality and reliability\n"
            "Your testing should be thorough and help improve the overall quality of the project."
        )


class ReviewerAgent(BaseAgent):
    """Reviews work from other agents and provides feedback."""
    
    def _get_role_specific_prompt(self) -> str:
        return (
            "Your role is to review work from other agents and provide constructive feedback. You should:\n"
            "1. Review code, documents, and other outputs from agents\n"
            "2. Identify issues, errors, and areas for improvement\n"
            "3. Provide specific, actionable feedback\n"
            "4. Ensure that work meets project requirements and quality standards\n"
            "5. Approve work that meets standards or request changes\n"
            "Your reviews should be thorough but constructive. Focus on helping improve the quality of the project."
        )
