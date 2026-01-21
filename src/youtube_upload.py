import os
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from src.config_loader import config
from src.logger import logger
import json

class YouTubeUploader:
    def __init__(self):
        self.scopes = ["https://www.googleapis.com/auth/youtube.upload"]
        self.client_id = config.youtube_client_id
        self.client_secret = config.youtube_client_secret
        self.refresh_token = config.youtube_refresh_token
        
    def get_authenticated_service(self):
        if not self.refresh_token:
            logger.error("No refresh token found.")
            return None

        # Create credentials object from Refresh Token
        creds_data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
            "token_uri": "https://oauth2.googleapis.com/token",
        }
        
        creds = Credentials.from_authorized_user_info(creds_data, self.scopes)

        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                logger.error(f"Failed to refresh token: {e}")
                return None

        return googleapiclient.discovery.build("youtube", "v3", credentials=creds)

    def upload_video(self, video_path, title, description, tags, publish_at_iso):
        youtube = self.get_authenticated_service()
        if not youtube:
            return None

        body = {
            "snippet": {
                "title": title[:100], # Max 100 chars
                "description": description[:5000],
                "tags": tags,
                "categoryId": "22" # People & Blogs
            },
            "status": {
                "privacyStatus": "private", # Must start private if scheduling
                "publishAt": publish_at_iso,
                "selfDeclaredMadeForKids": False
            }
        }

        logger.info(f"Uploading {title} scheduled for {publish_at_iso}")
        
        try:
            # Resumable upload
            request = youtube.videos().insert(
                part=",".join(body.keys()),
                body=body,
                media_body=googleapiclient.http.MediaFileUpload(video_path, chunksize=-1, resumable=True)
            )
            
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    logger.info(f"Uploaded {int(status.progress() * 100)}%")

            video_id = response.get("id")
            logger.info(f"Upload Complete! Video ID: {video_id}")
            return video_id

        except googleapiclient.errors.HttpError as e:
            logger.error(f"An HTTP error occurred: {e.resp.status} {e.content}")
            return None
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            return None

youtube_uploader = YouTubeUploader()
