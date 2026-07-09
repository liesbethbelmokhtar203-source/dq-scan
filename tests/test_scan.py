import subprocess, sys

def test_basic_scan():
    r = subprocess.run([sys.executable, "dq_scan.py", "examples/sample.csv"],
                       capture_output=True, text=True)
    assert r.returncode == 0
    assert "nulls=1" in r.stdout  # the empty amount cell
    assert "currency" in r.stdout

if __name__ == "__main__":
    test_basic_scan()
    print("ok")
