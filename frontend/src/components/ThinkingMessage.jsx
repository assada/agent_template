import React from 'react';
import { THINKING_STATES, MESSAGES } from '../constants/constants.js';

export const ThinkingMessage = ({ thinkingProcess, onToggleExpanded }) => {
    const { isActive, state, duration, history, isExpanded } = thinkingProcess;

    if (!isActive && state !== THINKING_STATES.COMPLETED) {
        return null;
    }

    if (state === THINKING_STATES.COMPLETED && history.length === 0 && duration === 0) {
        return null;
    }

    const getStateMessage = () => {
        switch (state) {
            case THINKING_STATES.THINKING:
                return MESSAGES.THINKING;
            case THINKING_STATES.RESPONDING:
                return MESSAGES.RESPONDING;
            case THINKING_STATES.COMPLETED:
                return `Thought for ${duration} seconds`;
            default:
                return MESSAGES.THINKING;
        }
    };

    const formatHistoryItem = (item) => {
        switch (item.type) {
            case 'tool_call':
                return `Tool call: ${item.content.name}(${JSON.stringify(item.content.args)})`;
            case 'tool_result':
                return `Tool result: ${item.content.tool_name} - ${item.content.content}`;
            case 'state_change':
                return `State: ${item.content}`;
            default:
                return item.content;
        }
    };

    const isClickable = state === THINKING_STATES.COMPLETED && history.length > 0;

    return (
        <div className="thinking-message">
            <div 
                className={`thinking-header ${isClickable ? 'clickable' : ''}`}
                onClick={isClickable ? onToggleExpanded : undefined}
            >
                <span className="thinking-text">{getStateMessage()}</span>
                {isClickable && (
                    <span className="thinking-toggle">
                        {isExpanded ? '▼' : '▶'}
                    </span>
                )}
            </div>
            
            {isExpanded && history.length > 0 && (
                <div className="thinking-history">
                    {history.map((item, index) => (
                        <div key={index} className="thinking-history-item">
                            <div className="thinking-timeline-dot"></div>
                            <div className="thinking-timeline-line"></div>
                            <div className="thinking-history-content">
                                {formatHistoryItem(item)}
                            </div>
                        </div>
                    ))}
                    <div className="thinking-history-item">
                        <div className="thinking-done">
                            <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor" xmlns="http://www.w3.org/2000/svg" className="thinking-done-icon">
                                <path d="M12.498 6.90887C12.7094 6.60867 13.1245 6.53642 13.4248 6.74774C13.7249 6.95913 13.7971 7.37424 13.5859 7.6745L9.62695 13.2995C9.51084 13.4644 9.32628 13.5681 9.125 13.5807C8.94863 13.5918 8.77583 13.5319 8.64453 13.4167L8.59082 13.364L6.50781 11.072L6.42773 10.9645C6.26956 10.6986 6.31486 10.3488 6.55273 10.1325C6.79045 9.91663 7.14198 9.9053 7.3916 10.0876L7.49219 10.1774L9.0166 11.8542L12.498 6.90887Z"></path>
                                <path fillRule="evenodd" clipRule="evenodd" d="M10.3333 2.08496C14.7046 2.08496 18.2483 5.62867 18.2483 10C18.2483 14.3713 14.7046 17.915 10.3333 17.915C5.96192 17.915 2.41821 14.3713 2.41821 10C2.41821 5.62867 5.96192 2.08496 10.3333 2.08496ZM10.3333 3.41504C6.69646 3.41504 3.74829 6.3632 3.74829 10C3.74829 13.6368 6.69646 16.585 10.3333 16.585C13.97 16.585 16.9182 13.6368 16.9182 10C16.9182 6.3632 13.97 3.41504 10.3333 3.41504Z"></path>
                            </svg>
                            <span>Done</span>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}; 