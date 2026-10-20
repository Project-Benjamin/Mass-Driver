"""Validate the user's existing portrait pack without altering its artwork."""
import hashlib
import json
from pathlib import Path
from PIL import Image


def audit_pack(directory: Path) -> dict:
    directory = directory.resolve()
    metadata_path = directory / "metadata.json"
    raw = metadata_path.read_bytes()
    metadata = json.loads(raw)
    assets = metadata.get("assets")
    if not isinstance(assets, list) or not assets:
        raise ValueError("Portrait metadata must include a nonempty assets list")
    seen, records = set(), []
    for item in assets:
        if item["id"] in seen:
            raise ValueError(f"Duplicate asset ID: {item['id']}")
        seen.add(item["id"])
        if len(item.get("files", [])) != 1:
            raise ValueError(f"Expected one portrait image for {item['id']}")
        file = item["files"][0]
        path = (directory / file["filename"]).resolve()
        if not path.is_relative_to(directory) or not path.is_file():
            raise ValueError("Portrait filename escapes pack or is missing")
        data = path.read_bytes()
        if len(data) != file["byteLength"]:
            raise ValueError(f"Portrait byte count differs from metadata: {path.name}")
        with Image.open(path) as image:
            image.load()
            if image.size != (file["width"], file["height"]):
                raise ValueError(f"Portrait dimensions differ from metadata: {path.name}")
            blank = image.convert("RGBA").getchannel("A").getbbox() is None
            records.append({"id": item["id"], "name": item["name"], "filename": path.name,
                            "size": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                            "width": image.width, "height": image.height,
                            "transparent_placeholder": blank})
    return {"format": "xenogears-definitive-portrait-audit-v1", "pack": str(directory),
            "metadata_sha256": hashlib.sha256(raw).hexdigest(), "asset_count": len(records),
            "assets": records, "installation_status": "texture_mapping_required",
            "note": "Artwork IDs are not native portrait selectors or DuckStation texture hashes."}
