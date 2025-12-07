"""
Test script to demonstrate screenshot import capability
"""

from agents.parser_agent import ParserAgent

def main():
    print("="*60)
    print("SCREENSHOT IMPORT TEST")
    print("="*60)
    
    print("\nThis test demonstrates that the system can import")
    print("schedules from SCREENSHOTS (PNG, JPG), not just PDFs!")
    
    # Initialize parser
    print("\nInitializing Parser Agent...")
    parser = ParserAgent()
    
    # Test with screenshot
    print("\nTesting with screenshot file...")
    print("Place a screenshot of your schedule in tests/sample_schedules/")
    print("Name it 'schedule_screenshot.png' or update the path below\n")
    
    file_path = input("Enter path to screenshot [tests/sample_schedules/schedule_screenshot.png]: ").strip()
    
    if not file_path:
        file_path = "tests/sample_schedules/schedule_screenshot.png"
    
    try:
        events = parser.parse_from_file(file_path)
        
        if events:
            print(f"\n✅ SUCCESS! Parsed {len(events)} events from screenshot!")
            print("\nSummary:")
            print(parser.get_summary(events))
        else:
            print("\n❌ No events could be parsed from the screenshot")
    
    except FileNotFoundError:
        print(f"\n❌ File not found: {file_path}")
        print("Please place a schedule screenshot in the tests/sample_schedules/ folder")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()