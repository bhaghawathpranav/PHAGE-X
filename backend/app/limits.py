"""Central request-size limits.

The legacy demo route accepts one synthetic single-record FASTA and is kept at
5 MB to bound request parsing for a path that does not perform real genomics.
The real assembly pipeline accepts multi-contig bacterial assemblies up to
15 MB because complete Klebsiella assemblies routinely exceed the demo cap.
"""

DEMO_FASTA_MAX_BYTES = 5_000_000
ASSEMBLY_FASTA_MAX_BYTES = 15_000_000

