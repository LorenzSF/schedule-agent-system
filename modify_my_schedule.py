"""
Interactive script to modify your calendar events
"""

from agents.change_manager_agent import ChangeManagerAgent

def main():
    print("="*60)
    print("📅 CALENDAR MODIFICATION TOOL")
    print("="*60)
    print("\nThis tool allows you to modify your calendar using natural language.")
    print("\nExamples:")
    print("  • 'move Applied AI to next Monday at 10am'")
    print("  • 'cancel Neural Networks on Thursday'")
    print("  • 'change location of Machine Learning to Room 505'")
    print("  • 'reschedule AI and Society to 5pm'")
    print("\nType 'help' for more examples, 'quit' to exit")
    print("="*60)
    
    agent = ChangeManagerAgent()
    
    while True:
        try:
            print("\n" + "-"*60)
            command = input("🔧 What would you like to change? ").strip()
            
            if not command:
                continue
            
            if command.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break
            
            if command.lower() == 'help':
                print("\n📖 EXAMPLES:")
                print("  Move events:")
                print("    • 'move [event] to [day] at [time]'")
                print("    • 'reschedule [event] to tomorrow'")
                print("\n  Cancel events:")
                print("    • 'cancel [event]'")
                print("    • 'delete [event]'")
                print("\n  Modify details:")
                print("    • 'change location of [event] to [new location]'")
                print("    • 'update [event] location to [new location]'")
                continue
            
            # Process command
            result = agent.process_command(command)
            
            # Display result with formatting
            print("\n" + "="*60)
            status = result.get('status')
            
            if status == 'success':
                print("✅ SUCCESS!")
                print(f"   {result.get('message')}")
                
                if result.get('changes'):
                    print("\n📝 Changes:")
                    for key, value in result['changes'].items():
                        print(f"   • {key}: {value}")
                
                if result.get('event'):
                    event = result['event']
                    print(f"\n📅 Updated Event:")
                    print(f"   • Title: {event.get('summary')}")
                    if event.get('start', {}).get('dateTime'):
                        print(f"   • Time: {event['start']['dateTime']}")
                    if event.get('location'):
                        print(f"   • Location: {event.get('location')}")
            
            elif status == 'error':
                print("❌ ERROR")
                print(f"   {result.get('message')}")
                if result.get('details'):
                    print(f"   Details: {result.get('details')}")
            
            elif status == 'ambiguous':
                print("⚠️  MULTIPLE MATCHES FOUND")
                print(f"   {result.get('message')}\n")
                print("   Matching events:")
                for i, event in enumerate(result.get('events', []), 1):
                    start = event.get('start', {}).get('dateTime', 'Unknown')
                    print(f"   {i}. {event.get('summary')}")
                    print(f"      at {start}")
                print("\n   💡 Tip: Be more specific (add date, time, or location)")
            
            print("="*60)
        
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")


if __name__ == "__main__":
    main()