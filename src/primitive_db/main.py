#!/usr/bin/env python3
"""Entry point for both console commands and module execution."""

from primitive_db.engine import run


def main():
    """Start the database application."""
    run()


if __name__ == "__main__":
    main()
