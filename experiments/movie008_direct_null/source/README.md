# Movie008 pre-outcome executable source

The q8 conditional mode-bank builder and shared utilities are deposited as browsable Python files before the mode bank or any fresh twin source is generated.

The exact remaining pre-outcome files—`run_experiment.py`, `verify_and_report.py`, and `run_all.py`—are stored in `Movie008_Remaining_Source.tar.xz`. Their individual SHA256 values are pinned in `../SOURCE_FREEZE.json`; the archive SHA256 is `7fdff2c831d5d861559269b348d70ba6323ee98a33a1a00aa46441527c331736`.

This packaging choice avoids a long sequence of independent contents-API writes while preserving the exact bytes before outcomes. The files will also be deposited individually with the completion record. The authenticated binary inputs remain outside GitHub in the Movie007 full artifact; `../INPUT_MANIFEST.json` records their hashes, shapes, and provenance.

Execution order:

```bash
python source/build_mode_bank.py
# freeze MODE_BANK.npz and MODE_BANK.json before fresh sources
python source/run_experiment.py
python source/verify_and_report.py
```

No physical ray call or Paper-I unit is authorized.
