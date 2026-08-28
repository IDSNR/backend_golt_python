from app.modules.auth.service import ProfileService
from app.modules.content.service import ContentService
from app.modules.notifications.service import NotificationService
from app.modules.social.service import SocialService
from app.modules.stories.service import StoryService
from app.modules.wallet.service import WalletService
from app.modules.commerce.service import CommerceService
from app.modules.subscriptions.service import SubscriptionService
from app.modules.access import ContentAccessService
from app.modules.dms import direct_message_service
from app.modules.media import media_service, media_storage

profile_service = ProfileService()
content_service = ContentService()
notification_service = NotificationService()
social_service = SocialService()
story_service = StoryService()
wallet_service = WalletService()
commerce_service = CommerceService()
subscription_service = SubscriptionService()
content_access_service = ContentAccessService(profile_service, social_service, subscription_service)
direct_message_service = direct_message_service
media_service = media_service
media_storage = media_storage
