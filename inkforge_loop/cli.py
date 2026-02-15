from __future__ import annotations

import argparse
from datetime import datetime, timezone

from .config import build_config
from .engine import run_loop


def _default_run_id() -> str:
    return datetime.now(timezone.utc).strftime("run-%Y%m%d-%H%M%S")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inkforge autonomous chapter loop")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="Run or resume an inkforge loop")
    run.add_argument("--workspace-root", default="inkforge", help="Root directory for generated runs")
    run.add_argument("--run-id", default=_default_run_id(), help="Run identifier")
    run.add_argument("--target-chapter", type=int, default=50, help="Stop when this chapter number is reached")
    run.add_argument(
        "--max-revision-loops", type=int, default=20, help="Max revise/re-critique loops before full restart"
    )
    run.add_argument("--max-total-failures", type=int, default=200, help="Abort run after this many chapter restarts")
    run.add_argument("--quality-overall-min", type=float, default=9.0, help="Minimum overall score")
    run.add_argument("--quality-category-min", type=float, default=8.0, help="Minimum per-category score")
    run.add_argument("--writer-agent", default="writer", help="OpenCode writer agent id")
    run.add_argument("--critic-model", default="sonnet", help="Claude model alias")
    run.add_argument("--reviser-model", default="gpt-5", help="Codex model")
    run.add_argument("--resume", action="store_true", help="Resume existing run state")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "run":
        cfg = build_config(
            workspace_root=args.workspace_root,
            run_id=args.run_id,
            target_chapter=args.target_chapter,
            max_revision_loops=args.max_revision_loops,
            quality_overall_min=args.quality_overall_min,
            quality_category_min=args.quality_category_min,
            max_total_failures=args.max_total_failures,
            writer_agent=args.writer_agent,
            critic_model=args.critic_model,
            reviser_model=args.reviser_model,
        )
        return run_loop(cfg, resume=args.resume)

    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
