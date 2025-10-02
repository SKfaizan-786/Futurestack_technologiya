"""
Tests for notification service.

Tests subscription management, trial notifications,
and service functionality with various scenarios.
"""
import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

from src.services.notification_service import NotificationService


class TestNotificationService:
    """Test the NotificationService class."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        self.service = NotificationService()
    
    @pytest.mark.asyncio
    async def test_init(self):
        """Test service initialization."""
        service = NotificationService()
        
        assert service.subscriptions == {}
        assert hasattr(service, 'subscriptions')
    
    @pytest.mark.asyncio
    async def test_create_subscription_success(self):
        """Test successful subscription creation."""
        email = "test@example.com"
        criteria = {
            "condition": "diabetes",
            "location": "California",
            "age_min": 18,
            "age_max": 65
        }
        preferences = {
            "frequency": "weekly",
            "notification_types": ["email", "sms"]
        }
        
        with patch('src.services.notification_service.datetime') as mock_datetime:
            mock_now = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
            mock_datetime.now.return_value = mock_now
            mock_datetime.timezone = timezone
            
            subscription_id = await self.service.create_subscription(
                email=email,
                criteria=criteria,
                preferences=preferences
            )
        
        # Check that subscription was created
        assert subscription_id.startswith("sub_")
        assert subscription_id in self.service.subscriptions
        
        subscription = self.service.subscriptions[subscription_id]
        assert subscription["email"] == email
        assert subscription["criteria"] == criteria
        assert subscription["preferences"] == preferences
        assert subscription["status"] == "active"
        assert subscription["created_at"] == mock_now
    
    @pytest.mark.asyncio
    async def test_create_subscription_generates_unique_ids(self):
        """Test that multiple subscriptions get unique IDs."""
        email = "test@example.com"
        criteria = {"condition": "diabetes"}
        preferences = {"frequency": "weekly"}
        
        # Mock datetime to return different timestamps for each call
        # Need 4 timestamps: 2 subscriptions × 2 datetime.now() calls each (ID + created_at)
        timestamps = [1000, 1000, 1001, 1001]
        with patch('src.services.notification_service.datetime') as mock_datetime:
            def mock_now(*args, **kwargs):
                timestamp = timestamps.pop(0) if timestamps else 9999
                mock_dt = MagicMock()
                mock_dt.timestamp.return_value = timestamp
                return mock_dt
            
            mock_datetime.now.side_effect = mock_now
            mock_datetime.timezone = timezone
            
            subscription_id1 = await self.service.create_subscription(email, criteria, preferences)
            subscription_id2 = await self.service.create_subscription(email, criteria, preferences)
        
        assert subscription_id1 != subscription_id2
        assert subscription_id1 == "sub_1000"
        assert subscription_id2 == "sub_1001"
        assert len(self.service.subscriptions) == 2
    
    @pytest.mark.asyncio
    async def test_get_subscription_existing(self):
        """Test getting an existing subscription."""
        email = "test@example.com"
        criteria = {"condition": "diabetes"}
        preferences = {"frequency": "weekly"}
        
        # Create subscription
        subscription_id = await self.service.create_subscription(email, criteria, preferences)
        
        # Get subscription
        result = await self.service.get_subscription(subscription_id)
        
        assert result is not None
        assert result["email"] == email
        assert result["criteria"] == criteria
        assert result["preferences"] == preferences
        assert result["status"] == "active"
    
    @pytest.mark.asyncio
    async def test_get_subscription_nonexistent(self):
        """Test getting a non-existent subscription."""
        result = await self.service.get_subscription("nonexistent_id")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_cancel_subscription_existing(self):
        """Test cancelling an existing subscription."""
        email = "test@example.com"
        criteria = {"condition": "diabetes"}
        preferences = {"frequency": "weekly"}
        
        # Create subscription
        subscription_id = await self.service.create_subscription(email, criteria, preferences)
        
        # Cancel subscription
        result = await self.service.cancel_subscription(subscription_id)
        
        assert result is True
        
        # Check that subscription is marked as cancelled
        subscription = self.service.subscriptions[subscription_id]
        assert subscription["status"] == "cancelled"
    
    @pytest.mark.asyncio
    async def test_cancel_subscription_nonexistent(self):
        """Test cancelling a non-existent subscription."""
        result = await self.service.cancel_subscription("nonexistent_id")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_check_new_trials(self):
        """Test checking for new trials (placeholder implementation)."""
        email = "test@example.com"
        criteria = {"condition": "diabetes"}
        preferences = {"frequency": "weekly"}
        
        # Create subscription
        subscription_id = await self.service.create_subscription(email, criteria, preferences)
        
        # Check for new trials
        trials = await self.service.check_new_trials(subscription_id)
        
        # Placeholder implementation should return empty list
        assert isinstance(trials, list)
        assert len(trials) == 0
    
    @pytest.mark.asyncio
    async def test_send_notification_success(self):
        """Test successful notification sending."""
        email = "test@example.com"
        criteria = {"condition": "diabetes"}
        preferences = {"frequency": "weekly"}
        
        # Create subscription
        subscription_id = await self.service.create_subscription(email, criteria, preferences)
        
        # Mock trials data
        trials = [
            {
                "id": "trial_1",
                "title": "Diabetes Study A",
                "description": "Testing new diabetes treatment"
            },
            {
                "id": "trial_2", 
                "title": "Diabetes Study B",
                "description": "Testing diabetes monitoring device"
            }
        ]
        
        # Send notification
        with patch('src.services.notification_service.logger') as mock_logger:
            result = await self.service.send_notification(subscription_id, trials)
        
        assert result is True
        
        # Check that logging occurred
        mock_logger.info.assert_called_once_with(
            f"Sending notification to subscription {subscription_id}"
        )
    
    @pytest.mark.asyncio
    async def test_send_notification_empty_trials(self):
        """Test sending notification with empty trials list."""
        email = "test@example.com"
        criteria = {"condition": "diabetes"}
        preferences = {"frequency": "weekly"}
        
        # Create subscription
        subscription_id = await self.service.create_subscription(email, criteria, preferences)
        
        # Send notification with empty trials
        result = await self.service.send_notification(subscription_id, [])
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_subscription_workflow(self):
        """Test complete subscription workflow."""
        email = "patient@example.com"
        criteria = {
            "condition": "heart disease",
            "location": "New York",
            "age_min": 30,
            "age_max": 70
        }
        preferences = {
            "frequency": "daily",
            "notification_types": ["email"],
            "time_preference": "morning"
        }
        
        # 1. Create subscription
        subscription_id = await self.service.create_subscription(
            email=email,
            criteria=criteria,
            preferences=preferences
        )
        
        assert subscription_id is not None
        
        # 2. Verify subscription exists and is active
        subscription = await self.service.get_subscription(subscription_id)
        assert subscription is not None
        assert subscription["status"] == "active"
        assert subscription["email"] == email
        
        # 3. Check for new trials
        trials = await self.service.check_new_trials(subscription_id)
        assert isinstance(trials, list)
        
        # 4. Send notification
        result = await self.service.send_notification(subscription_id, trials)
        assert result is True
        
        # 5. Cancel subscription
        cancel_result = await self.service.cancel_subscription(subscription_id)
        assert cancel_result is True
        
        # 6. Verify subscription is cancelled
        subscription = await self.service.get_subscription(subscription_id)
        assert subscription["status"] == "cancelled"
    
    @pytest.mark.asyncio
    async def test_multiple_subscriptions_independence(self):
        """Test that multiple subscriptions work independently."""
        # Mock datetime to return different timestamps for each call
        # Need 4 timestamps: 2 subscriptions × 2 datetime.now() calls each (ID + created_at)
        timestamps = [2000, 2000, 2001, 2001]
        with patch('src.services.notification_service.datetime') as mock_datetime:
            def mock_now(*args, **kwargs):
                timestamp = timestamps.pop(0) if timestamps else 9999
                mock_dt = MagicMock()
                mock_dt.timestamp.return_value = timestamp
                return mock_dt
            
            mock_datetime.now.side_effect = mock_now
            mock_datetime.timezone = timezone
            
            # Create first subscription
            subscription_id1 = await self.service.create_subscription(
                email="user1@example.com",
                criteria={"condition": "diabetes"},
                preferences={"frequency": "weekly"}
            )
            
            # Create second subscription  
            subscription_id2 = await self.service.create_subscription(
                email="user2@example.com",
                criteria={"condition": "cancer"},
                preferences={"frequency": "daily"}
            )
        
        # Verify both exist
        assert len(self.service.subscriptions) == 2
        assert subscription_id1 != subscription_id2
        assert subscription_id1 == "sub_2000"
        assert subscription_id2 == "sub_2001"
        
        sub1 = await self.service.get_subscription(subscription_id1)
        sub2 = await self.service.get_subscription(subscription_id2)
        
        assert sub1["email"] == "user1@example.com"
        assert sub2["email"] == "user2@example.com"
        assert sub1["criteria"]["condition"] == "diabetes"
        assert sub2["criteria"]["condition"] == "cancer"
        
        # Cancel first subscription
        await self.service.cancel_subscription(subscription_id1)
        
        # Verify first is cancelled, second is still active
        sub1 = await self.service.get_subscription(subscription_id1)
        sub2 = await self.service.get_subscription(subscription_id2)
        
        assert sub1["status"] == "cancelled"
        assert sub2["status"] == "active"
    
    @pytest.mark.asyncio
    async def test_create_subscription_logging(self):
        """Test that subscription creation is logged."""
        email = "test@example.com"
        criteria = {"condition": "diabetes"}
        preferences = {"frequency": "weekly"}
        
        with patch('src.services.notification_service.logger') as mock_logger:
            subscription_id = await self.service.create_subscription(
                email=email,
                criteria=criteria,
                preferences=preferences
            )
        
        # Check that logging occurred
        mock_logger.info.assert_called_once()
        log_call = mock_logger.info.call_args[0][0]
        assert f"Created subscription {subscription_id} for {email}" in log_call