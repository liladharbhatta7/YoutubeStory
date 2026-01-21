import json
import os
from src.config_loader import config
from src.logger import logger

class TopicPicker:
    def __init__(self):
        self.state_file = config.state_dir / "state.json"
        
    def load_state(self):
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                return json.load(f)
        return {"last_index": -1, "used_topics": []}

    def save_state(self, state):
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)

    def get_next_topics(self, count=3):
        topics = config.get_topics()
        state = self.load_state()
        last_index = state.get("last_index", -1)
        total_topics = len(topics)
        
        if total_topics == 0:
            logger.error("No topics found in config!")
            return []

        selected_topics = []
        current_index = last_index
        
        for _ in range(count):
            current_index = (current_index + 1) % total_topics
            topic = topics[current_index]
            selected_topics.append(topic)
        
        # Only update state after successful retrieval
        # Note: We ideally should update state only after successful video generation,
        # but to keep it simple and ensure rotation, we update now.
        # If a video fails, we just move on.
        state["last_index"] = current_index
        self.save_state(state)
        
        return selected_topics

topic_picker = TopicPicker()
