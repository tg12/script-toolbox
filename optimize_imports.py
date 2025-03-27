"""Copyright (C) 2025 James Sawyer
All rights reserved.

This script and the associated files are private
and confidential property. Unauthorized copying of
this file, via any medium, and the divulgence of any
contained information without express written consent
is strictly prohibited.

This script is intended for personal use only and should
not be distributed or used in any commercial or public
setting unless otherwise authorized by the copyright holder.
By using this script, you agree to abide by these terms.

DISCLAIMER: This script is provided 'as is' without warranty
of any kind, either express or implied, including, but not
limited to, the implied warranties of merchantability,
fitness for a particular purpose, or non-infringement. In no
event shall the authors or copyright holders be liable for
any claim, damages, or other liability, whether in an action
of contract, tort or otherwise, arising from, out of, or in
connection with the script or the use or other dealings in
the script.
"""

# -*- coding: utf-8 -*-
# pylint: disable=C0116, W0621, W1203, C0103, C0301, W1201, W0511, E0401, E1101, E0606
# C0116: Missing function or method docstring
# W0621: Redefining name %r from outer scope (line %s)
# W1203: Use % formatting in logging functions and pass the % parameters as arguments
# C0103: Constant name "%s" doesn't conform to UPPER_CASE naming style
# C0301: Line too long (%s/%s)
# W1201: Specify string format arguments as logging function parameters
# W0511: TODOs
# E1101: Module 'holidays' has no 'US' member (no-member) ... it does, so ignore this
# E0606: possibly-used-before-assignment, ignore this
# UP018: native-literals (UP018)

"""I got annoyed and decided to hack this tool together after seeing too many imports
buried inside functions. It scans Python files and moves these imports to the top of
the module where they belong.

This tool finds import statements declared inside functions and moves them to the top
of the module. Imports within functions should only be used to prevent circular imports,
for optional dependencies, or if an import is slow.

Run it on a directory and watch the magic happen, or use --dry-run to see what it would do
without making any changes.
"""

import argparse
import ast
import importlib
import logging
import os
import sys
from ast import NodeVisitor
from typing import List, Set, Tuple

# These library imports will not be moved to the top of the module
EXCLUDE_LIBS: Set[str] = {
    "urllib.request",
    "xlrd",
    "xlsxwriter",
}

EXCLUDE_FILES: Set[str] = {
    "__init__.py",
}


def setup_logging(verbose: bool = False) -> None:
    """Configure logging based on verbosity level.

    Args:
        verbose: If True, set log level to DEBUG, otherwise INFO

    """
    log_level = logging.DEBUG if verbose else logging.INFO
    log_format = "%(levelname)s: %(message)s"
    logging.basicConfig(level=log_level, format=log_format)


class ImportVisitor(NodeVisitor):
    """Visitor to find import statements inside function definitions."""

    def __init__(self, file_path: str) -> None:
        """Initialize the visitor.

        Args:
            file_path: Path to the file being analyzed

        """
        self.ret = 0  # Return code (0 = success, 1 = issues found)
        self.file_path = file_path
        self.line_numbers: List[int] = []
        self.imports_found: List[Tuple[int, str, str]] = []  # line_number, import_name, full_line

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit a function definition and look for imports inside it."""
        for sub_node in ast.walk(node):
            if self._is_movable_import_from(sub_node):
                self._process_import_from(sub_node)
            elif self._is_movable_import(sub_node):
                self._process_import(sub_node)

        self.generic_visit(node)

    def _is_movable_import_from(self, node: ast.AST) -> bool:
        """Check if the node is an ImportFrom that should be moved."""
        return isinstance(node, ast.ImportFrom) and node.module != "__main__" and node.module not in EXCLUDE_LIBS and node.module.split(".")[0] not in EXCLUDE_LIBS

    def _is_movable_import(self, node: ast.AST) -> bool:
        """Check if the node is an Import that should be moved."""
        return isinstance(node, ast.Import)

    def _process_import_from(self, node: ast.ImportFrom) -> None:
        """Process an ImportFrom node to determine if it should be moved."""
        try:
            importlib.import_module(node.module)
        except Exception:
            # If the module can't be imported, it's probably not a standard library
            pass
        else:
            message = f"{self.file_path}:{node.lineno}:{node.col_offset} {node.end_lineno} standard library import '{node.module}' should be at the top of the file"
            logging.info(message)

            # Store import information for later use
            import_stmt = f"from {node.module} import {', '.join(n.name for n in node.names)}"
            self.imports_found.append((node.lineno, node.module, import_stmt))

            self.ret = 1
            self.line_numbers.append(node.lineno)

    def _process_import(self, node: ast.Import) -> None:
        """Process an Import node to determine if it should be moved."""
        for name in node.names:
            if name.name == "__main__" or name.name in EXCLUDE_LIBS or name.name.split(".")[0] in EXCLUDE_LIBS:
                continue

            try:
                importlib.import_module(name.name)
            except Exception:
                # If the module can't be imported, it's probably not a standard library
                pass
            else:
                message = f"{self.file_path}:{node.lineno}:{node.col_offset} standard library import '{name.name}' should be at the top of the file"
                logging.info(message)

                # Store import information for later use
                import_stmt = f"import {name.name}"
                self.imports_found.append((node.lineno, name.name, import_stmt))

                self.ret = 1
                self.line_numbers.append(node.lineno)


def process_file(file_path: str, dry_run: bool = False) -> int:
    """Process a single Python file.

    Args:
        file_path: Path to the file to process
        dry_run: If True, don't modify files, just report what would change

    Returns:
        Integer return code (0 = success, 1 = issues found)

    """
    logging.debug(f"Processing file: {file_path}")

    with open(file_path, encoding="utf-8") as fd:
        content = fd.read()

    tree = ast.parse(content)
    visitor = ImportVisitor(file_path)
    visitor.visit(tree)

    if visitor.line_numbers:
        logging.info(f"Found {len(visitor.line_numbers)} imports to move in {file_path}")

        # Sort imports by module name for better organization
        visitor.imports_found.sort(key=lambda x: x[1])

        for _, module_name, import_stmt in visitor.imports_found:
            logging.info(f"  Will move: {import_stmt}")

        if dry_run:
            logging.info("Dry run: No changes made to the file")
            return visitor.ret

        content_lines = content.split("\n")
        import_lines = []

        # Make sure to iterate starting from the last element because we are removing lines by index
        for line_number in sorted(visitor.line_numbers, reverse=True):
            removed_line = content_lines.pop(line_number - 1)
            import_lines.append(removed_line)
            logging.debug(f"Removed line {line_number}: {removed_line.strip()}")

        # Add the imports at the top of the file
        for line in reversed(import_lines):
            content_lines.insert(0, line.strip())
            logging.debug(f"Added to top: {line.strip()}")

        if not dry_run:
            with open(file_path, encoding="utf-8", mode="w") as fd:
                fd.write("\n".join(content_lines))
            logging.info(f"Updated file: {file_path}")
    else:
        logging.debug(f"No issues found in {file_path}")

    return visitor.ret


def main() -> int:
    """Main entry point.

    Returns:
        Integer return code (0 = success, 1 = issues found)

    """
    parser = argparse.ArgumentParser(
        description="Find and fix imports inside functions by moving them to the top of the file",
    )
    parser.add_argument("folder", help="Folder to scan for Python files")
    parser.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        help="Don't modify files, just show what would be changed",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress all output except errors",
    )
    args = parser.parse_args()

    # Configure logging based on arguments
    if args.quiet:
        logging.basicConfig(level=logging.ERROR)
    else:
        setup_logging(args.verbose)

    logging.info(f"Scanning folder: {args.folder}")
    if args.dry_run:
        logging.info("Running in dry-run mode - no files will be modified")

    ret = 0
    files_processed = 0
    files_with_issues = 0

    for subdir, _, files in os.walk(args.folder):
        for file_ in files:
            if not file_.endswith(".py") or file_ in EXCLUDE_FILES:
                continue

            file_path = os.path.join(subdir, file_)
            files_processed += 1

            file_ret = process_file(file_path, args.dry_run)
            ret |= file_ret

            if file_ret:
                files_with_issues += 1

    # Summary at the end
    logging.info(f"Summary: Processed {files_processed} Python files")
    logging.info(f"Found issues in {files_with_issues} files")

    if args.dry_run and files_with_issues > 0:
        logging.info("Re-run without --dry-run to apply the changes")

    return ret


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        logging.info("Process interrupted by user")
        sys.exit(130)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}", exc_info=True)
        sys.exit(1)
