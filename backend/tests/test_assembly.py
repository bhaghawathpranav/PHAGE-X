from app.assembly import parse_assembly_fasta


def test_multicontig_assembly_qc_and_digest_are_deterministic():
    fasta = ">contig-a\n" + "ACGT" * 40 + "\n>contig-b\n" + "GGCC" * 30
    first_records, first = parse_assembly_fasta(fasta)
    second_records, second = parse_assembly_fasta(fasta)
    assert len(first_records) == 2
    assert first.total_length_bp == 280
    assert first.n50_bp == 160
    assert first.assembly_sha256 == second.assembly_sha256
    assert first_records == second_records


def test_assembly_rejects_invalid_alphabet():
    try:
        parse_assembly_fasta(">bad\n" + "ACGT" * 30 + "Z")
    except ValueError as error:
        assert "unsupported" in str(error)
    else:
        raise AssertionError("Invalid assembly alphabet was accepted")

