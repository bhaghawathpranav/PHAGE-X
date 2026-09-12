# Laboratory observation boundary

`POST /api/lab-observations` accepts a deliberately small, structured assay record tied to an analysis and phage ID. Allowed assays are spot test, plaque assay, efficiency of plating, and liquid culture. Allowed outcomes are susceptible, intermediate, resistant, and inconclusive.

The schema does not accept patient identifiers, free-text clinical notes, treatment information, or genomic sequence. `contains_patient_data` can only be `false`. Records are append-only research observations and never promote a prediction, retrain a model, or remove the laboratory-validation warning automatically.

Before multi-user deployment, this local SQLite adapter must be replaced with authenticated, access-controlled storage with retention rules, audit access, backups, deletion procedures, and institutional review of the data policy.
