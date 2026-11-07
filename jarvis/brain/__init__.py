"""
Brain module - The core intelligence of JARVIS
Handles command routing, intent parsing, task scheduling, self-learning AI, and internet learning.
"""

from .router import CommandRouter
from .scheduler import TaskScheduler
from .learning import LearningAI
from .internet_learning import InternetLearner

__all__ = ["CommandRouter", "TaskScheduler", "LearningAI", "InternetLearner", "router"]

# Global instances (initialized in server)
router = None
learning_ai = None
internet_learner = None
