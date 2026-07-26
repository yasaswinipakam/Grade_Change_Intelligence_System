"""CSV serialization and Markdown quality reporting."""
from __future__ import annotations
from pathlib import Path
import pandas as pd
class CSVExporter:
    def export_to_csv(self, records, filename):
        frame=pd.DataFrame(records); frame.to_csv(filename,index=False); return frame
    def write_report(self, frame, metrics, filename, seed, command):
        numeric=frame.select_dtypes("number").describe().round(3).to_markdown()
        correlations=frame[[c for c in ("Q_feed","V_line","P_heat","W","M","H") if c in frame]].corr().round(3).to_markdown()
        Path(filename).write_text(f"# Synthetic-data generation report\n\n## Execution metadata\n\n- Seed: `{seed}`\n- Command: `{command}`\n- Rows: `{len(frame)}`\n\n## Dataset and validation summary\n\n- Transitions: `{metrics['transitions']}`\n- Success rate: `{metrics['success_rate']:.2f}%`\n- All numeric values finite: `{metrics['all_finite']}`\n- Phase distribution: `{metrics['phase_counts']}`\n- Warnings: `{metrics['warnings'] or 'None'}`\n\n## Implementation decisions\n\n- Forward Euler with the specification’s one-minute timestep and calibrated constants.\n- Percent Gaussian noise is interpreted as standard deviation relative to current value.\n- Warm-up uses the specified five hundred steps and tolerance is `0.01%`.\n- Ramps are linear; steady rows are exported every five minutes while transitions remain one-minute rows.\n\n## Numeric summary\n\n{numeric}\n\n## Core correlation matrix\n\n{correlations}\n")
