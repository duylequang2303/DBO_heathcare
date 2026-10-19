# Requirements Document: Week 10 Web API Integration

## Introduction

This feature integrates the existing IDBO-based menu optimization solver into a web application. The system exposes the two-tier optimization pipeline through a FastAPI REST API and provides a browser-based user interface for generating personalized meal plans, visualizing nutritional information, and swapping individual menu items. This is a **technical prototype** for decision support, not a medical device, and does not replace professional nutritional or medical consultation.

## Glossary

- **System**: The FastAPI web application (`app/main.py` and associated modules)
- **Solver**: The existing `two_tier_optimize` function from `src/algorithms/two_tier_solver.py`
- **User_Profile**: A set of physiological parameters and preferences (`UserProfile` from `src/models/user_profile.py`)
- **Menu**: A collection of food items organized by meal type with portion sizes (`Menu` from `src/models/menu.py`)
- **Food_DB**: The singleton food database loaded from `data/processed/merged_food_nutrition.csv`
- **Slot**: A position within a meal where a food item is placed (e.g., "lunch_0", "lunch_1")
- **Pool**: The set of candidate food items valid for a specific slot, filtered by meal type, allergies, and dislikes
- **Target**: Nutritional goals (BMR, TDEE, calories, macronutrients) calculated from User_Profile
- **Frontend**: The browser-based user interface served as static HTML/CSS/JavaScript files
- **Seed**: A random number generator seed value ensuring deterministic solver behavior
- **Rounded_Portion**: Portion size rounded to the nearest 5 grams for display purposes only

## Requirements

### Requirement 1: FastAPI Application Bootstrap

**User Story:** As a system operator, I want the FastAPI application to start with a single command, so that I can quickly deploy and test the system.

#### Acceptance Criteria

1. THE System SHALL start when `uvicorn app.main:app` is executed
2. THE System SHALL load Food_DB exactly once during application startup
3. THE System SHALL serve static Frontend files from the `/` root path
4. THE System SHALL serve REST API endpoints under the `/api` prefix
5. THE System SHALL bind to a single network port for both static files and API

### Requirement 2: Health Check Endpoint

**User Story:** As a system operator, I want to verify the service is running, so that I can monitor system availability.

#### Acceptance Criteria

1. WHEN a GET request is sent to `/api/health`, THE System SHALL return HTTP 200
2. THE System SHALL include a JSON response body with status information

### Requirement 3: Profile Preset Management

**User Story:** As a developer, I want to retrieve predefined user profiles, so that I can test the system with consistent data.

#### Acceptance Criteria

1. THE System SHALL provide exactly three preset profiles: P1, P2, and P3
2. WHEN a GET request is sent to `/api/profiles`, THE System SHALL return all three preset profiles
3. THE System SHALL return profiles in JSON format matching the User_Profile schema
4. THE preset profiles SHALL match those defined in existing experimental scripts (P1: healthy adult, P2: weight loss, P3: medical conditions)

### Requirement 4: Nutritional Target Calculation

**User Story:** As a user, I want to calculate my nutritional targets from my profile, so that I understand my daily calorie and macronutrient needs.

#### Acceptance Criteria

1. WHEN a POST request with a valid User_Profile is sent to `/api/targets`, THE System SHALL calculate BMR using the Mifflin-St Jeor equation
2. WHEN a POST request with a valid User_Profile is sent to `/api/targets`, THE System SHALL calculate TDEE by multiplying BMR by the activity level factor
3. WHEN a POST request with a valid User_Profile is sent to `/api/targets`, THE System SHALL adjust daily calories based on the goal (lose/maintain/gain weight)
4. THE System SHALL calculate protein targets as 15-25% of daily calories
5. THE System SHALL calculate carbohydrate targets as 45-65% of daily calories
6. THE System SHALL calculate fat targets as 20-35% of daily calories
7. THE System SHALL return targets in JSON format with fields: `bmr`, `tdee`, `calories`, `protein_g`, `carbs_g`, `fat_g`, `fiber_g`, `sodium_mg`

### Requirement 5: Input Validation

**User Story:** As a system developer, I want to validate all user inputs, so that the system rejects malformed or dangerous data.

#### Acceptance Criteria

1. WHEN a User_Profile with age outside [0, 120] is submitted, THE System SHALL return HTTP 422
2. WHEN a User_Profile with weight_kg outside (0, 400] is submitted, THE System SHALL return HTTP 422
3. WHEN a User_Profile with height_cm outside (0, 250] is submitted, THE System SHALL return HTTP 422
4. WHEN a User_Profile with an invalid gender value is submitted, THE System SHALL return HTTP 422
5. WHEN a User_Profile with an invalid activity_level value is submitted, THE System SHALL return HTTP 422
6. WHEN a User_Profile with an invalid goal value is submitted, THE System SHALL return HTTP 422
7. WHEN a Seed value outside valid integer range is submitted, THE System SHALL return HTTP 422

### Requirement 6: Menu Generation

**User Story:** As a user, I want to generate a personalized meal plan, so that I can meet my nutritional targets while respecting my preferences and restrictions.

#### Acceptance Criteria

1. WHEN a POST request with User_Profile and Seed is sent to `/api/menu/generate`, THE System SHALL invoke the Solver with the specified seed
2. THE System SHALL execute the Solver in a background thread using `asyncio.to_thread` to avoid blocking the event loop
3. WHEN the configuration is "web", THE System SHALL use outer_iter=25, inner_iter=25, n_agents=10
4. WHEN the configuration is "smoke", THE System SHALL use outer_iter=5, inner_iter=5, n_agents=6
5. WHEN the configuration is "full", THE System SHALL use outer_iter=200, inner_iter=100, n_agents=20
6. THE System SHALL return a Menu with exactly `sum(meal_counts)` food items
7. THE System SHALL include both continuous portions and Rounded_Portions in the response
8. THE System SHALL include total daily nutritional values aggregated across all Menu items
9. THE System SHALL include the fitness score from the Solver
10. THE System SHALL include a list of constraint violations from validation

### Requirement 7: Menu Response Format

**User Story:** As a Frontend developer, I want a consistent JSON response format, so that I can reliably display menu information.

#### Acceptance Criteria

1. THE Menu response SHALL include an `items` array with each item containing: `food_id`, `name`, `slot`, `portion_g`, `portion_g_rounded`, `macros`
2. THE `macros` object for each item SHALL include: `calories`, `protein_g`, `carbs_g`, `fat_g`, `fiber_g`, `sodium_mg`
3. THE Menu response SHALL include a `totals` object with aggregated daily nutrition matching the `macros` structure
4. THE Menu response SHALL include a `targets` object with nutritional goals
5. THE Menu response SHALL include a `fitness` number representing solver quality
6. THE Menu response SHALL include a `violations` array of strings describing constraint violations
7. THE Menu response SHALL include a `diversity_pct` number if diversity metrics are available

### Requirement 8: Item Swap Functionality

**User Story:** As a user, I want to replace a single food item in my meal plan, so that I can adjust the menu to my preferences without regenerating the entire plan.

#### Acceptance Criteria

1. WHEN a POST request to `/api/menu/swap` specifies a valid Slot, THE System SHALL identify the food item at that position
2. WHEN `new_food_id` is null, THE System SHALL select a different food from the same Pool that is not already present in the same meal
3. WHEN `new_food_id` is provided, THE System SHALL verify it exists in the Pool for that Slot
4. THE System SHALL re-optimize portion sizes for the modified food list using the inner solver
5. THE System SHALL return the updated Menu with recalculated nutritional totals
6. THE System SHALL include a `delta` object showing changes in calories and macronutrients

### Requirement 9: Swap Constraint Enforcement

**User Story:** As a user, I want swap operations to respect my dietary restrictions, so that the system does not suggest foods I cannot eat.

#### Acceptance Criteria

1. WHEN a Slot identifier does not exist in the meal structure, THE System SHALL return HTTP 400
2. WHEN the Pool for a Slot contains no alternative foods, THE System SHALL return HTTP 409 and suggest the closest available alternative
3. WHEN `new_food_id` is already present in the same meal, THE System SHALL return HTTP 400
4. WHEN `new_food_id` violates allergy restrictions, THE System SHALL return HTTP 400
5. WHEN `new_food_id` violates dislike preferences, THE System SHALL return HTTP 400

### Requirement 10: Food Search

**User Story:** As a user, I want to search for foods by name, so that I can manually select items for swapping.

#### Acceptance Criteria

1. WHEN a GET request to `/api/foods` includes a query parameter `q`, THE System SHALL return foods whose names contain the query string (case-insensitive)
2. WHEN a GET request to `/api/foods` includes a limit parameter, THE System SHALL return at most that many results
3. WHEN no query parameter is provided, THE System SHALL return an empty list or a default set of foods
4. THE System SHALL return each food with fields: `food_id`, `name`, `calories`, `protein_g`, `carbs_g`, `fat_g`

### Requirement 11: Deterministic Solver Behavior

**User Story:** As a researcher, I want identical inputs to produce identical outputs, so that I can reproduce experimental results.

#### Acceptance Criteria

1. WHEN the same User_Profile, Seed, and configuration are provided twice, THE Solver SHALL produce identical food_ids
2. WHEN the same User_Profile, Seed, and configuration are provided twice, THE Solver SHALL produce identical portion sizes within floating-point tolerance
3. THE System SHALL NOT apply portion rounding before passing data to the Solver
4. THE System SHALL apply Rounded_Portion calculations only in the response JSON

### Requirement 12: Frontend Display

**User Story:** As a user, I want to see my meal plan in a table with nutritional information, so that I understand what I am eating.

#### Acceptance Criteria

1. THE Frontend SHALL display a form to input User_Profile fields
2. THE Frontend SHALL display a table of Menu items with columns: meal type, food name, portion (grams), calories, protein, carbs, fat, fiber, sodium
3. THE Frontend SHALL display total daily nutrition below the item table
4. THE Frontend SHALL display percentage achievement for each nutrient relative to Target
5. WHEN a Menu is loaded, THE Frontend SHALL display Rounded_Portions in the table, not continuous values

### Requirement 13: Nutritional Visualization

**User Story:** As a user, I want to see my nutritional achievement visually, so that I can quickly assess whether my meal plan meets my goals.

#### Acceptance Criteria

1. THE Frontend SHALL display progress bars for calories, protein, carbohydrates, fat, fiber, and sodium
2. THE progress bars SHALL show percentage of Target achieved (total / target * 100%)
3. THE Frontend SHALL display a radar chart showing nutritional balance across all macronutrients
4. THE radar chart SHALL use Chart.js library

### Requirement 14: Swap UI Interaction

**User Story:** As a user, I want to click a button on each food item to swap it, so that I can easily customize my meal plan.

#### Acceptance Criteria

1. THE Frontend SHALL display a "Swap" button next to each food item in the Menu table
2. WHEN the "Swap" button is clicked, THE Frontend SHALL send a POST request to `/api/menu/swap` with the item's Slot
3. WHEN the swap completes, THE Frontend SHALL update the table row with the new food item
4. WHEN the swap completes, THE Frontend SHALL update totals and visualizations with the new nutritional data
5. WHEN a swap fails, THE Frontend SHALL display an error message to the user

### Requirement 15: Violation Warnings

**User Story:** As a user, I want to see warnings when my meal plan violates nutritional constraints, so that I am aware of potential issues.

#### Acceptance Criteria

1. WHEN a Menu violates calorie constraints (±10%), THE Frontend SHALL display a red badge with the violation description
2. WHEN a Menu violates protein or carbohydrate constraints (±15%), THE Frontend SHALL display a yellow badge
3. WHEN a Menu violates fat constraints (±20%), THE Frontend SHALL display a yellow badge
4. WHEN a Menu violates fiber constraints (±30%), THE Frontend SHALL display a yellow badge
5. WHEN a Menu has no violations, THE Frontend SHALL display a green "All targets met" badge

### Requirement 16: Performance Requirements

**User Story:** As a user, I want the system to respond within a reasonable time, so that I can interact with it efficiently.

#### Acceptance Criteria

1. THE `/api/targets` endpoint SHALL respond within 100 milliseconds
2. THE `/api/menu/generate` endpoint with "web" configuration SHALL complete within 30 seconds
3. THE `/api/menu/swap` endpoint SHALL complete within 15 seconds
4. THE Food_DB SHALL remain in memory for the lifetime of the application process

### Requirement 17: Solver Integration Constraints

**User Story:** As a maintainer, I want to preserve the existing solver interface, so that I do not break existing experimental code.

#### Acceptance Criteria

1. THE System SHALL NOT modify the signature of `two_tier_optimize` function
2. THE System SHALL NOT modify the signature of `DBO.optimize` or `IDBO.optimize` methods
3. THE System SHALL NOT modify the `Menu.encode()` or `Menu.decode()` API
4. THE System SHALL use existing functions from `src/models/food_selector.py` for building pools and decoding selections

### Requirement 18: Data Integrity

**User Story:** As a researcher, I want all displayed nutritional data to come from the solver, so that I can trust the accuracy of the system.

#### Acceptance Criteria

1. THE System SHALL NOT hard-code nutritional values in API responses
2. THE System SHALL NOT estimate or proxy missing nutritional data
3. THE System SHALL calculate all nutritional totals by aggregating MenuItem values from the Menu
4. WHEN a nutrient field is missing or NaN in Food_DB, THE System SHALL treat it as 0.0
5. THE System SHALL NOT display negative, NaN, or infinite nutritional values

### Requirement 19: Error Handling

**User Story:** As a user, I want clear error messages when something goes wrong, so that I understand how to fix the problem.

#### Acceptance Criteria

1. WHEN the Solver fails to find a valid solution, THE System SHALL return HTTP 500 with a descriptive error message
2. WHEN Food_DB fails to load, THE System SHALL log the error and refuse to start
3. WHEN a Pool has insufficient foods, THE System SHALL return HTTP 409 with the pool name and available count
4. WHEN an internal exception occurs, THE System SHALL return HTTP 500 without exposing stack traces to the client

### Requirement 20: Static File Serving

**User Story:** As a deployment engineer, I want the FastAPI application to serve static files, so that I can deploy with a single process on one port.

#### Acceptance Criteria

1. THE System SHALL mount a StaticFiles handler at the root path `/`
2. THE System SHALL serve `index.html` from `app/static/index.html`
3. THE System SHALL serve CSS files from `app/static/css/`
4. THE System SHALL serve JavaScript files from `app/static/js/`
5. WHEN a request is made to `/`, THE System SHALL return the `index.html` file

