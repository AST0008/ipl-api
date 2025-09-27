from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date
from sqlalchemy.orm import relationship
from base import Base

class Team(Base):
    __tablename__ = "teams"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    
    # Relationships
    home_matches = relationship("Match", foreign_keys="[Match.team1_id]", back_populates="team1")
    away_matches = relationship("Match", foreign_keys="[Match.team2_id]", back_populates="team2")
    won_matches = relationship("Match", foreign_keys="[Match.winner_id]", back_populates="winner")
    innings = relationship("Inning", back_populates="team")

class Player(Base):
    __tablename__ = "players"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    
    # Relationships
    batting_stats = relationship("BattingStat", back_populates="player")

class Match(Base):
    __tablename__ = "matches"
    id = Column(Integer, primary_key=True, index=True)
    season = Column(Integer, index=True)
    date = Column(Date, nullable=True) # Made nullable to handle missing data
    venue = Column(String, nullable=True)
    
    team1_id = Column(Integer, ForeignKey("teams.id"))
    team2_id = Column(Integer, ForeignKey("teams.id"))
    winner_id = Column(Integer, ForeignKey("teams.id"), nullable=True)

    # Relationships
    team1 = relationship("Team", foreign_keys=[team1_id], back_populates="home_matches")
    team2 = relationship("Team", foreign_keys=[team2_id], back_populates="away_matches")
    winner = relationship("Team", foreign_keys=[winner_id], back_populates="won_matches")
    innings = relationship("Inning", back_populates="match")

class Inning(Base):
    __tablename__ = "innings"
    id = Column(Integer, primary_key=True, index=True)
    innings_no = Column(Integer)
    
    match_id = Column(Integer, ForeignKey("matches.id"))
    team_id = Column(Integer, ForeignKey("teams.id"))

    # Relationships
    match = relationship("Match", back_populates="innings")
    team = relationship("Team", back_populates="innings")
    batting_stats = relationship("BattingStat", back_populates="inning")

class BattingStat(Base):
    __tablename__ = "batting_stats"
    id = Column(Integer, primary_key=True, index=True)
    runs = Column(Integer)
    balls = Column(Integer)
    fours = Column(Integer)
    sixes = Column(Integer)
    strike_rate = Column(Float, nullable=True)

    inning_id = Column(Integer, ForeignKey("innings.id"))
    player_id = Column(Integer, ForeignKey("players.id"))

    # Relationships
    inning = relationship("Inning", back_populates="batting_stats")
    player = relationship("Player", back_populates="batting_stats")
