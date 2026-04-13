import React, { useState } from 'react';
import { EmulatorsState } from '../types';

interface SidebarProps {
  emulators: EmulatorsState;
}

export const Sidebar: React.FC<SidebarProps> = ({ emulators }) => {
  const [isExpanded, setIsExpanded] = useState(true);

  const isRunning = emulators.statusColor === 'green';
  const deviceName = isRunning ? emulators.status : 'No device';
  const connectionLabel = isRunning ? 'Connected' : 'Disconnected';

  return (
    <aside className={`sidebar${isExpanded ? ' sidebar--expanded' : ' sidebar--collapsed'}`}>
      <div className="sidebar-device-header">
        <div className="sidebar-device-icon" aria-hidden="true">
          <svg
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <rect width="24" height="24" rx="4" fill="#01684a" />
            <rect x="8" y="5" width="8" height="14" rx="2" fill="white" />
          </svg>
        </div>

        {isExpanded && (
          <div className="sidebar-device-info">
            <span className="sidebar-device-name" title={deviceName}>
              {deviceName}
            </span>
            <span
              className={`sidebar-device-status${isRunning ? ' sidebar-device-status--connected' : ''}`}
            >
              {isRunning && (
                <svg
                  className="sidebar-device-status-icon"
                  width="10"
                  height="10"
                  viewBox="0 0 10 10"
                  aria-hidden="true"
                >
                  <circle cx="5" cy="5" r="5" fill="currentColor" />
                </svg>
              )}
              {connectionLabel}
            </span>
          </div>
        )}

        <button
          className="sidebar-toggle"
          onClick={() => setIsExpanded(!isExpanded)}
          title={isExpanded ? 'Collapse sidebar' : 'Expand sidebar'}
          aria-label={isExpanded ? 'Collapse sidebar' : 'Expand sidebar'}
        >
          <svg
            className={`sidebar-chevron${isExpanded ? ' sidebar-chevron--expanded' : ''}`}
            width="16"
            height="16"
            viewBox="0 0 16 16"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            aria-hidden="true"
          >
            <path
              d="M6 4l4 4-4 4"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </button>
      </div>

      {isExpanded && (
        <nav className="sidebar-nav" aria-label="Main navigation">
          <a href="#top" className="sidebar-nav-item">
            <svg
              width="16"
              height="16"
              viewBox="0 0 16 16"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              aria-hidden="true"
            >
              <path
                d="M2 6.5L8 2l6 4.5V14H10v-4H6v4H2V6.5z"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            Dashboard
          </a>
        </nav>
      )}
    </aside>
  );
};
