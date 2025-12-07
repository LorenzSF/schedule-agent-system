"""
Parser Agent
Extracts schedule information from PDFs, images, or raw text and structures it.
"""

from pathlib import Path
from typing import List, Dict, Union, Optional
from datetime import datetime

import sys
sys.path.append(str(Path(__file__).parent.parent))

from utils.llm_client import LLMClient
from utils.pdf_extractor import PDFExtractor


class ParserAgent:
    """
    Agent responsible for parsing schedules from various sources.
    
    Capabilities:
    - Extract text from PDFs
    - Extract text from images (via OCR)
    - Parse raw text schedules
    - Use AI to structure unstructured schedule data
    - Validate and clean parsed events
    """
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        """
        Initialize the Parser Agent.
        
        Args:
            llm_client: LLM client instance (creates new one if not provided)
        """
        self.llm_client = llm_client or LLMClient()
        self.pdf_extractor = PDFExtractor(llm_client=self.llm_client)  # Pass LLM client
        
        print("✓ Parser Agent initialized")
    
    def parse_from_file(self, file_path: Union[str, Path]) -> List[Dict]:
        """
        Parse schedule from a file (PDF or image).
        
        Args:
            file_path: Path to schedule file
        
        Returns:
            List of structured event dictionaries
        """
        file_path = Path(file_path)
        
        print(f"\n{'='*60}")
        print(f"Parser Agent: Processing {file_path.name}")
        print(f"{'='*60}")
        
        # Step 1: Extract text from file
        try:
            raw_text = self.pdf_extractor.extract_from_file(file_path)
        except Exception as e:
            print(f"✗ Failed to extract text: {e}")
            return []
        
        # Step 2: Parse the extracted text
        return self.parse_from_text(raw_text)
    
    def parse_from_text(self, schedule_text: str) -> List[Dict]:
        """
        Parse schedule from raw text.
        
        Args:
            schedule_text: Raw schedule text
        
        Returns:
            List of structured event dictionaries
        """
        if not schedule_text or not schedule_text.strip():
            print("✗ No text to parse")
            return []
        
        print(f"\n📝 Parsing schedule text ({len(schedule_text)} characters)...")
        print(f"Preview: {schedule_text[:200]}...")
        
        # Step 1: Use LLM to extract structured events
        try:
            events = self.llm_client.parse_schedule_text(schedule_text)
        except Exception as e:
            print(f"✗ Failed to parse with LLM: {e}")
            return []
        
        if not events:
            print("⚠️  No events extracted from text")
            return []
        
        print(f"✓ Extracted {len(events)} event(s)")
        
        # Step 2: Validate and clean events
        validated_events = []
        for i, event in enumerate(events, 1):
            print(f"\n  Event {i}: {event.get('title', 'Untitled')}")
            
            # Validate required fields
            if self._validate_event(event):
                validated_events.append(event)
                print(f"    ✓ Valid")
                print(f"    Date: {event.get('date')}")
                print(f"    Time: {event.get('start_time')} - {event.get('end_time')}")
                if event.get('location'):
                    print(f"    Location: {event.get('location')}")
            else:
                print(f"    ✗ Invalid - skipping")
        
        print(f"\n✓ Parser Agent: {len(validated_events)} valid events")
        return validated_events
    
    def _validate_event(self, event: Dict) -> bool:
        """
        Validate that an event has all required fields.
        
        Args:
            event: Event dictionary to validate
        
        Returns:
            True if valid, False otherwise
        """
        required_fields = ['title', 'date', 'start_time', 'end_time']
        
        # Check required fields exist
        for field in required_fields:
            if field not in event or not event[field]:
                print(f"      Missing or empty: {field}")
                return False
        
        # Validate date format (YYYY-MM-DD)
        try:
            datetime.strptime(event['date'], '%Y-%m-%d')
        except ValueError:
            print(f"      Invalid date format: {event['date']}")
            return False
        
        # Validate time formats (HH:MM)
        for time_field in ['start_time', 'end_time']:
            try:
                datetime.strptime(event[time_field], '%H:%M')
            except ValueError:
                print(f"      Invalid time format for {time_field}: {event[time_field]}")
                return False
        
        return True
    
    def get_summary(self, events: List[Dict]) -> str:
        """
        Generate a human-readable summary of parsed events.
        
        Args:
            events: List of event dictionaries
        
        Returns:
            Summary string
        """
        if not events:
            return "No events parsed."
        
        summary = f"Parsed {len(events)} event(s):\n\n"
        
        # Group by date
        events_by_date = {}
        for event in events:
            date = event['date']
            if date not in events_by_date:
                events_by_date[date] = []
            events_by_date[date].append(event)
        
        # Format summary
        for date in sorted(events_by_date.keys()):
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            summary += f"{date_obj.strftime('%A, %B %d, %Y')}:\n"
            
            for event in sorted(events_by_date[date], key=lambda e: e['start_time']):
                summary += f"  • {event['start_time']}-{event['end_time']}: {event['title']}"
                if event.get('location'):
                    summary += f" ({event['location']})"
                summary += "\n"
            
            summary += "\n"
        
        return summary


def main():
    """
    Test the Parser Agent with sample data.
    """
    print("=" * 60)
    print("Testing Parser Agent")
    print("=" * 60)
    
    # Initialize agent
    agent = ParserAgent()
    
    # Test 1: Parse sample text schedule
    print("\n[Test 1] Parsing text schedule...")
    
    sample_schedule = """
UNIVERSITY SCHEDULE - Fall 2025

Monday, November 25, 2025
9:00 AM - 10:30 AM: Introduction to Artificial Intelligence
Location: Room 101, Engineering Building
Professor: Dr. Smith

11:00 AM - 12:30 PM: Advanced Mathematics
Location: Room 205, Math Building

2:00 PM - 4:00 PM: Computer Science Lab
Location: Computer Lab A

Tuesday, November 26, 2025
10:00 AM - 11:30 AM: Machine Learning Fundamentals
Location: Room 101, Engineering Building

1:00 PM - 3:00 PM: Soccer Practice
Location: University Sports Field
Coach: Martinez

Wednesday, November 27, 2025
9:00 AM - 10:30 AM: Data Structures and Algorithms
Location: Room 303

11:00 AM - 12:00 PM: Office Hours with Prof. Johnson
Location: Office 215

3:00 PM - 5:00 PM: Study Group - Final Exam Prep
Location: Library, Room 2B

Thursday, November 28, 2025
Thanksgiving Holiday - No Classes

Friday, November 29, 2025
10:00 AM - 12:00 PM: Project Presentation
Location: Auditorium
Team presentations for AI course
"""
    
    events = agent.parse_from_text(sample_schedule)
    
    # Display summary
    print("\n" + "="*60)
    print("PARSING RESULTS")
    print("="*60)
    print(agent.get_summary(events))
    
    # Test 2: Instructions for testing with real files
    print("="*60)
    print("To test with your own schedule file:")
    print("="*60)
    print("1. Save your schedule as PDF or image in: tests/sample_schedules/")
    print("2. Run this code:")
    print("")
    print("   agent = ParserAgent()")
    print("   events = agent.parse_from_file('tests/sample_schedules/your_schedule.pdf')")
    print("   print(agent.get_summary(events))")
    print("")
    print("="*60)


if __name__ == "__main__":
    main()