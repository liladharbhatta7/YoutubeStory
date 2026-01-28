import argparse
import sys
from src.topic_picker import topic_picker
from src.pipeline import pipeline
from src.utils_time import get_npt_time_today, get_three_daily_schedules
from src.report import report_manager
from src.logger import logger
import shutil
from src.config_loader import config


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=3, help="Number of videos to generate")
    args = parser.parse_args()

    logger.info("Starting Daily Run")

    # 1. Pick Topics
    topics = topic_picker.get_next_topics(count=args.count)
    if not topics:
        logger.error("No topics available.")
        sys.exit(1)

    # 2. Define Schedule Times (NPT)
    # Video1: 07:30, Video2: 12:30, Video3: 19:30
    schedule_times = get_three_daily_schedules()[:args.count]

    # 3. Pipeline Loop
    for i, topic in enumerate(topics):
        if i < len(schedule_times):
            sched_time = schedule_times[i]
        else:
            # Fallback for >3 videos: spaced out by 1 hour
            sched_time = schedule_times[-1]  # Simplification

        try:
            pipeline.process_story(topic, sched_time)
        except Exception as e:
            logger.error(f"Critical error processing topic {topic.get('id')}: {e}")
            # Continue to next

    # 4. Finalize Report
    report_manager.save()

    # 5. Global Cleanup (optional extra sweep)
    # Remove files in temp
    shutil.rmtree(config.root_dir / "temp", ignore_errors=True)
    (config.root_dir / "temp").mkdir()


if __name__ == "__main__":
    main()
