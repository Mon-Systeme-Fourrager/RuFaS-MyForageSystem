[![Flake8](https://img.shields.io/badge/Flake8-passed-brightgreen)](https://github.com/RuminantFarmSystems/MASM/actions/workflows/combined_format_lint_test_mypy.yml)
[![Pytest](https://img.shields.io/badge/Pytest-passed-brightgreen)](https://github.com/RuminantFarmSystems/MASM/actions/workflows/combined_format_lint_test_mypy.yml)
[![Coverage](https://img.shields.io/badge/Coverage-96%25-brightgreen)](https://github.com/RuminantFarmSystems/MASM/actions/workflows/combined_format_lint_test_mypy.yml)
[![Mypy](https://img.shields.io/badge/Mypy-3201%20errors-red)](https://github.com/RuminantFarmSystems/MASM/actions/workflows/combined_format_lint_test_mypy.yml)

---

# RuFaS: Ruminant Farm Systems

**RuFaS** is an open-source, next-generation, whole-farm modeling environment that simulates dairy farm production and environmental impact. It is designed to support research, innovation, and sustainable decision-making in ruminant animal agriculture.

---

# Dependency
For Mon Système Fourrager, the default branch is `dev-msf`.
This branch MUST NOT be deleted, since:
- it includes modifications to the RuFaS source code in order to allow its usage as a dependency
    (e.g. removing useless verifications of the python version and dependencies);
- it is used to produce the tags which are used in other repos (`rufas-api` and `msf-rufas`).

Therefore, `dev-msf` is NOT the branch that should be forked with RuFaS. Instead, the branch
`dev` is the one that should be synched with `origin`, then `dev-msf` should be `rebase` on `dev`.

````mermaid
flowchart LR
    subgraph rufas["RuFaS"]
        dev["dev"]
    end

    subgraph RuFaS-MyForageSystem
        dev --> dev_forked[dev] --> dev-msf[dev-msf] --> tags 
    end

    subgraph rufas-api
        tags --> models[[Pydantic models generation]] 
    end
    subgraph msf-rufas
        tags --> wrapper[[RuFaS wrapper]] 
    end

````