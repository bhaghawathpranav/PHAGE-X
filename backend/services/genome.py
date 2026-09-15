from typing import Tuple


VALID_BASES = set("ATGCN")


def parse_fasta(fasta_text: str) -> Tuple[str, str]:
    """
    Parse a FASTA-formatted genome.

    Returns:
        (header, sequence)
    """
    lines = [
        line.strip()
        for line in fasta_text.strip().splitlines()
        if line.strip()
    ]

    if not lines:
        raise ValueError("Genome input is empty.")

    if not lines[0].startswith(">"):
        raise ValueError("Invalid FASTA format: missing header.")

    header = lines[0][1:].strip()

    if not header:
        raise ValueError("FASTA header is empty.")

    sequence = "".join(lines[1:]).upper()

    if not sequence:
        raise ValueError("Genome sequence is empty.")

    invalid_bases = set(sequence) - VALID_BASES

    if invalid_bases:
        raise ValueError(
            f"Invalid DNA characters found: {sorted(invalid_bases)}"
        )

    return header, sequence


def validate_genome(fasta_text: str) -> bool:
    """Return True if the genome is valid FASTA."""
    parse_fasta(fasta_text)
    return True


def get_bacterium_id(
    fasta_text: str,
    bacterium_id: str | None = None,
) -> str:
    """
    Return the bacterium identifier.

    Uses the explicitly supplied ID when available.
    Otherwise uses the FASTA header.
    """
    if bacterium_id and bacterium_id.strip():
        return bacterium_id.strip()

    header, _ = parse_fasta(fasta_text)
    return header
