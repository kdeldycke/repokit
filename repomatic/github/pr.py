# Copyright Kevin Deldycke <kevin@deldycke.com> and contributors.
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.

"""GitHub pull request lifecycle helpers.

Generic primitives for querying and closing pull requests via the
{mod}`~repomatic.github.gh` wrapper. Used by workflows that need to
reconcile automation-managed PRs (like the `bump-version` job)
when their target state changes mid-flight.
"""

from __future__ import annotations

import json
import logging

from .gh import run_gh_command

TYPE_CHECKING = False
if TYPE_CHECKING:
    from typing import Any


def list_open_prs_by_branch(branch: str) -> list[dict[str, Any]]:
    """List open pull requests whose head branch matches `branch`.

    :param branch: The head branch name to filter on.
    :return: List of PR dicts with `number` and `title`. Empty if no
        open PR exists on `branch`.
    """
    output = run_gh_command([
        "pr",
        "list",
        "--state",
        "open",
        "--head",
        branch,
        "--json",
        "number,title",
    ])
    prs: list[dict[str, Any]] = json.loads(output)
    return prs


def close_pr(number: int, comment: str, delete_branch: bool = True) -> None:
    """Close a pull request with a comment.

    :param number: The PR number to close.
    :param comment: The comment to add when closing.
    :param delete_branch: When `True`, also delete the head branch.
    """
    args = [
        "pr",
        "close",
        str(number),
        "--comment",
        comment,
    ]
    if delete_branch:
        args.append("--delete-branch")
    run_gh_command(args)
    logging.info(f"Closed PR #{number}")


def close_open_prs_on_branch(branch: str, comment: str) -> list[int]:
    """Close every open PR whose head branch matches `branch`.

    Idempotent: a no-op when no open PR exists on the branch.

    :param branch: The head branch name to match.
    :param comment: The comment to add when closing each PR.
    :return: The list of PR numbers that were closed.
    """
    prs = list_open_prs_by_branch(branch)
    if not prs:
        logging.info(f"No open PR on branch {branch!r}, nothing to close.")
        return []
    closed: list[int] = []
    for pr in prs:
        close_pr(pr["number"], comment)
        closed.append(pr["number"])
    return closed
