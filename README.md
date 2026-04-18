# Thesis Project — Prompt Minimal vs Detailed (Python)

Obiettivo: per ogni esperimento generare **la stessa funzione** due volte (prompt minimale vs prompt dettagliato), eseguire **gli stessi test** e confrontare i risultati su:
- sintassi
- esecuzione (smoke run)
- test
- copertura
- lint
- type checking
- complessità
- sicurezza di base

## Struttura

- `experiments/Experiment01/` (e così via)
  - `basic.py` (versione con prompt base)
  - `advanced.py` (versione con prompt avanzato)
  - Nota: dentro ogni `ExperimentNN` devono esserci **solo questi 2 file**.
- `tests/Experiment01/` (e così via)
  - test pytest usati per entrambe le versioni
- `experiments_manifest.json`
  - definisce per ogni esperimento un *smoke call* (argomenti) usato per la verifica “esecuzione”
- `run_experiments.py`
  - runner che valuta `basic.py` vs `advanced.py` e stampa/salva i risultati

## Come aggiungere un esperimento

1. Crea `experiments/ExperimentNN/`.
2. Inserisci **solo**:
   - `basic.py`
   - `advanced.py`
3. Crea i test in `tests/ExperimentNN/` (uguali per entrambe le versioni).
4. Aggiungi/aggiorna la voce in `experiments_manifest.json`.

## Esecuzione

- Lancia il runner:
  - `python run_experiments.py`

Output:
- stampa un riepilogo su console
- salva un JSON in `results/` con tutti i dettagli
