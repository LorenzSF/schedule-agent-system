"""
Main Interface for Schedule Agent System
Complete CLI application with all features integrated.
"""

from pathlib import Path
from agents.orchestrator_agent import OrchestratorAgent
from datetime import datetime


def print_header():
    """Print application header."""
    print("\n" + "="*60)
    print("        📅 SCHEDULE AGENT SYSTEM")
    print("    AI-Powered Calendar Management")
    print("="*60)


def print_menu():
    """Print main menu."""
    print("\n" + "-"*60)
    print("MAIN MENU")
    print("-"*60)
    print("1. 📥 Import schedule from PDF/image")
    print("2. ✏️  Modify calendar event")
    print("3. 🔍 Check for conflicts")
    print("4. 📊 View system status")
    print("5. 💡 Ask AI for scheduling advice")
    print("6. ⚙️  Change settings")
    print("7. ❌ Exit")
    print("-"*60)


def import_schedule(orchestrator: OrchestratorAgent):
    """Handle schedule import workflow."""
    print("\n" + "="*60)
    print("📥 IMPORT SCHEDULE")
    print("="*60)
    
    # Ask for file path
    print("\nEnter the path to your schedule file:")
    print("(PDF or image - JPG, PNG, etc.)")
    print("Example: tests/sample_schedules/my_schedule.pdf")
    
    file_path = input("\nFile path: ").strip()
    
    # Remove quotes if user added them
    file_path = file_path.strip('"').strip("'")
    
    if not Path(file_path).exists():
        print(f"\n❌ File not found: {file_path}")
        return
    
    # Ask about conflict checking
    check_conflicts = input("\nCheck for scheduling conflicts? (yes/no) [yes]: ").strip().lower()
    check_conflicts = check_conflicts in ['', 'yes', 'y']
    
    # Import schedule
    result = orchestrator.import_schedule_from_file(
        file_path,
        check_conflicts=check_conflicts,
        ask_on_conflicts=True
    )
    
    # Show results
    print("\n" + "="*60)
    print("IMPORT RESULTS")
    print("="*60)
    
    if result['status'] == 'success':
        print(f"✅ Successfully imported {result['events_created']} events!")
        if result['events_skipped'] > 0:
            print(f"⚠️  Skipped {result['events_skipped']} events (duplicates or cancelled)")
        if result['events_failed'] > 0:
            print(f"❌ Failed to import {result['events_failed']} events")
    elif result['status'] == 'cancelled':
        print("❌ Import cancelled by user")
    else:
        print(f"❌ Import failed: {result['message']}")
    
    input("\nPress Enter to continue...")


def modify_event(orchestrator: OrchestratorAgent):
    """Handle event modification workflow."""
    print("\n" + "="*60)
    print("✏️  MODIFY EVENT")
    print("="*60)
    
    print("\nExamples of commands:")
    print("  • 'move Machine Learning to Friday at 2pm'")
    print("  • 'cancel Neural Networks on Thursday'")
    print("  • 'change location of Applied AI to Room 505'")
    print("  • 'reschedule AI and Society to next week'")
    
    command = input("\nEnter modification command: ").strip()
    
    if not command:
        print("❌ No command entered")
        return
    
    result = orchestrator.modify_event(command)
    
    # Show results
    print("\n" + "="*60)
    print("MODIFICATION RESULTS")
    print("="*60)
    
    if result['status'] == 'success':
        print(f"✅ {result['message']}")
        if result.get('changes'):
            print("\n📝 Changes made:")
            for key, value in result['changes'].items():
                print(f"  • {key}: {value}")
    elif result['status'] == 'ambiguous':
        print(f"⚠️  {result['message']}")
        print("\nMatching events found:")
        for i, event in enumerate(result.get('events', []), 1):
            start = event.get('start', {}).get('dateTime', 'Unknown')
            print(f"  {i}. {event.get('summary')} at {start}")
        print("\n💡 Tip: Be more specific in your command")
    else:
        print(f"❌ {result['message']}")
        if result.get('details'):
            print(f"Details: {result['details']}")
    
    input("\nPress Enter to continue...")


def check_conflicts(orchestrator: OrchestratorAgent):
    """Handle conflict checking workflow."""
    print("\n" + "="*60)
    print("🔍 CHECK FOR CONFLICTS")
    print("="*60)
    
    print("\nHow many days ahead would you like to check?")
    print("  1. Next 7 days (1 week)")
    print("  2. Next 14 days (2 weeks)")
    print("  3. Next 30 days (1 month)")
    print("  4. Custom range")
    
    choice = input("\nSelect option (1-4): ").strip()
    
    days_ahead_map = {
        '1': 7,
        '2': 14,
        '3': 30
    }
    
    if choice in days_ahead_map:
        days_ahead = days_ahead_map[choice]
    elif choice == '4':
        try:
            days_ahead = int(input("Enter number of days: "))
        except ValueError:
            print("❌ Invalid number")
            return
    else:
        print("❌ Invalid option")
        return
    
    result = orchestrator.check_schedule_conflicts(days_ahead=days_ahead)
    
    input("\nPress Enter to continue...")


def view_status(orchestrator: OrchestratorAgent):
    """Display system status."""
    print("\n" + "="*60)
    print("📊 SYSTEM STATUS")
    print("="*60)
    
    status = orchestrator.get_system_status()
    
    print("\n📅 Calendar Statistics:")
    print(f"  • Events (next 30 days): {status['total_events_30_days']}")
    print(f"  • Total conflicts detected: {status['conflicts_detected']}")
    print(f"    - Hard conflicts (overlaps): {status['hard_conflicts']}")
    print(f"    - Soft conflicts (tight schedules): {status['soft_conflicts']}")
    
    print("\n⚙️  Current Settings:")
    print(f"  • Minimum gap between events: {status['minimum_gap_setting']} minutes")
    
    print("\n🤖 Agent Status:")
    for agent, active in status['agents_active'].items():
        status_icon = "✅" if active else "❌"
        print(f"  {status_icon} {agent.replace('_', ' ').title()}")
    
    input("\nPress Enter to continue...")


def ask_ai_advice(orchestrator: OrchestratorAgent):
    """Get AI scheduling advice."""
    print("\n" + "="*60)
    print("💡 AI SCHEDULING ADVICE")
    print("="*60)
    
    print("\nAsk me anything about your schedule!")
    print("Examples:")
    print("  • 'When is the best time to add a 2-hour study session?'")
    print("  • 'Do I have any free time on Thursday?'")
    print("  • 'Is my schedule too packed this week?'")
    print("  • 'Suggest some time slots for a team meeting'")
    
    query = input("\nYour question: ").strip()
    
    if not query:
        print("❌ No question entered")
        return
    
    orchestrator.intelligent_schedule_suggestion(query)
    
    input("\nPress Enter to continue...")


def change_settings(orchestrator: OrchestratorAgent):
    """Change system settings."""
    print("\n" + "="*60)
    print("⚙️  SETTINGS")
    print("="*60)
    
    print("\nCurrent settings:")
    print(f"  • Minimum gap between events: {orchestrator.conflict_detector.minimum_gap_minutes} minutes")
    
    print("\nWhat would you like to change?")
    print("  1. Minimum gap between events")
    print("  2. Back to main menu")
    
    choice = input("\nSelect option: ").strip()
    
    if choice == '1':
        print("\nEnter new minimum gap in minutes:")
        print("(Current: {} minutes)".format(orchestrator.conflict_detector.minimum_gap_minutes))
        
        try:
            new_gap = int(input("New gap: "))
            if new_gap < 0:
                print("❌ Gap must be positive")
                return
            
            orchestrator.conflict_detector.set_minimum_gap(new_gap)
            print(f"\n✅ Minimum gap updated to {new_gap} minutes")
        except ValueError:
            print("❌ Invalid number")
    
    input("\nPress Enter to continue...")


def main():
    """Main application loop."""
    print_header()
    
    # Initialize orchestrator
    try:
        orchestrator = OrchestratorAgent()
    except Exception as e:
        print(f"\n❌ Failed to initialize system: {e}")
        return
    
    # Main loop
    while True:
        print_menu()
        choice = input("\nSelect option (1-7): ").strip()
        
        try:
            if choice == '1':
                import_schedule(orchestrator)
            elif choice == '2':
                modify_event(orchestrator)
            elif choice == '3':
                check_conflicts(orchestrator)
            elif choice == '4':
                view_status(orchestrator)
            elif choice == '5':
                ask_ai_advice(orchestrator)
            elif choice == '6':
                change_settings(orchestrator)
            elif choice == '7':
                print("\n👋 Thank you for using Schedule Agent System!")
                print("Goodbye!\n")
                break
            else:
                print("\n❌ Invalid option. Please select 1-7.")
                input("Press Enter to continue...")
        
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ An error occurred: {e}")
            print("Please try again.")
            input("Press Enter to continue...")


if __name__ == "__main__":
    main()