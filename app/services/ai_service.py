"""AI Service for processing tickets using Anthropic Claude API"""

import anthropic
from app.config import get_settings
from typing import Dict, Any
import json
import logging
import re

logger = logging.getLogger(__name__)
settings = get_settings()


class AIService:
    """Service for AI-powered ticket analysis using Anthropic Claude"""
    
    def __init__(self):
        """Initialize Anthropic client"""
        api_key = settings.ANTHROPIC_API_KEY
        if not api_key or api_key == "your-api-key-here":
            logger.warning(
                "ANTHROPIC_API_KEY not set or invalid. "
                "AI functionality will be disabled. "
                "Please set it in your .env file to enable AI processing."
            )
            self.client = None
        else:
            self.client = anthropic.Anthropic(api_key=api_key)
            logger.info(f"AIService initialized with model: {self.model}")
        
        self.model = settings.AI_MODEL
        self.max_tokens = settings.AI_MAX_TOKENS
        self.temperature = settings.AI_TEMPERATURE
        self.timeout = settings.AI_TIMEOUT
    
    def analyze_ticket(self, title: str, description: str, customer_name: str = None) -> Dict[str, Any]:
        """
        Analyze a ticket and return categorization, sentiment, urgency, and draft response.
        
        Args:
            title: Ticket title
            description: Ticket description
            customer_name: Optional customer name
            
        Returns:
            Dictionary with keys: category, sentiment_score, urgency, draft_response
            
        Raises:
            Exception: If AI processing fails
        """
        if not self.client:
            raise ValueError(
                "AI service is not configured. "
                "Please set ANTHROPIC_API_KEY in your .env file."
            )
        
        try:
            # Build the prompt
            prompt = self._build_prompt(title, description, customer_name)
            
            logger.info(f"Sending request to Claude API for ticket: {title[:50]}...")
            
            # Call Claude API
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            # Extract response
            response_text = message.content[0].text
            logger.info(f"Received response from Claude API: {response_text[:100]}...")
            
            # Parse JSON response
            result = self._parse_response(response_text)
            
            # Validate result
            self._validate_result(result)
            
            logger.info(f"Successfully analyzed ticket: category={result['category']}, urgency={result['urgency']}")
            
            return result
            
        except anthropic.APIError as e:
            logger.error(f"Anthropic API error: {e}")
            raise Exception(f"AI API error: {str(e)}")
        except Exception as e:
            logger.error(f"Error analyzing ticket: {e}")
            raise
    
    def _build_prompt(self, title: str, description: str, customer_name: str = None) -> str:
        """Build the prompt for Claude API"""
        customer_greeting = f" by {customer_name}" if customer_name else ""
        
        return f"""You are an expert customer support AI assistant. Analyze the following customer complaint{customer_greeting} and provide a structured response.

**Customer Complaint:**
Title: {title}
Description: {description}

**Your Task:**
1. Categorize the complaint into ONE of: billing, technical, feature_request
2. Score the sentiment from 1 (very negative) to 10 (very positive)
3. Determine urgency: high, medium, or low
4. Draft a polite, context-aware response (2-3 paragraphs)

**CRITICAL: Respond ONLY with valid JSON in this exact format:**
{{
  "category": "billing|technical|feature_request",
  "sentiment_score": 1-10,
  "urgency": "high|medium|low",
  "draft_response": "Your professional response here..."
}}

**Guidelines for Draft Response:**
- Address the customer by their concern
- Show empathy and understanding
- Provide actionable next steps
- Keep it professional but warm
- 2-3 paragraphs maximum

**Urgency Guidelines:**
- HIGH: Critical issues, service outages, billing errors, account access problems
- MEDIUM: General technical issues, feature requests, moderate complaints
- LOW: Minor questions, feedback, suggestions

Respond with JSON only, no preamble, no markdown, no explanation."""
    
    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Claude API response and extract JSON"""
        try:
            # Remove markdown code blocks if present
            text = response_text.strip()
            
            # Remove ```json and ``` markers
            if text.startswith("```"):
                lines = text.split("\n")
                # Remove first line (```json or ```)
                lines = lines[1:]
                # Remove last line if it's ```
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                text = "\n".join(lines)
            
            # Try to find JSON object in the text
            # Look for {...}
            json_match = re.search(r'\{[\s\S]*\}', text)
            if json_match:
                text = json_match.group(0)
            
            # Parse JSON
            result = json.loads(text)
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {response_text}")
            raise Exception(f"Invalid JSON response from AI: {str(e)}")
    
    def _validate_result(self, result: Dict[str, Any]) -> None:
        """Validate the AI response structure and values"""
        required_fields = ["category", "sentiment_score", "urgency", "draft_response"]
        
        # Check required fields
        for field in required_fields:
            if field not in result:
                raise Exception(f"Missing required field in AI response: {field}")
        
        # Validate category
        valid_categories = ["billing", "technical", "feature_request"]
        if result["category"] not in valid_categories:
            raise Exception(f"Invalid category: {result['category']}. Must be one of: {valid_categories}")
        
        # Validate sentiment_score
        if not isinstance(result["sentiment_score"], int):
            try:
                result["sentiment_score"] = int(result["sentiment_score"])
            except:
                raise Exception(f"sentiment_score must be an integer")
        
        if not (1 <= result["sentiment_score"] <= 10):
            raise Exception(f"sentiment_score must be between 1 and 10, got: {result['sentiment_score']}")
        
        # Validate urgency
        valid_urgencies = ["high", "medium", "low"]
        if result["urgency"] not in valid_urgencies:
            raise Exception(f"Invalid urgency: {result['urgency']}. Must be one of: {valid_urgencies}")
        
        # Validate draft_response
        if not isinstance(result["draft_response"], str) or len(result["draft_response"].strip()) < 10:
            raise Exception("draft_response must be a non-empty string with at least 10 characters")


# Singleton instance
ai_service = AIService()
