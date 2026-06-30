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
                data = json.load(f)
                if isinstance(data, list):
                    # Convert list format to dict for backwards compatibility
                    return {email: "newsletter" for email in data}
                elif isinstance(data, dict):
                    return data
            except Exception:
                return {}
    return {}

def save_processed_sender(email, category):
    path = Path("sandbox_processed_senders.json")
    senders = load_processed_senders()
    if email not in senders:
        senders[email] = category
        with open(path, "w") as f:
            json.dump(senders, f, indent=4)
        print(f"Saved {email} ({category}) to sandbox_processed_senders.json")

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

def extract_body(payload: dict) -> str:
    # Helper to recursively find parts by MIME type
    def find_parts(part: dict, target_mime: str, results: list):
        mime_type = part.get("mimeType", "")
        if mime_type == target_mime:
            data = part.get("body", {}).get("data", "")
            if data:
                try:
                    import base64
                    decoded = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
                    results.append(decoded)
                except Exception:
                    pass
        parts = part.get("parts", [])
        for p in parts:
            find_parts(p, target_mime, results)

    # 1. Try to find all text/plain and text/html parts
    parts_list = []
    find_parts(payload, "text/plain", parts_list)
    find_parts(payload, "text/html", parts_list)
    if parts_list:
        return "\n".join(parts_list)
        
    # 2. Fallback to payload body if present
    data = payload.get("body", {}).get("data", "")
    if data:
        try:
            import base64
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
        except Exception:
            pass
            
    return ""

def fetch_sender_history(service, email_addr):
    print(f"Fetching history for {email_addr}...")
    results = service.users().messages().list(userId="me", q=f"from:{email_addr}", maxResults=5).execute()
    messages = results.get("messages", [])
    
    history = []
    unsub_link = None
    for msg in messages:
        detail = service.service.users().messages().get(userId="me", id=msg["id"], format="full").execute() if hasattr(service, "service") else service.users().messages().get(userId="me", id=msg["id"], format="full").execute()
        headers = detail.get("payload", {}).get("headers", [])
        subject = ""
        for h in headers:
            if h.get("name", "").lower() == "subject":
                subject = h.get("value", "")
                break
        
        # Robust body extract (handles parts, text/plain, text/html, and single-part html)
        body = extract_body(detail.get("payload", {}))
                
        history.append({
            "subject": subject,
            "body": body
        })

        # Early check for unsubscribe link to save API quota
        link = find_unsubscribe_link(body)
        if link:
            unsub_link = link
            print("Found unsubscribe link. Interrupting history fetch early to save API quota.")
            break
            
    return history, unsub_link


def classify_sender(env, email_addr, history):
    print(f"Classifying sender {email_addr} using Ollama...")
    ollama_url = env.get("OLLAMA_BASE_URL", "http://localhost:11434")
    model = env.get("OLLAMA_MODEL", "qwen2.5:7b")
    
    history_str = ""
    for idx, item in enumerate(history, 1):
        history_str += f"Email {idx}:\nSubject: {item['subject']}\nBody: {item['body'][:1500]}\n\n"
        
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
    import time
    start_time = time.perf_counter()
    try:
        r = httpx.post(f"{ollama_url}/api/chat", json=payload, timeout=600.0)
        r.raise_for_status()
        duration = time.perf_counter() - start_time
        data = r.json()
        content = data["message"]["content"]
        result = json.loads(content)
        is_newsletter = result.get("is_newsletter", False)
        print(f"LLM Decision: is_newsletter = {is_newsletter} (took {duration:.2f}s) (raw output: {content})")
        return is_newsletter
    except Exception as e:
        duration = time.perf_counter() - start_time
        print(f"Error calling LLM after {duration:.2f}s: {e}")
        return False

class GeminiWebClassifier:
    def __init__(self, user_data_dir: Path):
        self.user_data_dir = user_data_dir
        self.playwright = None
        self.context = None
        self.page = None

    def __enter__(self):
        from playwright.sync_api import sync_playwright
        self.playwright = sync_playwright().start()
        
        # Launch Chromium/Chrome persistent context with evasion parameters to bypass "secure browser" checks
        user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        args = ["--disable-blink-features=AutomationControlled"]
        
        try:
            print("[Playwright] Attempting to launch persistent Chrome context...")
            self.context = self.playwright.chromium.launch_persistent_context(
                user_data_dir=str(self.user_data_dir.resolve()),
                headless=False,
                channel="chrome",
                slow_mo=100,
                user_agent=user_agent,
                args=args,
                ignore_default_args=["--enable-automation"]
            )
        except Exception as e:
            print(f"[Playwright] Failed to launch with Google Chrome channel ({e}). Falling back to Chromium...")
            self.context = self.playwright.chromium.launch_persistent_context(
                user_data_dir=str(self.user_data_dir.resolve()),
                headless=False,
                slow_mo=100,
                user_agent=user_agent,
                args=args,
                ignore_default_args=["--enable-automation"]
            )
        self.page = self.context.pages[0] if self.context.pages else self.context.new_page()
        
        # Navigate to Gemini
        print("[Playwright] Navigating to Gemini...")
        self.page.goto("https://gemini.google.com/", timeout=60000)
        self.page.wait_for_timeout(3000)
        
        # Check login status by checking prompt visibility
        selector = "div[contenteditable='true'], textarea#prompt-textarea, [role='combobox']"
        prompt_element = self.page.locator(selector).first
        
        try:
            prompt_element.wait_for(state="visible", timeout=3000)
            # Prompt the user to confirm they are using the correct logged-in account
            print("\n" + "="*50)
            print("👤  [Playwright] GEMINI SESSION DETECTED")
            print("Please check the browser window to confirm you are logged into the correct Google account.")
            input("PRESS ENTER in this terminal to continue if everything is correct...")
            print("="*50 + "\n")
        except Exception:
            print("\n" + "="*50)
            print("⚠️  [Playwright] GOOGLE LOGIN REQUIRED!")
            print("A browser window has opened. Please log into your Google account in that window.")
            input("Once logged in and Gemini is ready, PRESS ENTER in this terminal to continue...")
            print("="*50 + "\n")
            
            # Wait for input area to become visible
            prompt_element.wait_for(state="visible", timeout=0)
            
        return self

    def classify(self, email_addr, history):
        print(f"Classifying sender {email_addr} using Gemini Web...")
        import re
        import json
        
        # 1. Format the email history prompt
        history_str = ""
        for idx, item in enumerate(history, 1):
            history_str += f"Email {idx}:\nSubject: {item['subject']}\nBody: {item['body'][:1200]}\n\n"
            
        prompt_text = (
            "You are an email analysis bot. Analyze the sender's history and determine:\n"
            "1. If the sender is a Newsletter (automatic promotions, marketing, newsletters, content digests, subscriptions).\n"
            "2. If it is NOT a newsletter, classify it into exactly ONE of the following categories:\n"
            "   - 'personal': Direct human-to-human conversations or personal direct messages.\n"
            "   - 'profissional': Emails related to work, business, or professional activities.\n"
            "   - 'transactional': Invoices, billing, order tracking, purchase confirmations, or financial statements.\n"
            "   - 'security': Password resets, login alerts, 2FA verification codes, or access authorizations.\n"
            "   - 'notification': Calendar invites, system updates, social media notifications, or collaboration pings (Jira, Slack, GitHub).\n"
            "   - 'other': Emails that do not fall into any of the above categories.\n\n"
            "Return a JSON object conforming exactly to this schema:\n"
            "{\n"
            "  \"is_newsletter\": boolean,\n"
            "  \"category\": string\n"
            "}\n\n"
            f"Sender: {email_addr}\nHistory:\n{history_str}"
        )
        
        is_newsletter = False
        category = "other"
        
        try:
            # We go to the base URL to ensure we start a clean chat session or are on the main page
            self.page.goto("https://gemini.google.com/", timeout=60000)
            
            # Wait for prompt textarea
            selector = "div[contenteditable='true'], textarea#prompt-textarea, [role='combobox']"
            prompt_element = self.page.locator(selector).first
            prompt_element.wait_for(state="visible", timeout=15000)
            
            # Input the prompt
            print("[Playwright] Inputting prompt...")
            prompt_element.focus()
            prompt_element.fill(prompt_text)
            
            # Send
            self.page.wait_for_timeout(500)
            send_selectors = [
                "button[aria-label*='Send']",
                "button[aria-label*='Enviar']",
                "button.send-button",
                "button[type='submit']",
                "div.send-button-container button"
            ]
            send_button = None
            for sel in send_selectors:
                btn = self.page.locator(sel).first
                if btn.is_visible() and btn.is_enabled():
                    send_button = btn
                    break
                    
            if send_button:
                send_button.click()
            else:
                self.page.keyboard.press("Enter")
                
            print("[Playwright] Waiting for response to generate...")
            self.page.wait_for_timeout(4000)
            
            # Polling strategy for stability
            last_text = ""
            stable_count = 0
            for _ in range(60):
                responses = self.page.locator("message-content, .message-content, .model-response, div[class*='message-content']").all()
                if responses:
                    current_text = responses[-1].inner_text()
                    if current_text and current_text == last_text:
                        stable_count += 1
                        if stable_count >= 3:
                            break
                    else:
                        stable_count = 0
                        last_text = current_text
                self.page.wait_for_timeout(1000)
                
            print("[Playwright] Parsing response content...")
            json_match = re.search(r"\{[\s\S]*?\}", last_text)
            parsed_json = None
            if json_match:
                try:
                    parsed_json = json.loads(json_match.group(0))
                except Exception:
                    pass
            
            if parsed_json and isinstance(parsed_json, dict):
                is_newsletter = parsed_json.get("is_newsletter", False)
                category = parsed_json.get("category", "other")
            else:
                # Text-based fallback scanning
                lower_text = last_text.lower()
                is_newsletter = "is_newsletter\": true" in lower_text or '"is_newsletter": true' in lower_text
                
                # Check for categories in text
                for cat in ["personal", "profissional", "transactional", "security", "notification", "other"]:
                    if cat in lower_text:
                        category = cat
                        break
                        
            category = category.strip().lower()
            if is_newsletter:
                category = "newsletter"
                
            print(f"[Playwright] Gemini decision: is_newsletter = {is_newsletter}, category = {category}")
            
            # Delete chat thread
            print("[Playwright] Deleting chat thread...")
            try:
                # Open menu/sidebar if collapsed
                menu_btn = self.page.locator("button[aria-label*='Menu'], button[aria-label*='Expand']").first
                if menu_btn.is_visible():
                    menu_btn.click()
                    self.page.wait_for_timeout(500)
                    
                action_btn = self.page.locator("button[aria-label*='actions'], button[aria-label*='opções'], button[aria-label*='Options']").first
                if action_btn.is_visible():
                    action_btn.click()
                    
                    # Wait for and click the 'Delete' option in the dropdown menu
                    delete_opt = self.page.locator("span:has-text('Delete'), span:has-text('Excluir'), [role='menuitem']:has-text('Delete'), [role='menuitem']:has-text('Excluir'), [class*='delete']").first
                    delete_opt.wait_for(state="visible", timeout=5000)
                    delete_opt.click()
                    
                    # Wait for and click the 'Delete' button in the confirmation modal/dialog
                    confirm_btn = self.page.locator("[role='dialog'], mat-dialog-container, [class*='dialog']").locator("button:has-text('Delete'), button:has-text('Excluir')").first
                    confirm_btn.wait_for(state="visible", timeout=5000)
                    confirm_btn.click()
                    print("[Playwright] Chat thread successfully deleted.")
                    self.page.wait_for_timeout(1000)
            except Exception as delete_error:
                print(f"[Playwright] Could not delete chat session: {delete_error}")
                
        except Exception as e:
            print(f"[Playwright] Error in Gemini Web classification: {e}")
            
        return is_newsletter, category

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.context:
            self.context.close()
        if self.playwright:
            self.playwright.stop()

def chunk_senders(senders: set[str], max_len: int = 1000) -> list[str]:
    # Returns a list of criteria strings, each formatted as (email1 OR email2 OR ...)
    sorted_senders = sorted(list(senders))
    chunks = []
    current_chunk = []
    current_len = 0
    for sender in sorted_senders:
        added_len = len(sender)
        if not current_chunk:
            new_len = added_len + 2  # (sender)
        else:
            new_len = current_len + 4 + added_len  # ... OR sender)
            
        if new_len > max_len and current_chunk:
            chunks.append(f"({' OR '.join(current_chunk)})")
            current_chunk = [sender]
            current_len = len(sender) + 2
        else:
            current_chunk.append(sender)
            current_len = new_len
            
    if current_chunk:
        if len(current_chunk) > 1:
            chunks.append(f"({' OR '.join(current_chunk)})")
        else:
            chunks.append(current_chunk[0])
    return chunks


def create_gmail_filter(service, email_addr):
    print(f"Adding {email_addr} to consolidated Gmail commercial filter...")
    
    # 1. Fetch all filters
    try:
        results = service.users().settings().filters().list(userId="me").execute()
        filters = results.get("filter", [])
    except Exception as e:
        print(f"Error listing filters: {e}")
        filters = []
        
    target_filters = []
    # Find all existing consolidated filters that match the TRASH and UNREAD criteria and are 'from' filters
    for flt in filters:
        action = flt.get("action", {})
        add_labels = action.get("addLabelIds", [])
        remove_labels = action.get("removeLabelIds", [])
        if "TRASH" in add_labels and "UNREAD" in remove_labels and "from" in flt.get("criteria", {}):
            target_filters.append(flt)
            
    existing_senders = set()
    old_filter_ids = []
    
    for flt in target_filters:
        old_filter_ids.append(flt["id"])
        from_criteria = flt.get("criteria", {}).get("from", "")
        cleaned_from = from_criteria.strip()
        if cleaned_from.startswith("(") and cleaned_from.endswith(")"):
            cleaned_from = cleaned_from[1:-1].strip()
            
        import re
        parts = re.split(r'\s+[oO][rR]\s+', cleaned_from)
        for part in parts:
            p = part.strip().lower()
            if p:
                existing_senders.add(p)
                
    # Add new email address to set
    new_sender = email_addr.strip().lower()
    if new_sender in existing_senders:
        print(f"Sender {new_sender} already exists in consolidated filter. No changes needed.")
        return
        
    existing_senders.add(new_sender)
    
    # Format the new criteria chunks
    criteria_strings = chunk_senders(existing_senders, max_len=1000)
    
    # Track which filters to keep and which new ones to create
    filters_to_delete_ids = old_filter_ids.copy()
    new_filters_created = []
    success = True
    
    for criteria_str in criteria_strings:
        # Check if this exact chunk already exists in Gmail
        matched_filter = None
        for flt in target_filters:
            if flt.get("criteria", {}).get("from", "") == criteria_str:
                matched_filter = flt
                break
                
        if matched_filter:
            # Chunk already exists. Keep it and remove from delete list
            if matched_filter["id"] in filters_to_delete_ids:
                filters_to_delete_ids.remove(matched_filter["id"])
            print(f"Filter chunk already exists, keeping it (id: {matched_filter['id']})")
        else:
            filter_body = {
                "criteria": {"from": criteria_str},
                "action": {
                    "removeLabelIds": ["UNREAD", "INBOX"],
                    "addLabelIds": ["TRASH"]
                }
            }
            try:
                res = service.users().settings().filters().create(userId="me", body=filter_body).execute()
                new_filters_created.append(res["id"])
                print(f"Consolidated filter chunk created successfully (id: {res.get('id')})")
            except Exception as e:
                print(f"Error creating filter chunk: {e}")
                success = False
                break
                
    if success:
        for old_id in filters_to_delete_ids:
            try:
                print(f"Deleting old obsolete filter (id: {old_id})...")
                service.users().settings().filters().delete(userId="me", id=old_id).execute()
            except Exception as e:
                print(f"Error deleting old filter {old_id}: {e}")
    else:
        # Rollback newly created filters if creation failed
        print("Failed to create all new filters. Rolling back (deleting newly created chunks)...")
        for new_id in new_filters_created:
            try:
                service.users().settings().filters().delete(userId="me", id=new_id).execute()
            except Exception as rollback_err:
                print(f"Rollback error deleting filter {new_id}: {rollback_err}")

    # Retroactively trash all existing emails from the new sender
    try:
        print(f"Applying filter retroactively to all existing messages from {email_addr}...")
        messages = []
        next_page_token = None
        while True:
            results = service.users().messages().list(
                userId="me", q=f"from:{email_addr}", pageToken=next_page_token
            ).execute()
            messages.extend(results.get("messages", []))
            next_page_token = results.get("nextPageToken")
            if not next_page_token:
                break

        if messages:
            msg_ids = [m["id"] for m in messages]
            print(f"Moving {len(msg_ids)} existing messages to trash...")
            
            # Chunk into blocks of 1000 for batchModify API constraints
            chunk_size = 1000
            for i in range(0, len(msg_ids), chunk_size):
                chunk = msg_ids[i:i + chunk_size]
                print(f"Trashing chunk {i // chunk_size + 1} ({len(chunk)} messages)...")
                service.users().messages().batchModify(
                    userId="me",
                    body={
                        "ids": chunk,
                        "addLabelIds": ["TRASH"],
                        "removeLabelIds": ["INBOX", "UNREAD"]
                    }
                ).execute()
            print("Retroactive filter application completed.")
        else:
            print("No existing messages found to retroactively filter.")
    except Exception as e:
        print(f"Error applying filter retroactively: {e}")


def get_or_create_label(service, label_name):
    # List existing labels
    try:
        results = service.users().labels().list(userId="me").execute()
        labels = results.get("labels", [])
        for label in labels:
            if label["name"].lower() == label_name.lower():
                return label["id"]
    except Exception as e:
        print(f"Error listing labels: {e}")
        
    # Create label if not found
    try:
        print(f"Label '{label_name}' not found. Creating it...")
        label_body = {
            "name": label_name,
            "labelListVisibility": "labelShow",
            "messageListVisibility": "show"
        }
        created_label = service.users().labels().create(userId="me", body=label_body).execute()
        return created_label["id"]
    except Exception as e:
        print(f"Error creating label '{label_name}': {e}")
        return None


def create_gmail_category_filter(service, email_addr, category):
    # Capitalize label name and prepend prefix
    label_name = f"Gemini/{category.capitalize()}"
    
    # Determine if we should archive (remove from INBOX) for this category
    should_archive = category.lower() not in {"personal", "profissional", "other"}
    
    if should_archive:
        print(f"Adding {email_addr} to consolidated Gmail category filter: {label_name} (with Inbox archiving)...")
    else:
        print(f"Adding {email_addr} to consolidated Gmail category filter: {label_name} (keeping in Inbox)...")
    
    # 0. Get or create label ID
    label_id = get_or_create_label(service, label_name)
    if not label_id:
        print(f"Could not get or create label for '{label_name}'. Aborting filter creation.")
        return
        
    # 1. Fetch all filters
    try:
        results = service.users().settings().filters().list(userId="me").execute()
        filters = results.get("filter", [])
    except Exception as e:
        print(f"Error listing filters: {e}")
        filters = []
        
    target_filters = []
    # Find all existing category filters matching the label ID and expected archive/inbox action
    for flt in filters:
        action = flt.get("action", {})
        add_labels = action.get("addLabelIds", [])
        remove_labels = action.get("removeLabelIds", [])
        if label_id in add_labels and "from" in flt.get("criteria", {}):
            if should_archive and "INBOX" in remove_labels:
                target_filters.append(flt)
            elif not should_archive and "INBOX" not in remove_labels:
                target_filters.append(flt)
            
    existing_senders = set()
    old_filter_ids = []
    
    for flt in target_filters:
        old_filter_ids.append(flt["id"])
        from_criteria = flt.get("criteria", {}).get("from", "")
        cleaned_from = from_criteria.strip()
        if cleaned_from.startswith("(") and cleaned_from.endswith(")"):
            cleaned_from = cleaned_from[1:-1].strip()
            
        # Parse existing emails
        import re
        parts = re.split(r'\s+[oO][rR]\s+', cleaned_from)
        for part in parts:
            p = part.strip().lower()
            if p:
                existing_senders.add(p)
                
    # Add new email address to set
    new_sender = email_addr.strip().lower()
    if new_sender in existing_senders:
        print(f"Sender {new_sender} already exists in consolidated category filter. No changes needed.")
        return
        
    existing_senders.add(new_sender)
    
    # Format the new criteria chunks
    criteria_strings = chunk_senders(existing_senders, max_len=1000)
    
    # Track which filters to keep and which new ones to create
    filters_to_delete_ids = old_filter_ids.copy()
    new_filters_created = []
    success = True
    
    for criteria_str in criteria_strings:
        # Check if this exact chunk already exists in Gmail
        matched_filter = None
        for flt in target_filters:
            if flt.get("criteria", {}).get("from", "") == criteria_str:
                matched_filter = flt
                break
                
        if matched_filter:
            # Chunk already exists. Keep it and remove from delete list
            if matched_filter["id"] in filters_to_delete_ids:
                filters_to_delete_ids.remove(matched_filter["id"])
            print(f"Category filter chunk already exists, keeping it (id: {matched_filter['id']})")
        else:
            if should_archive:
                filter_body = {
                    "criteria": {"from": criteria_str},
                    "action": {
                        "removeLabelIds": ["INBOX"],
                        "addLabelIds": [label_id]
                    }
                }
            else:
                filter_body = {
                    "criteria": {"from": criteria_str},
                    "action": {
                        "addLabelIds": [label_id]
                    }
                }
            try:
                res = service.users().settings().filters().create(userId="me", body=filter_body).execute()
                new_filters_created.append(res["id"])
                print(f"Consolidated category filter chunk created successfully (id: {res.get('id')})")
            except Exception as e:
                print(f"Error creating category filter chunk: {e}")
                success = False
                break
            
    if success:
        for old_id in filters_to_delete_ids:
            try:
                print(f"Deleting old obsolete category filter (id: {old_id})...")
                service.users().settings().filters().delete(userId="me", id=old_id).execute()
            except Exception as e:
                print(f"Error deleting old category filter {old_id}: {e}")
    else:
        # Rollback newly created category filters if creation failed
        print("Failed to create all new category filters. Rolling back (deleting newly created chunks)...")
        for new_id in new_filters_created:
            try:
                service.users().settings().filters().delete(userId="me", id=new_id).execute()
            except Exception as rollback_err:
                print(f"Rollback error deleting category filter {new_id}: {rollback_err}")
        
    # Retroactively move all existing emails from the new sender
    try:
        print(f"Applying filter retroactively to all existing messages from {email_addr}...")
        messages = []
        next_page_token = None
        while True:
            results = service.users().messages().list(
                userId="me", q=f"from:{email_addr}", pageToken=next_page_token
            ).execute()
            messages.extend(results.get("messages", []))
            next_page_token = results.get("nextPageToken")
            if not next_page_token:
                break
                
        if messages:
            msg_ids = [m["id"] for m in messages]
            if should_archive:
                print(f"Adding label '{label_name}' and removing from INBOX for {len(msg_ids)} existing messages...")
                remove_ids = ["INBOX"]
            else:
                print(f"Adding label '{label_name}' to {len(msg_ids)} existing messages (keeping in INBOX)...")
                remove_ids = []
            
            chunk_size = 1000
            for i in range(0, len(msg_ids), chunk_size):
                chunk = msg_ids[i:i + chunk_size]
                body = {
                    "ids": chunk,
                    "addLabelIds": [label_id]
                }
                if remove_ids:
                    body["removeLabelIds"] = remove_ids
                    
                service.users().messages().batchModify(
                    userId="me",
                    body=body
                ).execute()
            print("Retroactive filter application completed.")
        else:
            print("No existing messages found to retroactively filter.")
    except Exception as e:
        print(f"Error applying filter retroactively: {e}")



def find_unsubscribe_link(body: str) -> str | None:
    import re
    import unicodedata
    
    # Normalize body to lower-case ASCII without diacritics/accents
    body_normalized = unicodedata.normalize('NFKD', body).encode('ASCII', 'ignore').decode('ASCII').lower()
    
    # 1. Keywords to search for (normalized to lowercase without accents)
    keywords = [
        "unsubscribe", "opt-out", "opt out", "descadastrar", 
        "descadastre", "desinscrever", "desinscreva", "cancelar inscricao", 
        "cancelar assinatura", "sair da lista",
        "nao queira mais receber",
        "nao deseja mais receber",
        "nao deseja",
        "nao desejar mais receber",
        "nao receber mais",
        "nao quero receber",
        "deixar de receber", "parar de receber",
        "preferencias de envio",
        "gerenciar preferencias",
        "remover de nossa lista", "remover seu e-mail", "remover seu email",
        "caso nao queira"
    ]
    
    # Check if any keyword is in the normalized body
    if not any(kw in body_normalized for kw in keywords):
        return None
        
    # 2. Try to find a URL that contains unsubscribe keywords inside the URL itself
    urls = re.findall(r'https?://[^\s<>"]+', body_normalized)
    unsub_url_keywords = ["unsubscribe", "unsub", "optout", "opt-out", "descadastrar", "desinscrever", "cancelar"]
    for url in urls:
        url_lower = url.lower()
        if any(kw in url_lower for kw in unsub_url_keywords):
            return url
            
    # 3. Look for a URL that is close to the keyword in the text (proximity match within 300 chars)
    for kw in keywords:
        # Match keyword followed by text, then URL
        pattern_after = re.compile(
            rf"{re.escape(kw)}[\s\S]{{0,300}}?(https?://[^\s<>\"\u200b]+)", re.IGNORECASE
        )
        match = pattern_after.search(body_normalized)
        if match:
            return match.group(1).rstrip(".,;)]}>")

        # Match URL followed by text, then keyword
        pattern_before = re.compile(
            rf"(https?://[^\s<>\"\u200b]+)[\s\S]{{0,300}}?{re.escape(kw)}", re.IGNORECASE
        )
        match = pattern_before.search(body_normalized)
        if match:
            return match.group(1).rstrip(".,;)]}>")

    # 4. Fallback: if keywords exist in the body, but no direct proximity match, return the last URL
    if urls:
        return urls[-1]
        
    return None

def input_with_timeout(prompt: str, timeout: float = 5.0, default: str = "y") -> str:
    import sys
    import select
    print(prompt, end="", flush=True)
    rlist, _, _ = select.select([sys.stdin], [], [], timeout)
    if rlist:
        val = sys.stdin.readline().strip().lower()
        return val if val else default
    else:
        print(f"\n[Timeout] Auto-selecting default: {default}")
        return default

def classify_sender_ollama(email_addr, history):
    model = "qwen2.5:7b" # "qwen2.5-coder:7b" # "gemma4:12b",
    print(f"Classifying sender {email_addr} using Ollama ({model})...")
    import json
    import httpx
    
    # Format the email history prompt
    history_str = ""
    for idx, item in enumerate(history, 1):
        history_str += f"Email {idx}:\nSubject: {item['subject']}\nBody: {item['body'][:1200]}\n\n"
        
    prompt_text = (
        "You are an email analysis bot. Analyze the sender's history and determine:\n"
        "1. If the sender is a Newsletter (automatic promotions, marketing, newsletters, content digests, subscriptions).\n"
        "2. If it is NOT a newsletter, classify it into exactly ONE of the following categories:\n"
        "   - 'personal': Direct human-to-human conversations or personal direct messages.\n"
        "   - 'profissional': Emails related to work, business, or professional activities.\n"
        "   - 'transactional': Invoices, billing, order tracking, purchase confirmations, or financial statements.\n"
        "   - 'security': Password resets, login alerts, 2FA verification codes, or access authorizations.\n"
        "   - 'notification': Calendar invites, system updates, social media notifications, or collaboration pings (Jira, Slack, GitHub).\n"
        "   - 'other': Emails that do not fall into any of the above categories.\n\n"
        "Return a JSON object conforming exactly to this schema:\n"
        "{\n"
        "  \"is_newsletter\": boolean,\n"
        "  \"category\": string\n"
        "}\n\n"
        f"Sender: {email_addr}\nHistory:\n{history_str}"
    )
    payload = {
        "model": model,
        "prompt": prompt_text,
        "format": "json",
        "stream": False,
        "options": {
            "temperature": 0.0
        }
    }
    
    import time
    start_time = time.perf_counter()
    
    # 5-minute timeout for local Ollama run
    r = httpx.post("http://localhost:11434/api/generate", json=payload, timeout=300.0)
    r.raise_for_status()
    
    duration = time.perf_counter() - start_time
    res_json = r.json()
    response_text = res_json.get("response", "")
    
    parsed_json = json.loads(response_text)
    is_newsletter = parsed_json.get("is_newsletter", False)
    category = parsed_json.get("category", "other")
    
    category = category.strip().lower()
    if is_newsletter:
        category = "newsletter"
        
    # Extract Ollama performance metrics
    total_duration = res_json.get("total_duration", 0) / 1e9
    load_duration = res_json.get("load_duration", 0) / 1e9
    prompt_eval_count = res_json.get("prompt_eval_count", 0)
    prompt_eval_duration = res_json.get("prompt_eval_duration", 0) / 1e9
    eval_count = res_json.get("eval_count", 0)
    eval_duration = res_json.get("eval_duration", 0) / 1e9
    tokens_per_sec = eval_count / eval_duration if eval_duration > 0 else 0
    print(
        f"[Ollama {model}] Decision: is_newsletter = {is_newsletter}, category = {category}\n"
        f"  - Total Time: {duration:.2f}s (Ollama API: {total_duration:.2f}s, Load: {load_duration:.2f}s, Prompt Eval: {prompt_eval_duration:.2f}s, Gen: {eval_duration:.2f}s)\n"
        f"  - Tokens: Prompt = {prompt_eval_count}, Response = {eval_count}\n"
        f"  - Generation Speed: {tokens_per_sec:.2f} tokens/sec"
    )
    return is_newsletter, category


def sync_newsletter_filters(service, newsletters: set[str]):
    try:
        results = service.users().settings().filters().list(userId="me").execute()
        filters = results.get("filter", [])
    except Exception as e:
        print(f"Error listing filters: {e}")
        filters = []
        
    old_filter_ids = []
    existing_senders = set()
    for flt in filters:
        action = flt.get("action", {})
        add_labels = action.get("addLabelIds", [])
        remove_labels = action.get("removeLabelIds", [])
        if "TRASH" in add_labels and "UNREAD" in remove_labels and "from" in flt.get("criteria", {}):
            old_filter_ids.append(flt["id"])
            from_criteria = flt.get("criteria", {}).get("from", "")
            cleaned_from = from_criteria.strip()
            if cleaned_from.startswith("(") and cleaned_from.endswith(")"):
                cleaned_from = cleaned_from[1:-1].strip()
            import re
            parts = re.split(r'\s+[oO][rR]\s+', cleaned_from)
            for part in parts:
                p = part.strip().lower()
                if p:
                    existing_senders.add(p)
                    
    # If the exact set of newsletters already exists in Gmail, skip update to avoid duplicate filter errors
    if newsletters == existing_senders:
        print("Newsletters are already in sync. No changes needed.")
        return
            
    # Chunk the entire newsletters set
    criteria_strings = chunk_senders(newsletters, max_len=1000)
    
    # Track which filters to keep and which new ones to create
    filters_to_delete_ids = old_filter_ids.copy()
    new_filters_created = []
    success = True
    
    # Target filters list in Gmail
    target_filters = []
    for flt in filters:
        action = flt.get("action", {})
        add_labels = action.get("addLabelIds", [])
        remove_labels = action.get("removeLabelIds", [])
        if "TRASH" in add_labels and "UNREAD" in remove_labels and "from" in flt.get("criteria", {}):
            target_filters.append(flt)
            
    for criteria_str in criteria_strings:
        # Check if this exact chunk already exists in Gmail
        matched_filter = None
        for flt in target_filters:
            if flt.get("criteria", {}).get("from", "") == criteria_str:
                matched_filter = flt
                break
                
        if matched_filter:
            # Chunk already exists. Keep it and remove from delete list
            if matched_filter["id"] in filters_to_delete_ids:
                filters_to_delete_ids.remove(matched_filter["id"])
            print(f"TRASH filter chunk already exists, keeping it (id: {matched_filter['id']})")
        else:
            filter_body = {
                "criteria": {"from": criteria_str},
                "action": {
                    "removeLabelIds": ["UNREAD", "INBOX"],
                    "addLabelIds": ["TRASH"]
                }
            }
            try:
                res = service.users().settings().filters().create(userId="me", body=filter_body).execute()
                new_filters_created.append(res["id"])
                print(f"Consolidated TRASH filter chunk created (id: {res.get('id')})")
            except Exception as e:
                print(f"Error creating TRASH filter chunk: {e}")
                success = False
                break
            
    if success:
        for old_id in filters_to_delete_ids:
            try:
                print(f"Deleting old obsolete TRASH filter (id: {old_id})...")
                service.users().settings().filters().delete(userId="me", id=old_id).execute()
            except Exception as e:
                print(f"Error deleting old TRASH filter {old_id}: {e}")
    else:
        print("Failed to create all new TRASH filters. Rolling back (deleting newly created chunks)...")
        for new_id in new_filters_created:
            try:
                service.users().settings().filters().delete(userId="me", id=new_id).execute()
            except Exception as rollback_err:
                print(f"Rollback error deleting TRASH filter {new_id}: {rollback_err}")


def sync_category_filters(service, category: str, senders: set[str]):
    label_name = f"Gemini/{category.capitalize()}"
    should_archive = category.lower() not in {"personal", "profissional", "other"}
    
    label_id = get_or_create_label(service, label_name)
    if not label_id:
        print(f"Could not get or create label for '{label_name}'. Aborting sync for this category.")
        return
        
    try:
        results = service.users().settings().filters().list(userId="me").execute()
        filters = results.get("filter", [])
    except Exception as e:
        print(f"Error listing filters: {e}")
        filters = []
        
    old_filter_ids = []
    existing_senders = set()
    for flt in filters:
        action = flt.get("action", {})
        add_labels = action.get("addLabelIds", [])
        remove_labels = action.get("removeLabelIds", [])
        if label_id in add_labels and "from" in flt.get("criteria", {}):
            matched = False
            if should_archive and "INBOX" in remove_labels:
                old_filter_ids.append(flt["id"])
                matched = True
            elif not should_archive and "INBOX" not in remove_labels:
                old_filter_ids.append(flt["id"])
                matched = True
                
            if matched:
                from_criteria = flt.get("criteria", {}).get("from", "")
                cleaned_from = from_criteria.strip()
                if cleaned_from.startswith("(") and cleaned_from.endswith(")"):
                    cleaned_from = cleaned_from[1:-1].strip()
                import re
                parts = re.split(r'\s+[oO][rR]\s+', cleaned_from)
                for part in parts:
                    p = part.strip().lower()
                    if p:
                        existing_senders.add(p)
                        
    # If the category is already in sync, skip update to avoid duplicate filter errors
    if senders == existing_senders:
        print(f"Category '{category}' is already in sync. No changes needed.")
        return
                
    criteria_strings = chunk_senders(senders, max_len=1000)
    
    # Track which filters to keep and which new ones to create
    filters_to_delete_ids = old_filter_ids.copy()
    new_filters_created = []
    success = True
    
    # Target filters list for this category currently in Gmail
    target_category_filters = []
    for flt in filters:
        action = flt.get("action", {})
        add_labels = action.get("addLabelIds", [])
        remove_labels = action.get("removeLabelIds", [])
        if label_id in add_labels and "from" in flt.get("criteria", {}):
            if should_archive and "INBOX" in remove_labels:
                target_category_filters.append(flt)
            elif not should_archive and "INBOX" not in remove_labels:
                target_category_filters.append(flt)
                
    for criteria_str in criteria_strings:
        # Check if this exact chunk already exists in Gmail
        matched_filter = None
        for flt in target_category_filters:
            if flt.get("criteria", {}).get("from", "") == criteria_str:
                matched_filter = flt
                break
                
        if matched_filter:
            # Chunk already exists. Keep it and remove from delete list
            if matched_filter["id"] in filters_to_delete_ids:
                filters_to_delete_ids.remove(matched_filter["id"])
            print(f"Category '{category}' filter chunk already exists, keeping it (id: {matched_filter['id']})")
        else:
            if should_archive:
                filter_body = {
                    "criteria": {"from": criteria_str},
                    "action": {
                        "removeLabelIds": ["INBOX"],
                        "addLabelIds": [label_id]
                    }
                }
            else:
                filter_body = {
                    "criteria": {"from": criteria_str},
                    "action": {
                        "addLabelIds": [label_id]
                    }
                }
            try:
                res = service.users().settings().filters().create(userId="me", body=filter_body).execute()
                new_filters_created.append(res["id"])
                print(f"Consolidated '{label_name}' filter chunk created (id: {res.get('id')})")
            except Exception as e:
                print(f"Error creating '{label_name}' filter chunk: {e}")
                success = False
                break
            
    if success:
        for old_id in filters_to_delete_ids:
            try:
                print(f"Deleting old obsolete '{label_name}' filter (id: {old_id})...")
                service.users().settings().filters().delete(userId="me", id=old_id).execute()
            except Exception as e:
                print(f"Error deleting old '{label_name}' filter {old_id}: {e}")
    else:
        print(f"Failed to create all new '{label_name}' filters. Rolling back (deleting newly created chunks)...")
        for new_id in new_filters_created:
            try:
                service.users().settings().filters().delete(userId="me", id=new_id).execute()
            except Exception as rollback_err:
                print(f"Rollback error deleting filter {new_id}: {rollback_err}")


def sync_processed_senders_to_gmail(service, processed_dict):
    # Group senders by category
    categories = {}
    for email, category in processed_dict.items():
        categories.setdefault(category, set()).add(email)
        
    print(f"Syncing filters for {len(processed_dict)} senders across {len(categories)} categories...")
    
    # 1. Sync newsletters (consolidated TRASH filters)
    newsletters = categories.get("newsletter", set())
    if newsletters:
        print(f"Syncing {len(newsletters)} newsletter senders...")
        sync_newsletter_filters(service, newsletters)
        
    # 2. Sync category filters
    for cat, senders in categories.items():
        if cat == "newsletter":
            continue
        print(f"Syncing {len(senders)} senders for category '{cat}'...")
        sync_category_filters(service, cat, senders)


def main():
    print("Starting Sandbox Spike...")
    env = load_env()
    service = get_gmail_service(env)
    
    processed_dict = load_processed_senders()
    processed_set = set(processed_dict.keys())
    print(f"Loaded processed list with {len(processed_set)} senders.")
    
    import sys
    if "--sync" in sys.argv:
        print("Sync mode activated: Rebuilding all Gmail filters from local JSON database...")
        sync_processed_senders_to_gmail(service, processed_dict)
        print("Sync completed successfully.")
        return

    print("Sync mode activated: Rebuilding all Gmail filters from local JSON database...")
    sync_processed_senders_to_gmail(service, processed_dict)
    print("Sync completed successfully.")
    
    user_data_dir = Path("sandbox/playwright_user_data")
    user_data_dir.mkdir(parents=True, exist_ok=True)
    
    with GeminiWebClassifier(user_data_dir) as classifier:
        next_page_token = None
        evaluated_messages_count = 0
        processed_senders_count = 0
        
        print("Starting message-by-message inbox analysis...")
        while True:
            print(f"Fetching page of inbox messages (token: {next_page_token})...")
            try:
                results = service.users().messages().list(
                    userId="me", 
                    q="label:INBOX", 
                    maxResults=50, 
                    pageToken=next_page_token
                ).execute()
            except Exception as e:
                print(f"Error listing messages: {e}")
                break
                
            messages = results.get("messages", [])
            next_page_token = results.get("nextPageToken")
            
            if not messages:
                print("No more messages in INBOX.")
                break
                
            print(f"Fetching metadata for {len(messages)} messages using Gmail API Batch Request...")
            senders_map = {}
            
            def batch_callback(request_id, response, exception):
                if exception is not None:
                    return
                msg_id = response.get("id")
                headers = response.get("payload", {}).get("headers", [])
                for h in headers:
                    if h.get("name", "").lower() == "from":
                        senders_map[msg_id] = h.get("value", "")
                        break
                        
            batch = service.new_batch_http_request(callback=batch_callback)
            for msg in messages:
                batch.add(service.users().messages().get(
                    userId="me",
                    id=msg["id"],
                    format="metadata",
                    metadataHeaders=["From"]
                ))
                
            try:
                batch.execute()
            except Exception as e:
                print(f"Error executing batch request: {e}")
                break
    
            for msg in messages:
                msg_id = msg["id"]
                evaluated_messages_count += 1
                
                from_val = senders_map.get(msg_id)
                if not from_val:
                    continue
                    
                email_addr = from_val
                if "<" in from_val and ">" in from_val:
                    email_addr = from_val.split("<")[1].split(">")[0]
                email_addr = email_addr.strip().lower()
                
                # Skip if already processed in this run or historically
                if email_addr in processed_set:
                    continue
                    
                # We found a new unprocessed sender!
                print(f"\n==========================================")
                print(f"Processing new sender: {email_addr} (From: {from_val})")
                
                history, unsub_link = fetch_sender_history(service, email_addr)
                print(f"Fetched {len(history)} messages from sender history.")
    
                is_newsletter = False
                category = "other"
                
                if unsub_link:
                    print(f"Unsubscribe link found: {unsub_link}")
                    
                    # Query user with 1 second timeout
                    prompt_str = f"Do you want to unsubscribe from '{email_addr}'? [Y/n] (Auto-yes in 1s): "
                    choice = input_with_timeout(prompt_str, timeout=1.0, default="y")
                    
                    if choice in ("y", "yes"):
                        try:
                            print("Attempting to unsubscribe by opening link...")
                            # Make a GET request to the unsubscribe link
                            r = httpx.get(unsub_link, timeout=10.0, follow_redirects=True)
                            print(f"Unsubscribe request status code: {r.status_code}")
                        except Exception as e:
                            print(f"Failed to request unsubscribe link: {e}")
                    else:
                        print("Skipped automated unsubscribe request.")
                    
                    # Bypass LLM: mark as newsletter directly
                    is_newsletter = True
                    category = "newsletter"
                else:
                    try:
                        is_newsletter, category = classify_sender_ollama(email_addr, history)
                    except Exception as ollama_error:
                        print(f"Ollama classification failed or timed out: {ollama_error}")
                        print("Falling back to Gemini Web (Playwright)...")
                        is_newsletter, category = classifier.classify(email_addr, history)
                
                if is_newsletter:
                    # Newsletters go to trash consolidated filter
                    create_gmail_filter(service, email_addr)
                    save_processed_sender(email_addr, "newsletter")
                else:
                    # Non-newsletters get category label applied and removed from Inbox
                    create_gmail_category_filter(service, email_addr, category)
                    save_processed_sender(email_addr, category)
    
                processed_set.add(email_addr)
                processed_senders_count += 1
                
            if not next_page_token:
                print("Reached the end of the INBOX (no nextPageToken).")
                break
                
        print(f"\nSandbox Spike completed. Evaluated {evaluated_messages_count} messages, processed {processed_senders_count} new senders.")

if __name__ == "__main__":
    main()
