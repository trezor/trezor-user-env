import React from 'react';

interface LogEvent {
  text: string;
  color: string;
}

interface EventLogSectionProps {
  logs: LogEvent[];
}

export const EventLogSection: React.FC<EventLogSectionProps> = ({ logs }) => {
  return (
    <section>
      <h3>Event Log</h3>
      {logs.map((log, index) => (
        <p key={`${log.text}-${index}`} style={{ color: log.color }}>
          {log.text} <br />
        </p>
      ))}
    </section>
  );
};
