import base64
import logging
from datetime import UTC, datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from src.config import settings
from src.domain.entities import Email, EmailAction
from src.ports.gmail import GmailPort

logger = logging.getLogger("zip.gmail")

# Scopes required to read, modify, and delete/trash emails
SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.labels",
    "https://www.googleapis.com/auth/gmail.settings.basic",
]


class GmailOAuthAdapter(GmailPort):
    """
    Adapter for GmailPort using Google OAuth2 credentials and the Google API Client.
    """

    def __init__(self) -> None:
        self.creds = self._get_credentials()
        self.service = build("gmail", "v1", credentials=self.creds)

    def _get_credentials(self) -> Credentials:
        """
        Retrieves OAuth2 credentials from the configured token file.
        Refreshes expired credentials if necessary, or runs the local
        authorization flow to generate a new token.
        """
        creds = None
        token_path = settings.gmail_token_path

        # Load existing token if available
        if token_path.exists():
            try:
                creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
                logger.info(
                    f"Loaded existing Gmail OAuth credentials from {token_path}"
                )
            except Exception as e:
                logger.warning(
                    f"Failed to load token from {token_path}: {e}. Initiating re-auth."
                )

        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    logger.info("Gmail OAuth token expired. Attempting refresh...")
                    creds.refresh(Request())
                except Exception as e:
                    logger.error(
                        f"Failed to refresh OAuth token: {e}. Re-authenticating..."
                    )
                    creds = None

            if not creds:
                if settings.gmail_credentials_path.exists():
                    logger.info(
                        f"Loading Gmail OAuth client config from file: {settings.gmail_credentials_path}"
                    )
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(settings.gmail_credentials_path), SCOPES
                    )
                else:
                    logger.info(
                        "credentials.json not found. Falling back to .env variables."
                    )
                    client_config = {
                        "installed": {
                            "client_id": settings.gmail_client_id,
                            "client_secret": settings.gmail_client_secret,
                            "project_id": settings.gmail_project_id,
                            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                            "token_uri": "https://oauth2.googleapis.com/token",
                            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                        }
                    }
                    if "dummy" in settings.gmail_client_id:
                        logger.warning(
                            "Using dummy credentials. OAuth flow will fail if run interactively."
                        )
                    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)

                logger.info(
                    "Starting local Gmail OAuth2 InstalledAppFlow redirect server..."
                )
                # This opens the browser for authentication (or prints link if running headlessly)
                creds = flow.run_local_server(port=0)

            # Save the credentials for the next run
            with open(token_path, "w") as token_file:
                token_file.write(creds.to_json())
                logger.info(f"Saved refreshed Gmail OAuth credentials to {token_path}")

        return creds

    def fetch_unread_emails(self, max_results: int = 20) -> list[Email]:
        """
        Fetches unread emails from the Gmail inbox.
        """
        try:
            logger.info(f"Fetching up to {max_results} unread emails from Gmail...")
            results = (
                self.service.users()
                .messages()
                .list(userId="me", q="is:unread", maxResults=max_results)
                .execute()
            )
            messages = results.get("messages", [])

            emails = []
            for msg in messages:
                email_detail = (
                    self.service.users()
                    .messages()
                    .get(userId="me", id=msg["id"], format="full")
                    .execute()
                )

                # Parse headers
                headers = email_detail.get("payload", {}).get("headers", [])
                subject = ""
                sender = ""
                date_str = ""

                for header in headers:
                    name = header.get("name", "").lower()
                    if name == "subject":
                        subject = header.get("value", "")
                    elif name == "from":
                        sender = header.get("value", "")
                    elif name == "date":
                        date_str = header.get("value", "")

                # Parse received date
                try:
                    # Parse standard email date header format (rfc2822)
                    from email.utils import parsedate_to_datetime

                    received_at = parsedate_to_datetime(date_str)
                except Exception:
                    # Fallback to current datetime in UTC if parsing fails
                    received_at = datetime.now(UTC)

                # Extract text body from payload
                body = self._extract_body(email_detail.get("payload", {}))

                emails.append(
                    Email(
                        id=msg["id"],
                        thread_id=msg["threadId"],
                        subject=subject,
                        sender=sender,
                        body=body,
                        received_at=received_at,
                        labels=email_detail.get("labelIds", []),
                    )
                )

            logger.info(f"Successfully fetched and parsed {len(emails)} emails")
            return emails

        except HttpError as error:
            logger.error(f"Gmail API HTTP error occurred: {error}")
            return []
        except Exception as error:
            logger.error(f"Unexpected error while fetching emails: {error}")
            return []

    def _extract_body(self, payload: dict) -> str:
        """
        Recursively extract text/plain parts from the email message payload.
        """
        body = ""
        mime_type = payload.get("mimeType", "")

        # Check if multipart payload
        parts = payload.get("parts", [])
        if parts:
            for part in parts:
                body += self._extract_body(part)
        else:
            # Leaf part, check if text/plain
            if mime_type == "text/plain":
                data = payload.get("body", {}).get("data", "")
                if data:
                    try:
                        # Decode base64url encoding typical of Gmail API body payload
                        decoded_bytes = base64.urlsafe_b64decode(data)
                        body += decoded_bytes.decode("utf-8", errors="ignore")
                    except Exception as e:
                        logger.error(f"Error decoding message body part: {e}")
        return body

    def apply_action(
        self, email_id: str, action: EmailAction, label_name: str | None = None
    ) -> None:
        """
        Applies the classification action to the message in Gmail.
        """
        try:
            logger.info(f"Applying action '{action.value}' to email {email_id}")

            if action == EmailAction.DELETE:
                # Trash the email
                self.service.users().messages().trash(
                    userId="me", id=email_id
                ).execute()
                logger.info(f"Email {email_id} moved to trash successfully")

            elif action == EmailAction.ARCHIVE:
                # Remove from inbox (Archive) and remove UNREAD label
                self.service.users().messages().modify(
                    userId="me",
                    id=email_id,
                    body={"removeLabelIds": ["INBOX", "UNREAD"]},
                ).execute()
                logger.info(f"Email {email_id} archived successfully")

            elif action == EmailAction.LABEL and label_name:
                # Create the label if it doesn't exist, and get its label ID
                label_id = self._get_or_create_label_id(label_name)

                # Apply new label, remove INBOX and UNREAD
                self.service.users().messages().modify(
                    userId="me",
                    id=email_id,
                    body={
                        "addLabelIds": [label_id],
                        "removeLabelIds": ["INBOX", "UNREAD"],
                    },
                ).execute()
                logger.info(
                    f"Email {email_id} tagged with label '{label_name}' and archived"
                )

            elif action == EmailAction.NONE:
                # Important: keep in inbox but remove UNREAD tag so we don't re-process in subsequent cycles
                self.service.users().messages().modify(
                    userId="me", id=email_id, body={"removeLabelIds": ["UNREAD"]}
                ).execute()
                logger.info(f"Email {email_id} kept in inbox (UNREAD label removed)")

        except HttpError as error:
            logger.error(
                f"Gmail API HTTP error applying action {action} to {email_id}: {error}"
            )
        except Exception as error:
            logger.error(
                f"Unexpected error applying action {action} to {email_id}: {error}"
            )

    def _get_or_create_label_id(self, label_name: str) -> str:
        """
        Retrieves the ID of a label by name, creating the label if it does not exist.
        """
        try:
            # List user labels
            response = self.service.users().labels().list(userId="me").execute()
            labels = response.get("labels", [])

            # Match existing label case-insensitively
            for lbl in labels:
                if lbl["name"].lower() == label_name.lower():
                    return lbl["id"]

            # Label not found, create new label
            logger.info(f"Label '{label_name}' does not exist. Creating it now...")
            new_label = {
                "name": label_name,
                "labelListVisibility": "labelShow",
                "messageListVisibility": "show",
            }
            created_label = (
                self.service.users()
                .labels()
                .create(userId="me", body=new_label)
                .execute()
            )
            return created_label["id"]

        except HttpError as error:
            logger.error(f"Error checking or creating label '{label_name}': {error}")
            raise

    def fetch_emails_by_sender(self, sender: str, max_results: int = 5) -> list[Email]:
        """
        Fetches emails from a specific sender.
        """
        try:
            logger.info(f"Fetching up to {max_results} emails from sender {sender}...")
            results = (
                self.service.users()
                .messages()
                .list(userId="me", q=f"from:{sender}", maxResults=max_results)
                .execute()
            )
            messages = results.get("messages", [])

            emails = []
            for msg in messages:
                email_detail = (
                    self.service.users()
                    .messages()
                    .get(userId="me", id=msg["id"], format="full")
                    .execute()
                )
                headers = email_detail.get("payload", {}).get("headers", [])
                subject = ""
                from_val = ""
                date_str = ""
                for h in headers:
                    n = h.get("name", "").lower()
                    if n == "subject":
                        subject = h.get("value", "")
                    elif n == "from":
                        from_val = h.get("value", "")
                    elif n == "date":
                        date_str = h.get("value", "")

                try:
                    from email.utils import parsedate_to_datetime

                    received_at = parsedate_to_datetime(date_str)
                except Exception:
                    received_at = datetime.now(UTC)

                body = self._extract_body(email_detail.get("payload", {}))
                emails.append(
                    Email(
                        id=msg["id"],
                        thread_id=msg["threadId"],
                        subject=subject,
                        sender=from_val,
                        body=body,
                        received_at=received_at,
                        labels=email_detail.get("labelIds", []),
                    )
                )
            return emails
        except Exception as e:
            logger.error(f"Error fetching emails from sender {sender}: {e}")
            return []

    def create_commercial_filter(self, sender_email: str) -> None:
        """
        Creates a Gmail filter to mark as read and delete emails from the sender.
        """
        try:
            logger.info(f"Creating commercial filter for sender: {sender_email}")
            filter_body = {
                "criteria": {"from": sender_email},
                "action": {
                    "removeLabelIds": ["UNREAD", "INBOX"],
                    "addLabelIds": ["TRASH"],
                },
            }
            self.service.users().settings().filters().create(
                userId="me", body=filter_body
            ).execute()
            logger.info(f"Successfully created filter for {sender_email}")
        except Exception as e:
            logger.error(f"Failed to create filter for {sender_email}: {e}")

    def filter_exists(self, sender_email: str) -> bool:
        """
        Checks if a filter already exists for the sender.
        """
        try:
            results = (
                self.service.users().settings().filters().list(userId="me").execute()
            )
            filters = results.get("filter", [])
            for flt in filters:
                frm = flt.get("criteria", {}).get("from", "")
                if frm.lower() == sender_email.lower():
                    return True
            return False
        except Exception as e:
            logger.error(f"Error checking filter existence for {sender_email}: {e}")
            return False
