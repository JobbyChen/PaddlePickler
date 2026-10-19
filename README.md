# 🏓 PaddlePicker — Personalized Pickleball Paddle Recommender

A Python-based recommendation application that helps pickleball players find paddles suited to their skill level, playing style, budget, and performance preferences.

Built with **Python and Streamlit**, PaddlePicker transforms user preferences and structured product data into personalized paddle recommendations.

## Project Overview

Choosing a pickleball paddle can be challenging because products differ in price, weight, handle length, thickness, and playing characteristics.

PaddlePicker simplifies this process through an interactive recommendation system. Users enter their preferences, and the application evaluates compatible paddles using a custom weighted scoring algorithm.

The goal is to make product comparisons more accessible, understandable, and personalized.

## Key Features

- **Personalized Recommendations:** Ranks paddles according to user preferences.
- **Weighted Scoring Algorithm:** Evaluates power, control, spin, forgiveness, skill compatibility, and playing style.
- **Budget Awareness:** Incorporates price preferences and penalties for exceeding the user's budget.
- **Advanced Filtering:** Filters by handle category, weight category, price category, and playing style.
- **Interactive Interface:** Uses Streamlit sliders, dropdowns, and selection controls.
- **Explainable Recommendations:** Describes why each recommended paddle matches the user's preferences.
- **Product Comparisons:** Displays prices, weights, handle lengths, thicknesses, and performance ratings.
- **Product Images and Links:** Supports product imagery, image attribution, and external product links when available.

## Technologies Used

| Technology | Purpose |
|---|---|
| Python | Application logic and recommendation algorithm |
| Streamlit | Interactive web interface |
| CSV | Structured paddle data storage |
| Python Dataclasses | Consistent product data representation |
| Custom Weighted Scoring | Ranking and personalization |

## How the Recommendation Algorithm Works

PaddlePicker uses a rule-based, weighted scoring model rather than machine learning.

The algorithm calculates a score for each paddle using:

1. **Performance preferences:** Users assign importance levels to power, control, spin, and forgiveness.
2. **Skill compatibility:** Paddles receive bonuses or penalties based on suitability for beginner, intermediate, or advanced players.
3. **Playing style:** Paddles matching the user's preferred style receive additional points.
4. **Budget compatibility:** The scoring system accounts for price preferences and penalizes paddles exceeding the user's maximum budget.
5. **Physical preferences:** Paddle weight and handle length are compared
