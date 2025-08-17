import React, { useState, useCallback } from 'react';
import { FiCopy, FiThumbsUp, FiThumbsDown } from 'react-icons/fi';
import { useSSE } from '../hooks/index.js';

export const MessageActions = ({ content, messageId, traceId, isUser = false }) => {
    const [copied, setCopied] = useState(false);
    const [rating, setRating] = useState(null);
    const [isSubmittingFeedback, setIsSubmittingFeedback] = useState(false);
    const { getUserId, getThreadId } = useSSE();

    const handleCopy = useCallback(async () => {
        try {
            await navigator.clipboard.writeText(content);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch (err) {
            console.error('Failed to copy:', err);
        }
    }, [content]);

    const submitFeedback = useCallback(async (feedbackValue) => {
        if (!traceId || isSubmittingFeedback) return;
        
        setIsSubmittingFeedback(true);
        
        try {
            const authToken = localStorage.getItem('authToken') || 'eyJ1c2VyX2lkIjogIjE0MzdhZGUzNzM1OTQ4OGU5NWMwNzI3YTFjZGYxNzg2ZDI0ZWRjZTMiLCAiZW1haWwiOiAidGVzdEBnbWFpbC5jb20ifQ==';
            const userId = getUserId();
            const threadId = getThreadId();
            
            const response = await fetch(`/api/v1/threads/${threadId}/feedback`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer ' + authToken
                },
                body: JSON.stringify({
                    feedback: feedbackValue,
                    trace_id: traceId,
                    user_id: userId,
                    agent_id: 'demo_agent',
                })
            });
            
            if (response.ok) {
                console.log(`Feedback submitted successfully: ${feedbackValue} for trace ${traceId}`);
            } else {
                console.error('Failed to submit feedback:', response.statusText);
            }
        } catch (error) {
            console.error('Error submitting feedback:', error);
        } finally {
            setIsSubmittingFeedback(false);
        }
    }, [traceId, getUserId, getThreadId, isSubmittingFeedback]);

    const handleRating = useCallback(async (ratingValue) => {
        if (rating === ratingValue) return;
        
        setRating(ratingValue);
        
        const feedbackValue = ratingValue === 'good' ? 1 : 0;
        await submitFeedback(feedbackValue);
    }, [rating, submitFeedback]);

    if (!traceId) {
        return null;
    }

    return (
        <div className="message-actions">
            <button 
                className="action-button copy-button"
                onClick={handleCopy}
                title="Copy"
            >
                <FiCopy />
                {copied && <span className="action-tooltip">Copied!</span>}
            </button>
            
            {isUser ? (
                <button 
                    className="action-button edit-button"
                    title="Edit message"
                >
                    <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                        <path d="M11.3312 3.56837C12.7488 2.28756 14.9376 2.33009 16.3038 3.6963L16.4318 3.83106C17.6712 5.20294 17.6712 7.29708 16.4318 8.66895L16.3038 8.80372L10.0118 15.0947C9.68833 15.4182 9.45378 15.6553 9.22179 15.8457L8.98742 16.0225C8.78227 16.1626 8.56423 16.2832 8.33703 16.3828L8.10753 16.4756C7.92576 16.5422 7.73836 16.5902 7.5216 16.6348L6.75695 16.7705L4.36339 17.169C4.22053 17.1928 4.06908 17.2188 3.94054 17.2285C3.84177 17.236 3.70827 17.2386 3.56261 17.2031L3.41417 17.1543C3.19115 17.0586 3.00741 16.8908 2.89171 16.6797L2.84581 16.5859C2.75951 16.3846 2.76168 16.1912 2.7716 16.0596C2.7813 15.931 2.80736 15.7796 2.83117 15.6367L3.2296 13.2432L3.36437 12.4785C3.40893 12.2616 3.45789 12.0745 3.52453 11.8926L3.6173 11.6621C3.71685 11.4352 3.83766 11.2176 3.97765 11.0127L4.15343 10.7783C4.34386 10.5462 4.58164 10.312 4.90538 9.98829L11.1964 3.6963L11.3312 3.56837Z"/>
                    </svg>
                </button>
            ) : (
                <>
                    <button 
                        className={`action-button rating-button ${rating === 'good' ? 'active' : ''}`}
                        onClick={() => handleRating('good')}
                        title="Good response"
                        disabled={isSubmittingFeedback}
                    >
                        <FiThumbsUp />
                    </button>
                    
                    <button 
                        className={`action-button rating-button ${rating === 'bad' ? 'active' : ''}`}
                        onClick={() => handleRating('bad')}
                        title="Bad response"
                        disabled={isSubmittingFeedback}
                    >
                        <FiThumbsDown />
                    </button>
                </>
            )}
        </div>
    );
}; 