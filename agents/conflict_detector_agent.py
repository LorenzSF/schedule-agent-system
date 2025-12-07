"""
Conflict Detector Agent
Detects scheduling conflicts, overlaps, and tight schedules.
"""

from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import sys

sys.path.append(str(Path(__file__).parent.parent))

from utils.llm_client import LLMClient
from agents.calendar_agent import CalendarAgent
from config.config import MINIMUM_GAP_MINUTES


class ConflictDetectorAgent:
    """
    Agent responsible for detecting scheduling conflicts.
    
    Capabilities:
    - Detect overlapping events (hard conflicts)
    - Detect tight schedules (insufficient travel time)
    - Detect back-to-back events (no buffer time)
    - Use AI to assess location-based feasibility
    - Suggest resolutions for conflicts
    - User-configurable minimum gap time
    """
    
    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        calendar_agent: Optional[CalendarAgent] = None,
        minimum_gap_minutes: Optional[int] = None
    ):
        """
        Initialize the Conflict Detector Agent.
        
        Args:
            llm_client: LLM client for AI-based assessments
            calendar_agent: Calendar agent to fetch events
            minimum_gap_minutes: Minimum time between events (None = ask user)
        """
        self.llm_client = llm_client or LLMClient()
        self.calendar_agent = calendar_agent or CalendarAgent()
        
        # If minimum gap not specified, ask user
        if minimum_gap_minutes is None:
            minimum_gap_minutes = self._ask_user_for_gap_preference()
        
        self.minimum_gap_minutes = minimum_gap_minutes
        
        print("✓ Conflict Detector Agent initialized")
        print(f"  ⚙️  Minimum gap time: {self.minimum_gap_minutes} minutes")
    
    def _ask_user_for_gap_preference(self) -> int:
        """
        Ask user for their preferred minimum gap between events.
        
        Returns:
            Minimum gap in minutes
        """
        print("\n" + "="*60)
        print("⚙️  CONFIGURATION: Minimum Gap Between Events")
        print("="*60)
        print("How much time do you need between events?")
        print("This is used to detect 'tight schedules'")
        print()
        print("Suggested values:")
        print("  • 0 min  - No buffer needed (back-to-back is OK)")
        print("  • 10 min - Quick transition (same building)")
        print("  • 15 min - Standard buffer (default)")
        print("  • 30 min - Travel time (different buildings)")
        print("  • 60 min - Lunch/break time")
        print()
        
        while True:
            try:
                response = input("Enter minimum gap in minutes [default: 15]: ").strip()
                
                if not response:
                    return MINIMUM_GAP_MINUTES  # Use default
                
                gap = int(response)
                
                if gap < 0:
                    print("❌ Please enter a positive number")
                    continue
                
                if gap > 120:
                    confirm = input(f"⚠️  {gap} minutes is quite long. Are you sure? (yes/no): ")
                    if confirm.lower() not in ['yes', 'y']:
                        continue
                
                print(f"✓ Minimum gap set to {gap} minutes")
                return gap
            
            except ValueError:
                print("❌ Please enter a valid number")
    
    def set_minimum_gap(self, minutes: int):
        """
        Update the minimum gap setting.
        
        Args:
            minutes: New minimum gap in minutes
        """
        self.minimum_gap_minutes = minutes
        print(f"✓ Minimum gap updated to {minutes} minutes")
    
    def get_current_settings(self) -> Dict:
        """
        Get current conflict detection settings.
        
        Returns:
            Dictionary with current settings
        """
        return {
            'minimum_gap_minutes': self.minimum_gap_minutes
        }
    
    def check_for_conflicts(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        days_ahead: int = 30,
        show_settings: bool = True
    ) -> Dict:
        """
        Check for conflicts in the calendar.
        
        Args:
            start_date: Start of date range (default: now)
            end_date: End of date range (default: start_date + days_ahead)
            days_ahead: Days to look ahead if end_date not specified
            show_settings: Whether to display current settings
        
        Returns:
            Dictionary with conflict analysis
        """
        print(f"\n{'='*60}")
        print("Conflict Detector: Analyzing schedule")
        print(f"{'='*60}")
        
        if show_settings:
            print(f"⚙️  Current settings:")
            print(f"   • Minimum gap between events: {self.minimum_gap_minutes} minutes")
            print()
        
        # Get date range
        if start_date is None:
            start_date = datetime.now()
        if end_date is None:
            end_date = start_date + timedelta(days=days_ahead)
        
        print(f"📅 Date range: {start_date.date()} to {end_date.date()}")
        
        # Fetch events
        print("\n[1/3] Fetching calendar events...")
        events = self.calendar_agent.get_events_in_range(start_date, end_date)
        
        if not events:
            print("✓ No events found in date range")
            return {
                'status': 'ok',
                'message': 'No events to check',
                'conflicts': []
            }
        
        print(f"✓ Found {len(events)} events")
        
        # Sort events by start time
        sorted_events = self._sort_events_by_time(events)
        
        # Detect conflicts
        print("\n[2/3] Detecting conflicts...")
        conflicts = []
        
        for i in range(len(sorted_events)):
            for j in range(i + 1, len(sorted_events)):
                conflict = self._check_event_pair(
                    sorted_events[i],
                    sorted_events[j]
                )
                if conflict:
                    conflicts.append(conflict)
        
        # Analyze with AI if needed
        print("\n[3/3] Analyzing with AI...")
        ai_analyzed_conflicts = []
        for conflict in conflicts:
            if conflict['type'] == 'tight_schedule':
                # Use AI to assess travel feasibility
                enhanced = self._enhance_with_ai_assessment(conflict)
                ai_analyzed_conflicts.append(enhanced)
            else:
                ai_analyzed_conflicts.append(conflict)
        
        # Summary
        print(f"\n{'='*60}")
        print("CONFLICT DETECTION SUMMARY")
        print(f"{'='*60}")
        
        if not ai_analyzed_conflicts:
            print("✓ No conflicts detected!")
            return {
                'status': 'ok',
                'message': 'No conflicts found',
                'conflicts': [],
                'total_events': len(events)
            }
        
        # Categorize conflicts
        hard_conflicts = [c for c in ai_analyzed_conflicts if c['severity'] == 'high']
        soft_conflicts = [c for c in ai_analyzed_conflicts if c['severity'] == 'medium']
        warnings = [c for c in ai_analyzed_conflicts if c['severity'] == 'low']
        
        print(f"❌ Hard conflicts (overlaps): {len(hard_conflicts)}")
        print(f"⚠️  Soft conflicts (tight schedules): {len(soft_conflicts)}")
        print(f"💡 Warnings (no buffer): {len(warnings)}")
        
        return {
            'status': 'conflicts_found',
            'message': f'Found {len(ai_analyzed_conflicts)} potential issues',
            'conflicts': ai_analyzed_conflicts,
            'total_events': len(events),
            'hard_conflicts': hard_conflicts,
            'soft_conflicts': soft_conflicts,
            'warnings': warnings
        }
    
    def check_new_event_conflicts(
        self,
        new_event_data: Dict,
        existing_events: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Check if a new event would cause conflicts.
        
        Args:
            new_event_data: Dictionary with new event details
            existing_events: Optional list of existing events
        
        Returns:
            Conflict analysis for the new event
        """
        # Parse new event times
        date_str = new_event_data['date']
        start_time_str = new_event_data['start_time']
        end_time_str = new_event_data['end_time']
        
        new_start = datetime.strptime(
            f"{date_str} {start_time_str}",
            "%Y-%m-%d %H:%M"
        )
        new_end = datetime.strptime(
            f"{date_str} {end_time_str}",
            "%Y-%m-%d %H:%M"
        )
        
        # Create a temporary event object
        temp_event = {
            'summary': new_event_data.get('title', 'New Event'),
            'start': {'dateTime': new_start.isoformat()},
            'end': {'dateTime': new_end.isoformat()},
            'location': new_event_data.get('location', '')
        }
        
        # Get existing events if not provided
        if existing_events is None:
            start_range = new_start - timedelta(days=1)
            end_range = new_end + timedelta(days=1)
            existing_events = self.calendar_agent.get_events_in_range(
                start_range,
                end_range
            )
        
        # Check for conflicts
        conflicts = []
        for event in existing_events:
            conflict = self._check_event_pair(temp_event, event)
            if conflict:
                conflicts.append(conflict)
        
        if not conflicts:
            return {
                'status': 'ok',
                'message': 'No conflicts',
                'conflicts': []
            }
        
        return {
            'status': 'conflicts_found',
            'message': f'Found {len(conflicts)} conflicts',
            'conflicts': conflicts
        }
    
    def _sort_events_by_time(self, events: List[Dict]) -> List[Dict]:
        """Sort events by start time."""
        def get_start_time(event):
            start_str = event.get('start', {}).get('dateTime', '')
            if start_str:
                return datetime.fromisoformat(start_str.replace('Z', '+00:00'))
            return datetime.max
        
        return sorted(events, key=get_start_time)
    
    def _check_event_pair(
        self,
        event1: Dict,
        event2: Dict
    ) -> Optional[Dict]:
        """Check if two events conflict."""
        # Get event times
        start1_str = event1.get('start', {}).get('dateTime')
        end1_str = event1.get('end', {}).get('dateTime')
        start2_str = event2.get('start', {}).get('dateTime')
        end2_str = event2.get('end', {}).get('dateTime')
        
        if not all([start1_str, end1_str, start2_str, end2_str]):
            return None
        
        try:
            start1 = datetime.fromisoformat(start1_str.replace('Z', '+00:00'))
            end1 = datetime.fromisoformat(end1_str.replace('Z', '+00:00'))
            start2 = datetime.fromisoformat(start2_str.replace('Z', '+00:00'))
            end2 = datetime.fromisoformat(end2_str.replace('Z', '+00:00'))
        except:
            return None
        
        # Check for direct overlap
        if self._times_overlap(start1, end1, start2, end2):
            return {
                'type': 'overlap',
                'severity': 'high',
                'event1': {
                    'title': event1.get('summary', 'Untitled'),
                    'start': start1.isoformat(),
                    'end': end1.isoformat(),
                    'location': event1.get('location', '')
                },
                'event2': {
                    'title': event2.get('summary', 'Untitled'),
                    'start': start2.isoformat(),
                    'end': end2.isoformat(),
                    'location': event2.get('location', '')
                },
                'message': 'Events overlap - cannot attend both',
                'suggestion': 'Reschedule one of the events'
            }
        
        # Check for tight schedule
        gap_minutes = self._calculate_gap(end1, start2)
        
        if 0 < gap_minutes < self.minimum_gap_minutes:
            return {
                'type': 'tight_schedule',
                'severity': 'medium',
                'event1': {
                    'title': event1.get('summary', 'Untitled'),
                    'start': start1.isoformat(),
                    'end': end1.isoformat(),
                    'location': event1.get('location', '')
                },
                'event2': {
                    'title': event2.get('summary', 'Untitled'),
                    'start': start2.isoformat(),
                    'end': end2.isoformat(),
                    'location': event2.get('location', '')
                },
                'gap_minutes': gap_minutes,
                'message': f'Only {gap_minutes} minutes between events (minimum: {self.minimum_gap_minutes})',
                'suggestion': 'Consider adding buffer time or checking travel distance'
            }
        
        # Check for back-to-back
        if gap_minutes == 0:
            loc1 = event1.get('location', '').strip()
            loc2 = event2.get('location', '').strip()
            
            if loc1 and loc2 and loc1.lower() != loc2.lower():
                return {
                    'type': 'back_to_back',
                    'severity': 'low',
                    'event1': {
                        'title': event1.get('summary', 'Untitled'),
                        'start': start1.isoformat(),
                        'end': end1.isoformat(),
                        'location': loc1
                    },
                    'event2': {
                        'title': event2.get('summary', 'Untitled'),
                        'start': start2.isoformat(),
                        'end': end2.isoformat(),
                        'location': loc2
                    },
                    'gap_minutes': 0,
                    'message': 'Back-to-back events at different locations',
                    'suggestion': 'Verify you can travel between locations instantly'
                }
        
        return None
    
    def _times_overlap(self, start1, end1, start2, end2) -> bool:
        """Check if two time ranges overlap."""
        return start1 < end2 and start2 < end1
    
    def _calculate_gap(self, end_time, start_time) -> int:
        """Calculate gap between events in minutes."""
        gap = start_time - end_time
        return int(gap.total_seconds() / 60)
    
    def _enhance_with_ai_assessment(self, conflict: Dict) -> Dict:
        """Use AI to assess travel feasibility."""
        try:
            assessment = self.llm_client.assess_travel_feasibility(
                conflict['event1'],
                conflict['event2'],
                conflict['gap_minutes']
            )
            
            conflict['ai_assessment'] = assessment
            
            if not assessment.get('feasible', True):
                conflict['severity'] = 'high'
                conflict['message'] += f" - AI: {assessment.get('reasoning', '')}"
        except Exception as e:
            print(f"  ⚠️  Could not get AI assessment: {e}")
        
        return conflict
    
    def format_conflict_report(self, conflicts: List[Dict]) -> str:
        """Format conflicts into a readable report."""
        if not conflicts:
            return "✓ No conflicts detected!"
        
        report = f"\n{'='*60}\n"
        report += "CONFLICT REPORT\n"
        report += f"{'='*60}\n"
        report += f"Total issues found: {len(conflicts)}\n"
        report += f"⚙️  (Minimum gap setting: {self.minimum_gap_minutes} minutes)\n\n"
        
        for i, conflict in enumerate(conflicts, 1):
            severity_icon = {
                'high': '❌',
                'medium': '⚠️',
                'low': '💡'
            }.get(conflict['severity'], '•')
            
            report += f"{severity_icon} Conflict {i}: {conflict['type'].replace('_', ' ').title()}\n"
            report += f"   Severity: {conflict['severity'].upper()}\n"
            report += f"   Event 1: {conflict['event1']['title']}\n"
            report += f"            {conflict['event1']['start']}\n"
            if conflict['event1'].get('location'):
                report += f"            at {conflict['event1']['location']}\n"
            
            report += f"   Event 2: {conflict['event2']['title']}\n"
            report += f"            {conflict['event2']['start']}\n"
            if conflict['event2'].get('location'):
                report += f"            at {conflict['event2']['location']}\n"
            
            report += f"   Issue: {conflict['message']}\n"
            report += f"   Suggestion: {conflict['suggestion']}\n"
            
            if conflict.get('ai_assessment'):
                ai = conflict['ai_assessment']
                report += f"   AI Analysis: {ai.get('reasoning', 'N/A')}\n"
            
            report += "\n"
        
        return report


def main():
    """Test the Conflict Detector Agent."""
    print("=" * 60)
    print("Testing Conflict Detector Agent")
    print("=" * 60)
    
    # Initialize agent (will ask user for gap preference)
    agent = ConflictDetectorAgent()
    
    # Check for conflicts
    print("\n[Test] Checking for conflicts in calendar...")
    result = agent.check_for_conflicts(days_ahead=7)
    
    if result['status'] == 'ok':
        print("\n✓ No conflicts found!")
    else:
        conflicts = result.get('conflicts', [])
        print(agent.format_conflict_report(conflicts))
    
    print("\n" + "="*60)
    print("✓ Test completed!")
    print("="*60)


if __name__ == "__main__":
    main()