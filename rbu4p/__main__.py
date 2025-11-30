import argparse
import datetime
import logging
import os
import pathlib
import shutil
import sys
import typing as t

from .app import RBU4Portainer
from .const import *
from .util import allow_insecure, str2bool


class Config(argparse.Namespace):
    url: str
    archive: t.Union[str, None]
    destination: str
    token: str
    insecure: bool
    force: t.Union[bool, None]
    verbose: int
    on_bad_endpoint: t.Literal["skip", "halt"]

    @classmethod
    def create_parser(cls) -> argparse.ArgumentParser:
        from . import __version__

        parser = argparse.ArgumentParser(
            prog="rbu4p",
            description="Rudimentary Backup Utility for Portainer",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            add_help=False,
        )
        parser.add_argument(
            "--help",
            "-h",
            "-?",
            action="help",
            help="Show this help message and exit",
        )
        parser.add_argument(
            "--version",
            "-V",
            action="version",
            version=f"%(prog)s v{__version__}",
            help="Show the program's version number and exit",
        )
        parser.add_argument(
            "--verbose",
            "-v",
            action="count",
            help="Verbosity. Pass once for error/warnings, twice for info, three times for debugging just rbu4p, four times for debugging everything",
        )
        url_kwargs = {"default": os.getenv(CONF_URL)}
        if not str(url_kwargs["default"] or "").strip():
            url_kwargs["required"] = True

        parser.add_argument(
            "--url",
            "-u",
            metavar="URL",
            help=f"Portainer API URL. Defaults to the value of the {CONF_URL} environment variable",
            **url_kwargs,
        )
        token_kwargs = {"default": os.getenv(CONF_TOKEN)}
        if not str(token_kwargs["default"] or "").strip():
            token_kwargs["required"] = True
        parser.add_argument(
            "--token",
            "-t",
            metavar="TOKEN",
            help=f"Portainer access token. Defaults to the value of the {CONF_TOKEN} environment variable",
            **token_kwargs,
        )
        parser.add_argument(
            "--destination",
            "-d",
            default=os.getenv(CONF_DESTINATION),
            metavar="FILEPATH",
            help=f"Destination output (without archive suffix). Defaults to the value of the {CONF_DESTINATION} environment variable. If unset, the format '4bu4p_{{timestamp}}' will be used",
        )
        parser.add_argument(
            "--archive",
            "-a",
            default=os.getenv(CONF_ARCHIVE),
            choices=["", *(x[0] for x in shutil.get_archive_formats())],
            type=lambda x: str(x or "").lower().strip(),
            help=f"Archive format (or none/empty string for a folder). Defaults to the value of the {CONF_ARCHIVE} environment variable",
        )
        parser.add_argument(
            "--insecure",
            "-k",
            action="store_true",
            default=str2bool(os.getenv(CONF_INSECURE), allow_none=True),
            help=f"Allow insecure server connections. Defaults to the value of the {CONF_INSECURE} environment variable",
        )
        parser.add_argument(
            "--force",
            "-f",
            action=argparse.BooleanOptionalAction,
            default=str2bool(os.getenv(CONF_FORCE), allow_none=True),
            help=f"Whether to overwrite the destination file. Defaults to the value of the {CONF_FORCE} environment variable. If unset, the default is to ask if in an interactive terminal, and to fail otherwise",
        )
        parser.add_argument(
            "--on-bad-endpoint",
            "-e",
            choices=["skip", "halt"],
            type=lambda x: str(x or "").lower().strip(),
            default=os.getenv(CONF_ON_BAD_ENDPOINT) or DEFAULT_ON_BAD_ENDPOINT,
            help=f"When encountering a bad endpoint, choose whether to skip it or halt entirely. Defaults to the value of the {CONF_ON_BAD_ENDPOINT} environment variable",
        )

        return parser

    @classmethod
    def create(cls, args=None, /) -> t.Self:
        parser = cls.create_parser()
        return parser.parse_args(args=args, namespace=cls())


if __name__ == "__main__":
    args = Config.create()
    destination = pathlib.Path(
        args.destination or f"rbu4p_{int(datetime.datetime.now().timestamp())}"
    )

    if args.verbose:
        if args.verbose >= 4:
            level = logging.DEBUG
        elif args.verbose >= 3:
            logging.getLogger("rbu4p").setLevel(logging.DEBUG)
            level = logging.INFO
        elif args.verbose >= 2:
            level = logging.INFO
        elif args.verbose >= 1:
            level = logging.WARNING

        logging.basicConfig(level=level)

    with allow_insecure(args.insecure):
        app = RBU4Portainer(
            args.url,
            args.token,
            destination,
            force=args.force,
            archive=args.archive,
            verify=None if args.insecure is None else not args.insecure,
            on_bad_endpoint=args.on_bad_endpoint,
        )
        sys.exit(app())
