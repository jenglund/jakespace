# Ranqr - Song Ranking System

A sophisticated song ranking system using pairwise comparisons with triangle inconsistency detection and resolution.

## Features

- **Pairwise Comparisons**: Rank songs by comparing them two at a time
- **Histogram Analysis**: View score distributions and statistics
- **Fixed Triangles Mode**: Detect and resolve ranking inconsistencies (cycles) in the comparison graph
  - Automatically identifies triangular cycles (A > B > C > A)
  - Calculates "dissonance" to prioritize the most problematic cycles
  - Provides 6 possible resolutions with predicted impact on overall consistency

## Installation

```bash
pip install -r requirements.txt
```

## Running Tests

```bash
pytest -v --cov=backend tests/
```

## Running the Application

```bash
python backend/app.py
```

Then open `frontend/index.html` in your browser.

## How Fixed Triangles Works

1. **Detection**: The system finds all cycles of three songs where rankings are inconsistent
2. **Dissonance Calculation**: For each triangle, calculates the sum of the two largest score differences
3. **Prioritization**: Shows the triangle with highest dissonance first
4. **Resolution**: Presents all 6 possible orderings and shows how each would affect overall consistency
