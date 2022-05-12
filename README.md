# Adapting Consensus Algorithms for Reduced Latency with Multi-Armed Bandits
This readme shows how to set up and run the experiments for this project.

## Requirements

Code has been tested on Python 3.8 from Anaconda. Packages required:

 - numpy
 - matplotlib
 - joblib


## Running Simulations

### n=10, m up to 3

```python run_simulation.py configs/project_experiments/test_n_10_max_m_3_g0.6_f-3_super_config.yaml output/results.pkl```

Experiment for fixed `m=3`:

```python run_simulation.py configs/project_experiments/test_n_10_max_m_3_g0.6_f-3_super_config.yaml output/results_fixed_m_3.pkl 3```

### n=13, m up to 4

```python run_simulation.py configs/project_experiments/exp_n_13_max_m_4_super_config.yaml output/results_n13.pkl```

Experiment for fixed `m=4`:

```python run_simulation.py configs/project_experiments/exp_n_13_max_m_4_super_config.yaml output/results_fixed_m4.pkl 4```

## Visualizations

### n=10, m up to 3

```python analyze_results.py output/results.pkl configs/project_experiments/test_n_10_max_m_3_g0.6_f-3_super_config.yaml output/results_fixed_m_3.pkl```

### n=13, m up to 4

```python analyze_results.py output/results_n13.pkl configs/project_experiments/test_n_10_max_m_3_g0.6_f-3_super_config.yaml output/results_fixed_m4.pkl```
