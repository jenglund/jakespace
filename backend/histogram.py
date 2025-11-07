"""
Histogram generation for score distribution analysis.
"""
from typing import Dict, List
from backend.models import Song
import numpy as np


class HistogramGenerator:
    """Generates histogram data for score distributions."""
    
    @staticmethod
    def generate_score_histogram(num_bins: int = 10) -> Dict:
        """
        Generate histogram data for song score distribution.
        
        Args:
            num_bins: Number of bins to use in the histogram
            
        Returns:
            Dictionary containing histogram data and statistics
        """
        songs = Song.query.all()
        
        if not songs:
            return {
                'bins': [],
                'counts': [],
                'statistics': {
                    'mean': 0,
                    'median': 0,
                    'std_dev': 0,
                    'min': 0,
                    'max': 0,
                    'total_songs': 0
                }
            }
        
        scores = [song.score for song in songs]
        
        # Calculate histogram
        counts, bin_edges = np.histogram(scores, bins=num_bins)
        
        # Format bins as ranges
        bins = []
        for i in range(len(bin_edges) - 1):
            bins.append({
                'min': float(bin_edges[i]),
                'max': float(bin_edges[i + 1]),
                'label': f"{bin_edges[i]:.0f}-{bin_edges[i+1]:.0f}"
            })
        
        # Calculate statistics
        statistics = {
            'mean': float(np.mean(scores)),
            'median': float(np.median(scores)),
            'std_dev': float(np.std(scores)),
            'min': float(np.min(scores)),
            'max': float(np.max(scores)),
            'total_songs': len(songs)
        }
        
        return {
            'bins': bins,
            'counts': [int(c) for c in counts],
            'statistics': statistics
        }
    
    @staticmethod
    def generate_comparison_histogram(num_bins: int = 10) -> Dict:
        """
        Generate histogram data for comparison count distribution.
        
        Args:
            num_bins: Number of bins to use in the histogram
            
        Returns:
            Dictionary containing histogram data and statistics
        """
        songs = Song.query.all()
        
        if not songs:
            return {
                'bins': [],
                'counts': [],
                'statistics': {
                    'mean': 0,
                    'median': 0,
                    'std_dev': 0,
                    'min': 0,
                    'max': 0,
                    'total_songs': 0
                }
            }
        
        comparison_counts = [song.wins + song.losses for song in songs]
        
        # Calculate histogram
        counts, bin_edges = np.histogram(comparison_counts, bins=num_bins)
        
        # Format bins as ranges
        bins = []
        for i in range(len(bin_edges) - 1):
            bins.append({
                'min': int(bin_edges[i]),
                'max': int(bin_edges[i + 1]),
                'label': f"{int(bin_edges[i])}-{int(bin_edges[i+1])}"
            })
        
        # Calculate statistics
        statistics = {
            'mean': float(np.mean(comparison_counts)),
            'median': float(np.median(comparison_counts)),
            'std_dev': float(np.std(comparison_counts)),
            'min': int(np.min(comparison_counts)),
            'max': int(np.max(comparison_counts)),
            'total_songs': len(songs)
        }
        
        return {
            'bins': bins,
            'counts': [int(c) for c in counts],
            'statistics': statistics
        }
