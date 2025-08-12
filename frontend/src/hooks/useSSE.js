import {useCallback, useRef} from 'react';
import {SSE} from 'sse.js';
import {useChatStore} from '../store/index.js';
import {
    CSS_CLASSES,
    MESSAGE_SUBTYPES,
    MESSAGES,
    SENDER_TYPES,
    STATUSES,
    THINKING_STATES
} from '../constants/constants.js';

const USER_ID = '1437ade37359488e95c0727a1cdf1786d24edce3';

export const useSSE = () => {
    const sseRef = useRef(null);
    const sseVersionRef = useRef(0);
    const {
        threads,
        currentThreadId,
        setThreads,
        setCurrentThreadId,
        addThread,
        setConnectionStatus,
        setLoading,
        setSending,
        appendToCurrentAssistantMessage,
        addMessage,
        finalizeAssistantMessage,
        clearCurrentAssistantMessage,
        clearMessages,
        setCurrentAssistantMessage,
        loadHistory,
        startThinkingProcess,
        setThinkingState,
        addThinkingEvent,
        completeThinkingProcess,
        clearThinkingProcess,
        resetChatContext
    } = useChatStore();

    const loadChatHistory = useCallback(async () => {
        setLoading(true);

        try {
            if (sseRef.current) {
                sseRef.current.close();
            }

            const authToken = localStorage.getItem('authToken') || 'eyJ1c2VyX2lkIjogIjE0MzdhZGUzNzM1OTQ4OGU5NWMwNzI3YTFjZGYxNzg2ZDI0ZWRjZTMiLCAiZW1haWwiOiAidGVzdEBnbWFpbC5jb20ifQ==';
            if (!currentThreadId) {
                setLoading(false);
                return;
            }

            const version = ++sseVersionRef.current;

            clearMessages();

            const historicalMessages = [];
            sseRef.current = new SSE(`/api/v1/threads/${currentThreadId}/history`, {
                headers: {
                    'Authorization': 'Bearer ' + authToken
                },
                autoReconnect: false,
                start: false
            });

            const handleHistoryMessage = (e) => {
                if (version !== sseVersionRef.current) return;
                const data = parseEventData(e);
                if (!data) return;
                historicalMessages.push(data);
            };

            const handleHistoryOpen = () => {
                if (version !== sseVersionRef.current) return;
                console.log('History SSE connection opened');
            };

            const handleHistoryError = (e) => {
                if (version !== sseVersionRef.current) return;
                console.error('History SSE Error:', e);
                const errorMessage = extractErrorMessage(e);
                addMessage(errorMessage, SENDER_TYPES.SYSTEM, MESSAGE_SUBTYPES.ERROR, CSS_CLASSES.ERROR);
                setLoading(false);
            };

            const handleHistoryEnd = () => {
                if (version !== sseVersionRef.current) return;
                console.log('History loading completed');

                if (historicalMessages.length > 0) {
                    loadHistory(historicalMessages);
                }

                setLoading(false);
                if (sseRef.current) {
                    sseRef.current.close();
                    sseRef.current = null;
                }
            };

            sseRef.current.addEventListener('open', handleHistoryOpen);
            sseRef.current.addEventListener('ai_message', handleHistoryMessage);
            sseRef.current.addEventListener('human_message', handleHistoryMessage);
            sseRef.current.addEventListener('ui', handleHistoryMessage);
            sseRef.current.addEventListener('tool_call', handleHistoryMessage);
            sseRef.current.addEventListener('tool_result', handleHistoryMessage);
            sseRef.current.addEventListener('error', handleHistoryError);
            sseRef.current.addEventListener('stream_end', handleHistoryEnd);
            sseRef.current.addEventListener('readystatechange', (e) => {
                if (version !== sseVersionRef.current) return;
                if (e.readyState === 2) {
                    setLoading(false);
                }
            });

            sseRef.current.stream();

        } catch (error) {
            console.error('Error loading chat history:', error);
            addMessage('Error loading chat history', SENDER_TYPES.SYSTEM, MESSAGE_SUBTYPES.ERROR, CSS_CLASSES.ERROR);
            setLoading(false);
        }
    }, [currentThreadId, setLoading, addMessage, loadHistory, parseEventData, extractErrorMessage, clearMessages]);

    const parseEventData = useCallback((e) => {
        try {
            return JSON.parse(e.data);
        } catch (parseError) {
            console.error('Error parsing event data:', parseError);
            return null;
        }
    }, []);

    const extractErrorMessage = useCallback((e) => {
        if (!e.data) return MESSAGES.RECEIVE_ERROR;

        try {
            const errorData = JSON.parse(e.data);
            return errorData.content || MESSAGES.RECEIVE_ERROR;
        } catch (parseError) {
            console.error('Error parsing error data:', parseError);
            return MESSAGES.RECEIVE_ERROR;
        }
    }, []);

    const handleSSEOpen = useCallback(() => {
        console.log('SSE connection opened');
        setConnectionStatus(STATUSES.CONNECTED, MESSAGES.CONNECTED);
        setLoading(false);
    }, [setConnectionStatus, setLoading]);

    const handleAIMessage = useCallback((e) => {
        const data = parseEventData(e);
        if (!data) return;

        if (data.content) {
            setCurrentAssistantMessage(data.content, data.trace_id);
        }
    }, [parseEventData, setCurrentAssistantMessage]);

    const handleToolCall = useCallback((e) => {
        const data = parseEventData(e);
        if (!data) return;

        console.log('Tool Call:', data);

        addThinkingEvent('tool_call', data);
    }, [parseEventData, addThinkingEvent]);

    const handleToolResult = useCallback((e) => {
        const data = parseEventData(e);
        if (!data) return;

        console.log('Tool Result:', data);

        addThinkingEvent('tool_result', data);
    }, [parseEventData, addThinkingEvent]);

    const handleToken = useCallback((e) => {
        const data = parseEventData(e);
        if (!data) return;

        setThinkingState(THINKING_STATES.RESPONDING);

        if (data.content) {
            appendToCurrentAssistantMessage(data.content);
        }
    }, [parseEventData, appendToCurrentAssistantMessage, setThinkingState]);

    const handleUIMessage = useCallback((e) => {
        const data = parseEventData(e);
        if (!data) return;

        addMessage(data, SENDER_TYPES.ASSISTANT, MESSAGE_SUBTYPES.UI, CSS_CLASSES.UI_MESSAGE);
    }, [parseEventData, addMessage]);

    const handleSSEError = useCallback((e) => {
        console.error('SSE Error:', e);
        setConnectionStatus(STATUSES.DISCONNECTED, MESSAGES.CONNECTION_ERROR);

        const errorMessage = extractErrorMessage(e);
        addMessage(errorMessage, SENDER_TYPES.SYSTEM, MESSAGE_SUBTYPES.ERROR, CSS_CLASSES.ERROR);

        setLoading(false);
        setSending(false);
    }, [setConnectionStatus, extractErrorMessage, addMessage, setLoading, setSending]);

    const handleSSEAbort = useCallback(() => {
        console.log('SSE connection closed - resetting sending state');
        setConnectionStatus(STATUSES.DISCONNECTED, MESSAGES.DISCONNECTED);
        setSending(false);
        setLoading(false);
    }, [setConnectionStatus, setSending, setLoading]);

    const handleReadyStateChange = useCallback((e) => {
        const stateMessages = {
            0: [STATUSES.CONNECTING, MESSAGES.CONNECTING],
            1: [STATUSES.CONNECTED, MESSAGES.CONNECTED],
            2: [STATUSES.DISCONNECTED, MESSAGES.DISCONNECTED]
        };

        const [status, message] = stateMessages[e.readyState] || [];
        if (status && message) {
            setConnectionStatus(status, message);
            if (e.readyState === 2) {
                setSending(false);
            }
        }
    }, [setConnectionStatus, setSending]);

    const handleStreamEnd = useCallback(() => {
        console.log('Stream ended - resetting states');

        completeThinkingProcess();
        finalizeAssistantMessage();
        setSending(false);
        setLoading(false);
        setConnectionStatus(STATUSES.DISCONNECTED, MESSAGES.READY);

        if (sseRef.current) {
            sseRef.current.close();
        }
    }, [completeThinkingProcess, finalizeAssistantMessage, setSending, setLoading, setConnectionStatus]);

    const setupSSEListeners = useCallback(() => {
        if (!sseRef.current) return;

        const handlers = {
            'open': handleSSEOpen,
            'thread': (e) => {
                const data = parseEventData(e);
                if (data?.id) {
                    const id = String(data.id);
                    setCurrentThreadId(id);
                    const exists = (useChatStore.getState().threads || []).some(t => String(t.id) === id);
                    if (!exists) {
                        addThread({ id, agent_id: data.agent_id, meta: data.meta || {}, status: data.status });
                    }
                }
            },
            'ai_message': handleAIMessage,
            'tool_call': handleToolCall,
            'tool_result': handleToolResult,
            'token': handleToken,
            'ui': handleUIMessage,
            'error': handleSSEError,
            'abort': handleSSEAbort,
            'readystatechange': handleReadyStateChange,
            'stream_end': handleStreamEnd
        };

        Object.entries(handlers).forEach(([event, handler]) => {
            sseRef.current.addEventListener(event, handler);
        });
    }, [
        handleSSEOpen,
        handleAIMessage,
        handleToolCall,
        handleToolResult,
        handleToken,
        handleUIMessage,
        handleSSEError,
        handleSSEAbort,
        handleReadyStateChange,
        handleStreamEnd
    ]);

    const sendMessage = useCallback(async (message) => {
        if (!message.trim()) return;

        if (sseRef.current) {
            sseRef.current.close();
        }

        setSending(true);
        setLoading(true);
        clearCurrentAssistantMessage();
        startThinkingProcess();

        try {
            const authToken = localStorage.getItem('authToken') || 'eyJ1c2VyX2lkIjogIjE0MzdhZGUzNzM1OTQ4OGU5NWMwNzI3YTFjZGYxNzg2ZDI0ZWRjZTMiLCAiZW1haWwiOiAidGVzdEBnbWFpbC5jb20ifQ==';
            const version = ++sseVersionRef.current;
            sseRef.current = new SSE(`/api/v1/runs/stream`, {
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer ' + authToken
                },
                payload: JSON.stringify({
                    input: message,
                    thread_id: currentThreadId,
                    metadata: {
                        user_id: USER_ID,
                    },
                    agent_id: 'demo_agent',
                }),
                autoReconnect: false,
                start: false
            });

            const guardedSetup = () => {
                if (!sseRef.current) return;
                const handlers = {
                    'open': handleSSEOpen,
                    'thread': (e) => { if (version !== sseVersionRef.current) return; const data = parseEventData(e); if (data?.id) { const id = String(data.id); setCurrentThreadId(id); const exists = (useChatStore.getState().threads || []).some(t => String(t.id) === id); if (!exists) { addThread({ id, agent_id: data.agent_id, meta: data.meta || {}, status: data.status }); } } },
                    'ai_message': (e) => { if (version !== sseVersionRef.current) return; handleAIMessage(e); },
                    'tool_call': (e) => { if (version !== sseVersionRef.current) return; handleToolCall(e); },
                    'tool_result': (e) => { if (version !== sseVersionRef.current) return; handleToolResult(e); },
                    'token': (e) => { if (version !== sseVersionRef.current) return; handleToken(e); },
                    'ui': (e) => { if (version !== sseVersionRef.current) return; handleUIMessage(e); },
                    'error': (e) => { if (version !== sseVersionRef.current) return; handleSSEError(e); },
                    'abort': (e) => { if (version !== sseVersionRef.current) return; handleSSEAbort(e); },
                    'readystatechange': (e) => { if (version !== sseVersionRef.current) return; handleReadyStateChange(e); },
                    'stream_end': (e) => { if (version !== sseVersionRef.current) return; handleStreamEnd(e); },
                };
                Object.entries(handlers).forEach(([event, handler]) => sseRef.current.addEventListener(event, handler));
            };

            guardedSetup();
            sseRef.current.stream();

        } catch (error) {
            console.error('Error:', error);
            addMessage(MESSAGES.CREATE_ERROR, SENDER_TYPES.SYSTEM, MESSAGE_SUBTYPES.ERROR, CSS_CLASSES.ERROR);
            setLoading(false);
            setSending(false);
        }
    }, [
        setSending,
        setLoading,
        clearCurrentAssistantMessage,
        startThinkingProcess,
        setupSSEListeners,
        addMessage,
        currentThreadId
    ]);

    const closeConnection = useCallback(() => {
        if (sseRef.current) {
            sseRef.current.close();
            sseRef.current = null;
        }
    }, []);

    const fetchThreads = useCallback(async () => {
        try {
            const authToken = localStorage.getItem('authToken') || 'eyJ1c2VyX2lkIjogIjE0MzdhZGUzNzM1OTQ4OGU5NWMwNzI3YTFjZGYxNzg2ZDI0ZWRjZTMiLCAiZW1haWwiOiAidGVzdEBnbWFpbC5jb20ifQ==';
            const res = await fetch('/api/v1/threads', {
                headers: { 'Authorization': 'Bearer ' + authToken }
            });
            const data = await res.json();
            setThreads(data);
        } catch (e) {
            console.error('Failed to fetch threads', e);
        }
    }, [setThreads]);

    const newChat = useCallback(async () => {
        if (sseRef.current) {
            sseRef.current.close();
            sseRef.current = null;
        }
        setCurrentThreadId(null);
        resetChatContext();
    }, [setCurrentThreadId, resetChatContext]);

    return {
        sendMessage,
        closeConnection,
        loadChatHistory,
        fetchThreads,
        newChat,
        getUserId: () => USER_ID,
        getThreadId: () => currentThreadId,
        setCurrentThreadId,
    };
}; 