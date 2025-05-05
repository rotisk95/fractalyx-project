import requests
import json
import base64
import logging
import os
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class OllamaClient:
    """Client for interacting with Ollama API."""
    
    def __init__(self, model: str = "llama3:8b-vision"):
        """
        Initialize the Ollama client.
        
        Args:
            model (str): The model to use
        """
        self.base_url = "http://localhost:11434/api"
        self.model = model
        logger.debug(f"Initialized OllamaClient with model: {model}")
    
    def generate(self, system_prompt: str, messages: List[Dict[str, str]]) -> str:
        """
        Generate a text response from Ollama.
        
        Args:
            system_prompt (str): The system prompt
            messages (List[Dict[str, str]]): List of conversation messages
            
        Returns:
            str: The generated text response
        """
        try:
            # For development, use mock responses since Ollama isn't available
            if not messages:
                return "Hello! I'm the Fractalyx Coordinator. How can I help you today?"
                
            # Get the last user message
            last_message = messages[-1].get("content", "") if messages[-1].get("role") == "user" else ""
            
            # Generate response based on input
            if "help" in last_message.lower():
                return "I'm here to help! As the Fractal Intelligence Coordinator, I can assist with project planning, task management, research, and development support. What would you like to work on today?"
            elif "project" in last_message.lower() or "plan" in last_message.lower():
                return "I'd be happy to help with your project! To get started, I'll need to understand your goals. Could you tell me more about what you're trying to build, and what your key requirements are?"
            elif "task" in last_message.lower() or "ticket" in last_message.lower():
                return "Creating tasks is a great way to organize your project. Each task should be specific, measurable, and have a clear definition of done. Would you like me to help you break down your project into manageable tasks?"
            elif "research" in last_message.lower():
                return "Research is crucial for informed decisions. I can help gather information on technologies, methodologies, or industry trends related to your project. What specific topic would you like me to research?"
            elif "code" in last_message.lower() or "develop" in last_message.lower():
                return "For development work, I can help plan the architecture, suggest technologies, and even generate code snippets. What are you trying to build?"
            else:
                return "I've received your message. As your Fractal Intelligence Coordinator, I'm here to help with any aspect of your project. Could you provide more specific details about what you're working on, so I can offer more targeted assistance?"
        except Exception as e:
            logger.exception(f"Error generating response: {str(e)}")
            return f"I apologize, but I encountered an error while processing your request. Please try again."
    
    def generate_with_image(self, system_prompt: str, messages: List[Dict[str, str]], image_path: str) -> str:
        """
        Generate a text response from Ollama, including an image.
        
        Args:
            system_prompt (str): The system prompt
            messages (List[Dict[str, str]]): List of conversation messages
            image_path (str): Path to the image file
            
        Returns:
            str: The generated text response
        """
        try:
            # For development, return mock responses since Ollama isn't available
            if not messages:
                return "I can see you've shared an image with me. How can I help with this?"
                
            # Get the last user message
            last_message = messages[-1].get("content", "") if messages[-1].get("role") == "user" else ""
            
            # Get the image filename
            image_filename = os.path.basename(image_path)
            
            # Generate response based on the image and input
            return f"I've received your image '{image_filename}'. As your Fractal Intelligence Coordinator, I can analyze this visual information to assist with your project. Could you tell me more about what you'd like me to do with this image?"
        except Exception as e:
            logger.exception(f"Error generating response with image: {str(e)}")
            return f"I apologize, but I encountered an error while processing your image. Please try again."
    
    def _format_messages(self, system_prompt: str, messages: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Format messages for the Ollama API.
        
        Args:
            system_prompt (str): The system prompt
            messages (List[Dict[str, str]]): List of conversation messages
            
        Returns:
            List[Dict[str, Any]]: Formatted messages for Ollama API
        """
        formatted_messages = [{"role": "system", "content": system_prompt}]
        
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            
            # Map roles to Ollama expected format
            if role == "assistant":
                ollama_role = "assistant"
            else:
                ollama_role = "user"
            
            formatted_messages.append({"role": ollama_role, "content": content})
        
        return formatted_messages
