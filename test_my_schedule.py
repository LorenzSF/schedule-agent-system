"""
Test script to parse your own schedule PDF/image
"""

from agents.parser_agent import ParserAgent

def main():
    # Initialize the Parser Agent
    print("Initializing Parser Agent...")
    agent = ParserAgent()
    
    # Parse your schedule file
    file_path = 'tests/sample_schedules/my_schedule.pdf'
    
    print(f"\nParsing file: {file_path}")
    events = agent.parse_from_file(file_path)
    
    # Display the summary
    print("\n" + "="*60)
    print("PARSED SCHEDULE SUMMARY")
    print("="*60)
    print(agent.get_summary(events))
    
    # Display raw event data (useful for debugging)
    print("\n" + "="*60)
    print("RAW EVENT DATA")
    print("="*60)
    import json
    print(json.dumps(events, indent=2))
    
    print(f"\n✓ Successfully parsed {len(events)} events!")


if __name__ == "__main__":
    main()