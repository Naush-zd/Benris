import argparse

import uvicorn


def main() -> None:
    parser = argparse.ArgumentParser(prog="agentctl")
    subparsers = parser.add_subparsers(dest="command", required=True)
    start = subparsers.add_parser("start", help="Start the local Benris control plane")
    start.add_argument("--host", default="127.0.0.1")
    start.add_argument("--port", default=8000, type=int)
    args = parser.parse_args()

    if args.command == "start":
        uvicorn.run("src.api.server:app", host=args.host, port=args.port, reload=False)