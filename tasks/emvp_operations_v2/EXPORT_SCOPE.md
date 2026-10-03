# Export scope

Only independently authored task-design contracts, source citations, audit findings and static tests are included. Publisher PDFs, extracted full article text, publisher pixels, caches and the builder/exporter are excluded.

Public repository inclusion is not actor runtime visibility: apply RELEASE_BOUNDARY.json. No runtime loader, robot world, hardware, controller, physics/scientific solver or measurements are supplied. No repository LICENSE is added or changed.

Run python -B tests/run_validation.py from this directory. Optional source-byte verification accepts only an explicit external --source-dir; source files are never bundled.
