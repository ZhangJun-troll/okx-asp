"""Launch all 4 agents in parallel."""
import uvicorn, multiprocessing, sys
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

def run_agent(module: str, port: int):
    uvicorn.run(f"agents.{module}:app", host="0.0.0.0", port=port, log_level="warning")

if __name__ == "__main__":
    agents = [
        ("dispatcher.main", 8001),
        ("collector.main",  8002),
        ("analyst.main",    8003),
        ("settlement.main", 8004),
        ("summarizer.main", 8005),
    ]
    procs = []
    for module, port in agents:
        p = multiprocessing.Process(target=run_agent, args=(module, port), daemon=True)
        p.start()
        procs.append(p)
        print(f"  ✓ {module} → http://localhost:{port}")

    print("\nAll agents running. Press Ctrl+C to stop.")
    try:
        for p in procs:
            p.join()
    except KeyboardInterrupt:
        for p in procs:
            p.terminate()
        sys.exit(0)
