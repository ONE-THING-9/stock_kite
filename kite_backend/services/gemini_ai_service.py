import google.generativeai as genai
from typing import Optional
from utils.logger import setup_logger
from utils.config import settings
from models.gemini_ai import GeminiRequest, GeminiResponse, GeminiError

class GeminiAIService:
    def __init__(self):
        self.logger = setup_logger(__name__)
        self.api_key = settings.gemini_api_key
        
        if not self.api_key:
            self.logger.error("GEMINI_API_KEY not found in environment variables")
            raise ValueError("GEMINI_API_KEY must be set in environment variables")
        
        # Configure the Gemini API
        genai.configure(api_key=self.api_key)
        self.logger.info("Gemini AI service initialized successfully")
    
    def generate_response(self, request: GeminiRequest) -> GeminiResponse:
        """
        Generate response from Gemini AI based on the request
        """
        try:
            self.logger.info(f"Generating response using model: {request.model_name}")
            
            # Initialize the model
            model = genai.GenerativeModel(request.model_name)
            
            # Configure generation parameters
            generation_config = genai.types.GenerationConfig(
                temperature=request.temperature,
                max_output_tokens=request.max_tokens,
                top_p=request.top_p,
                top_k=request.top_k
            )
            
            # Generate response
            response = model.generate_content(
                request.prompt,
                generation_config=generation_config
            )
            # Extract response data
            response_text = "No response generated"
            if response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                if candidate.content and candidate.content.parts:
                    # Get text from the first part
                    response_text = candidate.content.parts[0].text if candidate.content.parts[0].text else "No response generated"
            
            # Get token count if available
            token_count = None
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                token_count = response.usage_metadata.total_token_count
            
            # Get finish reason if available
            finish_reason = None
            if response.candidates and len(response.candidates) > 0:
                fr = response.candidates[0].finish_reason
                if fr is not None:
                    # Handle both enum and integer values
                    if hasattr(fr, 'name'):
                        finish_reason = fr.name
                    else:
                        # Map integer values to string names
                        finish_reason_map = {
                            1: "STOP",
                            2: "MAX_TOKENS", 
                            3: "SAFETY",
                            4: "RECITATION",
                            5: "OTHER"
                        }
                        finish_reason = finish_reason_map.get(fr, str(fr))
            
            # Get safety ratings if available
            safety_ratings = None
            if response.candidates and len(response.candidates) > 0 and response.candidates[0].safety_ratings:
                safety_ratings = [
                    {
                        "category": rating.category.name,
                        "probability": rating.probability.name
                    } 
                    for rating in response.candidates[0].safety_ratings
                ]
            
            self.logger.info(f"Successfully generated response with {len(response_text)} characters")
            
            return GeminiResponse(
                status="success",
                response_text=response_text,
                model_used=request.model_name,
                token_count=token_count,
                finish_reason=finish_reason,
                safety_ratings=safety_ratings
            )
            
        except Exception as e:
            error_message = str(e)
            self.logger.error(f"Error generating Gemini response: {error_message}")
            
            return GeminiResponse(
                status="error",
                response_text=f"Error: {error_message}",
                model_used=request.model_name
            )
    
    def list_available_models(self) -> list:
        """
        List available Gemini models
        """
        try:
            models = []
            for model in genai.list_models():
                if 'generateContent' in model.supported_generation_methods:
                    models.append({
                        "name": model.name,
                        "display_name": model.display_name,
                        "description": model.description
                    })
            return models
        except Exception as e:
            self.logger.error(f"Error listing models: {str(e)}")
            return []