# ⚾ Diamond Edge — MLB Betting Analysis Dashboard

A locally-run MLB moneyline betting analysis tool that scrapes Baseball Reference and applies three statistical models to predict game outcomes with full mathematical transparency.

## Models Used
- **Pythagorean Expectation** (25%) — estimates true win% from runs scored/allowed
- **Log5 Method** (35%) — head-to-head win probability from season records
- **Poisson Regression** (40%) — models run scoring distributions to simulate outcomes

## Features
- Today's MLB games with blended win probabilities
- Full mathematical workings shown for every prediction
- 95% confidence intervals across models
- Moneyline edge calculator vs. market odds
- Dark-themed Flask dashboard, fully portable

## Requirements
- Python 3.8+
- Internet connection (scrapes Baseball Reference)

## Setup

1. Clone the repo: