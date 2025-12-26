"""Entry point for running metaframe as a module."""

import sys


def main():
    """Main entry point - launches GUI by default, CLI if arguments provided."""
    if len(sys.argv) > 1:
        from metaframe.cli.main import cli
        cli()
    else:
        from metaframe.gui.main_window import main as gui_main
        gui_main()


if __name__ == "__main__":
    main()
