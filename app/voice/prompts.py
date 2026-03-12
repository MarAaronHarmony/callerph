"""System prompt loader — loads business-specific prompts from markdown files."""

from pathlib import Path

PROMPTS_DIR = Path(__file__).parent.parent.parent / "prompts"


def load_prompt(prompt_file: str) -> str:
    """Load a system prompt from the prompts directory.

    Args:
        prompt_file: Filename (e.g., 'pagepro.md') relative to prompts/ directory.

    Returns:
        The prompt content as a string.

    Raises:
        FileNotFoundError: If the prompt file doesn't exist.
    """
    path = PROMPTS_DIR / prompt_file
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return path.read_text(encoding="utf-8")


def get_prompt_for_number(phone_number: str) -> str | None:
    """Look up the system prompt for a given Twilio phone number.

    Args:
        phone_number: The Twilio phone number that was called.

    Returns:
        The prompt content, or None if no client is mapped to this number.
    """
    from sqlmodel import Session, select

    from app.db.database import get_engine
    from app.models.client import Client

    with Session(get_engine()) as session:
        client = session.exec(
            select(Client).where(
                Client.phone_number == phone_number, Client.is_active == True  # noqa: E712
            )
        ).first()

        if not client:
            return None

        return load_prompt(client.prompt_file)
