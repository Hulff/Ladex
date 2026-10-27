"""PyInstaller entry point that preserves the tabconv package context."""

from tabconv.cli import main

raise SystemExit(main())
