## Python script to convert Intercom conversations (and contacts) to Chatwoot
📢 Preface: The large majority of this code was AI-generated.  I studied the APIs on Postman, made changes to better suit an average import, worked around API limits.  Luckily I was able to snapshot my Chatwoot install and play around with different settings.

## 📌 Features

✅ Fetches conversations from Intercom \
✅ Creates or reuses contacts in Chatwoot \
✅ Imports all messages and replies \
✅ Handles duplicate contacts automatically \
✅ Retries failed API calls (Handles 429 Too Many Requests) \
✅ Command-line input for conversation range 


## 📢 This will send initial email notifications to users (and the Chatwoot assigned agent). I highly recommend disabling SMTP

## Configure emails[​](https://www.chatwoot.com/docs/self-hosted/configuration/environment-variables#configure-emails "Direct link to Configure emails")

For development, you don't need an email provider. Chatwoot uses the  [letter-opener](https://github.com/ryanb/letter_opener)  gem to test emails locally.  Leave SMTP settings blank in the .env file

----

# Installation

1. **Clone the Repository**

> git clone https://github.com/yourusername/intercom-to-chatwoot.git 
> cd intercom-to-chatwoot

2. **Install Dependencies**

> pip install requests bs4

# Obtain API Credentials

### **Get Intercom API Token**

1.  **Go to Intercom Developer Hub**: Intercom Developer Hub
    
2.  **Create a New App**
    
    -   Click **"New App"**
    -   Name it something like `"Intercom Exporter"`
    -   Select **"Internal Integration"**
    -   Click **"Create App"**
3.  **Generate API Key**
    
    -   Navigate to **"Authentication"**
    -   Copy your **Access Token** (e.g., `Bearer dG9rOmE...`)

### **Get Chatwoot API Token**

1.  Login to Chatwoot with a NON-SuperADMIN account
2.  Go to Profile → Access Token (At the bottom)
3.  Copy the Access Token

## **Configuration**

Edit the import.py to add your API keys:

    INTERCOM_API_KEY = 'Bearer YOUR_INTERCOM_API_KEY'
    CHATWOOT_API_KEY = 'YOUR_CHATWOOT_API_KEY'
    CHATWOOT_HOST = 'https://subdomain.yourchatwootdomain.com' # FQDM, do not include paths
    INBOX_ID = 6  # Update with your Chatwoot Inbox ID`

## **Usage**

Run the script with a **Intercom conversation ID range**:

    python script.py <start_id> <end_id>

### **Example**

`python script.py 1 50`

This will **import conversations from Intercom with IDs 1 to 50**.

### Example output

    [LOG]: Fetching conversation 261 from Intercom...
    [LOG]: Intercom response status: 200
    [LOG]: Processing conversation with email: [REDACTED], name: [REDACTED]
    [LOG]: Checking for existing contact: [REDACTED]
    [LOG]: ✅ Found existing contact [REDACTED] with ID 115.
    [LOG]: ✅ Created Chatwoot conversation: 397 for [REDACTED]
    [LOG]: 📨 Initial message response: 200, {"id":3112,"content":"[REDACTED]","inbox_id":6,"conversation_id":397,"message_type":0,"content_type":"text","status":"sent","content_attributes":{},"created_at":1739979099,"private":false,"source_id":null,"sender":{"additional_attributes":{},"custom_attributes":{},"email":"[REDACTED]","id":115,"identifier":null,"name":"[REDACTED]","phone_number":null,"thumbnail":"","type":"contact"}}
    [LOG]: ⚠ Skipping empty message from Fin
    [LOG]: 📩 Sending message from Curtis Hall: Does this import script work?
    [LOG]: 📨 Message response: 200, {"id":3113,"content":"Intercom to Chatwoot script,"inbox_id":6,"conversation_id":397,"message_type":1,"content_type":"text","status":"sent","content_attributes":{},"created_at":1739979099,"private":false,"source_id":null,"sender":{"id":3,"name":"API Import","available_name":"API Import","avatar_url":"","type":"user","availability_status":"offline","thumbnail":""}}
    [LOG]: 📩 Sending message from [REDACTED]: [REDACTED]
    [LOG]: 📨 Message response: 200, {"id":3114,"content":"[REDACTED]","inbox_id":6,"conversation_id":397,"message_type":0,"content_type":"text","status":"sent","content_attributes":{},"created_at":1739979099,"private":false,"source_id":null,"sender":{"additional_attributes":{},"custom_attributes":{},"email":"[REDACTED]","id":115,"identifier":null,"name":"[REDACTED]","phone_number":null,"thumbnail":"","type":"contact"}}
    [LOG]: 📩 Sending message from Curtis Hall: Feel free to post pull requests.  You can download the latest here: [https://github.com/bluecherrydvr/unity/releases/tag/bleeding_edge](https://github.com/curtishall/intercom_to_chatwoot)
    [LOG]: 📨 Message response: 200, {"id":3115,"content":"Thank you","inbox_id":6,"conversation_id":397,"message_type":1,"content_type":"text","status":"sent","content_attributes":{},"created_at":1739979099,"private":false,"source_id":null,"sender":{"id":3,"name":"API Import","available_name":"API Import","avatar_url":"","type":"user","availability_status":"offline","thumbnail":""}}
    [LOG]: ⚠ Skipping empty message from Curtis Hall

## **🔍Debugging**

If something goes wrong:

-   **Check the logs** printed by the script
-   If contacts **fail to create**, ensure the **API key has write permissions**
-   If rate limits (`429 Too Many Requests`) are hit, the script **automatically retries**
-   If needed, **rerun the script for missing conversations**


## **💡 Notes**

-   **Existing contacts are reused** to prevent duplicates
-   The script **waits 2 seconds** between API calls to avoid rate limits
-   Only **valid conversations** (with email & messages) are imported
-   The **imported_date** field is added to each conversation in Chatwoot

## Contributing

Pull requests are welcome! I probably won't be able to test once our Intercom account is closed
