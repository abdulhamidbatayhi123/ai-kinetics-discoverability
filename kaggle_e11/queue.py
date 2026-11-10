"""E11 Kaggle queue (about 2,000 samples per run). The account's five CPU slots are shared with other projects, so at
most MAX_MINE E11 kernels run at once; a push Kaggle refuses is retried at the next poll. Pushes are
recorded in registry.txt and never repeated. Only the part file and the log are downloaded
(--file-pattern). Poll results other than an explicit 'not found' count as unknown, never absent.

    python kaggle_e11/queue.py
"""
import os
import re
import subprocess
import time

HERE = os.path.dirname(os.path.abspath(__file__))
KAGGLE = r"C:\Users\abdulhamid batayhi\AppData\Local\Programs\Python\Python313\Scripts\kaggle.exe"
SLUG = "abdulhamidbatayhi/p2-e11-fine-{}"
REG = os.path.join(HERE, "registry.txt")
PARTS = range(9)
MAX_MINE = 2


def run(*a):
    try:
        r = subprocess.run([KAGGLE, *a], capture_output=True, text=True, timeout=600)
        return (r.stdout + r.stderr).strip()
    except subprocess.TimeoutExpired:
        return "TIMEOUT"


def status(p):
    out = run("kernels", "status", SLUG.format(p))
    m = re.search(r'status "KernelWorkerStatus\.(\w+)"', out)
    return m.group(1) if m else "UNKNOWN"


def log(msg):
    line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}"
    print(line, flush=True)
    open(REG, "a").write(line + "\n")


def part(p):
    return os.path.join(HERE, "out", f"k{p}", f"e11_part{p}.json")


def main():
    pushed = {int(m) for m in re.findall(r"\bk(\d) pushed", open(REG).read())} if os.path.exists(REG) else set()
    while not all(os.path.exists(part(p)) for p in PARTS):
        st = {p: (status(p) if p in pushed else "NOT_PUSHED") for p in PARTS if not os.path.exists(part(p))}
        busy = sum(s in ("RUNNING", "QUEUED", "UNKNOWN") for s in st.values())
        for p, s in st.items():
            if s == "COMPLETE":
                d = os.path.dirname(part(p))
                os.makedirs(d, exist_ok=True)
                run("kernels", "output", SLUG.format(p), "-p", d, "--file-pattern", r"e11_part.*\.json$|.*\.log$")
                if os.path.exists(part(p)):
                    try:                                   # hub rule: never mark done without checking content
                        import json
                        d = json.load(open(part(p)))
                        log(f"k{p} output downloaded: {len(d['rows'])} rows, codes {d['codes']}, kit {d['kit_commit'][:7]}")
                    except Exception as ex:
                        os.remove(part(p))
                        log(f"k{p} output unreadable ({ex}); removed, will retry")
            elif s in ("ERROR", "CANCEL_ACKNOWLEDGED"):
                log(f"k{p} status {s}: needs attention")
            elif s == "NOT_PUSHED" and busy < MAX_MINE:
                out = run("kernels", "push", "-p", os.path.join(HERE, f"k{p}"))
                if "successfully pushed" in out:
                    pushed.add(p)
                    busy += 1
                    log(f"k{p} pushed")
                else:
                    print(f"k{p} push refused: {out.splitlines()[-1] if out else 'no output'}", flush=True)
                    break                      # account full: retry at the next poll
        print(time.strftime("%H:%M:%S"), st, flush=True)
        time.sleep(300)
    log("ALL_OUTPUTS_DOWNLOADED")


if __name__ == "__main__":
    main()
