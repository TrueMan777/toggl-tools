import requests
import os
import logging
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv

# Set up logging
logger = logging.getLogger(__name__)

class TogglApiClient:
    """
    Client for interacting with the Toggl API v9.
    """
    BASE_URL = "https://api.track.toggl.com/api/v9/"

    def __init__(self, api_key=None):
        """
        Initialize the Toggl API client.

        Args:
            api_key (str, optional): Toggl API key. If not provided, will try to load from environment.
        """
        # If api_key is explicitly provided, use it
        if api_key:
            self.api_key = api_key
            logger.debug("Using provided API key")
        else:
            # Otherwise, load from .env file, overriding any existing environment variables
            # Save the original environment variable if it exists
            original_api_key = os.environ.get("TOGGL_API_KEY")

            # Load from .env file (this will override environment variables)
            load_dotenv(override=True)

            # Get the API key from the environment (now from .env if it exists there)
            self.api_key = os.getenv("TOGGL_API_KEY")

            # If we got a different key from .env, log it
            if self.api_key != original_api_key:
                logger.debug("Using API key from .env file (overriding environment variable)")
            else:
                logger.debug("Using API key from environment variable")

        if not self.api_key:
            raise ValueError("Toggl API key is required. Set TOGGL_API_KEY environment variable or pass it directly.")

        self.auth = requests.auth.HTTPBasicAuth(self.api_key, "api_token")
        
        # Get workspace ID
        self.workspace_id = self._get_default_workspace_id()
        
        logger.debug("Toggl API client initialized")

    def _get_default_workspace_id(self):
        """
        Get the default workspace ID for the user.
        
        Returns:
            int: Default workspace ID
        """
        url = f"{self.BASE_URL}me"
        response = self._make_request("GET", url)
        if response and 'default_workspace_id' in response:
            logger.debug(f"Using default workspace ID: {response['default_workspace_id']}")
            return response['default_workspace_id']
        else:
            # Fallback to getting the first workspace
            url = f"{self.BASE_URL}workspaces"
            workspaces = self._make_request("GET", url)
            if workspaces and len(workspaces) > 0:
                logger.debug(f"Using first workspace ID: {workspaces[0]['id']}")
                return workspaces[0]['id']
            else:
                raise ValueError("Could not determine workspace ID")

    def get_time_entries(self, start_date, end_date):
        """
        Retrieve time entries for a specified date range.

        Args:
            start_date (datetime): Start date (inclusive)
            end_date (datetime): End date (inclusive)

        Returns:
            list: List of time entries
        """
        # Convert dates to UTC ISO format for the API
        start_date_utc = start_date.astimezone(pytz.UTC).isoformat().replace('+00:00', 'Z')
        end_date_utc = end_date.astimezone(pytz.UTC).isoformat().replace('+00:00', 'Z')

        url = f"{self.BASE_URL}me/time_entries"
        params = {
            "start_date": start_date_utc,
            "end_date": end_date_utc
        }

        logger.info(f"Retrieving time entries from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        response = self._make_request("GET", url, params=params)
        logger.info(f"Retrieved {len(response)} time entries")
        return response

    def create_time_entry(self, description, start_time, end_time, tags=None, project_id=None, billable=False):
        """
        Create a new time entry in Toggl.
        
        Args:
            description (str): Description of the time entry
            start_time (datetime): Start time of the entry
            end_time (datetime): End time of the entry
            tags (list): List of tags to apply to the entry
            project_id (int): Project ID to associate with the entry
            billable (bool): Whether the entry is billable
            
        Returns:
            dict: The created time entry data
        """
        logger.info(f"Creating time entry: {description}")
        
        # Calculate duration in seconds
        duration = int((end_time - start_time).total_seconds())
        
        # Format start time in ISO 8601 format
        start_str = start_time.astimezone(pytz.UTC).isoformat().replace('+00:00', 'Z')
        
        # Format end time in ISO 8601 format
        stop_str = end_time.astimezone(pytz.UTC).isoformat().replace('+00:00', 'Z')
        
        # Prepare the time entry data
        time_entry_data = {
            'created_with': 'toggl_overnight_splitter',
            'description': description,
            'duration': duration,
            'start': start_str,
            'stop': stop_str,
            'billable': billable,
            'wid': self.workspace_id  # Add workspace ID
        }
        
        # Add tags if provided
        if tags:
            time_entry_data['tags'] = tags
            
        # Add project_id if provided
        if project_id:
            time_entry_data['project_id'] = project_id
            
        logger.debug(f"Time entry data: {time_entry_data}")
        
        # Make the API request
        url = f"{self.BASE_URL}workspaces/{self.workspace_id}/time_entries"
        logger.debug(f"Making POST request to {url}")
        
        try:
            response = requests.post(
                url,
                json=time_entry_data,
                auth=self.auth
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            try:
                error_content = response.json()
                logger.error(f"HTTP Error: {e}, Response content: {error_content}")
            except:
                logger.error(f"HTTP Error: {e}, Could not parse response content")
            raise
        except Exception as e:
            logger.error(f"Error creating time entry: {e}")
            raise

    def update_time_entry(self, entry_id, entry_data):
        """
        Update an existing time entry.

        Args:
            entry_id (str): ID of the time entry to update
            entry_data (dict): Updated time entry data

        Returns:
            dict: Updated time entry
        """
        url = f"{self.BASE_URL}me/time_entries/{entry_id}"
        logger.info(f"Updating time entry {entry_id}: {entry_data.get('description', 'No description')}")
        response = self._make_request("PUT", url, json=entry_data)
        logger.info(f"Updated time entry {entry_id}")
        return response

    def delete_time_entry(self, entry_id):
        """
        Delete a time entry.

        Args:
            entry_id (str): ID of the time entry to delete

        Returns:
            bool: True if successful
        """
        url = f"{self.BASE_URL}workspaces/{self.workspace_id}/time_entries/{entry_id}"
        logger.info(f"Deleting time entry {entry_id}")
        self._make_request("DELETE", url)
        logger.info(f"Deleted time entry {entry_id}")
        return True

    def _make_request(self, method, url, **kwargs):
        """
        Make a request to the Toggl API with error handling and rate limiting.

        Args:
            method (str): HTTP method
            url (str): API endpoint URL
            **kwargs: Additional arguments to pass to requests

        Returns:
            dict or list: Response data

        Raises:
            requests.exceptions.HTTPError: If the request fails
        """
        try:
            logger.debug(f"Making {method} request to {url}")
            response = requests.request(method, url, auth=self.auth, **kwargs)
            response.raise_for_status()

            # Return None for successful DELETE requests (they don't return content)
            if method == "DELETE":
                return None

            # Return JSON response for other requests
            return response.json() if response.content else None

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                # Handle rate limiting
                retry_after = int(e.response.headers.get('Retry-After', 60))
                logger.warning(f"Rate limit exceeded. Retrying after {retry_after} seconds...")
                import time
                time.sleep(retry_after)
                return self._make_request(method, url, **kwargs)
            else:
                # Re-raise other HTTP errors
                logger.error(f"HTTP Error: {e}")
                raise
        except requests.exceptions.RequestException as e:
            # Handle connection errors
            logger.error(f"Request Error: {e}")
            raise