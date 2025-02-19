import requests
import time
import sys
from datetime import datetime
from bs4 import BeautifulSoup

# API credentials
INTERCOM_API_KEY = 'INTERCOM_API_KEY' # Found on Intercom developer hub
CHATWOOT_API_KEY = 'CHATWOOT_API_KEY' # Can NOT be a SuperAdmin account, has to be an admin account.
CHATWOOT_HOST = 'https://support.bluecherrydvr.com' # Just the base URL, script does the rest and will add paths
INBOX_ID = 2 # Update with your Chatwoot Inbox ID

def log(message):
    """Logs messages to the console."""
    print(f"[LOG]: {message}")

def strip_html(content):
    """Removes HTML tags from a given content string."""
    if content:
        soup = BeautifulSoup(content, 'html.parser')
        return soup.get_text()
    return ""

def fetch_intercom_conversation_by_id(conversation_id):
    """Fetches a conversation from Intercom API and handles pagination for conversation parts."""
    log(f"Fetching conversation {conversation_id} from Intercom...")

    url = f'https://api.intercom.io/conversations/{conversation_id}?include=contacts,conversation_parts'
    headers = {'Authorization': INTERCOM_API_KEY, 'Accept': 'application/json'}

    full_conversation = None
    all_parts = []  # Store all conversation parts (messages)

    while url:
        response = requests.get(url, headers=headers)
        log(f"Intercom response status: {response.status_code}")

        if response.status_code != 200:
            log(f"Failed to fetch conversation: {response.status_code}, {response.text}")
            return None

        data = response.json()

        if not full_conversation:
            full_conversation = data

        if 'conversation_parts' in data and 'conversation_parts' in data['conversation_parts']:
            all_parts.extend(data['conversation_parts']['conversation_parts'])

        url = data.get('conversation_parts', {}).get('pages', {}).get('next')

    if full_conversation:
        full_conversation['conversation_parts']['conversation_parts'] = all_parts

    return full_conversation

def create_chatwoot_conversation(email, name, conv):
    """Creates a Chatwoot conversation and imports messages from Intercom."""

    log(f"Checking for existing contact: {email}")
    search_url = f"{CHATWOOT_HOST}/api/v1/accounts/2/contacts/search?q={email}"
    headers = {'api_access_token': CHATWOOT_API_KEY}

    search_response = requests.get(search_url, headers=headers)

    contact_id = None

    if search_response.status_code == 200:
        search_data = search_response.json()
        if search_data.get("meta", {}).get("count", 0) > 0:
            contact_id = search_data["payload"][0]["id"]
            log(f"✅ Found existing contact {email} with ID {contact_id}.")
        else:
            log(f"⚠ No existing contact found for {email}. Attempting to create a new one.")
    else:
        log(f"❌ Failed to search for contact: {search_response.status_code}, {search_response.text}")
        return

    if not contact_id:
        contact_url = f"{CHATWOOT_HOST}/api/v1/accounts/2/contacts"
        data = {'name': name or 'Unknown User', 'email': email, 'inbox_id': INBOX_ID}

        for attempt in range(3):  # Retry up to 3 times for rate limits
            response = requests.post(contact_url, headers=headers, json=data)
            response_text = response.text  # Capture full response

            if response.status_code in [200, 201]:
                contact_data = response.json()

                # ✅ Correctly extract the contact ID from the "payload" section
                contact_id = contact_data.get("payload", {}).get("contact", {}).get("id")

                if contact_id:
                    log(f"✅ Successfully created new contact with ID {contact_id}.")
                    break
                else:
                    log(f"❌ Contact creation response did not return an ID. Full response: {response_text}")
                    return

            elif response.status_code == 422 and "Email has already been taken" in response_text:
                log(f"⚠ Contact already exists for {email}. Fetching existing contact.")
                search_response = requests.get(search_url, headers=headers)
                if search_response.status_code == 200:
                    search_data = search_response.json()
                    if search_data.get("meta", {}).get("count", 0) > 0:
                        contact_id = search_data["payload"][0]["id"]
                        log(f"✅ Retrieved existing contact ID {contact_id} after duplicate error.")
                        break
                log(f"❌ Failed to retrieve existing contact after duplicate error.")
                return

            elif response.status_code == 429:  # Too many requests (rate limit)
                log(f"⏳ Rate limit hit while creating contact {email}. Retrying in 5 seconds...")
                time.sleep(5)
            else:
                log(f"❌ Failed to create contact: {response.status_code}, Full response: {response_text}")
                return

    if not contact_id:
        log(f"❌ Contact creation failed, skipping conversation for {email}.")
        return

    conv_url = f"{CHATWOOT_HOST}/api/v1/accounts/2/conversations"
    conv_data = {
        'inbox_id': INBOX_ID,
        'contact_id': contact_id,
        'custom_attributes': {
            'imported_date': datetime.utcfromtimestamp(conv.get('created_at')).isoformat()
        }
    }
    conv_response = requests.post(conv_url, headers=headers, json=conv_data)

    if conv_response.status_code in [200, 201]:
        conversation_id = conv_response.json().get('id')
        log(f"✅ Created Chatwoot conversation: {conversation_id} for {email}")

        initial_message = strip_html(conv.get('source', {}).get('body', ''))
        if initial_message:
            msg_url = f"{CHATWOOT_HOST}/api/v1/accounts/2/conversations/{conversation_id}/messages"
            msg_data = {'content': initial_message, 'message_type': 'incoming'}
            msg_response = requests.post(msg_url, headers=headers, json=msg_data)
            log(f"📨 Initial message response: {msg_response.status_code}, {msg_response.text}")
        else:
            log(f"⚠ No initial message found for conversation {conversation_id}")

        for part in conv.get('conversation_parts', {}).get('conversation_parts', []):
            author_type = part['author']['type']
            message_type = 'incoming' if author_type in ['user', 'contact'] else 'outgoing'
            content = strip_html(part.get('body', ''))

            if not content:
                log(f"⚠ Skipping empty message from {part['author'].get('name', 'Unknown')}")
                continue

            log(f"📩 Sending message from {part['author'].get('name', 'Unknown')}: {content}")

            msg_url = f"{CHATWOOT_HOST}/api/v1/accounts/2/conversations/{conversation_id}/messages"
            msg_data = {'content': content, 'message_type': message_type}
            msg_response = requests.post(msg_url, headers=headers, json=msg_data)
            log(f"📨 Message response: {msg_response.status_code}, {msg_response.text}")

    else:
        log(f"❌ Failed to create conversation: {conv_response.status_code}, {conv_response.text}")

def main():
    """Main script execution to process Intercom conversations."""

    if len(sys.argv) != 3:
        log("❌ Error: Please provide start and end conversation IDs as arguments.")
        log("Usage: python script.py <start_id> <end_id>")
        sys.exit(1)

    start_id = int(sys.argv[1])
    end_id = int(sys.argv[2])

    for conversation_id in range(start_id, end_id + 1):
        conv = fetch_intercom_conversation_by_id(str(conversation_id))
        if not conv:
            continue

        email, name = conv['source']['author'].get('email'), conv['source']['author'].get('name', 'Unknown User')
        if email:
            log(f"Processing conversation with email: {email}, name: {name}")
            create_chatwoot_conversation(email, name, conv)
        else:
            log("❌ No valid contact found, skipping this conversation.")

        time.sleep(2)

if __name__ == "__main__":
    main()
