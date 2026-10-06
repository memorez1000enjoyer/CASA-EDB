"""One command rebuilds everything:  python build_all.py [--quick] [--no-render]

1. export.py  - STL per part (print orientation), STEP per part, state assemblies
2. render.py  - PNG renders (needs a display; on Linux run under `xvfb-run -a`)
3. verify.py  - §9 checks -> ../VERIFICATION.md
4. zip the output folder -> ../../EBD_Clip_v1.1_output.zip
"""
import os
import sys
import shutil
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))


def run(args):
    print(">>", " ".join(args), flush=True)
    subprocess.run(args, cwd=HERE, check=True)


def main():
    py = sys.executable
    run([py, "export.py"])
    if "--no-render" not in sys.argv:
        if os.environ.get("DISPLAY") or sys.platform != "linux":
            run([py, "render.py"])
        elif shutil.which("xvfb-run"):
            run(["xvfb-run", "-a", py, "render.py"])
        else:
            print("no display and no xvfb-run: skipping renders")
    run([py, "verify.py"] + (["--quick"] if "--quick" in sys.argv else []))
    zip_base = os.path.join(os.path.dirname(ROOT), "EBD_Clip_v1.1_output")
    shutil.make_archive(zip_base, "zip", os.path.dirname(ROOT), os.path.basename(ROOT))
    print("wrote", zip_base + ".zip")


if __name__ == "__main__":
    main()
