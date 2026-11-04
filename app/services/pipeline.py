"""
MANTIQ data pipeline

"""

from dataclasses import dataclass

import pandas as pd
import streamlit as st

from app.services import data_service, model_service
from app.services.data_service import DataError, SplitInfo
from app.services.model_service import IntegrityResult


@dataclass(frozen=True)
class Pipeline:
    features: pd.DataFrame     # ims_features.csv + 'time' + 'recording'
    timeline: pd.DataFrame     # bearing_timeline.csv (test period only)
    scored: pd.DataFrame       # recomputed scores for ALL recordings
    conditions: pd.DataFrame   # rolling condition per recording
    split: SplitInfo
    integrity: IntegrityResult
    notes: list                # plain-language data and model notes


def build_pipeline() -> Pipeline:
    """Plain Python version (no Streamlit needed), used by the terminal checks."""
    # Imported here so a missing condition_engine guard becomes a readable error.
    from app.services import condition_service

    features = data_service.load_features()
    timeline = data_service.load_timeline()
    split = data_service.locate_split(features, timeline)
    artifacts, model_notes = model_service.load_artifacts()
    scored = model_service.score_recordings(features, artifacts)
    integrity = model_service.compare_with_timeline(scored, timeline, split)
    conditions = condition_service.compute_conditions(scored)

    notes = data_service.data_quality_notes(features) + model_notes
    if not split.matches_training_script:
        notes.append(
            f"The first unseen recording is number {split.first_test_recording}, but "
            f"int(len * 0.60) from bearing_analysis.py implies {split.expected_train_count + 1}. "
            "The timeline file may have been created from a different features file."
        )
    return Pipeline(features, timeline, scored, conditions, split, integrity, notes)


@st.cache_resource(show_spinner="Scoring the historical recordings with the trained models...")
def get_pipeline() -> Pipeline:
    return build_pipeline()


def get_pipeline_or_stop() -> Pipeline:
    """For pages: returns the pipeline, or shows a friendly error and stops the page."""
    try:
        return get_pipeline()
    except (DataError, ImportError) as exc:
        st.error(str(exc))
        st.stop()