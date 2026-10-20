"""Build and validate A7 inside the existing Pages artifact, without publishing."""
import os
import tempfile
from pathlib import Path

from build_a7_query_runtime import build as build_runtime
from build_a7_explorer_preview import build as build_site


def commit_site(dist, site, backup):
    """Install a complete generated site, restoring it if the final rename fails."""
    os.rename(dist, backup)
    try:
        os.rename(site, dist)
    except OSError:
        os.rename(backup, dist)
        raise


def materialize(dist):
    dist = Path(dist).resolve()
    # Nothing is installed until the entire native runtime and embedding pass.
    with tempfile.TemporaryDirectory(prefix='.a7-public-', dir=dist.parent) as temporary:
        temporary = Path(temporary)
        build_runtime(dist/'data/site-data.json', temporary/'runtime')
        receipt = build_site(dist, temporary/'runtime', temporary/'site', public=True)
        from a7_explorer_release import validate_explorer
        validate_explorer(lambda path: (temporary/'site'/path).read_bytes(), full=True)
        backup = temporary/'previous'
        commit_site(dist, temporary/'site', backup)
        # This is an offline build transaction. Pages uploads only the complete
        # validated dist in its existing artifact/job, never these directories.
    return receipt
