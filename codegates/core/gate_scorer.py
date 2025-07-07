"""
Gate Scoring System - Calculates weighted scores for each hard gate
"""

from typing import Dict
from ..models import GateType


class GateScorer:
    """Calculates gate scores with weighting and quality adjustments"""
    
    # Gate weights (higher = more important)
    GATE_WEIGHTS = {
        GateType.AVOID_LOGGING_SECRETS: 2.0,     # Security critical
        GateType.ERROR_LOGS: 1.8,                # Error handling critical
        GateType.STRUCTURED_LOGS: 1.6,           # Observability
        GateType.AUDIT_TRAIL: 1.5,               # Compliance
        GateType.AUTOMATED_TESTS: 1.4,           # Quality
        GateType.RETRY_LOGIC: 1.3,               # Reliability
        GateType.CIRCUIT_BREAKERS: 1.3,          # Reliability
        GateType.TIMEOUTS: 1.2,                  # Performance
        GateType.HTTP_CODES: 1.2,                # API quality
        GateType.CORRELATION_ID: 1.1,            # Tracing
        GateType.LOG_API_CALLS: 1.1,             # Observability
        GateType.THROTTLING: 1.0,                # Performance
        GateType.UI_ERRORS: 1.0,                 # UX
        GateType.UI_ERROR_TOOLS: 1.0,            # Monitoring
        GateType.LOG_BACKGROUND_JOBS: 0.9,       # Monitoring
    }
    
    # Quality multipliers based on implementation quality
    QUALITY_MULTIPLIERS = {
        'excellent': 1.0,    # 90-100%
        'good': 0.9,         # 80-89%
        'fair': 0.8,         # 70-79%
        'poor': 0.6,         # 60-69%
        'bad': 0.4           # <60%
    }
    
    def calculate_gate_score(self, coverage: float, quality_score: float, 
                           gate_type: GateType) -> float:
        """Calculate weighted score for a gate"""
        
        # Get base weight for this gate type
        weight = self.GATE_WEIGHTS.get(gate_type, 1.0)
        
        # Calculate quality multiplier
        quality_multiplier = self._get_quality_multiplier(quality_score)
        
        # Calculate base score (coverage + quality weighted)
        base_score = (coverage * 0.7) + (quality_score * 0.3)
        
        # Apply weight and quality multiplier
        weighted_score = base_score * weight * quality_multiplier
        
        # Normalize to 0-100 scale
        final_score = min(weighted_score, 100.0)
        
        return final_score
    
    def calculate_overall_score(self, gate_scores: Dict[GateType, float]) -> float:
        """Calculate overall project score from individual gate scores"""
        
        if not gate_scores:
            return 0.0
        
        total_weighted_score = 0.0
        total_weight = 0.0
        
        for gate_type, score in gate_scores.items():
            weight = self.GATE_WEIGHTS.get(gate_type, 1.0)
            total_weighted_score += score * weight
            total_weight += weight
        
        return total_weighted_score / total_weight if total_weight > 0 else 0.0
    
    def _get_quality_multiplier(self, quality_score: float) -> float:
        """Get quality multiplier based on quality score"""
        
        if quality_score >= 70:
            return self.QUALITY_MULTIPLIERS['excellent']
        elif quality_score >= 50:
            return self.QUALITY_MULTIPLIERS['good']
        elif quality_score >= 40:
            return self.QUALITY_MULTIPLIERS['fair']
        elif quality_score >= 30:
            return self.QUALITY_MULTIPLIERS['poor']
        else:
            return self.QUALITY_MULTIPLIERS['bad']
    
    def get_score_breakdown(self, coverage: float, quality_score: float,
                          gate_type: GateType) -> Dict[str, float]:
        """Get detailed score breakdown for transparency"""
        
        weight = self.GATE_WEIGHTS.get(gate_type, 1.0)
        quality_multiplier = self._get_quality_multiplier(quality_score)
        base_score = (coverage * 0.7) + (quality_score * 0.3)
        final_score = min(base_score * weight * quality_multiplier, 100.0)
        
        return {
            'coverage_contribution': coverage * 0.7,
            'quality_contribution': quality_score * 0.3,
            'base_score': base_score,
            'gate_weight': weight,
            'quality_multiplier': quality_multiplier,
            'final_score': final_score
        }
    
    def get_gate_priority(self, gate_type: GateType) -> str:
        """Get priority level for a gate type"""
        
        weight = self.GATE_WEIGHTS.get(gate_type, 1.0)
        
        if weight >= 1.5:
            return "CRITICAL"
        elif weight >= 1.2:
            return "HIGH"
        elif weight >= 1.0:
            return "MEDIUM"
        else:
            return "LOW" 