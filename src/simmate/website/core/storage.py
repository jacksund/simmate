from django.contrib.staticfiles.storage import ManifestStaticFilesStorage


class SimmateManifestStaticFilesStorage(ManifestStaticFilesStorage):
    """
    A `ManifestStaticFilesStorage` that leaves certain vendored bundles
    untouched during `collectstatic`.

    Django's manifest storage renames every static file to include a content
    hash. That breaks self-loading webpack bundles (e.g. ChemDraw JS), whose
    runtime requests its own dynamically-imported chunks by their *original*
    filenames. Once Django hashes those chunks, the original names no longer
    exist on disk and the chunk requests 404. Django only rewrites `url(...)`
    and sourcemap references inside css/js, so it cannot fix a webpack chunk
    map.

    To avoid this, we skip hashing (and post-processing) for any file whose
    name starts with one of `excluded_prefixes`. Those files are copied to
    `STATIC_ROOT` and served under their original names, while every other
    static file is still content-hashed and cache-busted as usual.
    """

    # Directory prefixes (posix-style, as static file names always are) whose
    # contents must keep their original filenames. Add other self-loading
    # webpack bundles here if needed.
    excluded_prefixes = ("chemdrawweb/",)

    # Don't 500 the page when a static reference isn't in the manifest; the
    # path passes through unchanged (and 404s in the browser) instead. This
    # matches the default (non-hashed) storage's tolerance and acts as a
    # backstop for the excluded bundles' internal, non-manifested chunks.
    manifest_strict = False

    def _is_excluded(self, name):
        return name.startswith(self.excluded_prefixes)

    def hashed_name(self, name, content=None, filename=None):
        # Used during `collectstatic` post-processing. Returning the name
        # unchanged keeps the bundle's files at their original paths on disk.
        if self._is_excluded(name):
            return name
        return super().hashed_name(name, content=content, filename=filename)

    def stored_name(self, name):
        # Used at runtime by `url()` / the `{% static %}` tag. Excluded files
        # are never added to the manifest (see `post_process`), so resolve them
        # to their original path directly. This keeps the bundle working even
        # if `manifest_strict` is later turned back on.
        if self._is_excluded(name):
            return name
        return super().stored_name(name)

    def post_process(self, paths, dry_run=False, **options):
        # Drop excluded files before delegating so Django never tries to hash
        # them or rewrite their (webpack-managed) internal references.
        paths = {
            name: storage_and_path
            for name, storage_and_path in paths.items()
            if not self._is_excluded(name)
        }
        yield from super().post_process(paths, dry_run=dry_run, **options)
