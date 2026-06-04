from dataclasses import dataclass, field
from typing import List
from datetime import datetime


@dataclass
class ProjectConfig:
    client: str
    project: str
    project_type: str
    delivery_date: str       # YYYY-MM-DD
    num_clips: int
    platforms: List[str]
    formats: List[str]
    version: str             # e.g. "01"
    language: str
    initial_status: str
    output_path: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))

    def folder_name(self) -> str:
        from scalecut.naming import sanitize
        client = sanitize(self.client)
        project = sanitize(self.project)
        date = self.delivery_date.replace("-", "")
        return f"{client}_{project}_{date}"

    def to_dict(self) -> dict:
        return {
            "client": self.client,
            "project": self.project,
            "project_type": self.project_type,
            "delivery_date": self.delivery_date,
            "num_clips": self.num_clips,
            "platforms": self.platforms,
            "formats": self.formats,
            "version": self.version,
            "language": self.language,
            "initial_status": self.initial_status,
            "output_path": self.output_path,
            "created_at": self.created_at,
        }
