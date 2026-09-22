#!/usr/bin/env python3
"""生成本机实测耗时表和图，临时目录运行，避免覆盖项目中的题目文件。"""
import csv
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

project = Path(__file__).resolve().parent
main = project / "main.py"
if not main.is_file():
    raise SystemExit("请将 performance_plot.py 放在 main.py 所在的项目目录后运行。")

results = []
for n in (100, 1000, 10000):
    with tempfile.TemporaryDirectory() as tmp:
        start = time.perf_counter()
        subprocess.run(
            [sys.executable, str(main), "-n", str(n), "-r", "100"],
            cwd=tmp, check=True, stdout=subprocess.DEVNULL
        )
        seconds = time.perf_counter() - start
    print(f"{n} 题：{seconds:.3f} 秒")
    results.append((n, seconds))

with (project / "benchmark.csv").open("w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(("Questions", "Seconds"))
    writer.writerows(results)

fig, ax = plt.subplots(figsize=(7.5, 4.5))
ax.bar([str(n) for n, _ in results], [t for _, t in results])
ax.set(xlabel="Number of questions", ylabel="Elapsed time (s)", title="Exercise generation performance")
fig.tight_layout()
fig.savefig(project / "performance.png", dpi=240)
plt.close(fig)
print("输出：benchmark.csv、performance.png（当前版本实测，不是优化前后对比）")
