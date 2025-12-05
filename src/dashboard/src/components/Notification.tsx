import React from 'react';

interface NotificationData {
  showPopup: boolean;
  text: string;
  header: string;
  isError: boolean;
}

interface NotificationProps {
  notification: NotificationData;
  onClose: () => void;
}

export const Notification: React.FC<NotificationProps> = ({ notification, onClose }) => {
  if (!notification.showPopup) return null;

  return (
    <div id="notifications-popup" className="popup" onClick={onClose}>
      <div
        className={`popup-content half-page-margins ${
          notification.isError ? 'red-border' : 'green-border'
        }`}
        onClick={(e) => e.stopPropagation()}
      >
        <span className="close-button" onClick={onClose}>
          &times;
        </span>
        <h1>{notification.header}</h1>
        <div style={{ fontSize: 'xx-large' }}>{notification.text}</div>
      </div>
    </div>
  );
};
