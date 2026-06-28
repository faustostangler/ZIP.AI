import json
import logging
import os
from pathlib import Path

from src.config import settings
from src.ports.processed_senders import ProcessedSendersPort

logger = logging.getLogger("zip.json_senders")


class JsonProcessedSendersAdapter(ProcessedSendersPort):
    """
    Adapter implementing ProcessedSendersPort using a local JSON file.
    """

    def __init__(self, file_path: Path | None = None) -> None:
        self.file_path = file_path or settings.processed_senders_json_path
        # Ensure parent directories exist
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def _read_file(self) -> list[str]:
        if not self.file_path.exists():
            return []
        try:
            with open(self.file_path, encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return [str(item) for item in data]
                return []
        except Exception as e:
            logger.warning(
                f"Failed to read processed senders file at {self.file_path}: {e}. Returning empty list."
            )
            return []

    def _write_file(self, senders: list[str]) -> None:
        # Atomic write to prevent corruption
        temp_file = self.file_path.with_suffix(".tmp")
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(senders, f, indent=4)
            # Atomically replace target file
            os.replace(temp_file, self.file_path)
        except Exception as e:
            logger.error(
                f"Failed to write processed senders file at {self.file_path}: {e}"
            )
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except Exception:
                    pass
            raise

    def is_processed(self, email_address: str) -> bool:
        senders = self._read_file()
        normalized = email_address.strip().lower()
        return any(sender.strip().lower() == normalized for sender in senders)

    def mark_as_processed(self, email_address: str) -> None:
        normalized = email_address.strip().lower()
        senders = self._read_file()
        if normalized not in [s.strip().lower() for s in senders]:
            senders.append(normalized)
            self._write_file(senders)
            logger.info(f"Marked sender {normalized} as processed.")

    def get_all_processed(self) -> list[str]:
        return self._read_file()
