"""
Triangle detection and resolution logic for identifying and fixing ranking inconsistencies.

A triangle (cycle) occurs when:
- Song A beats Song B
- Song B beats Song C  
- Song C beats Song A

This creates a logical inconsistency in the rankings.
"""
from typing import List, Dict, Tuple, Set
from itertools import permutations
from backend.models import Song, Comparison, db


class Triangle:
    """Represents a triangular inconsistency in the ranking graph."""
    
    def __init__(self, song_a: Song, song_b: Song, song_c: Song,
                 a_beats_b: bool, b_beats_c: bool, c_beats_a: bool):
        """
        Initialize a triangle.
        
        Args:
            song_a, song_b, song_c: The three songs forming the triangle
            a_beats_b: Whether A has beaten B in comparisons
            b_beats_c: Whether B has beaten C in comparisons
            c_beats_a: Whether C has beaten A in comparisons
        """
        self.songs = (song_a, song_b, song_c)
        self.edges = {
            (song_a.id, song_b.id): a_beats_b,
            (song_b.id, song_c.id): b_beats_c,
            (song_c.id, song_a.id): c_beats_a
        }
        self.dissonance = self._calculate_dissonance()
    
    def _calculate_dissonance(self) -> float:
        """
        Calculate the dissonance of this triangle.
        
        Dissonance is the sum of the two largest score differences.
        We ignore the smallest difference as it's likely the "weak link".
        
        Returns:
            The dissonance value (higher = more problematic)
        """
        song_a, song_b, song_c = self.songs
        
        # Calculate absolute differences between all pairs
        diffs = [
            abs(song_a.score - song_b.score),
            abs(song_b.score - song_c.score),
            abs(song_c.score - song_a.score)
        ]
        
        # Sort and sum the two largest
        diffs.sort(reverse=True)
        return diffs[0] + diffs[1]
    
    def get_all_orderings(self) -> List[Dict]:
        """
        Get all 6 possible orderings of the three songs with predicted dissonance.
        
        Returns:
            List of dicts containing ordering info and predicted dissonance change
        """
        orderings = []
        song_a, song_b, song_c = self.songs
        
        # Generate all 6 permutations (3! = 6)
        for perm in permutations([song_a, song_b, song_c]):
            first, second, third = perm
            
            # Calculate what the new dissonance would be if we enforced this ordering
            # by adjusting scores to match (hypothetical)
            predicted_change = self._predict_dissonance_change(first, second, third)
            
            orderings.append({
                'ordering': [first.id, second.id, third.id],
                'songs': [
                    {'id': first.id, 'title': first.title, 'artist': first.artist, 'score': first.score},
                    {'id': second.id, 'title': second.title, 'artist': second.artist, 'score': second.score},
                    {'id': third.id, 'title': third.title, 'artist': third.artist, 'score': third.score}
                ],
                'predicted_dissonance_change': predicted_change,
                'description': f"{first.title} > {second.title} > {third.title}"
            })
        
        return orderings
    
    def _predict_dissonance_change(self, first: Song, second: Song, third: Song) -> float:
        """
        Predict how dissonance would change if we enforce a specific ordering.
        
        This calculates what the impact would be on the current triangle's dissonance
        if we added comparisons to enforce this ordering.
        
        Args:
            first, second, third: The songs in desired order (first > second > third)
            
        Returns:
            Predicted change in dissonance (negative = improvement)
        """
        current_dissonance = self.dissonance
        
        # Calculate what dissonance would be if scores were consistent with this ordering
        # We assume scores would need to match the ordering
        score_diffs = [
            abs(first.score - second.score),
            abs(second.score - third.score),
            abs(first.score - third.score)
        ]
        
        # Check if current scores already match this ordering
        scores_match_ordering = (
            first.score >= second.score >= third.score or
            first.score <= second.score <= third.score
        )
        
        if scores_match_ordering:
            # This ordering is already consistent with scores, so dissonance should decrease
            new_dissonance = 0  # Perfect consistency
        else:
            # Calculate expected dissonance after enforcing this ordering
            # In the worst case, we'd need to flip relationships, increasing dissonance initially
            score_diffs.sort(reverse=True)
            new_dissonance = score_diffs[0] + score_diffs[1]
        
        return new_dissonance - current_dissonance
    
    def to_dict(self) -> Dict:
        """Convert triangle to dictionary representation."""
        return {
            'songs': [s.to_dict() for s in self.songs],
            'dissonance': self.dissonance,
            'orderings': self.get_all_orderings()
        }


class TriangleDetector:
    """Detects and manages triangular inconsistencies in rankings."""
    
    @staticmethod
    def find_all_triangles() -> List[Triangle]:
        """
        Find all triangular inconsistencies in the current ranking data.
        
        Returns:
            List of Triangle objects, sorted by dissonance (highest first)
        """
        # Get all comparisons and build adjacency information
        comparisons = Comparison.query.all()
        
        # Build a directed graph of who beat whom
        # wins_against[a][b] = True means song A has beaten song B
        wins_against = {}
        
        for comp in comparisons:
            if comp.winner_id not in wins_against:
                wins_against[comp.winner_id] = set()
            wins_against[comp.winner_id].add(comp.loser_id)
        
        # Find all songs that have participated in comparisons
        all_song_ids = set(wins_against.keys())
        for losers in wins_against.values():
            all_song_ids.update(losers)
        
        # Load all songs
        songs = {s.id: s for s in Song.query.filter(Song.id.in_(all_song_ids)).all()}
        
        # Find triangles: for each triple of songs, check if they form a cycle
        triangles = []
        song_ids = list(all_song_ids)
        
        for i in range(len(song_ids)):
            for j in range(i + 1, len(song_ids)):
                for k in range(j + 1, len(song_ids)):
                    song_a_id, song_b_id, song_c_id = song_ids[i], song_ids[j], song_ids[k]
                    
                    # Check all possible cycles
                    # Cycle 1: A -> B -> C -> A
                    if (song_b_id in wins_against.get(song_a_id, set()) and
                        song_c_id in wins_against.get(song_b_id, set()) and
                        song_a_id in wins_against.get(song_c_id, set())):
                        
                        triangles.append(Triangle(
                            songs[song_a_id], songs[song_b_id], songs[song_c_id],
                            True, True, True
                        ))
                    
                    # Cycle 2: A -> C -> B -> A
                    if (song_c_id in wins_against.get(song_a_id, set()) and
                        song_b_id in wins_against.get(song_c_id, set()) and
                        song_a_id in wins_against.get(song_b_id, set())):
                        
                        triangles.append(Triangle(
                            songs[song_a_id], songs[song_c_id], songs[song_b_id],
                            True, True, True
                        ))
        
        # Sort by dissonance (highest first)
        triangles.sort(key=lambda t: t.dissonance, reverse=True)
        
        return triangles
    
    @staticmethod
    def apply_ordering(song_ids: List[int]) -> bool:
        """
        Apply a chosen ordering by adding a comparison that enforces it.
        
        Args:
            song_ids: List of 3 song IDs in desired order (first > second > third)
            
        Returns:
            True if successful, False otherwise
        """
        if len(song_ids) != 3:
            return False
        
        first_id, second_id, third_id = song_ids
        
        # Verify songs exist
        songs = Song.query.filter(Song.id.in_(song_ids)).all()
        if len(songs) != 3:
            return False
        
        # Add comparisons to enforce this ordering
        # first > second
        comp1 = Comparison(winner_id=first_id, loser_id=second_id)
        # second > third  
        comp2 = Comparison(winner_id=second_id, loser_id=third_id)
        # first > third (transitive, but we record it for completeness)
        comp3 = Comparison(winner_id=first_id, loser_id=third_id)
        
        db.session.add_all([comp1, comp2, comp3])
        
        # Update song statistics
        for song in songs:
            if song.id == first_id:
                song.wins += 2  # Beat both second and third
            elif song.id == second_id:
                song.wins += 1  # Beat third
                song.losses += 1  # Lost to first
            else:  # third_id
                song.losses += 2  # Lost to both first and second
        
        db.session.commit()
        return True
