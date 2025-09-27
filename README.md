# IPL Data Scraping and API

This project provides a complete solution for ingesting historical Indian Premier League (IPL) match data, storing it in a robust relational database, and exposing it through a high-performance RESTful API built with FastAPI.

## Key Features

- **Automated Data Scraping:** Script scrapes and process IPL data files from 2008 to 2025 (`ipl_{year}.json`), cleans the data, and populates the database.
- **Robust Database Schema:** Uses SQLAlchemy for relational schema covering players, teams, matches, innings, and batting statistics.
- **Data Cleaning:** Cleans player names by removing suffixes like `(c)` and `†` to prevent duplicates.
- **High-Performance API:** Built with Python and FastAPI to serve cleaned IPL data.
- **Interactive Documentation:** Swagger UI for exploring and testing endpoints.
- **Atomic Transactions:** Ingestion script rolls back changes for a match if errors occur, ensuring data integrity.

## Project Structure

```
.
├── ipl_2008.json        # Example data file (place all season files here)
├── ipl_2009.json
├── ...
├── db.py                # SQLAlchemy database setup and session management
├── models.py            # SQLAlchemy ORM models (table definitions)
├── schemas.py           # Pydantic schemas for validation and API responses
├── data_ingestion.py    # Script for ingesting all data into the DB
├── main.py              # FastAPI app with all API endpoints
└── requirements.txt     # Project dependencies
```

## Setup and Installation

### Clone the Repository

```sh
git clone <your-repository-url>
cd <your-repository-directory>
```

### Create and Activate a Virtual Environment

#### For Windows

```sh
python -m venv venv
.\venv\Scripts\activate
```

#### For macOS/Linux

```sh
python3 -m venv venv
source venv/bin/activate
```

### Install Dependencies

```sh
pip install -r requirements.txt
```

### Add Data Files

Place your IPL data files (e.g., `ipl_2008.json`, `ipl_2009.json`, etc.) in the root directory.

## How to Run

There are two main steps: ingesting the data and starting the API server.

### Step 1: Ingest the Data

Run the ingestion script to create `ipl_stats.db` and populate it with data from your JSON files.

```sh
python ingest.py
```

### Step 2: Start the API Server

Start the FastAPI server using Uvicorn.

```sh
uvicorn main:app --reload
```

The API will be running at [http://127.0.0.1:8000](http://127.0.0.1:8000).

## API Endpoints

Test endpoints interactively at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

### 1. Get All Teams

- **Endpoint:** `GET /teams`
- **Description:** Retrieves all teams.
- **Example Request:** `http://127.0.0.1:8000/teams`
- **Example Response:**
    ```json
    [
        { "id": 1, "name": "KKR" },
        { "id": 2, "name": "RCB" }
    ]
    ```

### 2. Get All Players

- **Endpoint:** `GET /players`
- **Description:** Retrieves all players.
- **Example Request:** `http://127.0.0.1:8000/players`
- **Example Response:**
    ```json
    [
        { "id": 1, "name": "Sourav Ganguly" },
        { "id": 2, "name": "Brendon McCullum" }
    ]
    ```

### 3. Get Match Scorecard

- **Endpoint:** `GET /matches/{match_id}`
- **Description:** Retrieves detailed scorecard for a match.
- **Example Request:** `http://127.0.0.1:8000/matches/1`
- **Example Response:**
    ```json
    {
        "id": 1,
        "season": 2008,
        "team1": { "id": 1, "name": "KKR" },
        "team2": { "id": 2, "name": "RCB" },
        "innings": [
            {
                "innings_no": 1,
                "team": { "id": 1, "name": "KKR" },
                "batting_stats": [
                    {
                        "runs": 158, "balls": 73, "fours": 10, "sixes": 13, "strike_rate": 216.43,
                        "player": { "id": 2, "name": "Brendon McCullum" }
                    }
                ]
            }
        ]
    }
    ```

### 4. Get Player Career Stats

- **Endpoint:** `GET /players/{player_id}/stats`
- **Description:** Retrieves career batting stats for a player.
- **Example Request:** `http://127.0.0.1:8000/players/2/stats`
- **Example Response:**
    ```json
    {
        "player_id": 2,
        "player_name": "Brendon McCullum",
        "matches_played": 109,
        "total_runs": 2880,
        "total_balls": 2110,
        "fifties": 10,
        "hundreds": 2,
        "strike_rate": 136.49
    }
    ```

### 5. Get Head-to-Head Stats

- **Endpoint:** `GET /stats/head-to-head`
- **Description:** Retrieves match history between two teams.
- **Parameters:** `team1_id` (integer), `team2_id` (integer)
- **Example Request:** `http://127.0.0.1:8000/stats/head-to-head?team1_id=1&team2_id=2`
- **Example Response:**
    ```json
    {
        "team1_name": "KKR",
        "team2_name": "RCB",
        "total_matches": 32,
        "team1_wins": 0,
        "team2_wins": 0
    }
    ```

> **Note:** `team1_wins` and `team2_wins` are `0` as the source JSON files do not contain match winner info. The API reflects available data.

## Technology Stack

- **Backend Framework:** FastAPI
- **Database ORM:** SQLAlchemy
- **Data Validation:** Pydantic
- **Database:** Neon DB
- **ASGI Server:** Uvicorn
