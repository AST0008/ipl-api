from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, case
from typing import List

from db import SessionLocal, engine, Base
from models import Player, Team, Match, Inning, BattingStat
import schemas


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="IPL Data API",
    description="An API to explore player and match statistics from the Indian Premier League.",
    version="1.0.0",
)

# Dependency to get a DB session for each request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/", tags=["Root"])
def read_root():
    """ A simple welcome message for the root api."""
    return {"message": "Welcome to the IPL Data API. Go to /docs for an interactive API documentation."}

@app.get("/teams", response_model=List[schemas.TeamResponse], tags=["Teams"])
def get_all_teams(db: Session = Depends(get_db)):
    """
    Retrieves a list of all teams in the database.
    """
    teams = db.query(Team).all()
    return teams

@app.get("/teams/{team_id}/players", response_model=List[schemas.PlayerResponse], tags=["Teams"])
def get_players_by_team(team_id: int, db: Session = Depends(get_db)):
    """
    Retrieves a list of all unique players who have played for a specific team.
    """
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    players = (
        db.query(Player)
        .join(BattingStat, Player.id == BattingStat.player_id)
        .join(Inning, BattingStat.inning_id == Inning.id)
        .filter(Inning.team_id == team_id)
        .distinct()
        .all()
    )
    return players

@app.get("/stats/leaderboard/{season}", response_model=List[schemas.PlayerSeasonStats], tags=["Stats"])
def get_season_leaderboard(season: int, top_n: int = 10, db: Session = Depends(get_db)):
    """
    Retrieves the top N run-scorers for a specific season.
    """
    leaderboard = (
        db.query(
            Player.id.label("player_id"),
            Player.name.label("player_name"),
            func.sum(BattingStat.runs).label("total_runs"),
            func.sum(BattingStat.balls).label("total_balls")
        )
        .join(BattingStat, Player.id == BattingStat.player_id)
        .join(Inning, BattingStat.inning_id == Inning.id)
        .join(Match, Inning.match_id == Match.id)
        .filter(Match.season == season)
        .group_by(Player.id, Player.name)
        .order_by(func.sum(BattingStat.runs).desc())
        .limit(top_n)
        .all()
    )

    # Calculate strike rate for each player
    results = []
    for row in leaderboard:
        strike_rate = (row.total_runs / row.total_balls * 100) if row.total_balls > 0 else 0
        results.append(
            schemas.PlayerSeasonStats(
                player_id=row.player_id,
                player_name=row.player_name,
                total_runs=row.total_runs,
                total_balls=row.total_balls,
                strike_rate=round(strike_rate, 2)
            )
        )
    return results

@app.get("/matches/{match_id}", response_model=schemas.MatchResponse)
def get_match(match_id: int, db: Session = Depends(get_db)):
    match = (
        db.query(Match)
        .options(
            joinedload(Match.team1),
            joinedload(Match.team2),
            joinedload(Match.innings).joinedload(Inning.team),
            joinedload(Match.innings).joinedload(Inning.batting_stats).joinedload(BattingStat.player),
        )
        .filter(Match.id == match_id)
        .first()
    )
    print("match", match)
    
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    
    return match

@app.get("/players/{player_id}/stats", response_model=schemas.PlayerCareerStats, tags=["Players"])
def get_player_career_stats(player_id: int, db: Session = Depends(get_db)):
    """
    Retrieves the overall career batting statistics for a single player,
    including runs, strike rate, and number of 50s and 100s.
    """
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    stats = (
        db.query(
            func.count(func.distinct(Inning.match_id)).label("matches_played"),
            func.sum(BattingStat.runs).label("total_runs"),
            func.sum(BattingStat.balls).label("total_balls"),
            # Use a CASE statement to count scores of 50+ and 100+
            func.sum(case((BattingStat.runs >= 50, 1), else_=0)).label("fifties"),
            func.sum(case((BattingStat.runs >= 100, 1), else_=0)).label("hundreds")
        )
        .join(Inning, BattingStat.inning_id == Inning.id)
        .filter(BattingStat.player_id == player_id)
        .first()
    )

    # Handle cases where a player might exist but has no batting stats
    if not stats or stats.total_runs is None:
        return schemas.PlayerCareerStats(
            player_id=player.id, player_name=player.name, matches_played=0,
            total_runs=0, total_balls=0, fifties=0, hundreds=0, strike_rate=0.0
        )

    strike_rate = (stats.total_runs / stats.total_balls * 100) if stats.total_balls > 0 else 0

    return schemas.PlayerCareerStats(
        player_id=player.id,
        player_name=player.name,
        matches_played=stats.matches_played,
        total_runs=stats.total_runs,
        total_balls=stats.total_balls,
        fifties=stats.fifties,
        hundreds=stats.hundreds,
        strike_rate=round(strike_rate, 2)
    )

@app.get("/stats/head-to-head", response_model=schemas.HeadToHeadStats, tags=["Stats"])
def get_head_to_head_stats(team1_id: int, team2_id: int, db: Session = Depends(get_db)):
    """
    Retrieves the head-to-head match statistics between two teams.

    """
    team1 = db.query(Team).filter(Team.id == team1_id).first()
    team2 = db.query(Team).filter(Team.id == team2_id).first()

    if not team1 or not team2:
        raise HTTPException(status_code=404, detail="One or both teams not found")
    if team1_id == team2_id:
        raise HTTPException(status_code=400, detail="Team IDs must be different")

    # This query finds all matches played between the two specified teams.
    query = db.query(Match).filter(
        ((Match.team1_id == team1_id) & (Match.team2_id == team2_id)) |
        ((Match.team1_id == team2_id) & (Match.team2_id == team1_id))
    )
    
    total_matches = query.count()
    # These will be 0 until winner_id is populated in the database.
    team1_wins = query.filter(Match.winner_id == team1_id).count()
    team2_wins = query.filter(Match.winner_id == team2_id).count()

    return schemas.HeadToHeadStats(
        team1_name=team1.name,
        team2_name=team2.name,
        total_matches=total_matches,
        team1_wins=team1_wins,
        team2_wins=team2_wins,
    )

