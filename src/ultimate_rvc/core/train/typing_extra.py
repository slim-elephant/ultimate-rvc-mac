"""
Module which defines extra types used by modules in the
ultimate_rvc.core.train package.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ModelInfo(BaseModel):
    """
    Information about a voice model to be trained.

    Attributes
    ----------
    sample_rate : PretrainedSampleRate
        The sample rate of the post-processed audio to train the model
        on.

    """

    sample_rate: int
    # TODO add more attributes later


class TrainingInfo(BaseModel):
    """
    Information about the ongoing training of a voice model.

    Attributes
    ----------
    process_pids : list[int], default = []
        The ids of the processes running the training.

    """

    process_pids: list[int] = []
    # TODO add more attributes later
    model_config = ConfigDict(extra="allow")
