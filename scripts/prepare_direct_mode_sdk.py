"""Prepare the official SDK archive format expected by genlayer-test 0.29.2."""
from pathlib import Path
import hashlib
import shutil
import tempfile
from urllib.request import Request, urlopen


VERSION = "v0.2.16"
URL = "https://github.com/genlayerlabs/genvm/releases/download/v0.2.16/genvm-universal.tar.xz"
SHA256 = "4f0b358ec98ec148be9b95cdfb0f0e1a6cbe64da0194fdfac3fffc6f5d1d93e2"
CACHE = Path.home() / ".cache"
destination = CACHE / "gltest-direct" / f"genvm-universal-{VERSION}.tar.xz"
destination.parent.mkdir(parents=True, exist_ok=True)


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


if destination.exists() and sha256_file(destination) == SHA256:
    print(f"Direct Mode SDK {VERSION} is already cached and verified")
    raise SystemExit(0)

cached = CACHE / "genvm-linter" / f"genvm-universal-{VERSION}.tar.xz"
if cached.exists():
    shutil.copyfile(cached, destination)
else:
    request = Request(URL, headers={"User-Agent": "Spatch Direct Mode test setup"})
    with urlopen(request, timeout=300) as response, tempfile.NamedTemporaryFile(
        dir=destination.parent, delete=False
    ) as temp:
        temp_path = Path(temp.name)
        digest = hashlib.sha256()
        while chunk := response.read(1024 * 1024):
            temp.write(chunk)
            digest.update(chunk)
    if digest.hexdigest() != SHA256:
        temp_path.unlink(missing_ok=True)
        raise SystemExit("Official Direct Mode SDK archive SHA-256 did not match its pinned digest")
    temp_path.replace(destination)

if sha256_file(destination) != SHA256:
    raise SystemExit("Cached Direct Mode SDK archive failed SHA-256 verification")
print(f"Prepared and verified official GenVM Direct Mode SDK {VERSION}")
