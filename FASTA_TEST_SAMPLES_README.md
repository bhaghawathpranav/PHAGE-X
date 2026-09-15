# PHAGE-X FASTA test set

These five unmodified RefSeq genome assemblies are public `Klebsiella pneumoniae` test inputs from NCBI. They are intended for software demonstration and pipeline testing only.

## How to use a sample

1. Start PHAGE-X and open `http://127.0.0.1:5173/`.
2. Go to **Choose your input** and select **Use my FASTA**.
3. Select **Choose FASTA file** and choose one `.fna` file from this package.
4. Click **Check assembly** to run FASTA parsing and assembly QC.
5. Click **Extract K locus** to run species confirmation and Kaptive typing.
6. Click **Generate phage shortlist** to run ESM-2 feature extraction and the XGBoost catalog ranking.

The first ESM-2 run can take longer because the model is loaded into memory. Later runs may reuse cached embeddings.

## Expected results verified on 2026-09-15

| File | NCBI strain | Bases | Contigs | ANI | K locus | Full ranking |
|---|---|---:|---:|---:|---|---|
| `GCF_000364385.3_ASM36438v3_genomic.fna` | ATCC BAA-2146 | 5,781,501 | 5 | 99.6154% | KL74 | Pass |
| `GCF_000739495.1_ASM73949v1_genomic.fna` | carbapenem-resistant blaNDM-1 | 5,510,332 | 3 | 99.4309% | KL108 | Pass |
| `GCF_001022035.1_ASM102203v1_genomic.fna` | CAV1392 | 5,552,491 | 3 | 99.6858% | KL125 | Pass |
| `GCF_001022235.1_ASM102223v1_genomic.fna` | CAV1596 | 5,620,516 | 3 | 99.6092% | KL107 | Pass |
| `GCF_001185665.2_ASM118566v3_genomic.fna` | MGH83 | 5,969,148 | 5 | 99.0406% | KL42 | Pass |

ANI is the fastANI match against the PHAGE-X `K. pneumoniae` species reference. A passing software result is not evidence of phage susceptibility or treatment effectiveness.

## Official NCBI sources

- [GCF_000364385.3](https://www.ncbi.nlm.nih.gov/datasets/genome/GCF_000364385.3/)
- [GCF_000739495.1](https://www.ncbi.nlm.nih.gov/datasets/genome/GCF_000739495.1/)
- [GCF_001022035.1](https://www.ncbi.nlm.nih.gov/datasets/genome/GCF_001022035.1/)
- [GCF_001022235.1](https://www.ncbi.nlm.nih.gov/datasets/genome/GCF_001022235.1/)
- [GCF_001185665.2](https://www.ncbi.nlm.nih.gov/datasets/genome/GCF_001185665.2/)

## SHA-256 checksums

```text
09daf5ed0792910798be0570c72fd0e56468eaeecb7bcc3eea63a4af4cc948ea  GCF_000364385.3_ASM36438v3_genomic.fna
48ce79d02ed214c0e293f85fbae3060a8c86b5b7389a2b91e156c7d23ad7ba45  GCF_000739495.1_ASM73949v1_genomic.fna
33ed2088fde17ae6d38b9f41e3c5905d896af0c0b460c07315a19879702f87de  GCF_001022035.1_ASM102203v1_genomic.fna
0b444f91bf204100eed5655c05fc2d38f2eb4fb0f771b4623935acee063b22a2  GCF_001022235.1_ASM102223v1_genomic.fna
9438f1bc98776c4c762cfd217872399dc1a111c26a169b2fbe0ce98b65e222e2  GCF_001185665.2_ASM118566v3_genomic.fna
```
