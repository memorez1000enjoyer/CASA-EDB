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
    write_zip()


def write_zip():
    """Zip the output folder (no Python caches) -> ../../EBD_Clip_v1.1_output.zip"""
    import zipfile
    zip_path = os.path.join(os.path.dirname(ROOT), "EBD_Clip_v1.1_output.zip")
    base = os.path.dirname(ROOT)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for d, dirs, files in os.walk(ROOT):
            dirs[:] = sorted(x for x in dirs if x != "__pycache__")
            for f in sorted(files):
                if not f.endswith(".pyc"):
                    p = os.path.join(d, f)
                    z.write(p, os.path.relpath(p, base))
    print("wrote", zip_path)


if __name__ == "__main__":
    main()
