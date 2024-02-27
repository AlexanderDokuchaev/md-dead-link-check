from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Any, Dict, List, Optional

import toml

PROJECT_NAME = "md_dead_link_check"


@dataclass
class Config:
    timeout: int = 10
    exclude_links: List[str] = field(default_factory=lambda: [])
    exclude_files: List[str] = field(default_factory=lambda: [])
    check_web_links: bool = True


def get_config(root_dir: Path, config_path: Optional[Path]) -> Config:

    if not config_path:
        config_path = root_dir / "pyproject.toml"
    config = Config()

    if config_path.is_file():
        pyproject_toml = toml.load(config_path)
        toml_config: Dict[str, Any] = pyproject_toml.get("tool", {}).get(PROJECT_NAME, {})

        for key, value in toml_config.items():
            if hasattr(config, key):
                setattr(config, key, value)
            else:
                raise ConnectionError(
                    f"Unexpected config key `{key}` in {config_path.name}. "
                    f"Available keys: [{', '.join(config.__annotations__)}]"
                )
    return config
