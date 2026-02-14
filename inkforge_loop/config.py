from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LoopConfig:
    workspace_root: Path
    run_id: str
    target_chapter: int = 50
    max_revision_loops: int = 20
    quality_overall_min: float = 9.0
    quality_category_min: float = 8.0
    max_total_failures: int = 200
    writer_agent: str = "writer"
    critic_model: str = "sonnet"
    reviser_model: str = "gpt-5"
    run_runtime_tests: bool = False

    @property
    def run_root(self) -> Path:
        return self.workspace_root / self.run_id

    @property
    def manuscript_dir(self) -> Path:
        return self.run_root / "manuscript"

    @property
    def plans_dir(self) -> Path:
        return self.run_root / "plans"

    @property
    def logs_dir(self) -> Path:
        return self.run_root / "logs"

    @property
    def artifacts_dir(self) -> Path:
        return self.run_root / "artifacts"

    @property
    def state_dir(self) -> Path:
        return self.run_root / "state"

    @property
    def run_state_path(self) -> Path:
        return self.state_dir / "run_state.json"


def build_config(
    workspace_root: str,
    run_id: str,
    target_chapter: int,
    max_revision_loops: int,
    quality_overall_min: float,
    quality_category_min: float,
    max_total_failures: int,
    writer_agent: str,
    critic_model: str,
    reviser_model: str,
) -> LoopConfig:
    if target_chapter <= 0:
        raise ValueError("target_chapter must be positive")
    if max_revision_loops <= 0:
        raise ValueError("max_revision_loops must be positive")
    if max_total_failures <= 0:
        raise ValueError("max_total_failures must be positive")
    return LoopConfig(
        workspace_root=Path(workspace_root),
        run_id=run_id,
        target_chapter=target_chapter,
        max_revision_loops=max_revision_loops,
        quality_overall_min=quality_overall_min,
        quality_category_min=quality_category_min,
        max_total_failures=max_total_failures,
        writer_agent=writer_agent,
        critic_model=critic_model,
        reviser_model=reviser_model,
    )
