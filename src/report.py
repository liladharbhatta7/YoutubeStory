import json
import os
from datetime import datetime
from src.config_loader import config
from src.logger import logger

class DailyReport:
    def __init__(self):
        self.entries = []
        self.start_time = datetime.now()
        self.report_file = config.root_dir / "report.json"

    def add_entry(self, story_id, topic_id, title, publish_at, video_id, status, error=None):
        entry = {
            "story_id": story_id,
            "topic_id": topic_id,
            "title": title,
            "publish_at": publish_at,
            "youtube_video_id": video_id,
            "status": status,
            "error": str(error) if error else None,
            "timestamp": datetime.now().isoformat()
        }
        self.entries.append(entry)
        logger.info(f"Report Entry Added: {json.dumps(entry, indent=2)}")

    def save(self):
        report_data = {
            "run_date": self.start_time.strftime("%Y-%m-%d"),
            "run_start_time": self.start_time.isoformat(),
            "run_end_time": datetime.now().isoformat(),
            "videos": self.entries
        }
        
        with open(self.report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Report saved to {self.report_file}")

report_manager = DailyReport()
