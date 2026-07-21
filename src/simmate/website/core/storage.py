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

    def _is_excluded(self, name):
        return name.startswith(self.excluded_prefixes)

    def hashed_name(self, name, content=None, filename=None):
        # Both the `{% static %}` lookup and the on-disk copy resolve through
        # here, so returning the name unchanged keeps the bundle at its
        # original path.
        if self._is_excluded(name):
            return name
        return super().hashed_name(name, content=content, filename=filename)

    def post_process(self, paths, dry_run=False, **options):
        # Drop excluded files before delegating so Django never tries to hash
        # them or rewrite their (webpack-managed) internal references.
        paths = {
            name: storage_and_path
            for name, storage_and_path in paths.items()
            if not self._is_excluded(name)
        }
        yield from super().post_process(paths, dry_run=dry_run, **options)
