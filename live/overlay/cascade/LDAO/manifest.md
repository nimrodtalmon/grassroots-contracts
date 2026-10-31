# A run of the cascade on LDAO

- Contract: `LDAO` (`ldao` to the checker), its owner's two files `programs/ldao/LDAO.txt` and `programs/ldao/LDAO.glp`, copied here as they stood at `fa053838`.
- The paper: ` (not on this machine)` at `unknown`, for the paper's own record.
- The tools: this repository at `fa053838` --- programs/gsc (the printer of the schemas' notation, notation_contract/1, the checker, check/2, and the compiler to VMAT, compile_contract/2), programs/vglp/cva/compiler (the compiler to the canonical CVA platform, compile/5, and its reader of the pragmas, pragmas.sh), glp_runtime's :emit (the canonical compilation to GLP).
- Run on 2026-10-31 15:40 UTC by `cascade.sh ldao`; the suite's Section CAS re-runs it and holds these files to what the tools print.

| Artefact | What it holds |
|---|---|
| `LDAO.txt` | the contract |
| `LDAO.glp` | the act schemas, as terms |
| `schemas.txt` | the act schemas in GSC's notation, printed from the terms |
| `verdict.txt` | the checker's verdict: `syntactically_grassroots` |
| `vmat.tex` | the VMAT form, 19 displays, one per schema |
| `platform.vglp` | the canonical CVA platform, as printed |
| `platform.glp` | the platform compiled to GLP, as emitted |
| `interface.glp` | the platform's interface in sGLP's term form, as programs/sglp/cva/interface.sh prints it |
| (no run) | vGLP keeps no plays for ldao |

What the tools refused or lacked:
- run: vGLP keeps no plays for ldao
