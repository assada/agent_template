import React, {useCallback, useEffect, useLayoutEffect, useRef, useState} from 'react';
import {useChatStore} from '../store/index.js';
import {useSSE} from '../hooks/index.js';
import {Message} from './Message.jsx';
import {ThinkingMessage} from './ThinkingMessage.jsx';
import {ConnectionStatus} from './ConnectionStatus.jsx';
import {ThreadList} from './ThreadList.jsx';
import {MESSAGE_SUBTYPES, SENDER_TYPES, THINKING_STATES} from '../constants/constants.js';

export const ChatApp = () => {
    const {
        messages,
        input,
        isLoading,
        isSending,
        connectionStatus,
        currentAssistantMessage,
        currentAssistantTraceId,
        thinkingProcess,
        setInput,
        addMessage,
        clearInput,
        toggleThinkingExpanded,
        toggleThinkingMessageExpanded
    } = useChatStore();

    const {sendMessage, closeConnection, loadChatHistory, fetchThreads, setCurrentThreadId, newChat} = useSSE();
    const messagesEndRef = useRef(null);
    const inputRef = useRef(null);

    const [theme, setTheme] = useState(() => {
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme) {
            return savedTheme;
        }
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    });

    useEffect(() => {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
    }, [theme]);

    useEffect(() => {
        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
        const handleChange = (e) => {
            if (!localStorage.getItem('theme')) {
                setTheme(e.matches ? 'dark' : 'light');
            }
        };

        mediaQuery.addEventListener('change', handleChange);
        return () => mediaQuery.removeEventListener('change', handleChange);
    }, []);

    const toggleTheme = useCallback(() => {
        setTheme(prev => prev === 'light' ? 'dark' : 'light');
    }, []);

    useLayoutEffect(() => {
        messagesEndRef.current?.scrollIntoView({behavior: 'smooth'});
    }, [messages.length, currentAssistantMessage]);

    useEffect(() => {
        if (inputRef.current) {
            inputRef.current.focus();
        }

        fetchThreads();

        return () => {
            closeConnection();
        };
    }, [closeConnection]);

    useEffect(() => {
        if (inputRef.current && !input) {
            inputRef.current.style.height = 'auto';
        }
    }, [input]);

    const handleSendMessage = useCallback(async () => {
        if (!input.trim() || isSending) return;

        addMessage(input, SENDER_TYPES.USER, MESSAGE_SUBTYPES.MESSAGE);
        const messageToSend = input;
        clearInput();

        await sendMessage(messageToSend);
    }, [input, isSending, addMessage, clearInput, sendMessage]);

    const handleKeyDown = useCallback((e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    }, [handleSendMessage]);

    const handleInputChange = useCallback((e) => {
        setInput(e.target.value);

        const textarea = e.target;
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
    }, [setInput]);

    return (
        <div className="app-container">
            <header className="app-header">
                <button
                    className="theme-toggle"
                    onClick={toggleTheme}
                    aria-label="Toggle theme"
                >
                    {theme === 'light' ? '🌙' : '☀️'}
                </button>
            </header>

            <div className="app-content">
                <aside className="sidebar">
                    <button className="new-chat-btn" onClick={newChat}>New chat</button>
                    <ThreadList onSelect={(id) => { setCurrentThreadId(id); loadChatHistory(); }} />
                </aside>
                <div className="chat-container">
                    <div className="chat-messages">
                    {messages.length === 0 && !currentAssistantMessage && (
                        <div className="empty-chat-header">
                            <div className="empty-chat-content">
                                <h1 className="empty-chat-title">What's on the agenda today?</h1>
                            </div>
                        </div>
                    )}
                    
                    {messages.map((message) => (
                        <Message
                            key={message.id}
                            message={message}
                            onToggleThinkingExpanded={toggleThinkingMessageExpanded}
                        />
                    ))}

                    {(thinkingProcess.isActive || thinkingProcess.state !== THINKING_STATES.COMPLETED) && (
                        <ThinkingMessage
                            thinkingProcess={thinkingProcess}
                            onToggleExpanded={toggleThinkingExpanded}
                        />
                    )}

                    {currentAssistantMessage && (
                        <Message
                            message={{
                                id: 'current-assistant',
                                content: currentAssistantMessage,
                                sender: SENDER_TYPES.ASSISTANT,
                                messageType: MESSAGE_SUBTYPES.MESSAGE,
                                className: isSending ? 'typing-cursor' : '',
                                traceId: currentAssistantTraceId
                            }}
                        />
                    )}

                        <div ref={messagesEndRef}/>
                    </div>
                </div>
            </div>

            <div className="input-container">
                    <div className="composer-form">
                        <div className="composer-container">
                            <div className="composer-input-area">
                                <div className="composer-input-wrapper">
                                    <div className="composer-input-content">
                                    <textarea
                                        ref={inputRef}
                                        value={input}
                                        onChange={handleInputChange}
                                        onKeyDown={handleKeyDown}
                                        placeholder="Ask anything"
                                        className="chat-input"
                                        autoFocus
                                        rows={1}
                                    />
                                    </div>
                                </div>
                            </div>
                            <div className="composer-actions">
                                <div className="composer-actions-left">
                                    <button
                                        type="button"
                                        className="composer-btn"
                                        aria-label="Add files"
                                        title="Add files"
                                    >
                                        <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                                            <path
                                                d="M9.33496 16.5V10.665H3.5C3.13273 10.665 2.83496 10.3673 2.83496 10C2.83496 9.63273 3.13273 9.33496 3.5 9.33496H9.33496V3.5C9.33496 3.13273 9.63273 2.83496 10 2.83496C10.3673 2.83496 10.665 3.13273 10.665 3.5V9.33496H16.5L16.6338 9.34863C16.9369 9.41057 17.165 9.67857 17.165 10C17.165 10.3214 16.9369 10.5894 16.6338 10.6514L16.5 10.665H10.665V16.5C10.665 16.8673 10.3673 17.165 10 17.165C9.63273 17.165 9.33496 16.8673 9.33496 16.5Z"/>
                                        </svg>
                                    </button>
                                    <button
                                        type="button"
                                        className="composer-btn"
                                        aria-label="Tools"
                                        title="Tools"
                                    >
                                        <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                                            <path
                                                d="M7.91626 11.0013C9.43597 11.0013 10.7053 12.0729 11.011 13.5013H16.6663L16.801 13.515C17.1038 13.5771 17.3311 13.8453 17.3313 14.1663C17.3313 14.4875 17.1038 14.7555 16.801 14.8177L16.6663 14.8314H11.011C10.7056 16.2601 9.43619 17.3314 7.91626 17.3314C6.39643 17.3312 5.1269 16.2601 4.82153 14.8314H3.33325C2.96598 14.8314 2.66821 14.5336 2.66821 14.1663C2.66839 13.7992 2.96609 13.5013 3.33325 13.5013H4.82153C5.12713 12.0729 6.39665 11.0015 7.91626 11.0013ZM7.91626 12.3314C6.90308 12.3316 6.08148 13.1532 6.0813 14.1663C6.0813 15.1797 6.90297 16.0011 7.91626 16.0013C8.9297 16.0013 9.75122 15.1798 9.75122 14.1663C9.75104 13.153 8.92959 12.3314 7.91626 12.3314ZM12.0833 2.66829C13.6031 2.66829 14.8725 3.73966 15.178 5.16829H16.6663L16.801 5.18196C17.1038 5.24414 17.3313 5.51212 17.3313 5.83333C17.3313 6.15454 17.1038 6.42253 16.801 6.4847L16.6663 6.49837H15.178C14.8725 7.92701 13.6031 8.99837 12.0833 8.99837C10.5634 8.99837 9.29405 7.92701 8.98853 6.49837H3.33325C2.96598 6.49837 2.66821 6.2006 2.66821 5.83333C2.66821 5.46606 2.96598 5.16829 3.33325 5.16829H8.98853C9.29405 3.73966 10.5634 2.66829 12.0833 2.66829ZM12.0833 3.99837C11.0698 3.99837 10.2483 4.81989 10.2483 5.83333C10.2483 6.84677 11.0698 7.66829 12.0833 7.66829C13.0967 7.66829 13.9182 6.84677 13.9182 5.83333C13.9182 4.81989 13.0967 3.99837 12.0833 3.99837Z"/>
                                        </svg>
                                    </button>
                                </div>
                                <div className="composer-actions-right">
                                    <button
                                        type="button"
                                        className="composer-btn"
                                        aria-label="Voice input"
                                        title="Voice input"
                                    >
                                        <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                                            <path
                                                d="M15.7806 10.1963C16.1326 10.3011 16.3336 10.6714 16.2288 11.0234L16.1487 11.2725C15.3429 13.6262 13.2236 15.3697 10.6644 15.6299L10.6653 16.835H12.0833L12.2171 16.8486C12.5202 16.9106 12.7484 17.1786 12.7484 17.5C12.7484 17.8214 12.5202 18.0894 12.2171 18.1514L12.0833 18.165H7.91632C7.5492 18.1649 7.25128 17.8672 7.25128 17.5C7.25128 17.1328 7.5492 16.8351 7.91632 16.835H9.33527L9.33429 15.6299C6.775 15.3697 4.6558 13.6262 3.84992 11.2725L3.76984 11.0234L3.74445 10.8906C3.71751 10.5825 3.91011 10.2879 4.21808 10.1963C4.52615 10.1047 4.84769 10.2466 4.99347 10.5195L5.04523 10.6436L5.10871 10.8418C5.8047 12.8745 7.73211 14.335 9.99933 14.335C12.3396 14.3349 14.3179 12.7789 14.9534 10.6436L15.0052 10.5195C15.151 10.2466 15.4725 10.1046 15.7806 10.1963ZM12.2513 5.41699C12.2513 4.17354 11.2437 3.16521 10.0003 3.16504C8.75675 3.16504 7.74835 4.17343 7.74835 5.41699V9.16699C7.74853 10.4104 8.75685 11.418 10.0003 11.418C11.2436 11.4178 12.2511 10.4103 12.2513 9.16699V5.41699ZM13.5814 9.16699C13.5812 11.1448 11.9781 12.7479 10.0003 12.748C8.02232 12.748 6.41845 11.1449 6.41828 9.16699V5.41699C6.41828 3.43889 8.02221 1.83496 10.0003 1.83496C11.9783 1.83514 13.5814 3.439 13.5814 5.41699V9.16699Z"/>
                                        </svg>
                                    </button>
                                    <button
                                        type="button"
                                        onClick={handleSendMessage}
                                        disabled={isSending || !input.trim()}
                                        className="send-button"
                                        aria-label="Send message"
                                        title="Send message"
                                    >
                                        {isSending ? (
                                            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"
                                                 className="animate-spin">
                                                <path
                                                    d="M12,4a8,8,0,0,1,7.89,6.7A1.53,1.53,0,0,0,21.38,12h0a1.5,1.5,0,0,0,1.48-1.75,11,11,0,0,0-21.72,0A1.5,1.5,0,0,0,2.62,12h0a1.53,1.53,0,0,0,1.49-1.3A8,8,0,0,1,12,4Z"/>
                                            </svg>
                                        ) : (
                                            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                                                <path
                                                    d="M7.33496 15.5V4.5C7.33496 4.13275 7.63275 3.83499 8 3.83496C8.36727 3.83496 8.66504 4.13273 8.66504 4.5V15.5C8.66504 15.8673 8.36727 16.165 8 16.165C7.63275 16.165 7.33496 15.8673 7.33496 15.5ZM11.335 13.1309V7.20801C11.335 6.84075 11.6327 6.54298 12 6.54297C12.3673 6.54297 12.665 6.84074 12.665 7.20801V13.1309C12.665 13.4981 12.3672 13.7959 12 13.7959C11.6328 13.7959 11.335 13.4981 11.335 13.1309ZM3.33496 11.3535V8.81543C3.33496 8.44816 3.63273 8.15039 4 8.15039C4.36727 8.15039 4.66504 8.44816 4.66504 8.81543V11.3535C4.66504 11.7208 4.36727 12.0186 4 12.0186C3.63273 12.0186 3.33496 11.7208 3.33496 11.3535ZM15.335 11.3535V8.81543C15.335 8.44816 15.6327 8.15039 16 8.15039C16.3673 8.15039 16.665 8.44816 16.665 8.81543V11.3535C16.665 11.7208 16.3673 12.0186 16 12.0186C15.6327 12.0186 15.335 11.7208 15.335 11.3535Z"/>
                                            </svg>
                                        )}
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

            <ConnectionStatus
                status={connectionStatus.status}
                message={connectionStatus.message}
            />
        </div>
    );
}; 