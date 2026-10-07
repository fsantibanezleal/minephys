# Quickstart 000 — using minephys and adding a model
Spec: ./spec.md

## Use a model (consumer)

```bash
uv add "minephys @ git+https://github.com/fsantibanezleal/minephys"
```

```python
import numpy as np
import minephys
from minephys import haulage

# SI at the API: kg, fractions, W, m/s
v = haulage.rimpull_limited_speed(power=1.8e6, mass=400_000.0, total_resistance=0.12)

# arrays broadcast
v_grid = haulage.rimpull_limited_speed(power=1.8e6, mass=400_000.0, total_resistance=np.linspace(0.04, 0.16, 4))

# hostile input raises, naming the argument
try:
    haulage.rimpull_limited_speed(power=1.8e6, mass=-1.0, total_resistance=0.12)
except minephys.InputError as err:
    print(err.argument)  # "mass"
```

Every function's docstring is its model card: equation, units, source and page, validity range and the knowledge rows
it reads. Rows marked UNVERIFIED are never defaults for site or material values; pass your own.

## Add or change a model (contributor)

1. **Spec.** Add the requirement rows (EARS) to the module spec, with the oracle named in its `plan.md`.
2. **Knowledge rows.** Add every constant to the module's table with value or range, units, role, citation, page,
   verification and symbol (`data-model.md`). If you read the value on the primary source, mark it `verified` with the
   date; otherwise leave it `UNVERIFIED` and say in `notes` where the transcription comes from.
3. **Tests first.** Write the failing tests in their own file `tests/<level>/test_t_<nnn>_<xxx>_<slug>.py` with
   `@pytest.mark.req("<ID>")`, `@pytest.mark.oracle("<kind>", "<reference>")` and, for each verified row it pins,
   `@pytest.mark.knowledge("<row id>")`. Lock them and commit `[red]`.
4. **Implement** until they pass without touching the locked tests; commit `[green]`.
5. **Regenerate** the knowledge pages (`uv run python tools/gen_knowledge_docs.py`) and run every check listed in
   `CONTRIBUTING.md`.
