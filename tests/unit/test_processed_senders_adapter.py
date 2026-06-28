from pathlib import Path

from src.adapters.json_processed_senders import JsonProcessedSendersAdapter


def test_json_adapter_lifecycle(tmp_path: Path):
    json_file = tmp_path / "senders.json"
    adapter = JsonProcessedSendersAdapter(file_path=json_file)

    # Initial state
    assert not adapter.is_processed("newsletter@xyz.com")
    assert adapter.get_all_processed() == []

    # Mark as processed
    adapter.mark_as_processed("newsletter@xyz.com")
    assert adapter.is_processed("newsletter@xyz.com")
    # Verify case insensitivity
    assert adapter.is_processed("NEWSLETTER@xyz.com")
    assert adapter.get_all_processed() == ["newsletter@xyz.com"]

    # Re-instantiate adapter to ensure actual file storage
    new_adapter = JsonProcessedSendersAdapter(file_path=json_file)
    assert new_adapter.is_processed("newsletter@xyz.com")


def test_json_adapter_corrupted_file(tmp_path: Path):
    json_file = tmp_path / "corrupt.json"
    with open(json_file, "w") as f:
        f.write("invalid json content")

    adapter = JsonProcessedSendersAdapter(file_path=json_file)
    # Should handle errors and return False/empty
    assert not adapter.is_processed("any@email.com")
    assert adapter.get_all_processed() == []

    # Should allow marking and healing the file
    adapter.mark_as_processed("any@email.com")
    assert adapter.is_processed("any@email.com")
    assert adapter.get_all_processed() == ["any@email.com"]
