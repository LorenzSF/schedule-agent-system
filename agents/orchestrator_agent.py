"""
Orchestrator Agent
Coordinates all other agents for complex workflows.
"""

from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import sys

sys.path.append(str(Path(__file__).parent.parent))

from agents.parser_agent import ParserAgent
from agents.calendar_agent import CalendarAgent
from agents.change_manager_agent import ChangeManagerAgent
from agents.conflict_detector_agent import ConflictDetectorAgent
from utils.llm_client import LLMClient


class OrchestratorAgent:
    """
    Master agent that coordinates all other agents.
    
    Capabilities:
    - Orchestrate complex multi-agent workflows
    - Parse schedules and import to calendar
    - Manage calendar modifications
    - Detect and resolve conflicts
    - Provide intelligent suggestions
    - Handle error recovery
    """
    
    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        minimum_gap_minutes: Optional[int] = None
    ):
        """
        Initialize the Orchestrator Agent.
        
        Args:
            llm_client: Shared LLM client for all agents
            minimum_gap_minutes: Minimum gap setting (None = ask user)
        """
        print("="*60)
        print("🤖 Initializing Schedule Agent System")
        print("="*60)
        
        # Initialize shared LLM client
        self.llm_client = llm_client or LLMClient()
        
        # Initialize all sub-agents
        print("\n📋 Initializing agents...")
        self.parser_agent = ParserAgent(llm_client=self.llm_client)
        self.calendar_agent = CalendarAgent()
        self.conflict_detector = ConflictDetectorAgent(
            llm_client=self.llm_client,
            calendar_agent=self.calendar_agent,
            minimum_gap_minutes=minimum_gap_minutes
        )
        self.change_manager = ChangeManagerAgent(
            llm_client=self.llm_client,
            calendar_agent=self.calendar_agent
        )
        
        print("\n✓ All agents initialized successfully!")
        print("="*60)
    
    def import_schedule_from_file(
        self,
        file_path: str,
        check_conflicts: bool = True,
        ask_on_conflicts: bool = True
    ) -> Dict:
        """
        Complete workflow: Parse schedule file and import to calendar.
        
        Args:
            file_path: Path to schedule file (PDF or image)
            check_conflicts: Whether to check for conflicts
            ask_on_conflicts: Whether to ask user on conflicts
        
        Returns:
            Dictionary with workflow results
        """
        print("\n" + "="*60)
        print("🔄 WORKFLOW: Import Schedule")
        print("="*60)
        
        # Step 1: Parse schedule
        print("\n[1/3] Parsing schedule file...")
        events = self.parser_agent.parse_from_file(file_path)
        
        if not events:
            return {
                'status': 'error',
                'message': 'No events could be parsed from file',
                'events_parsed': 0
            }
        
        print(f"\n✓ Successfully parsed {len(events)} events")
        
        # Step 2: Show summary and ask for confirmation
        print("\n[2/3] Schedule summary:")
        print(self.parser_agent.get_summary(events))
        
        response = input(f"\n📥 Import these {len(events)} events to calendar? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            return {
                'status': 'cancelled',
                'message': 'User cancelled import',
                'events_parsed': len(events)
            }
        
        # Step 3: Create events in calendar
        print("\n[3/3] Creating events in calendar...")
        results = self.calendar_agent.create_events_batch(
            events,
            check_duplicates=True,
            check_conflicts=check_conflicts,
            ask_on_conflicts=ask_on_conflicts
        )
        
        # Final summary
        return {
            'status': 'success',
            'message': f'Imported {len(results["successful"])} events',
            'events_parsed': len(events),
            'events_created': len(results['successful']),
            'events_skipped': len(results['skipped']),
            'events_failed': len(results['failed']),
            'details': results
        }
    
    def modify_event(self, command: str, interactive: bool = True) -> Dict:
        """
        Workflow: Modify calendar event with natural language.
        
        Args:
            command: Natural language modification command
        
        Returns:
            Dictionary with modification results
        """
        print("\n" + "="*60)
        print("🔄 WORKFLOW: Modify Event")
        print("="*60)
        
        result = self.change_manager.process_command(command, interactive=interactive)
        
        # If successful, check for new conflicts
        if result['status'] == 'success' and result.get('event'):
            print("\n[Post-modification] Checking for new conflicts...")
            conflict_check = self.conflict_detector.check_for_conflicts(days_ahead=7)
            
            if conflict_check['status'] == 'conflicts_found':
                print("\n⚠️  Warning: The modification created new conflicts:")
                print(self.conflict_detector.format_conflict_report(
                    conflict_check['conflicts']
                ))
        
        return result
    
    def check_schedule_conflicts(
        self,
        days_ahead: int = 7
    ) -> Dict:
        """
        Workflow: Check calendar for conflicts.
        
        Args:
            days_ahead: Number of days to check
        
        Returns:
            Dictionary with conflict analysis
        """
        print("\n" + "="*60)
        print("🔄 WORKFLOW: Check Conflicts")
        print("="*60)
        
        result = self.conflict_detector.check_for_conflicts(days_ahead=days_ahead)
        
        if result['conflicts']:
            print(self.conflict_detector.format_conflict_report(result['conflicts']))
        
        return result
    
    def intelligent_schedule_suggestion(
        self,
        query: str
    ) -> Dict:
        """
        Use AI to provide intelligent scheduling suggestions.
        
        Args:
            query: User's scheduling question/request
        
        Returns:
            Dictionary with AI suggestions
        """
        print("\n" + "="*60)
        print("🔄 WORKFLOW: Intelligent Suggestion")
        print("="*60)
        print(f"Query: {query}")
        
        # Get upcoming events for context
        events = self.calendar_agent.get_events_in_range(
            datetime.now(),
            datetime.now() + timedelta(days=30)
        )
        
        # Format events for AI
        events_context = "\n".join([
            f"- {e.get('summary')}: {e.get('start', {}).get('dateTime', 'No time')}"
            for e in events[:20]
        ])
        
        prompt = f"""
You are an intelligent scheduling assistant. The user has asked:

"{query}"

Their current schedule includes:
{events_context}

Provide helpful, actionable advice about:
- Best times to schedule new events
- Potential conflicts or issues
- Suggestions for reorganizing their schedule
- Any other relevant insights

Be concise and practical.
"""
        
        try:
            response = self.llm_client.generate_completion(
                prompt=prompt,
                system_prompt="You are a helpful scheduling assistant with expertise in time management and calendar optimization."
            )
            
            print("\n💡 AI Suggestion:")
            print(response)
            
            return {
                'status': 'success',
                'suggestion': response
            }
        except Exception as e:
            print(f"\n✗ Error getting AI suggestion: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def get_system_status(self) -> Dict:
        """
        Get overall system status and statistics.
        
        Returns:
            Dictionary with system status
        """
        from datetime import timedelta
        
        # Get events for next 30 days
        events = self.calendar_agent.get_events_in_range(
            datetime.now(),
            datetime.now() + timedelta(days=30)
        )
        
        # Check for conflicts
        conflict_result = self.conflict_detector.check_for_conflicts(
            days_ahead=30,
            show_settings=False
        )
        
        return {
            'total_events_30_days': len(events),
            'conflicts_detected': len(conflict_result.get('conflicts', [])),
            'hard_conflicts': len(conflict_result.get('hard_conflicts', [])),
            'soft_conflicts': len(conflict_result.get('soft_conflicts', [])),
            'minimum_gap_setting': self.conflict_detector.minimum_gap_minutes,
            'agents_active': {
                'parser': True,
                'calendar': True,
                'change_manager': True,
                'conflict_detector': True
            }
        }


def main():
    """Test the Orchestrator Agent."""
    print("Testing Orchestrator Agent")
    
    # Initialize
    orchestrator = OrchestratorAgent()
    
    # Test: Get system status
    print("\n[Test] Getting system status...")
    status = orchestrator.get_system_status()
    
    print("\n📊 System Status:")
    print(f"  Events (next 30 days): {status['total_events_30_days']}")
    print(f"  Conflicts detected: {status['conflicts_detected']}")
    print(f"  Minimum gap setting: {status['minimum_gap_setting']} minutes")
    
    print("\n✓ Orchestrator test completed!")


if __name__ == "__main__":
    main()
