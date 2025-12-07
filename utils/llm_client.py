"""
LLM Client for interacting with Azure OpenAI API
Handles all AI-powered functionality for the schedule agent system
"""
import warnings
warnings.filterwarnings('ignore', message='Core Pydantic V1 functionality')

import json
from typing import Dict, List, Optional
from openai import AzureOpenAI

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from config.config import (
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_DEPLOYMENT,
    AZURE_API_VERSION,
    TEMPERATURE,
    MAX_TOKENS,
)


class LLMClient:
    """
    Client for interacting with Azure OpenAI GPT-4.
    Handles structured prompts and responses for schedule management.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        deployment: Optional[str] = None
    ):
        """
        Initialize the LLM client.
        
        Args:
            api_key: Azure OpenAI API key (defaults to config)
            endpoint: Azure endpoint URL (defaults to config)
            deployment: Model deployment name (defaults to config)
        """
        self.api_key = api_key or AZURE_OPENAI_API_KEY
        self.endpoint = endpoint or AZURE_OPENAI_ENDPOINT
        self.deployment = deployment or AZURE_OPENAI_DEPLOYMENT
        
        if not self.api_key:
            raise ValueError(
                "Azure OpenAI API key not found. "
                "Check your config.py file."
            )
        
        # Initialize Azure OpenAI client
        self.client = AzureOpenAI(
            api_key=self.api_key,
            api_version=AZURE_API_VERSION,
            azure_endpoint=self.endpoint
        )
        
        self.max_tokens = MAX_TOKENS
        self.temperature = TEMPERATURE
        
        print(f"✓ LLM Client initialized")
        print(f"  Endpoint: {self.endpoint}")
        print(f"  Deployment: {self.deployment}")
    
    def generate_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate a text completion from GPT-4.
        
        Args:
            prompt: The user prompt/question
            system_prompt: System instructions for GPT-4 (optional)
            temperature: Randomness (0-1, default from config)
            max_tokens: Max response length (default from config)
        
        Returns:
            GPT-4's text response
        """
        try:
            # Use defaults if not specified
            temp = temperature if temperature is not None else self.temperature
            tokens = max_tokens if max_tokens is not None else self.max_tokens
            
            # Build messages
            messages = []
            
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            messages.append({"role": "user", "content": prompt})
            
            # Make API call
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=messages,
                temperature=temp,
                max_tokens=tokens
            )
            
            # Extract text from response
            return response.choices[0].message.content
        
        except Exception as e:
            print(f"✗ Error generating completion: {e}")
            raise
    
    def generate_json_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> Dict:
        """
        Generate a structured JSON response from GPT-4.
        
        This is useful for getting structured data like parsed schedules,
        event modifications, etc.
        
        Args:
            prompt: The user prompt
            system_prompt: System instructions (optional)
            temperature: Randomness (0-1)
        
        Returns:
            Parsed JSON as a Python dictionary
        """
        try:
            # Add JSON instruction to system prompt
            json_system = (
                "You are a helpful assistant that ALWAYS responds with valid JSON. "
                "Never include markdown formatting, explanations, or any text outside the JSON object. "
                "Respond ONLY with a valid JSON object."
            )
            
            if system_prompt:
                json_system = system_prompt + "\n\n" + json_system
            
            # Get completion
            response_text = self.generate_completion(
                prompt=prompt,
                system_prompt=json_system,
                temperature=temperature
            )
            
            # Clean response (remove markdown if present)
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]  # Remove ```json
            if response_text.startswith("```"):
                response_text = response_text[3:]  # Remove ```
            if response_text.endswith("```"):
                response_text = response_text[:-3]  # Remove ```
            response_text = response_text.strip()
            
            # Parse JSON
            return json.loads(response_text)
        
        except json.JSONDecodeError as e:
            print(f"✗ Error parsing JSON response: {e}")
            print(f"Raw response: {response_text}")
            raise
        except Exception as e:
            print(f"✗ Error generating JSON completion: {e}")
            raise
    
    def parse_schedule_text(self, schedule_text: str) -> List[Dict]:
        """
        Parse raw schedule text into structured event data.
        
        This is a key function that will be used by the Parser Agent.
        
        Args:
            schedule_text: Raw text extracted from PDF or image
        
        Returns:
            List of event dictionaries with structured data
        """
        prompt = f"""
Extract all calendar events from the following schedule text.

Return a JSON array of events. Each event should have:
- title: Event name/title
- date: Date in YYYY-MM-DD format
- start_time: Start time in HH:MM format (24-hour)
- end_time: End time in HH:MM format (24-hour)
- location: Location/room (if mentioned, otherwise empty string)
- description: Any additional details (optional)
- recurrence: "none", "daily", "weekly", or "monthly" (if mentioned)

If any information is unclear or missing, use your best judgment based on context.
If times are not specified, estimate reasonable times based on the event type.

Schedule text:
{schedule_text}

Return ONLY the JSON array, no other text.
"""
        
        system_prompt = """
You are an expert at parsing academic and personal schedules.
You understand various schedule formats and can extract structured information.
Always return valid JSON with all required fields.
"""
        
        try:
            result = self.generate_json_completion(prompt, system_prompt)
            
            # Ensure result is a list
            if isinstance(result, dict) and 'events' in result:
                return result['events']
            elif isinstance(result, list):
                return result
            else:
                print(f"⚠️  Unexpected response format: {result}")
                return []
        
        except Exception as e:
            print(f"✗ Error parsing schedule: {e}")
            return []
    
    def parse_modification_command(self, command: str, existing_events: List[Dict]) -> Dict:
        """
        Parse a natural language modification command.
        
        This will be used by the Change Manager Agent.
        
        Args:
            command: Natural language command (e.g., "move soccer to Tuesday")
            existing_events: List of current calendar events for context
        
        Returns:
            Dictionary with parsed modification details
        """
        # Format existing events for context
        events_context = "\n".join([
            f"- {e.get('summary', 'Untitled')}: {e.get('start', {}).get('dateTime', 'No date')}"
            for e in existing_events[:20]  # Limit to 20 most recent
        ])
        
        prompt = f"""
Parse this calendar modification command and return the action details.

Current events in calendar:
{events_context}

User command: "{command}"

Return a JSON object with:
{{
  "action": "move" | "delete" | "modify" | "create",
  "event_identifier": "text to identify which event (name or description)",
  "confidence": 0.0-1.0 (how confident you are about identifying the event),
  "modifications": {{
    "new_date": "YYYY-MM-DD" (if date changes),
    "new_start_time": "HH:MM" (if start time changes),
    "new_end_time": "HH:MM" (if end time changes),
    "new_title": "text" (if title changes),
    "new_location": "text" (if location changes)
  }},
  "reasoning": "brief explanation of your interpretation"
}}

If the command is ambiguous or unclear, set confidence < 0.7 and explain in reasoning.
"""
        
        system_prompt = """
You are an expert at understanding natural language commands for calendar management.
You can interpret informal language and context to determine user intent.
Always return valid JSON with all required fields.
"""
        
        try:
            return self.generate_json_completion(prompt, system_prompt)
        except Exception as e:
            print(f"✗ Error parsing modification command: {e}")
            return {
                "action": "unknown",
                "confidence": 0.0,
                "reasoning": f"Error: {str(e)}"
            }
    
    def assess_travel_feasibility(
        self,
        event1: Dict,
        event2: Dict,
        gap_minutes: int
    ) -> Dict:
        """
        Use AI to assess if travel time between events is feasible.
        
        Args:
            event1: First event (with location)
            event2: Second event (with location)
            gap_minutes: Time gap between events in minutes
        
        Returns:
            Assessment dictionary with feasibility and reasoning
        """
        loc1 = event1.get('location', 'Unknown location')
        loc2 = event2.get('location', 'Unknown location')
        
        prompt = f"""
Assess if this schedule is feasible:

Event 1: {event1.get('summary', 'Event')} at {loc1}
Event 2: {event2.get('summary', 'Event')} at {loc2}
Time gap: {gap_minutes} minutes

Return JSON:
{{
  "feasible": true/false,
  "confidence": 0.0-1.0,
  "estimated_travel_minutes": number,
  "reasoning": "explanation",
  "recommendation": "what to do if not feasible"
}}

Consider:
- Typical travel time between these locations
- Time needed to pack up and prepare
- Buffer for unexpected delays
"""
        
        try:
            return self.generate_json_completion(prompt)
        except Exception as e:
            print(f"✗ Error assessing travel feasibility: {e}")
            return {
                "feasible": True,
                "confidence": 0.0,
                "reasoning": f"Error: {str(e)}"
            }

    def extract_text_from_image(self, image_base64: str) -> str:
            """
            Extract text from an image using GPT-4 Vision.
        
            This is used as an alternative to Tesseract OCR.
            No local installation required!
        
            Args:
                image_base64: Base64-encoded image string
        
            Returns:
                Extracted text from the image
            """
            try:
             # Create vision message
                messages = [
                    {
                        "role": "user",
                        "content": [
                            {
                             "type": "text",
                                "text": """Extract all text from this image. This is likely a schedule or calendar.
                            
    Return the text exactly as it appears, preserving:
    - All dates and times
    - All event names
    - All locations
    - All other visible text

    Format the output in a clear, readable way. If it's a schedule, maintain the chronological order."""
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                "url": f"data:image/png;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ]
            
                # Make API call
                response = self.client.chat.completions.create(
                  model=self.deployment,
                  messages=messages,
                  max_tokens=self.max_tokens,
                  temperature=0.0  # Deterministic for OCR
                )
            
                # Extract text from response
                return response.choices[0].message.content
        
            except Exception as e:
                print(f"✗ Error extracting text from image: {e}")
                raise

def main():
    """
    Test function to verify LLM integration is working.
    """
    print("=" * 60)
    print("Testing Azure OpenAI Integration")
    print("=" * 60)
    
    try:
        # Initialize client
        print("\n[Test 1] Initializing LLM client...")
        client = LLMClient()
        
        # Test 2: Simple completion
        print("\n[Test 2] Testing simple completion...")
        response = client.generate_completion(
            prompt="Say 'Hello! I am GPT-4 and I'm ready to help with schedule management.' in one sentence."
        )
        print(f"Response: {response}")
        
        # Test 3: JSON completion
        print("\n[Test 3] Testing JSON completion...")
        json_response = client.generate_json_completion(
            prompt='Return a JSON object with three fields: name="Schedule Agent", status="active", version=1'
        )
        print(f"JSON Response: {json.dumps(json_response, indent=2)}")
        
        # Test 4: Parse sample schedule
        print("\n[Test 4] Testing schedule parsing...")
        sample_schedule = """
Monday, November 25, 2025
- 9:00 AM - 10:30 AM: Introduction to AI (Room 101)
- 11:00 AM - 12:30 PM: Mathematics Lecture (Room 205)
- 2:00 PM - 4:00 PM: Lab Session (Computer Lab A)

Tuesday, November 26, 2025
- 10:00 AM - 11:30 AM: Machine Learning (Room 101)
- 1:00 PM - 3:00 PM: Soccer Practice (Sports Field)
"""
        
        events = client.parse_schedule_text(sample_schedule)
        print(f"Parsed {len(events)} events:")
        for event in events:
            print(f"  - {event.get('title')} on {event.get('date')} at {event.get('start_time')}")
        
        # Test 5: Parse modification command
        print("\n[Test 5] Testing modification command parsing...")
        mock_events = [
            {"summary": "Soccer Practice", "start": {"dateTime": "2025-11-26T13:00:00"}},
            {"summary": "Machine Learning", "start": {"dateTime": "2025-11-26T10:00:00"}}
        ]
        
        modification = client.parse_modification_command(
            "move soccer practice to Wednesday at 3pm",
            mock_events
        )
        print(f"Parsed modification:")
        print(f"  Action: {modification.get('action')}")
        print(f"  Event: {modification.get('event_identifier')}")
        print(f"  Confidence: {modification.get('confidence')}")
        print(f"  Reasoning: {modification.get('reasoning')}")
        
        print("\n" + "=" * 60)
        print("✓ All LLM tests completed successfully!")
        print("Your Azure OpenAI integration is working correctly.")
        print("=" * 60)
    
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        print("\nPlease check:")
        print("1. Your Azure endpoint and API key are correct")
        print("2. The deployment name is correct")
        print("3. Your internet connection is working")


if __name__ == "__main__":
    main()
