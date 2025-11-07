"""
Main Flask application for ranqr.
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
from backend.models import db, Song, Comparison
from backend.triangle_detector import TriangleDetector
from backend.histogram import HistogramGenerator
import os


def create_app(config=None):
    """Application factory for creating Flask app instances."""
    app = Flask(__name__)
    
    # Configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = config.get('DATABASE_URI', 'sqlite:///ranqr.db') if config else 'sqlite:///ranqr.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    db.init_app(app)
    CORS(app)
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    # Routes
    
    @app.route('/api/songs', methods=['GET'])
    def get_songs():
        """Get all songs."""
        songs = Song.query.order_by(Song.score.desc()).all()
        return jsonify([song.to_dict() for song in songs])
    
    @app.route('/api/songs', methods=['POST'])
    def add_song():
        """Add a new song."""
        data = request.json
        
        if not data or 'title' not in data or 'artist' not in data:
            return jsonify({'error': 'Missing required fields'}), 400
        
        song = Song(
            title=data['title'],
            artist=data['artist'],
            score=data.get('score', 1500.0)
        )
        
        db.session.add(song)
        db.session.commit()
        
        return jsonify(song.to_dict()), 201
    
    @app.route('/api/songs/<int:song_id>', methods=['GET'])
    def get_song(song_id):
        """Get a specific song."""
        song = Song.query.get_or_404(song_id)
        return jsonify(song.to_dict())
    
    @app.route('/api/comparisons', methods=['GET'])
    def get_comparisons():
        """Get all comparisons."""
        comparisons = Comparison.query.order_by(Comparison.timestamp.desc()).all()
        return jsonify([comp.to_dict() for comp in comparisons])
    
    @app.route('/api/comparisons', methods=['POST'])
    def add_comparison():
        """Add a new comparison (record that one song beat another)."""
        data = request.json
        
        if not data or 'winner_id' not in data or 'loser_id' not in data:
            return jsonify({'error': 'Missing required fields'}), 400
        
        winner_id = data['winner_id']
        loser_id = data['loser_id']
        
        if winner_id == loser_id:
            return jsonify({'error': 'A song cannot beat itself'}), 400
        
        # Verify songs exist
        winner = Song.query.get_or_404(winner_id)
        loser = Song.query.get_or_404(loser_id)
        
        # Create comparison
        comparison = Comparison(winner_id=winner_id, loser_id=loser_id)
        db.session.add(comparison)
        
        # Update song statistics
        winner.wins += 1
        loser.losses += 1
        
        # Update ELO-style scores
        k_factor = 32
        expected_winner = 1 / (1 + 10 ** ((loser.score - winner.score) / 400))
        expected_loser = 1 / (1 + 10 ** ((winner.score - loser.score) / 400))
        
        winner.score += k_factor * (1 - expected_winner)
        loser.score += k_factor * (0 - expected_loser)
        
        db.session.commit()
        
        return jsonify(comparison.to_dict()), 201
    
    @app.route('/api/triangles', methods=['GET'])
    def get_triangles():
        """Get all triangular inconsistencies, sorted by dissonance."""
        triangles = TriangleDetector.find_all_triangles()
        return jsonify([triangle.to_dict() for triangle in triangles])
    
    @app.route('/api/triangles/resolve', methods=['POST'])
    def resolve_triangle():
        """
        Resolve a triangle by applying a chosen ordering.
        
        Expects JSON with 'song_ids' array of 3 IDs in desired order.
        """
        data = request.json
        
        if not data or 'song_ids' not in data:
            return jsonify({'error': 'Missing song_ids'}), 400
        
        song_ids = data['song_ids']
        
        if len(song_ids) != 3:
            return jsonify({'error': 'Must provide exactly 3 song IDs'}), 400
        
        success = TriangleDetector.apply_ordering(song_ids)
        
        if success:
            return jsonify({'success': True, 'message': 'Ordering applied'}), 200
        else:
            return jsonify({'error': 'Failed to apply ordering'}), 400
    
    @app.route('/api/histogram/scores', methods=['GET'])
    def get_score_histogram():
        """Get histogram of score distribution."""
        num_bins = request.args.get('bins', default=10, type=int)
        histogram = HistogramGenerator.generate_score_histogram(num_bins)
        return jsonify(histogram)
    
    @app.route('/api/histogram/comparisons', methods=['GET'])
    def get_comparison_histogram():
        """Get histogram of comparison count distribution."""
        num_bins = request.args.get('bins', default=10, type=int)
        histogram = HistogramGenerator.generate_comparison_histogram(num_bins)
        return jsonify(histogram)
    
    @app.route('/api/stats', methods=['GET'])
    def get_stats():
        """Get overall statistics."""
        total_songs = Song.query.count()
        total_comparisons = Comparison.query.count()
        triangles = TriangleDetector.find_all_triangles()
        
        return jsonify({
            'total_songs': total_songs,
            'total_comparisons': total_comparisons,
            'total_triangles': len(triangles),
            'max_dissonance': triangles[0].dissonance if triangles else 0
        })
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
