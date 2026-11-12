"""
Socket.IO Server & Real-Time Event Dispatcher for Nestora.
Provides real-time updates for bed map inventory, allocations, notifications, and audit activities.
"""

import logging
from datetime import datetime, timezone
import socketio

logger = logging.getLogger(__name__)

# Initialize Socket.IO Server with threading async mode for standard WSGI & Django workers
sio = socketio.Server(
    cors_allowed_origins='*',
    async_mode='threading',
    ping_timeout=25,
    ping_interval=10,
    logger=False,
    engineio_logger=False
)


@sio.event
def connect(sid, environ, auth=None):
    """Handle new Socket.IO client connection."""
    logger.info(f"⚡ Socket.IO client connected: {sid}")
    # Acknowledge connection
    sio.emit('connected', {
        'status': 'online',
        'sid': sid,
        'server_time': datetime.now(timezone.utc).isoformat(),
        'message': 'Connected to Nestora Real-Time Live Sync'
    }, to=sid)


@sio.event
def disconnect(sid):
    """Handle client disconnection."""
    logger.info(f"⚡ Socket.IO client disconnected: {sid}")


@sio.event
def subscribe(sid, data):
    """
    Allow client to subscribe to specific room channels.
    Channels: 'bedmap', 'allocations', 'notifications', 'role_admin', 'role_student'
    """
    if isinstance(data, dict):
        channel = data.get('channel')
        role = data.get('role')
        if channel:
            sio.enter_room(sid, f"channel_{channel}")
            logger.info(f"Client {sid} subscribed to channel_{channel}")
        if role in ('admin', 'student'):
            sio.enter_room(sid, f"role_{role}")
            logger.info(f"Client {sid} joined role room: role_{role}")


@sio.event
def ping_live(sid, data=None):
    """Simple healthcheck/ping from client."""
    sio.emit('pong_live', {
        'timestamp': datetime.now(timezone.utc).isoformat()
    }, to=sid)


# ---------------------------------------------------------------------------
# Public Broadcasting Helpers (callable from Django views, signals, or tasks)
# ---------------------------------------------------------------------------

def broadcast_bed_update(bed_label, status, student_name=None, student_id=None, room_number=None):
    """
    Broadcast a real-time bed inventory change to all active clients and the bedmap channel.
    """
    try:
        payload = {
            'event': 'bed_updated',
            'bed_label': bed_label,
            'status': status,
            'student_name': student_name or 'Unassigned',
            'student_id': student_id,
            'room_number': room_number,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }
        # Emit to all connected clients
        sio.emit('bed_updated', payload)
        logger.info(f"📢 Broadcast bed_updated: {bed_label} -> {status}")
    except Exception as exc:
        logger.error(f"Failed to broadcast bed_updated: {exc}")


def broadcast_allocation_override(student_name, new_bed, old_bed=None, reason=None, actor="Head Warden"):
    """
    Broadcast a warden draft override in real time.
    """
    try:
        payload = {
            'event': 'allocation_override',
            'student_name': student_name,
            'new_bed': new_bed,
            'old_bed': old_bed,
            'reason': reason or 'Warden administrative adjustment',
            'actor': actor,
            'timestamp': datetime.now(timezone.utc).strftime("%H:%M:%S"),
        }
        sio.emit('allocation_override', payload)
        # Also emit activity feed update
        sio.emit('new_activity', {
            'actor': actor,
            'action': f"Reassigned {student_name} to {new_bed}",
            'time': "Just now"
        })
        logger.info(f"📢 Broadcast allocation_override for {student_name}")
    except Exception as exc:
        logger.error(f"Failed to broadcast allocation_override: {exc}")


def broadcast_notification(title, message, level='info', target_role='all'):
    """
    Broadcast an in-app notification toast to users.
    target_role can be 'all', 'admin', or 'student'.
    """
    try:
        payload = {
            'title': title,
            'message': message,
            'level': level,  # 'info', 'success', 'warning', 'danger'
            'timestamp': datetime.now(timezone.utc).strftime("%H:%M"),
        }
        if target_role in ('admin', 'student'):
            sio.emit('notification', payload, room=f"role_{target_role}")
        else:
            sio.emit('notification', payload)
        logger.info(f"📢 Broadcast notification: '{title}' to {target_role}")
    except Exception as exc:
        logger.error(f"Failed to broadcast notification: {exc}")
