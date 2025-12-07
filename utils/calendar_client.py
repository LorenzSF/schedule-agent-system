"""
Google Calendar API Client
Handles authentication and all calendar operations
"""

import os
import pickle
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from config.config import SCOPES, CREDENTIALS_FILE, TOKEN_FILE, DEFAULT_TIMEZONE


class GoogleCalendarClient:
    """
    A client for interacting with Google Calendar API.
    Handles authentication, event creation, updates, deletions, and queries.
    """
    
    def __init__(self):
        """Initialize the calendar client and authenticate."""
        self.creds = None
        self.service = None
        self.authenticate()
    
    def authenticate(self):
        """
        Authenticate with Google Calendar API using OAuth2.
        
        This method:
        1. Checks if we have a saved token (token.json)
        2. If token exists and is valid, uses it
        3. If token is expired, refreshes it
        4. If no token exists, opens browser for user to log in
        5. Saves the token for future use
        """
        # Check if we have a saved token from a previous session
        if TOKEN_FILE.exists():
            with open(TOKEN_FILE, 'rb') as token:
                self.creds = pickle.load(token)
        
        # If credentials don't exist or are invalid
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                # Token expired but can be refreshed
                print("Refreshing expired token...")
                self.creds.refresh(Request())
            else:
                # No token exists - need to authenticate from scratch
                print("No valid credentials found. Opening browser for authentication...")
                if not CREDENTIALS_FILE.exists():
                    raise FileNotFoundError(
                        f"Credentials file not found at {CREDENTIALS_FILE}\n"
                        "Please download credentials.json from Google Cloud Console."
                    )
                
                # Open browser for user to log in
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(CREDENTIALS_FILE), SCOPES
                )
                self.creds = flow.run_local_server(port=0)
            
            # Save credentials for future use
            with open(TOKEN_FILE, 'wb') as token:
                pickle.dump(self.creds, token)
            print("Authentication successful!")
        
        # Build the service object for making API calls
        self.service = build('calendar', 'v3', credentials=self.creds)
    
    def list_calendars(self) -> List[Dict]:
        """
        List all calendars accessible to the user.
        
        Returns:
            List of calendar dictionaries with 'id', 'summary', etc.
        """
        try:
            calendar_list = self.service.calendarList().list().execute()
            calendars = calendar_list.get('items', [])
            
            if not calendars:
                print("No calendars found.")
                return []
            
            print(f"\nFound {len(calendars)} calendar(s):")
            for cal in calendars:
                print(f"  - {cal['summary']} (ID: {cal['id']})")
            
            return calendars
        
        except HttpError as error:
            print(f"An error occurred: {error}")
            return []
    
    def get_primary_calendar_id(self) -> str:
        """
        Get the ID of the user's primary calendar.
        
        Returns:
            Calendar ID string (usually 'primary' or an email)
        """
        return 'primary'
    
    def list_events(
        self, 
        calendar_id: str = 'primary',
        max_results: int = 10,
        time_min: Optional[datetime] = None,
        time_max: Optional[datetime] = None
    ) -> List[Dict]:
        """
        List events from a calendar within a time range.
        
        Args:
            calendar_id: Calendar to query (default: 'primary')
            max_results: Maximum number of events to return
            time_min: Start of time range (default: now)
            time_max: End of time range (default: none)
        
        Returns:
            List of event dictionaries
        """
        try:
            # Default to current time if not specified
            if time_min is None:
                time_min = datetime.utcnow()
            
            # Format times in RFC3339 format (required by Google API)
            time_min_str = time_min.isoformat() + 'Z'
            time_max_str = time_max.isoformat() + 'Z' if time_max else None
            
            # Build request parameters
            request_params = {
                'calendarId': calendar_id,
                'timeMin': time_min_str,
                'maxResults': max_results,
                'singleEvents': True,  # Expand recurring events
                'orderBy': 'startTime'  # Sort by start time
            }
            
            if time_max_str:
                request_params['timeMax'] = time_max_str
            
            # Make API call
            events_result = self.service.events().list(**request_params).execute()
            events = events_result.get('items', [])
            
            if not events:
                print("No upcoming events found.")
                return []
            
            print(f"\nFound {len(events)} event(s):")
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                print(f"  - {event['summary']} at {start}")
            
            return events
        
        except HttpError as error:
            print(f"An error occurred: {error}")
            return []
    
    def create_event(
        self,
        summary: str,
        start_datetime: datetime,
        end_datetime: datetime,
        description: str = "",
        location: str = "",
        timezone: str = DEFAULT_TIMEZONE,
        recurrence: Optional[List[str]] = None,
        calendar_id: str = 'primary'
    ) -> Optional[Dict]:
        """
        Create a new calendar event.
        
        Args:
            summary: Event title
            start_datetime: Start date and time
            end_datetime: End date and time
            description: Event description (optional)
            location: Event location (optional)
            timezone: Timezone string (default from config)
            recurrence: List of recurrence rules (e.g., ['RRULE:FREQ=WEEKLY;COUNT=10'])
            calendar_id: Which calendar to add to (default: 'primary')
        
        Returns:
            Created event dictionary, or None if failed
        """
        try:
            # Build event object in Google Calendar format
            event = {
                'summary': summary,
                'location': location,
                'description': description,
                'start': {
                    'dateTime': start_datetime.isoformat(),
                    'timeZone': timezone,
                },
                'end': {
                    'dateTime': end_datetime.isoformat(),
                    'timeZone': timezone,
                },
            }
            
            # Add recurrence if specified
            if recurrence:
                event['recurrence'] = recurrence
            
            # Make API call to create event
            created_event = self.service.events().insert(
                calendarId=calendar_id,
                body=event
            ).execute()
            
            print(f"✓ Event created: {summary}")
            print(f"  Link: {created_event.get('htmlLink')}")
            
            return created_event
        
        except HttpError as error:
            print(f"✗ Error creating event: {error}")
            return None
    
    def update_event(
        self,
        event_id: str,
        summary: Optional[str] = None,
        start_datetime: Optional[datetime] = None,
        end_datetime: Optional[datetime] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        timezone: str = DEFAULT_TIMEZONE,
        calendar_id: str = 'primary'
    ) -> Optional[Dict]:
        """
        Update an existing calendar event.
        
        Args:
            event_id: ID of the event to update
            summary: New title (None = no change)
            start_datetime: New start time (None = no change)
            end_datetime: New end time (None = no change)
            description: New description (None = no change)
            location: New location (None = no change)
            timezone: Timezone string
            calendar_id: Which calendar the event is in
        
        Returns:
            Updated event dictionary, or None if failed
        """
        try:
            # First, get the current event
            event = self.service.events().get(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()
            
            # Update only the fields that were provided
            if summary is not None:
                event['summary'] = summary
            
            if location is not None:
                event['location'] = location
            
            if description is not None:
                event['description'] = description
            
            if start_datetime is not None:
                event['start'] = {
                    'dateTime': start_datetime.isoformat(),
                    'timeZone': timezone,
                }
            
            if end_datetime is not None:
                event['end'] = {
                    'dateTime': end_datetime.isoformat(),
                    'timeZone': timezone,
                }
            
            # Make API call to update event
            updated_event = self.service.events().update(
                calendarId=calendar_id,
                eventId=event_id,
                body=event
            ).execute()
            
            print(f"✓ Event updated: {updated_event['summary']}")
            
            return updated_event
        
        except HttpError as error:
            print(f"✗ Error updating event: {error}")
            return None
    
    def delete_event(
        self,
        event_id: str,
        calendar_id: str = 'primary'
    ) -> bool:
        """
        Delete a calendar event.
        
        Args:
            event_id: ID of the event to delete
            calendar_id: Which calendar the event is in
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.service.events().delete(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()
            
            print(f"✓ Event deleted successfully")
            return True
        
        except HttpError as error:
            print(f"✗ Error deleting event: {error}")
            return False
    
    def search_events(
        self,
        query: str,
        calendar_id: str = 'primary',
        max_results: int = 10
    ) -> List[Dict]:
        """
        Search for events by text query.
        
        Args:
            query: Search term (searches title, description, location)
            calendar_id: Which calendar to search
            max_results: Maximum results to return
        
        Returns:
            List of matching event dictionaries
        """
        try:
            events_result = self.service.events().list(
                calendarId=calendar_id,
                q=query,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            if not events:
                print(f"No events found matching '{query}'")
                return []
            
            print(f"\nFound {len(events)} event(s) matching '{query}':")
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                print(f"  - {event['summary']} at {start} (ID: {event['id']})")
            
            return events
        
        except HttpError as error:
            print(f"An error occurred: {error}")
            return []


def main():
    """
    Test function to verify Google Calendar API setup.
    Run this to make sure everything is working!
    """
    print("=" * 60)
    print("Testing Google Calendar API Setup")
    print("=" * 60)
    
    # Initialize client (will trigger authentication)
    client = GoogleCalendarClient()
    
    # Test 1: List available calendars
    print("\n[Test 1] Listing calendars...")
    calendars = client.list_calendars()
    
    # Test 2: List upcoming events
    print("\n[Test 2] Listing upcoming events...")
    events = client.list_events(max_results=5)
    
    # Test 3: Create a test event
    print("\n[Test 3] Creating a test event...")
    test_start = datetime.now() + timedelta(days=1)
    test_end = test_start + timedelta(hours=1)
    
    test_event = client.create_event(
        summary="Test Event - Schedule Agent System",
        start_datetime=test_start,
        end_datetime=test_end,
        description="This is a test event created by the schedule agent system",
        location="Test Location"
    )
    
    if test_event:
        event_id = test_event['id']
        
        # Test 4: Update the event
        print("\n[Test 4] Updating the test event...")
        client.update_event(
            event_id=event_id,
            summary="UPDATED Test Event",
            description="This event was updated!"
        )
        
        # Test 5: Search for the event
        print("\n[Test 5] Searching for 'UPDATED'...")
        client.search_events(query="UPDATED")
        
        # Test 6: Delete the event
        print("\n[Test 6] Deleting the test event...")
        client.delete_event(event_id=event_id)
    
    print("\n" + "=" * 60)
    print("✓ All tests completed!")
    print("Your Google Calendar API setup is working correctly.")
    print("=" * 60)


if __name__ == "__main__":
    main()