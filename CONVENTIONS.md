# Project Conventions (AI Instruction)

This file provides critical context for AI agents working on this project. **Read this first!**

## Environment & Python
- **Python Path**: Use `./.venv/bin/python`. This is a symbolic link to the `bo_env` Conda environment.
- **No `conda activate`**: Do not try to run `conda activate`. Instead, use the direct path to the python binary.

## Project Structure
- `src/main.py`: Main entry point for experiments.
- `src/bo_transform.py`: Core logic for 8D space transformation.
- `results/`: Output directory for all experiment reports and plots.

## Running Experiments
To run all functions:
```bash
./.venv/bin/python src/main.py --all
```

To run a specific function:
```bash
./.venv/bin/python src/main.py <function_name>
```

## Logs & Memory
- `states.md`: This file acts as the project's long-term memory. Read it to understand past decisions and current progress.
