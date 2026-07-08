"""Build-time: download/convert JMdict_e into data/jmdict_e.tsv.gz.

Usage: python build_jmdict.py <path-to-JMdict_e or JMdict_e.gz>
"""

import gzip
import shutil
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from zhongwen_reader.jmdict import convert_xml

src = Path(sys.argv[1])
out = Path(__file__).parent / "data" / "jmdict_e.tsv.gz"

t = time.perf_counter()
if src.suffix == ".gz":
    with gzip.open(src, "rb") as f_in, tempfile.NamedTemporaryFile(
        delete=False, suffix=".xml"
    ) as f_out:
        shutil.copyfileobj(f_in, f_out)
        src = Path(f_out.name)

count = convert_xml(src, out)
print(f"{count} entries -> {out} ({out.stat().st_size / 1e6:.1f} MB) "
      f"in {time.perf_counter() - t:.1f}s")
