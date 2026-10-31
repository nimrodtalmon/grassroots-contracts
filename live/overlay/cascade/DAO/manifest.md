# A run of the cascade on DAO

- Contract: `DAO` (`dao` to the checker), its owner's two files `programs/dao/DAO.txt` and `programs/dao/DAO.glp`, copied here as they stood at `fa053838`.
- The paper: ` (not on this machine)` at `unknown`, for the paper's own record.
- The tools: this repository at `fa053838` --- programs/gsc (the printer of the schemas' notation, notation_contract/1, the checker, check/2, and the compiler to VMAT, compile_contract/2), programs/vglp/cva/compiler (the compiler to the canonical CVA platform, compile/5, and its reader of the pragmas, pragmas.sh), glp_runtime's :emit (the canonical compilation to GLP).
- Run on 2026-10-31 18:52 UTC by `cascade.sh dao`; the suite's Section CAS re-runs it and holds these files to what the tools print.

| Artefact | What it holds |
|---|---|
| `DAO.txt` | the contract |
| `DAO.glp` | the act schemas, as terms |
| `schemas.txt` | the act schemas in GSC's notation, printed from the terms |
| `verdict.txt` | the checker's verdict: `syntactically_grassroots` |
| `vmat.tex` | the VMAT form, 17 displays, one per schema |
| `platform.vglp` | the canonical CVA platform, as printed |
| `platform.glp` | the platform compiled to GLP, as emitted |
| `interface.glp` | the platform's interface in sGLP's term form, as programs/sglp/cva/interface.sh prints it |
| (no run) | vGLP keeps no plays for dao |

What the tools refused or lacked:
- run: vGLP keeps no plays for dao
