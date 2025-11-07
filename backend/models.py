"""
Data models for the ranqr application.
"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Song(db.Model):
    """Represents a song in the ranking system."""
    __tablename__ = 'songs'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    artist = db.Column(db.String(200), nullable=False)
    score = db.Column(db.Float, default=1500.0)  # ELO-style rating
    wins = db.Column(db.Integer, default=0)
    losses = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Song {self.id}: {self.title} by {self.artist} (score: {self.score})>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'artist': self.artist,
            'score': self.score,
            'wins': self.wins,
            'losses': self.losses,
            'total_comparisons': self.wins + self.losses
        }


class Comparison(db.Model):
    """Represents a pairwise comparison between two songs."""
    __tablename__ = 'comparisons'
    
    id = db.Column(db.Integer, primary_key=True)
    winner_id = db.Column(db.Integer, db.ForeignKey('songs.id'), nullable=False)
    loser_id = db.Column(db.Integer, db.ForeignKey('songs.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    winner = db.relationship('Song', foreign_keys=[winner_id])
    loser = db.relationship('Song', foreign_keys=[loser_id])
    
    def __repr__(self):
        return f"<Comparison {self.id}: Song {self.winner_id} > Song {self.loser_id}>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'winner_id': self.winner_id,
            'loser_id': self.loser_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
