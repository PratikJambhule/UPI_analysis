"""CLI entry point for the UPI Analytics Pipeline."""

import argparse
import sys

from src.pipeline.orchestrator import PipelineOrchestrator


def main():
    parser = argparse.ArgumentParser(
        description="UPI Analytics Pipeline — run ETL and analytics stages"
    )
    parser.add_argument(
        "--stage",
        choices=PipelineOrchestrator.VALID_STAGES,
        default="all",
        help="Pipeline stage to execute (default: all)",
    )
    args = parser.parse_args()

    orchestrator = PipelineOrchestrator()
    success = orchestrator.run_stage(args.stage)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
