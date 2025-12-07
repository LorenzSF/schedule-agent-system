"""
Create your parsed schedule in Google Calendar with conflict checking
"""

from agents.parser_agent import ParserAgent
from agents.calendar_agent import CalendarAgent
from agents.conflict_detector_agent import ConflictDetectorAgent

def main():
    print("="*60)
    print("📅 SCHEDULE TO CALENDAR PIPELINE")
    print("="*60)
    
    # Step 1: Configure conflict detection
    print("\n[Configuration] Setting up conflict detection...")
    conflict_detector = ConflictDetectorAgent()
    
    # Step 2: Parse the schedule
    print("\n[Step 1] Parsing schedule from PDF...")
    parser = ParserAgent()
    events = parser.parse_from_file('tests/sample_schedules/my_schedule.pdf')
    
    if not events:
        print("✗ No events to create. Exiting.")
        return
    
    print(f"\n✓ Parsed {len(events)} events")
    print(parser.get_summary(events))
    
    # Step 3: Ask for confirmation
    print("\n" + "="*60)
    response = input(f"Create these {len(events)} events in Google Calendar? (yes/no): ")
    
    if response.lower() not in ['yes', 'y']:
        print("Cancelled.")
        return
    
    # Step 4: Create events with conflict checking
    print("\n[Step 2] Creating events in Google Calendar...")
    print("(Conflicts will be detected and you'll be asked for confirmation)")
    
    calendar = CalendarAgent()
    results = calendar.create_events_batch(
        events,
        check_duplicates=True,
        check_conflicts=True,
        ask_on_conflicts=True  # This will ask user on conflicts
    )
    
    # Step 5: Show final results
    print("\n" + "="*60)
    print("FINAL RESULTS")
    print("="*60)
    print(f"✓ Successfully created: {len(results['successful'])} events")
    print(f"⚠️  Skipped (duplicates/cancelled): {len(results['skipped'])} events")
    print(f"✗ Failed: {len(results['failed'])} events")
    
    if results['successful']:
        print("\n🎉 Check your Google Calendar!")
        print("Your schedule has been imported.")


if __name__ == "__main__":
    main()