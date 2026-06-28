import os
import json
import base64
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import httpx

SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.labels",
    "https://www.googleapis.com/auth/gmail.settings.basic",
]

# Simple .env parser to avoid importing config.py
def load_env():
    env_vars = {}
    env_path = Path(".env")
    if env_path.exists():
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env_vars[k.strip()] = v.strip()
    return env_vars

def get_gmail_service(env):
    token_path = Path("token.json")
    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            credentials_path = Path("credentials.json")
            if credentials_path.exists():
                print(f"Loading Gmail OAuth client config from file: {credentials_path}")
                flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
            else:
                print("credentials.json not found. Falling back to .env variables.")
                client_config = {
                    "installed": {
                        "client_id": env.get("GMAIL_CLIENT_ID"),
                        "client_secret": env.get("GMAIL_CLIENT_SECRET"),
                        "project_id": env.get("GMAIL_PROJECT_ID"),
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    }
                }
                flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, "w") as token_file:
            token_file.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)

def load_processed_senders():
    path = Path("sandbox_processed_senders.json")
    if path.exists():
        with open(path, "r") as f:
            try:
                return json.load(f)
            except Exception:
                return []
    return []

def save_processed_sender(email):
    path = Path("sandbox_processed_senders.json")
    senders = load_processed_senders()
    if email not in senders:
        senders.append(email)
        with open(path, "w") as f:
            json.dump(senders, f, indent=4)
        print(f"Saved {email} to sandbox_processed_senders.json")

def find_unseen_sender(service, processed_list):
    print("Listing latest inbox messages...")
    results = service.users().messages().list(userId="me", q="label:INBOX", maxResults=20).execute()
    messages = results.get("messages", [])
    
    for msg in messages:
        msg_id = msg["id"]
        detail = service.users().messages().get(userId="me", id=msg_id, format="metadata", metadataHeaders=["From"]).execute()
        headers = detail.get("payload", {}).get("headers", [])
        from_val = ""
        for h in headers:
            if h.get("name", "").lower() == "from":
                from_val = h.get("value", "")
                break
        
        if not from_val:
            continue
        
        # Extract email address
        # format is: "Name <email@address.com>" or just "email@address.com"
        email_addr = from_val
        if "<" in from_val and ">" in from_val:
            email_addr = from_val.split("<")[1].split(">")[0]
            email_name = from_val.split("<")[0].strip()
        email_addr = email_addr.strip().lower()
        
        if email_addr not in processed_list:
            print(f"Found unseen sender: {email_addr} ({email_name})")
            return email_addr, from_val
        else:
            print(f"Sender already processed: {email_addr}")
            
    return None, None

def fetch_sender_history(service, email_addr):
    print(f"Fetching history for {email_addr}...")
    results = service.users().messages().list(userId="me", q=f"from:{email_addr}", maxResults=5).execute()
    messages = results.get("messages", [])
    
    history = []
    for msg in messages:
        detail = service.service.users().messages().get(userId="me", id=msg["id"], format="full").execute() if hasattr(service, "service") else service.users().messages().get(userId="me", id=msg["id"], format="full").execute()
        headers = detail.get("payload", {}).get("headers", [])
        subject = ""
        for h in headers:
            if h.get("name", "").lower() == "subject":
                subject = h.get("value", "")
                break
        
        # Simple body extract
        body = ""
        payload = detail.get("payload", {})
        parts = payload.get("parts", [])
        if parts:
            for part in parts:
                if part.get("mimeType") == "text/plain":
                    data = part.get("body", {}).get("data", "")
                    if data:
                        body = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
                        break
        else:
            data = payload.get("body", {}).get("data", "")
            if data:
                body = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
                
        history.append({
            "subject": subject,
            "body": body[:200]  # truncate
        })
    return history

def classify_sender(env, email_addr, history):
    print(f"Classifying sender {email_addr} using Ollama...")
    ollama_url = env.get("OLLAMA_BASE_URL", "http://localhost:11434")
    model = env.get("OLLAMA_MODEL", "qwen2.5:7b")
    
    history_str = ""
    for idx, item in enumerate(history, 1):
        history_str += f"Email {idx}:\nSubject: {item['subject']}\nBody: {item['body']}\n\n"
        
    system_prompt = (
        "You are an email analysis bot. Analyze the sender's history and decide if the sender is a Newsletter "
        "(automatic promotions, newsletters, updates, subscriptions) or Transactional/Personal (specific receipts, "
        "personal replies, critical single updates, passwords).\n"
        "Return a JSON object conforming exactly to this schema:\n"
        "{\n"
        "  \"is_newsletter\": boolean\n"
        "}"
    )
    
    user_prompt = f"Sender: {email_addr}\nHistory:\n{history_str}"
    
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "format": {
            "type": "object",
            "properties": {
                "is_newsletter": {"type": "boolean"}
            },
            "required": ["is_newsletter"]
        },
        "stream": False,
        "options": {
            "temperature": 0.0
        }
    }
    
    try:
        r = httpx.post(f"{ollama_url}/api/chat", json=payload, timeout=30.0)
        r.raise_for_status()
        data = r.json()
        content = data["message"]["content"]
        result = json.loads(content)
        is_newsletter = result.get("is_newsletter", False)
        print(f"LLM Decision: is_newsletter = {is_newsletter} (raw output: {content})")
        return is_newsletter
    except Exception as e:
        print(f"Error calling LLM: {e}")
        return False

def create_gmail_filter(service, email_addr):
    print(f"Creating Gmail filter for {email_addr} to trash future messages...")
    filter_body = {
        "criteria": {"from": email_addr},
        "action": {
            "removeLabelIds": ["UNREAD", "INBOX"],
            "addLabelIds": ["TRASH"]
        }
    }
    try:
        res = service.users().settings().filters().create(userId="me", body=filter_body).execute()
        print(f"Filter created: {res}")
    except Exception as e:
        print(f"Error creating filter: {e}")

def find_unsubscribe_link(body: str) -> str | None:
    import re
    # Find all URLs in the body
    urls = re.findall(r'https?://[^\s<>"]+', body)
    
    # First pass: check if any URL itself contains unsubscribe-like keywords
    unsub_url_keywords = ["unsubscribe", "unsub", "optout", "opt-out", "descadastrar", "desinscrever", "cancelar"]
    for url in urls:
        url_lower = url.lower()
        if any(kw in url_lower for kw in unsub_url_keywords):
            return url
            
    # Second pass: check if body contains unsubscribe keywords, and if so, check if we have any URL
    body_lower = body.lower()
    body_keywords = ["unsubscribe", "opt out", "opt-out", "desinscrever", "descadastrar", "cancelar inscrição", "cancelar inscricao"]
    if any(kw in body_lower for kw in body_keywords) and urls:
        # Return the last URL, as unsubscribe links are usually at the bottom of the email
        return urls[-1]
        
    return None

def main():
    print("Starting Sandbox Spike...")
    env = load_env()
    service = get_gmail_service(env)
    
    processed_list = load_processed_senders()
    print(f"Loaded processed list: {processed_list}")
    
    email_addr, raw_from = find_unseen_sender(service, processed_list)
    if not email_addr:
        print("No unseen senders found in latest messages.")
        return
        
    history = fetch_sender_history(service, email_addr)
    print(f"Fetched {len(history)} messages from sender history.")
    
    # Check for unsubscribe links in the history
    unsub_link = None
    for email in history:
        link = find_unsubscribe_link(email["body"])
        if link:
            unsub_link = link
            break

    is_newsletter = False
    if unsub_link:
        print(f"Unsubscribe link found: {unsub_link}")
        try:
            print("Attempting to unsubscribe by opening link...")
            # Make a GET request to the unsubscribe link
            r = httpx.get(unsub_link, timeout=10.0, follow_redirects=True)
            print(f"Unsubscribe request status code: {r.status_code}")
        except Exception as e:
            print(f"Failed to request unsubscribe link: {e}")
        
        # Bypass LLM: mark as newsletter directly
        is_newsletter = True
    else:
        is_newsletter = classify_sender(env, email_addr, history)
    
    if is_newsletter:
        create_gmail_filter(service, email_addr)
    else:
        print(f"Sender {email_addr} is transactional. No filter created.")
        
    save_processed_sender(email_addr)
    print("Sandbox Spike completed successfully!")

if __name__ == "__main__":
    main()
