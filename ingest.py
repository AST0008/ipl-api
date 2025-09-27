import json
import re
from sqlalchemy.orm import Session
from db import Base, engine, SessionLocal
from models import Player, Team, Match, Inning, BattingStat
from schemas import MatchSchema

def create_database():
    """Creates all database tables."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created.")

def get_or_create(session: Session, model, **kwargs):
    """
    Checks if an instance of a model exists in the database.
    If it exists, it returns the instance.
    If not, it creates a new one without committing.
    """
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    else:
        instance = model(**kwargs)
        session.add(instance)
        return instance

def clean_player_name(name: str) -> str:
    """Removes suffixes like (c) and † from player names."""
    # This regex removes characters like (c), †, or trailing asterisks from names.
    return re.sub(r'\s*\(c\)\s*|\s*†\s*|\s*\*+\s*$', '', name).strip()

def safe_int(val: str) -> int:
    """Safely converts a string to an integer, defaulting to 0."""
    return int(val) if val and val.isdigit() else 0

def safe_float(val: str):
    """Safely converts a string to a float, returning None for invalid values."""
    if val in ("-", "", None):
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None

def ingest_match_data(session: Session, match_data: dict, season: int):
    """
    Validates and ingests data for a single match into the database.
    This function is now atomic, committing only once at the end.
    """
    try:
        if 'teams' not in match_data or 'innings' not in match_data:
            print(f"Skipping a match in season {season}: Missing 'teams' or 'innings' key.")
            return

        info_dict = {
            "teams": match_data["teams"],
            "dates": None,  # This data is not available in the new JSON format
            "venue": None,  # This data is not available in the new JSON format
            "outcome": None # This data is not available in the new JSON format
        }

        # Reconstruct the data to ensure it fits our Pydantic schema before validation
        cleaned_data = {
            "info": info_dict,
            "innings": match_data.get("innings", [])
        }
        # --- End Data Cleaning ---

        # Validate the cleaned data with Pydantic schema
        match_info = MatchSchema(**cleaned_data)
        info = match_info.info
 
        team1 = get_or_create(session, Team, name=info.teams[0])
        team2 = get_or_create(session, Team, name=info.teams[1])
        
 
        winner_team = None

        match = Match(
            season=season,
            date=None, 
            venue=None,
            team1_id=team1.id,
            team2_id=team2.id,
            winner_id=None
        )
        session.add(match)
        session.flush() 

        for idx, inn_data in enumerate(match_info.innings, start=1):
            batting_team_full_name = inn_data.name.split('(')[0].strip()
            # Find the corresponding team object (created from short name)
            batting_team_short_name = info.teams[idx -1]
            batting_team = get_or_create(session, Team, name=batting_team_short_name)
            
            inning = Inning(
                match_id=match.id,
                team_id=batting_team.id,
                innings_no=idx
            )
            session.add(inning)
            session.flush() # Flush to get inning.id

            for b_stat in inn_data.batting:
                # Skip extras or other non-player entries
                if "player" not in b_stat:
                    continue
                
                cleaned_name = clean_player_name(b_stat["player"])
                player = get_or_create(session, Player, name=cleaned_name)
                
                stat = BattingStat(
                    inning_id=inning.id,
                    player_id=player.id,
                    runs=safe_int(b_stat.get("runs")),
                    balls=safe_int(b_stat.get("balls")),
                    fours=safe_int(b_stat.get("fours")),
                    sixes=safe_int(b_stat.get("sixes")),
                    strike_rate=safe_float(b_stat.get("strike_rate")),
                )
                session.add(stat)
        
        session.commit()
        print(f"Successfully ingested match: {info.teams[0]} vs {info.teams[1]}")

    except Exception as e:
        session.rollback()
        print(f"Failed to ingest a match for season {season}. Error: {e}")


if __name__ == "__main__":
    create_database()

    db = SessionLocal()
    
    # --- AUTOMATION LOOP ---
    # Loop through all seasons from 2008 to 2025
    for year in range(2008, 2025):
        file_path = f"ipl_{year}.json"
        print(f"\n--- Processing Season {year} ---")
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                matches_in_season = json.load(f)
            
            for match_json in matches_in_season:
                ingest_match_data(db, match_json, season=year)

        except FileNotFoundError:
            print(f"Data file not found for season {year}: {file_path}")
        except json.JSONDecodeError:
            print(f"Error decoding JSON from file: {file_path}")
        except Exception as e:
            print(f"An unexpected error occurred while processing {file_path}: {e}")

    db.close()
    print("\n--- Data ingestion complete for all seasons. ---")

