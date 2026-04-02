import argparse
import pathlib
import subprocess
import sys


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Batch process BVH files with scripts/bvh_to_robot.py"
    )
    parser.add_argument(
        "--input_dir",
        type=str,
        default="lafan1",
        help="Directory containing BVH files.",
    )
    parser.add_argument(
        "--format",
        choices=["lafan1", "nokov"],
        default="lafan1",
        help="Input BVH format.",
    )
    parser.add_argument(
        "--robot",
        choices=[
            "unitree_g1",
            "unitree_g1_with_hands",
            "booster_t1",
            "stanford_toddy",
            "fourier_n1",
            "engineai_pm01",
            "pal_talos",
            "x2_ultra",
        ],
        default="x2_ultra",
        help="Target robot type.",
    )
    parser.add_argument(
        "--video_dir",
        type=str,
        default="videos",
        help="Output directory for mp4 files.",
    )
    parser.add_argument(
        "--save_dir",
        type=str,
        default="outputs",
        help="Output directory for pkl files.",
    )
    parser.add_argument(
        "--no_rate_limit",
        action="store_true",
        default=False,
        help="Do not pass --rate_limit to bvh_to_robot.py.",
    )
    parser.add_argument(
        "--no_record_video",
        action="store_true",
        default=False,
        help="Do not pass --record_video to bvh_to_robot.py.",
    )
    parser.add_argument(
        "--skip_existing",
        action="store_true",
        default=False,
        help="Skip files whose mp4 and pkl already exist.",
    )
    parser.add_argument(
        "--stop_on_error",
        action="store_true",
        default=False,
        help="Stop immediately if one file fails.",
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        default=False,
        help="Print commands without executing them.",
    )
    args = parser.parse_args()

    repo_root = pathlib.Path(__file__).resolve().parent.parent
    script_path = repo_root / "scripts" / "bvh_to_robot.py"
    input_dir = (repo_root / args.input_dir).resolve()
    video_dir = (repo_root / args.video_dir).resolve()
    save_dir = (repo_root / args.save_dir).resolve()

    if not input_dir.exists():
        print(f"[ERROR] Input directory not found: {input_dir}")
        return 1

    bvh_files = sorted(input_dir.rglob("*.bvh"))
    if not bvh_files:
        print(f"[WARN] No .bvh files found in: {input_dir}")
        return 0

    video_dir.mkdir(parents=True, exist_ok=True)
    save_dir.mkdir(parents=True, exist_ok=True)

    failed = 0
    processed = 0
    skipped = 0

    print(f"[INFO] Found {len(bvh_files)} BVH files under {input_dir}")

    for idx, bvh_path in enumerate(bvh_files, start=1):
        rel = bvh_path.relative_to(input_dir)
        rel_no_suffix = rel.with_suffix("")
        video_path = video_dir / f"{rel_no_suffix}.mp4"
        save_path = save_dir / f"{rel_no_suffix}.pkl"

        video_path.parent.mkdir(parents=True, exist_ok=True)
        save_path.parent.mkdir(parents=True, exist_ok=True)

        if args.skip_existing and video_path.exists() and save_path.exists():
            skipped += 1
            print(f"[{idx}/{len(bvh_files)}] [SKIP] {rel}")
            continue

        cmd = [
            sys.executable,
            str(script_path),
            "--bvh_file",
            str(bvh_path),
            "--format",
            args.format,
            "--robot",
            args.robot,
            "--video_path",
            str(video_path),
            "--save_path",
            str(save_path),
        ]

        if not args.no_rate_limit:
            cmd.append("--rate_limit")
        if not args.no_record_video:
            cmd.append("--record_video")

        print(f"[{idx}/{len(bvh_files)}] [RUN] {rel}")
        print(" ".join(cmd))

        if args.dry_run:
            processed += 1
            continue

        result = subprocess.run(cmd, cwd=str(repo_root))
        if result.returncode == 0:
            processed += 1
        else:
            failed += 1
            print(f"[ERROR] Failed: {rel} (exit code {result.returncode})")
            if args.stop_on_error:
                break

    print(
        f"[DONE] processed={processed}, skipped={skipped}, failed={failed}, total={len(bvh_files)}"
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
