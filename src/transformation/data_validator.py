"""Data quality validation with fluent API and structured reports."""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List
import json

import pandas as pd
from loguru import logger


@dataclass
class ValidationResult:
    """Single validation check result."""
    check_name: str
    passed: bool
    details: str
    severity: str = "warning"  # critical | warning | info


class DataValidator:
    """Fluent validator: chain checks, then call .report() to evaluate."""

    def __init__(self, df: pd.DataFrame, dataset_name: str):
        self.df = df
        self.dataset_name = dataset_name
        self.results: List[ValidationResult] = []

    def check_not_empty(self) -> "DataValidator":
        self.results.append(ValidationResult(
            check_name="non_empty",
            passed=len(self.df) > 0,
            details=f"Row count: {len(self.df)}",
            severity="critical",
        ))
        return self

    def check_no_nulls(self, columns: List[str]) -> "DataValidator":
        for col in columns:
            if col not in self.df.columns:
                self.results.append(ValidationResult(
                    check_name=f"column_exists_{col}",
                    passed=False,
                    details=f"Column '{col}' not found",
                    severity="critical",
                ))
                continue
            null_count = int(self.df[col].isna().sum())
            null_pct = null_count / len(self.df) * 100
            self.results.append(ValidationResult(
                check_name=f"no_nulls_{col}",
                passed=null_count == 0,
                details=f"{null_count} nulls ({null_pct:.1f}%)",
                severity="critical" if null_pct > 10 else "warning",
            ))
        return self

    def check_positive_values(self, columns: List[str]) -> "DataValidator":
        for col in columns:
            if col in self.df.columns and pd.api.types.is_numeric_dtype(self.df[col]):
                neg_count = int((self.df[col] < 0).sum())
                self.results.append(ValidationResult(
                    check_name=f"positive_{col}",
                    passed=neg_count == 0,
                    details=f"{neg_count} negative values",
                    severity="critical",
                ))
        return self

    def check_date_range(self, date_col: str, min_year: int = 2017) -> "DataValidator":
        if date_col in self.df.columns:
            col = pd.to_datetime(self.df[date_col])
            self.results.append(ValidationResult(
                check_name=f"date_range_{date_col}",
                passed=int(col.dt.year.min()) >= min_year,
                details=f"Range: {col.min()} to {col.max()}",
                severity="warning",
            ))
        return self

    def check_no_duplicates(self, subset: List[str]) -> "DataValidator":
        existing = [c for c in subset if c in self.df.columns]
        if existing:
            dup_count = int(self.df.duplicated(subset=existing).sum())
            self.results.append(ValidationResult(
                check_name=f"no_duplicates_{'_'.join(existing)}",
                passed=dup_count == 0,
                details=f"{dup_count} duplicate rows",
                severity="warning",
            ))
        return self

    def report(self, save_path: Path | None = None) -> bool:
        """Log report and return True if all critical checks pass."""
        logger.info(f"{'='*50}")
        logger.info(f"VALIDATION: {self.dataset_name}")
        logger.info(f"{'='*50}")

        all_critical_passed = True
        report_rows = []

        for r in self.results:
            icon = "✅" if r.passed else ("❌" if r.severity == "critical" else "⚠️")
            logger.info(f"  {icon} [{r.severity.upper()}] {r.check_name}: {r.details}")
            if not r.passed and r.severity == "critical":
                all_critical_passed = False
            report_rows.append({
                "check": r.check_name,
                "passed": r.passed,
                "details": r.details,
                "severity": r.severity,
            })

        status = "PASSED" if all_critical_passed else "FAILED"
        logger.info(f"  Overall: {status}\n")

        if save_path:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            report_data = {
                "dataset": self.dataset_name,
                "timestamp": datetime.utcnow().isoformat(),
                "status": status,
                "checks": report_rows,
            }
            save_path.write_text(json.dumps(report_data, indent=2))
            logger.info(f"  Report saved → {save_path}")

        return all_critical_passed
