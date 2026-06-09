import logging
import sys
from src.adapters.gmail_adapter import GmailOAuthAdapter
from src.adapters.ollama_adapter import OllamaLLMAdapter
from src.config import settings
from src.domain.use_cases import ProcessInboxUseCase

logger = logging.getLogger("zip.cli")

def main() -> None:
    """
    Primary CLI driver that boots up the adapters and runs the ZIP process.
    """
    logger.info("Starting Zero Inbox Gmail (ZIP) run...")
    logger.info(f"Environment: {settings.env} | Target LLM: {settings.ollama_model}")
    
    try:
        # Instantiate adapters (driven actors)
        # GmailOAuthAdapter triggers the OAuth validation flow
        gmail_adapter = GmailOAuthAdapter()
        ollama_adapter = OllamaLLMAdapter()
        
        # Instantiate use case (orchestrator)
        use_case = ProcessInboxUseCase(
            gmail_port=gmail_adapter,
            llm_port=ollama_adapter
        )
        
        # Execute processing loop (up to 20 emails by default)
        logger.info("Executing use case...")
        results = use_case.execute(max_emails=20)
        
        # Log results summary
        logger.info("=" * 60)
        logger.info(f"ZIP Execution Summary: processed {len(results)} emails.")
        for idx, res in enumerate(results, start=1):
            logger.info(
                f"[{idx}] Email ID: {res.email_id} | "
                f"Action: {res.action.value.upper()} | "
                f"Label: {res.label_to_add or 'N/A'} | "
                f"Reason: {res.reason}"
            )
        logger.info("=" * 60)
        logger.info("ZIP run completed successfully.")
        
    except Exception as e:
        logger.critical(f"ZIP run failed due to a critical initialization error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
