"""
Calendar Agent
Manages calendar operations - creates, updates, and deletes events.
"""

from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import sys

sys.path.append(str(Path(__file__).parent.parent))

from utils.calendar_client import GoogleCalendarClient
from config.config import DEFAULT_TIMEZONE


class CalendarAgent:
    """
    Agent responsible for calendar operations.
    
    Capabilities:
    - Create events in Google Calendar
    - Update existing events
    - Delete events
    - Search for events
    - Batch operations (create multiple events)
    - Duplicate detection
    """
    
    def __init__(self, calendar_client: Optional[GoogleCalendarClient] = None):
        """
        Initialize the Calendar Agent.
        
        Args:
            calendar_client: Google Calendar client (creates new one if not provided)
        """
        self.calendar_client = calendar_client or GoogleCalendarClient()
        self.calendar_id = 'primary'  # Use primary calendar
        
        print("✓ Calendar Agent initialized")
    
    def create_event_from_parsed_data(self, event_data: Dict) -> Optional[Dict]:
        """
        Create a single calendar event from parsed schedule data.
        
        Args:
            event_data: Event dictionary from Parser Agent
                Expected format:
                {
                    "title": "Event name",
                    "date": "YYYY-MM-DD",
                    "start_time": "HH:MM",
                    "end_time": "HH:MM",
                    "location": "Location",
                    "description": "Description",
                    "recurrence": "none/daily/weekly/monthly"
                }
        
        Returns:
            Created event dictionary from Google Calendar, or None if failed
        """
        try:
            # Parse date and times
            date_str = event_data['date']
            start_time_str = event_data['start_time']
            end_time_str = event_data['end_time']
            
            # Combine date and time
            start_datetime = datetime.strptime(
                f"{date_str} {start_time_str}",
                "%Y-%m-%d %H:%M"
            )
            end_datetime = datetime.strptime(
                f"{date_str} {end_time_str}",
                "%Y-%m-%d %H:%M"
            )
            
            # Handle recurrence
            recurrence = None
            recurrence_type = event_data.get('recurrence', 'none').lower()
            
            if recurrence_type == 'daily':
                recurrence = ['RRULE:FREQ=DAILY;COUNT=30']  # 30 days
            elif recurrence_type == 'weekly':
                recurrence = ['RRULE:FREQ=WEEKLY;COUNT=15']  # 15 weeks
            elif recurrence_type == 'monthly':
                recurrence = ['RRULE:FREQ=MONTHLY;COUNT=6']  # 6 months
            
            # Create event
            created_event = self.calendar_client.create_event(
                summary=event_data['title'],
                start_datetime=start_datetime,
                end_datetime=end_datetime,
                description=event_data.get('description', ''),
                location=event_data.get('location', ''),
                timezone=DEFAULT_TIMEZONE,
                recurrence=recurrence,
                calendar_id=self.calendar_id
            )
            
            return created_event
        
        except Exception as e:
            print(f"✗ Error creating event '{event_data.get('title', 'Unknown')}': {e}")
            return None
    
    def create_events_batch(
        self, 
        events_data: List[Dict],
        check_duplicates: bool = True,
        check_conflicts: bool = True,
        ask_on_conflicts: bool = True
    ) -> Dict[str, List]:
        """
        Create multiple events in batch.
        
        Args:
            events_data: List of event dictionaries from Parser Agent
            check_duplicates: Whether to check for existing events first
            check_conflicts: Whether to check for scheduling conflicts
            ask_on_conflicts: Whether to ask user for confirmation on conflicts        
        
        Returns:
            Dictionary with 'successful', 'failed', and 'skipped' lists
        """
        results = {
            'successful': [],
            'failed': [],
            'skipped': []
        }
        
        print(f"\n{'='*60}")
        print(f"Calendar Agent: Creating {len(events_data)} events")
        print(f"{'='*60}")
        
        # Optionally check for duplicates
        existing_events = []
        if check_duplicates or check_conflicts:
            print("\n Checking calendar......")
            # Get events from the date range
            if events_data:
                min_date = min(e['date'] for e in events_data)
                max_date = max(e['date'] for e in events_data)
                
                time_min = datetime.strptime(min_date, '%Y-%m-%d')
                time_max = datetime.strptime(max_date, '%Y-%m-%d') + timedelta(days=1)
                
                existing_events = self.calendar_client.list_events(
                    calendar_id=self.calendar_id,
                    max_results=100,
                    time_min=time_min,
                    time_max=time_max
                )

        # Check for conflicts if enabled
        conflicts_found = []
        if check_conflicts:
            from agents.conflict_detector_agent import ConflictDetectorAgent
            conflict_detector = ConflictDetectorAgent(calendar_agent=self)
        
            print("\n⚙️  Checking for scheduling conflicts...")
            for event_data in events_data:
                conflict_result = conflict_detector.check_new_event_conflicts(
                    event_data,
                    existing_events
                )
                if conflict_result['status'] == 'conflicts_found':
                    conflicts_found.append({
                        'event': event_data,
                        'conflicts': conflict_result['conflicts']
                })
    
        # If conflicts found and user wants to be asked
        if conflicts_found and ask_on_conflicts:
            print(f"\n{'='*60}")
            print(f"⚠️  CONFLICTS DETECTED")
            print(f"{'='*60}")
            print(f"Found {len(conflicts_found)} event(s) with conflicts:\n")
        
            for item in conflicts_found:
                event = item['event']
                conflicts = item['conflicts']
            
                print(f"📅 Event: {event['title']}")
                print(f"   Date: {event['date']} {event['start_time']}-{event['end_time']}")
                print(f"   Conflicts with {len(conflicts)} existing event(s):")
            
            for conflict in conflicts:
                severity_icon = {'high': '❌', 'medium': '⚠️', 'low': '💡'}
                icon = severity_icon.get(conflict['severity'], '•')
                print(f"     {icon} {conflict['message']}")
                print(f"        vs. {conflict['event2']['title']}")
            print()
        
        response = input("⚠️  Do you want to proceed anyway? (yes/no): ").strip().lower()
        
        if response not in ['yes', 'y']:
            print("\n❌ Operation cancelled by user")
            results['skipped'] = events_data
            return results
        
        print("\n✓ User confirmed - proceeding with creation...")

        # Create each event
        for i, event_data in enumerate(events_data, 1):
            title = event_data.get('title', 'Untitled')
            date = event_data.get('date', 'Unknown date')
            start_time = event_data.get('start_time', '00:00')
            
            print(f"\n[{i}/{len(events_data)}] {title}")
            print(f"  📅 {date} at {start_time}")
            
            # Check for duplicates
            if check_duplicates and self._is_duplicate(event_data, existing_events):
                print(f"  ⚠️  Skipped - already exists in calendar")
                results['skipped'].append(event_data)
                continue
            
            # Create event
            created_event = self.create_event_from_parsed_data(event_data)
            
            if created_event:
                results['successful'].append({
                    'original_data': event_data,
                    'calendar_event': created_event
                })
            else:
                results['failed'].append(event_data)
        
        # Summary
        print(f"\n{'='*60}")
        print("BATCH CREATION SUMMARY")
        print(f"{'='*60}")
        print(f"✓ Successful: {len(results['successful'])}")
        print(f"✗ Failed: {len(results['failed'])}")
        print(f"⚠️  Skipped (duplicates): {len(results['skipped'])}")
        print(f"{'='*60}")
        
        return results
    
    def _is_duplicate(self, new_event: Dict, existing_events: List[Dict]) -> bool:
        """
        Check if an event already exists in the calendar.
        
        Args:
            new_event: Event data to check
            existing_events: List of existing calendar events
        
        Returns:
            True if duplicate found, False otherwise
        """
        new_title = new_event['title'].lower()
        new_date = new_event['date']
        new_start = new_event['start_time']
        
        for existing in existing_events:
            existing_title = existing.get('summary', '').lower()
            existing_start = existing.get('start', {}).get('dateTime', '')
            
            # Parse existing event datetime
            if existing_start:
                try:
                    existing_dt = datetime.fromisoformat(existing_start.replace('Z', '+00:00'))
                    existing_date = existing_dt.strftime('%Y-%m-%d')
                    existing_time = existing_dt.strftime('%H:%M')
                    
                    # Check if title, date, and time match
                    if (new_title == existing_title and 
                        new_date == existing_date and 
                        new_start == existing_time):
                        return True
                except:
                    continue
        
        return False
    
    def get_events_in_range(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict]:
        """
        Get all events within a date range.
        
        Args:
            start_date: Start of range
            end_date: End of range
        
        Returns:
            List of calendar events
        """
        return self.calendar_client.list_events(
            calendar_id=self.calendar_id,
            time_min=start_date,
            time_max=end_date,
            max_results=100
        )
    
    def delete_event(self, event_id: str) -> bool:
        """
        Delete an event by ID.
        
        Args:
            event_id: Google Calendar event ID
        
        Returns:
            True if successful, False otherwise
        """
        return self.calendar_client.delete_event(
            event_id=event_id,
            calendar_id=self.calendar_id
        )
    
    def update_event(
        self,
        event_id: str,
        **kwargs
    ) -> Optional[Dict]:
        """
        Update an existing event.
        
        Args:
            event_id: Google Calendar event ID
            **kwargs: Fields to update (summary, start_datetime, end_datetime, etc.)
        
        Returns:
            Updated event dictionary, or None if failed
        """
        return self.calendar_client.update_event(
            event_id=event_id,
            calendar_id=self.calendar_id,
            **kwargs
        )


def main():
    """
    Test the Calendar Agent.
    """
    print("=" * 60)
    print("Testing Calendar Agent")
    print("=" * 60)
    
    # Initialize agent
    agent = CalendarAgent()
    
    # Test 1: Create a single event
    print("\n[Test 1] Creating a single test event...")
    
    test_event = {
        "title": "Calendar Agent Test Event",
        "date": "2025-12-10",
        "start_time": "14:00",
        "end_time": "15:00",
        "location": "Test Room 123",
        "description": "This is a test event created by the Calendar Agent",
        "recurrence": "none"
    }
    
    created = agent.create_event_from_parsed_data(test_event)
    
    if created:
        event_id = created['id']
        print(f"\n✓ Event created successfully!")
        print(f"  Event ID: {event_id}")
        print(f"  View in calendar: {created.get('htmlLink')}")
        
        # Test 2: Delete the test event
        print("\n[Test 2] Deleting the test event...")
        agent.delete_event(event_id)
    
    # Test 3: Batch creation (sample data)
    print("\n[Test 3] Testing batch creation...")
    
    sample_events = [
        {
            "title": "Batch Test Event 1",
            "date": "2025-12-11",
            "start_time": "09:00",
            "end_time": "10:00",
            "location": "Room A",
            "description": "First test event",
            "recurrence": "none"
        },
        {
            "title": "Batch Test Event 2",
            "date": "2025-12-11",
            "start_time": "11:00",
            "end_time": "12:00",
            "location": "Room B",
            "description": "Second test event",
            "recurrence": "none"
        }
    ]
    
    results = agent.create_events_batch(sample_events, check_duplicates=False)
    
    # Clean up test events
    print("\n[Cleanup] Deleting test events...")
    for item in results['successful']:
        event_id = item['calendar_event']['id']
        agent.delete_event(event_id)
    
    print("\n" + "="*60)
    print("✓ Calendar Agent tests completed!")
    print("="*60)


if __name__ == "__main__":
    main()