"""
Change Manager Agent
Handles natural language commands to modify calendar events.
"""

from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import sys
import re

sys.path.append(str(Path(__file__).parent.parent))

from utils.llm_client import LLMClient
from utils.calendar_client import GoogleCalendarClient
from agents.calendar_agent import CalendarAgent


class ChangeManagerAgent:
    """
    Agent responsible for handling calendar modifications via natural language.
    
    Capabilities:
    - Parse natural language modification commands
    - Search for matching events
    - Move events to new dates/times
    - Cancel/delete events
    - Update event details (title, location, description)
    - Handle ambiguous commands with user confirmation
    """
    
    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        calendar_agent: Optional[CalendarAgent] = None
    ):
        """
        Initialize the Change Manager Agent.
        
        Args:
            llm_client: LLM client for parsing commands
            calendar_agent: Calendar agent for modifications
        """
        self.llm_client = llm_client or LLMClient()
        self.calendar_agent = calendar_agent or CalendarAgent()
        
        print("✓ Change Manager Agent initialized")
    
    def process_command(self, command: str) -> Dict:
        """
        Process a natural language modification command.
        
        Args:
            command: Natural language command (e.g., "move soccer to Friday")
        
        Returns:
            Result dictionary with status and details
        """
        print(f"\n{'='*60}")
        print(f"Change Manager: Processing command")
        print(f"{'='*60}")
        print(f"Command: \"{command}\"")
        
        # Step 1: Get upcoming events for context
        print("\n[1/4] Fetching calendar events for context...")
        upcoming_events = self._get_context_events()
        print(f"✓ Found {len(upcoming_events)} upcoming events")
        
        # Step 2: Parse the command with LLM
        print("\n[2/4] Parsing command with AI...")
        parsed_command = self.llm_client.parse_modification_command(
            command,
            upcoming_events
        )
        
        print(f"✓ Action: {parsed_command.get('action')}")
        print(f"  Target: {parsed_command.get('event_identifier')}")
        print(f"  Confidence: {parsed_command.get('confidence')}")
        print(f"  Reasoning: {parsed_command.get('reasoning')}")
        
        # Check confidence
        if parsed_command.get('confidence', 0) < 0.5:
            return {
                'status': 'error',
                'message': 'Command unclear or ambiguous',
                'details': parsed_command.get('reasoning')
            }
        
        # Step 3: Find matching event(s)
        print("\n[3/4] Searching for matching events...")
        matching_events = self._find_matching_events(
            parsed_command.get('event_identifier', ''),
            upcoming_events
        )
        
        if not matching_events:
            return {
                'status': 'error',
                'message': 'No matching events found',
                'searched_for': parsed_command.get('event_identifier')
            }
        
        if len(matching_events) > 1:
            return {
                'status': 'ambiguous',
                'message': f'Found {len(matching_events)} matching events',
                'events': matching_events
            }
        
        target_event = matching_events[0]
        print(f"✓ Found event: {target_event.get('summary')}")
        print(f"  Current: {target_event.get('start', {}).get('dateTime')}")
        
        # Step 4: Execute the modification
        print("\n[4/4] Executing modification...")
        action = parsed_command.get('action')
        
        if action == 'move':
            result = self._move_event(target_event, parsed_command)
        elif action == 'delete':
            result = self._delete_event(target_event)
        elif action == 'modify':
            result = self._modify_event(target_event, parsed_command)
        else:
            result = {
                'status': 'error',
                'message': f'Unsupported action: {action}'
            }
        
        return result
    
    def _get_context_events(self, days_ahead: int = 30) -> List[Dict]:
        """
        Get upcoming events for context.
        
        Args:
            days_ahead: Number of days to look ahead
        
        Returns:
            List of upcoming events
        """
        start_date = datetime.now()
        end_date = start_date + timedelta(days=days_ahead)
        
        return self.calendar_agent.get_events_in_range(start_date, end_date)
    
    def _find_matching_events(
        self,
        identifier: str,
        events: List[Dict]
    ) -> List[Dict]:
        """
        Find events matching the identifier.
        Handles event names, dates, and combinations.
        
        Args:
            identifier: Event identifier (can include name and date like "Event: 2025-12-04T11:00:00")
            events: List of events to search
        
        Returns:
            List of matching events
        """
        # Try to extract date from the end of the identifier
        target_date = None
        event_name = identifier.lower()
        
        # Look for ISO date format (YYYY-MM-DD) anywhere in the identifier
        import re
        date_pattern = r'(\d{4}-\d{2}-\d{2})'
        date_match = re.search(date_pattern, identifier)

        if date_match:
            try:
             date_str = date_match.group(1)
             target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
             # Remove the date part from event name
             event_name = identifier.split(date_str)[0]
             # Clean up event name (remove trailing colons and spaces)
             event_name = event_name.rstrip(': T').lower()
             print(f"  🔍 Searching for: '{event_name}' on {target_date}")
            except Exception as e:
                print(f"  ⚠️  Could not parse date: {e}")
    
        if not target_date:
            print(f"  🔍 Searching for: '{event_name}' (any date)")
    
        matching = []
        
        for event in events:
            title = event.get('summary', '').lower()
            location = event.get('location', '').lower()
            description = event.get('description', '').lower()
            
            # Check if event name matches
            name_matches = (
                event_name in title or 
                title in event_name or
                event_name in location or 
                event_name in description
            )
            
            if not name_matches:
                continue
            
            # If we have a target date, also check date match
            if target_date:
                event_date_str = event.get('start', {}).get('dateTime', '')
                if event_date_str:
                    try:
                        event_dt = datetime.fromisoformat(event_date_str.replace('Z', '+00:00'))
                        if event_dt.date() == target_date:
                            matching.append(event)
                            print(f"    ✓ Matched: {title} on {event_dt.date()}")
                    except Exception as e:
                        print(f"    ⚠️  Could not parse event date: {e}")
                else:
                    # All-day event or no datetime
                    matching.append(event)
            else:
                # No date filter, include all name matches
                matching.append(event)
        
        return matching
    
    def _move_event(self, event: Dict, parsed_command: Dict) -> Dict:
        """
        Move an event to a new date/time.
        
        Args:
            event: Event to move
            parsed_command: Parsed command with new date/time
        
        Returns:
            Result dictionary
        """
        modifications = parsed_command.get('modifications', {})
        
        # Get current event details
        current_start = event['start'].get('dateTime')
        current_end = event['end'].get('dateTime')
        
        if not current_start:
            return {
                'status': 'error',
                'message': 'Event does not have a datetime (might be all-day event)'
            }
        
        # Parse current datetime
        current_start_dt = datetime.fromisoformat(current_start.replace('Z', '+00:00'))
        current_end_dt = datetime.fromisoformat(current_end.replace('Z', '+00:00'))
        duration = current_end_dt - current_start_dt
        
        # Calculate new datetime
        new_start_dt = current_start_dt
        new_end_dt = current_end_dt
        
        # Update date if specified
        if modifications.get('new_date'):
            new_date = datetime.strptime(modifications['new_date'], '%Y-%m-%d')
            new_start_dt = new_start_dt.replace(
                year=new_date.year,
                month=new_date.month,
                day=new_date.day
            )
            new_end_dt = new_start_dt + duration
        
        # Update time if specified
        if modifications.get('new_start_time'):
            new_time = datetime.strptime(modifications['new_start_time'], '%H:%M')
            new_start_dt = new_start_dt.replace(
                hour=new_time.hour,
                minute=new_time.minute
            )
            new_end_dt = new_start_dt + duration
        
        # Update end time if specified
        if modifications.get('new_end_time'):
            new_time = datetime.strptime(modifications['new_end_time'], '%H:%M')
            new_end_dt = new_end_dt.replace(
                hour=new_time.hour,
                minute=new_time.minute
            )
        
        # Update the event
        updated_event = self.calendar_agent.update_event(
            event_id=event['id'],
            start_datetime=new_start_dt,
            end_datetime=new_end_dt
        )
        
        if updated_event:
            return {
                'status': 'success',
                'message': 'Event moved successfully',
                'event': updated_event,
                'changes': {
                    'old_start': current_start,
                    'new_start': new_start_dt.isoformat()
                }
            }
        else:
            return {
                'status': 'error',
                'message': 'Failed to update event'
            }
    
    def _delete_event(self, event: Dict) -> Dict:
        """
        Delete an event.
        
        Args:
            event: Event to delete
        
        Returns:
            Result dictionary
        """
        success = self.calendar_agent.delete_event(event['id'])
        
        if success:
            return {
                'status': 'success',
                'message': 'Event deleted successfully',
                'deleted_event': event.get('summary')
            }
        else:
            return {
                'status': 'error',
                'message': 'Failed to delete event'
            }
    
    def _modify_event(self, event: Dict, parsed_command: Dict) -> Dict:
        """
        Modify event details (title, location, description).
        
        Args:
            event: Event to modify
            parsed_command: Parsed command with modifications
        
        Returns:
            Result dictionary
        """
        modifications = parsed_command.get('modifications', {})
        
        # Build update parameters
        update_params = {}
        
        if modifications.get('new_title'):
            update_params['summary'] = modifications['new_title']
        
        if modifications.get('new_location'):
            update_params['location'] = modifications['new_location']
        
        if modifications.get('new_description'):
            update_params['description'] = modifications['new_description']
        
        if not update_params:
            return {
                'status': 'error',
                'message': 'No modifications specified'
            }
        
        # Update the event
        updated_event = self.calendar_agent.update_event(
            event_id=event['id'],
            **update_params
        )
        
        if updated_event:
            return {
                'status': 'success',
                'message': 'Event modified successfully',
                'event': updated_event,
                'changes': update_params
            }
        else:
            return {
                'status': 'error',
                'message': 'Failed to modify event'
            }


def main():
    """
    Test the Change Manager Agent.
    """
    print("=" * 60)
    print("Testing Change Manager Agent")
    print("=" * 60)
    
    # Initialize agent
    agent = ChangeManagerAgent()
    
    print("\n" + "="*60)
    print("INTERACTIVE TEST MODE")
    print("="*60)
    print("Try commands like:")
    print("  - 'move Machine Learning to Friday at 2pm'")
    print("  - 'cancel AI and Society'")
    print("  - 'change location of Neural Networks to Room 101'")
    print("  - 'reschedule Applied AI to next Monday'")
    print("\nType 'quit' to exit")
    print("="*60)
    
    while True:
        try:
            command = input("\n📝 Enter command: ").strip()
            
            if not command:
                continue
            
            if command.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            # Process the command
            result = agent.process_command(command)
            
            # Display result
            print("\n" + "="*60)
            print("RESULT")
            print("="*60)
            
            status = result.get('status')
            
            if status == 'success':
                print(f"✓ {result.get('message')}")
                if result.get('changes'):
                    print(f"\nChanges made:")
                    for key, value in result['changes'].items():
                        print(f"  - {key}: {value}")
            
            elif status == 'error':
                print(f"✗ {result.get('message')}")
                if result.get('details'):
                    print(f"  Details: {result.get('details')}")
            
            elif status == 'ambiguous':
                print(f"⚠️  {result.get('message')}")
                print("\nMatching events:")
                for i, event in enumerate(result.get('events', []), 1):
                    start = event.get('start', {}).get('dateTime', 'Unknown')
                    print(f"  {i}. {event.get('summary')} at {start}")
                print("\nPlease be more specific in your command.")
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n✗ Error: {e}")


if __name__ == "__main__":
    main()