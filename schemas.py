from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import date

# These schemas are used for data validation before it enters the database.

class BattingSchema(BaseModel):
    player: str
    runs: str
    balls: str
    fours: str
    sixes: str
    strike_rate: str

class InningSchema(BaseModel):
    name: str
    batting: List[Dict[str, Any]]

class OutcomeSchema(BaseModel):
    winner: Optional[str] = None

class InfoSchema(BaseModel):
    teams: List[str]
    dates: Optional[List[date]]
    venue: Optional[str]
    outcome: Optional[OutcomeSchema]

class MatchSchema(BaseModel):
    info: InfoSchema
    innings: List[InningSchema]




class PlayerResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class TeamResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class BattingStatResponse(BaseModel):
    runs: int
    balls: int
    fours: int
    sixes: int
    strike_rate: Optional[float] = None
    player: Optional[PlayerResponse] = None

    class Config:
        from_attributes = True
        
class InningResponse(BaseModel):
    innings_no: int
    team: TeamResponse # Nested team info
    batting_stats: List[BattingStatResponse]

    class Config:
        from_attributes = True

class MatchResponse(BaseModel):
    id: int
    season: int
    team1: TeamResponse
    team2: TeamResponse
    innings: List[InningResponse]

    class Config:
        from_attributes = True

class PlayerSeasonStats(BaseModel):
    player_id: int
    player_name: str
    total_runs: int
    total_balls: int
    strike_rate: Optional[float]

class PlayerCareerStats(BaseModel):
    player_id: int
    player_name: str
    matches_played: int
    total_runs: int
    total_balls: int
    fifties: int
    hundreds: int
    strike_rate: Optional[float]

class HeadToHeadStats(BaseModel):
    team1_name: str
    team2_name: str
    total_matches: int
    team1_wins: int
    team2_wins: int

