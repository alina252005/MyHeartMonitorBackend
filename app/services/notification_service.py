from firebase_admin import messaging

def send_notification(token: str, status: str):
    if status == "approved":
        title = "Appointment Approved"
        body = "Your appointment has been approved"
    else:
        title = "Appointment Rejected"
        body = "Your appointment has been rejected"

    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        data={
            "title": title,
            "body": body,
            "status": status
        },
        android=messaging.AndroidConfig(
            priority="high",
            notification=messaging.AndroidNotification(
                channel_id="high_importance_channel",
                sound="default"
            ),
        ),
        token=token,
    )

    messaging.send(message)