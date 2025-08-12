import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm'
import { MessageActions } from './MessageActions.jsx';
import UIMessage from './UIMessage.jsx';
import { ThinkingMessage } from './ThinkingMessage.jsx';
import { CSS_CLASSES, SENDER_TYPES, MESSAGE_SUBTYPES, THINKING_STATES } from '../constants/constants.js';

export const Message = ({ message, showActions = true, onToggleThinkingExpanded }) => {
    const { id, content, sender, messageType, className = '', traceId, thinkingData } = message;
    
    const isUser = sender === SENDER_TYPES.USER;
    const isAssistant = sender === SENDER_TYPES.ASSISTANT;
    const isCurrentAssistant = id === 'current-assistant';
    const isRegularMessage = messageType === MESSAGE_SUBTYPES.MESSAGE;
    const isUIMessage = messageType === MESSAGE_SUBTYPES.UI;

    if (thinkingData) {
        const thinkingProcess = {
            isActive: false,
            state: THINKING_STATES.COMPLETED,
            startTime: null,
            endTime: null,
            duration: thinkingData.duration,
            history: thinkingData.history,
            isExpanded: thinkingData.isExpanded
        };
        
        return (
            <ThinkingMessage 
                thinkingProcess={thinkingProcess}
                onToggleExpanded={() => onToggleThinkingExpanded && onToggleThinkingExpanded(id)}
            />
        );
    }
    
    return (
        <article 
            className="message-article"
            data-message-id={id}
            data-message-author-role={isUser ? 'user' : 'assistant'}
            data-testid={`conversation-message-${id}`}
        >
            <div className="message-container">
                <div className="message-content-wrapper">
                    <div className="message-content-container">
                        <div className={`message-content ${isUser ? 'user-content' : 'assistant-content'} ${className}`}>
                            <div className="message-inner">
                                {isUIMessage ? (
                                    <UIMessage message={content} />
                                ) : isAssistant && isRegularMessage ? (
                                    <ReactMarkdown remarkPlugins={[[remarkGfm, {singleTilde: false}]]}>{content}</ReactMarkdown>
                                ) : (
                                    <div className="message-text">
                                        {content}
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                    
                    {(isAssistant || isUser) && !isCurrentAssistant && showActions && (
                        <div className="message-actions-wrapper">
                            <div className="message-actions-container">
                                <MessageActions 
                                    content={content} 
                                    messageId={id} 
                                    traceId={traceId}
                                    isUser={isUser}
                                />
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </article>
    );
}; 