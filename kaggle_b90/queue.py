"""B90 Kaggle queue: push any kernel not yet on Kaggle when a CPU slot is free (limit 5), download each
kernel's output once it is COMPLETE, stop when all six outputs are local. Every poll result other than
an explicit 'not found' counts as unknown (retry later), never as 'absent' (PAPER_WORKFLOW_LESSONS: a 429
storm once made queues resubmit finished kernels). Pushes are recorded in registry.txt and never repeated.

    python kaggle_b90/queue.py
"""
import os
import re
import subprocess
import time

HERE = os.path.dirname(os.path.abspath(__file__))
KAGGLE = r"C:\Users\abdulhamid batayhi\AppData\Local\Programs\Python\Python313\Scripts\kaggle.exe"
SLUG = "abdulhamidbatayhi/p2-b90-o1ident-{}"
REG = os.path.join(HERE, "registry.txt")
PARTS = range(6)


def run(*a):
    r = subprocess.run([KAGGLE, *a], capture_output=True, text=True, timeout=600)
    return (r.stdout + r.stderr).strip()


def status(p):
    out = run("kernels", "status", SLUG.format(p))
    m = re.search(r'status "KernelWorkerStatus\.(\w+)"', out)
    if m:
        return m.group(1)
    if "Permission 'kernels.get' was denied" in out or "404" in out:
        return "ABSENT"
    return "UNKNOWN"


def log(msg):
    line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}"
    print(line, flush=True)
    open(REG, "a").write(line + "\n")


def main():
    pushed = {int(m) for m in re.findall(r"\bk(\d) pushed", open(REG).read())} if os.path.exists(REG) else set()
    pushed |= {0, 1, 2, 4, 5}      # first batch, pushed 2026-11-08 (registry line 'pushed k0-k5', k3 failed)
    done = {p for p in PARTS if os.path.exists(os.path.join(HERE, "out", f"k{p}", f"o1ident_part{p}.json"))}
    while len(done) < len(PARTS):
        st = {p: status(p) for p in PARTS if p not in done}
        busy = sum(s in ("RUNNING", "QUEUED") for s in st.values())
        for p, s in st.items():
            if s == "COMPLETE":
                d = os.path.join(HERE, "out", f"k{p}")
                os.makedirs(d, exist_ok=True)
                run("kernels", "output", SLUG.format(p), "-p", d)
                if os.path.exists(os.path.join(d, f"o1ident_part{p}.json")):
                    done.add(p)
                    log(f"k{p} output downloaded")
            elif s in ("ERROR", "CANCEL_ACKNOWLEDGED"):
                log(f"k{p} status {s}: needs attention")
            elif s == "ABSENT" and p not in pushed and busy < 5:
                out = run("kernels", "push", "-p", os.path.join(HERE, f"k{p}"))
                if "successfully pushed" in out:
                    pushed.add(p)
                    busy += 1
                    log(f"k{p} pushed")
                else:
                    log(f"k{p} push not accepted yet: {out[-120:]}")
        print(time.strftime("%H:%M:%S"), st, "done", sorted(done), flush=True)
        if len(done) < len(PARTS):
            time.sleep(300)
    log("ALL_OUTPUTS_DOWNLOADED")


if __name__ == "__main__":
    main()
