# Local review export scope

Only files explicitly named in EXPORT_ALLOWLIST.json are eligible for the local review handoff. They are original English task-design documents, JSON contracts and original static Python checks. This is not authorization to publish; the parent reviews publication separately.

Excluded: publisher PDFs, rendered source pages, screenshots, source text extractions, movie files, third-party CAD, raw source data, reconstructed source plots, credentials and machine-specific paths. Source hashes identify inspected private bytes without packaging those bytes. A tool-rendered main-text snapshot hash is not a publisher HTML or PDF identity hash.

The paper publisher reports Creative Commons Attribution 4.0 with third-party exceptions. That statement is not used to import source assets. The project does not relicense the paper, apparatus designs or third-party materials. No new repository license is asserted by this package.

The allowlist hashes all payload files except itself and VERIFICATION.json to avoid circular receipts. Exact file-set and hash checks are necessary before parent integration. No browser/UI/display claim, simulation claim or hardware validation claim is included.
