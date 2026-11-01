"""One-shot local queue: wait for verified stable V, then launch frozen Ridge ablation."""
from core import *
import argparse
from datetime import datetime, timezone, timedelta
import html
import subprocess
import sys
import traceback


def render(root, state):
    formal = root / "formal_01"
    try:
        progress = read(formal / "status.json")
    except (OSError, ValueError):
        progress = {}
    labels = {"waiting_for_V": "排队中：等待实验五完成与核验",
              "running": "Li–Niu 对照正在计算", "completed": "计算与独立核验完成",
              "failed": "运行失败，请检查错误日志"}
    phase = state["phase"]
    done, total = progress.get("tasks_done", 0), progress.get("tasks_total", 520)
    now = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")
    text = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta http-equiv="refresh" content="10"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Li–Niu 对照 · 排队与实时进度</title>
<style>body{{max-width:950px;margin:36px auto;padding:0 20px;font:17px/1.8 'Microsoft YaHei',sans-serif;color:#253146;background:#f5f7fa}}
section{{background:white;border:1px solid #dce2eb;border-radius:12px;padding:24px;margin:20px 0}}h1{{font-size:26px}}a{{color:#235db7}}
pre{{white-space:pre-wrap;font:14px/1.8 Consolas,monospace}}progress{{width:100%;height:22px}}</style></head>
<body><h1>Li–Niu 与完整系数分数：Ridge 对照</h1><p>北京时间 {now} · 每 10 秒刷新页面</p>
<section><strong>{labels.get(phase, phase)}</strong><p>{html.escape(state.get('reason', ''))}</p>
<p>正式任务：{done} / {total} 个数据—预算任务；共 104,000 条逐次指标。</p>
<progress value="{done}" max="{total}"></progress>
<p>正式阶段：{html.escape(str(progress.get('phase', '尚未开始')))}</p></section>
<section><p>前置实验五必须完成全部随机抽样、稳定性门禁与独立结果核验。315/318 等目标分块进度不代表完成。</p>
<p>本实验先做精确分数对照：UNI、NORM、LEV、LN_floor、FULL_OPT；不执行 NOPL 外层迭代。</p>
<p><a href="formal_01/RESULTS.md">结果报告</a>　<a href="formal_01/comparison.png">结果图</a>　
<a href="formal_01/primary_comparison.json">唯一主比较</a>　<a href="run.log">运行日志</a>　
<a href="error.log">错误日志</a></p></section>
<section><pre>{html.escape(json.dumps(state, ensure_ascii=False, indent=2))}</pre></section>
</body></html>"""
    temporary = root / "实时进度.tmp.html"
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, root / "实时进度.html")


def queue(prepared, root, predecessor, pilot, poll=30):
    root, prepared = Path(root).resolve(), Path(prepared).resolve()
    root.mkdir(parents=True, exist_ok=True)
    lock = root / "queue.lock"
    with lock.open("x", encoding="utf-8") as stream:
        stream.write(str(os.getpid()))
    try:
        seal = verify_prepared(prepared, check_live=True)
        acceptance = read(pilot)
        if not acceptance.get("passed") or acceptance.get("sources") != seal["sources"]:
            raise ValueError("Pilot does not certify this frozen preparation")
        config = read(prepared / "protocol.json")
        if config.get("scope") != "formal_reused_inputs_ablation":
            raise ValueError("A pilot fixture cannot be automatically released")
        while True:
            ready, reason = predecessor_ready(predecessor)
            state = dict(phase="waiting_for_V", completed=False, reason=reason,
                         pid=os.getpid(), checked_at=time.time(), predecessor=str(predecessor),
                         preparation_identity=digest(prepared / "seal.json"))
            save(root / "queue_status.json", state)
            render(root, state)
            if ready:
                break
            time.sleep(poll)
        # If code was edited while queued, stop rather than silently change the protocol.
        verify_prepared(prepared, check_live=True)
        script = prepared / "source_snapshot" / "run_experiment.py"
        command = [sys.executable, "-B", "-X", "utf8", str(script), "run",
                   "--prepared", str(prepared), "--output", str(root / "formal_01"),
                   "--predecessor", str(predecessor), "--pilot", str(pilot),
                   "--workers", str(config["workers"])]
        with (root / "run.log").open("a", encoding="utf-8") as stdout, \
             (root / "error.log").open("a", encoding="utf-8") as stderr:
            process = subprocess.Popen(command, stdout=stdout, stderr=stderr,
                                       creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
            state.update(phase="running", reason=reason, controller_pid=process.pid,
                         launched_at=time.time(), command=command)
            save(root / "launch_receipt.json", state)
            while process.poll() is None:
                state["checked_at"] = time.time()
                save(root / "queue_status.json", state)
                render(root, state)
                time.sleep(min(15, poll))
        execution = read(root / "formal_01/execution.json")
        validation = read(root / "formal_01/independent_validation.json")
        if process.returncode or not execution.get("completed") or not validation.get("passed"):
            raise ValueError("Ridge run failed; see error.log and retained task records")
        state.update(phase="completed", completed=True, reason="全部任务、独立核验和分析报告已完成",
                     finished_at=time.time())
        save(root / "queue_status.json", state)
        render(root, state)
    except BaseException as error:
        state = dict(phase="failed", completed=False, pid=os.getpid(), checked_at=time.time(),
                     reason=type(error).__name__ + ": " + str(error))
        save(root / "queue_status.json", state)
        render(root, state)
        raise
    finally:
        lock.unlink(missing_ok=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepared", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--predecessor", type=Path, required=True)
    parser.add_argument("--pilot", type=Path, required=True)
    parser.add_argument("--poll", type=int, default=30, choices=range(5, 61))
    args = parser.parse_args()
    try:
        queue(args.prepared, args.root, args.predecessor, args.pilot, args.poll)
    except Exception:
        traceback.print_exc()
        sys.exit(1)
