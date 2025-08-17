import { create } from 'zustand';
import { STATUSES, MESSAGES, SENDER_TYPES, MESSAGE_SUBTYPES, CSS_CLASSES, THINKING_STATES } from '../constants/constants.js';

export const useChatStore = create((set, get) => ({
    threads: [],
    currentThreadId: null,
    isSidebarOpen: true,
    messages: [],
    input: '',
    isLoading: false,
    isSending: false,
    connectionStatus: {
        status: STATUSES.DISCONNECTED,
        message: MESSAGES.READY
    },
    currentAssistantMessage: '',
    currentAssistantTraceId: null,
    thinkingProcess: {
        isActive: false,
        state: THINKING_STATES.THINKING,
        startTime: null,
        endTime: null,
        duration: 0,
        history: [],
        isExpanded: false
    },
    
    setInput: (input) => set({ input }),

    setThreads: (threads) => set({ threads }),

    setCurrentThreadId: (threadId) => set({ currentThreadId: threadId }),

    addThread: (thread) => set((state) => ({
        threads: [thread, ...state.threads],
        currentThreadId: thread.id,
    })),

    removeThread: (threadId) => set((state) => ({
        threads: state.threads.filter(t => String(t.id) !== String(threadId)),
        currentThreadId: state.currentThreadId === threadId ? null : state.currentThreadId,
    })),
    
    setLoading: (isLoading) => set({ isLoading }),
    
    setSending: (isSending) => set({ isSending }),
    
    setConnectionStatus: (status, message) => 
        set({ connectionStatus: { status, message } }),
    
    setCurrentAssistantMessage: (message, traceId = null) => 
        set({ currentAssistantMessage: message, currentAssistantTraceId: traceId }),
    
    appendToCurrentAssistantMessage: (content) => 
        set((state) => ({ 
            currentAssistantMessage: state.currentAssistantMessage + content 
        })),
    
    addMessage: (content, sender = SENDER_TYPES.USER, messageType = MESSAGE_SUBTYPES.MESSAGE, className = '', traceId = null) => 
        set((state) => ({
            messages: [...state.messages, {
                id: Date.now() + Math.random(),
                content,
                sender,
                messageType,
                className,
                traceId,
                timestamp: new Date().toISOString()
            }]
        })),
    
    loadHistory: (historyMessages) => {
        const transformedMessages = historyMessages.map((msg, index) => {
            const baseId = Date.now() + index;
            
            switch (msg.type) {
                case 'human_message':
                    return {
                        id: baseId,
                        content: msg.content,
                        sender: SENDER_TYPES.USER,
                        messageType: MESSAGE_SUBTYPES.MESSAGE,
                        className: '',
                        traceId: null,
                        timestamp: new Date().toISOString()
                    };
                case 'ai_message':
                    return {
                        id: baseId,
                        content: msg.content,
                        sender: SENDER_TYPES.ASSISTANT,
                        messageType: MESSAGE_SUBTYPES.MESSAGE,
                        className: '',
                        traceId: msg.trace_id || null,
                        timestamp: new Date().toISOString()
                    };
                case 'tool_call':
                    return {
                        id: baseId,
                        content: `🔧 Tool call: ${msg.name}(${JSON.stringify(msg.args)})`,
                        sender: SENDER_TYPES.ASSISTANT,
                        messageType: MESSAGE_SUBTYPES.TOOL_CALL,
                        className: CSS_CLASSES.TOOL_CALL,
                        traceId: null,
                        timestamp: new Date().toISOString()
                    };
                case 'tool_result':
                    return {
                        id: baseId,
                        content: `🔧 ${msg.tool_name}: ${msg.content}`,
                        sender: SENDER_TYPES.ASSISTANT,
                        messageType: MESSAGE_SUBTYPES.TOOL_RESULT,
                        className: CSS_CLASSES.TOOL_CALL,
                        traceId: null,
                        timestamp: new Date().toISOString()
                    };
                default:
                    return {
                        id: baseId,
                        content: msg.content || '',
                        sender: SENDER_TYPES.SYSTEM,
                        messageType: MESSAGE_SUBTYPES.MESSAGE,
                        className: '',
                        traceId: null,
                        timestamp: new Date().toISOString()
                    };
            }
        });
        
        set({ messages: transformedMessages });
    },
    
    finalizeAssistantMessage: () => {
        const { currentAssistantMessage, currentAssistantTraceId } = get();
        if (currentAssistantMessage) {
            set((state) => ({
                messages: [...state.messages, {
                    id: Date.now() + Math.random(),
                    content: currentAssistantMessage,
                    sender: SENDER_TYPES.ASSISTANT,
                    messageType: MESSAGE_SUBTYPES.MESSAGE,
                    className: '',
                    traceId: currentAssistantTraceId,
                    timestamp: new Date().toISOString()
                }],
                currentAssistantMessage: '',
                currentAssistantTraceId: null
            }));
        }
    },
    
    clearInput: () => set({ input: '' }),
    
    clearCurrentAssistantMessage: () => set({ currentAssistantMessage: '', currentAssistantTraceId: null }),

    clearMessages: () => set({
        messages: [],
        currentAssistantMessage: '',
        currentAssistantTraceId: null,
    }),

    startThinkingProcess: () => set((state) => ({
        thinkingProcess: {
            ...state.thinkingProcess,
            isActive: true,
            state: THINKING_STATES.THINKING,
            startTime: Date.now(),
            endTime: null,
            duration: 0,
            history: [],
            isExpanded: false
        }
    })),
    
    setThinkingState: (newState) => set((state) => ({
        thinkingProcess: {
            ...state.thinkingProcess,
            state: newState
        }
    })),
    
    addThinkingEvent: (type, content) => set((state) => ({
        thinkingProcess: {
            ...state.thinkingProcess,
            history: [
                ...state.thinkingProcess.history,
                {
                    type,
                    timestamp: Date.now(),
                    content
                }
            ]
        }
    })),
    
    completeThinkingProcess: () => set((state) => {
        const endTime = Date.now();
        const duration = state.thinkingProcess.startTime ? 
            Math.round((endTime - state.thinkingProcess.startTime) / 1000) : 0;

        const shouldAddThinkingMessage = state.thinkingProcess.history.length > 0 || duration > 0;
        
        return {
            messages: shouldAddThinkingMessage ? [
                ...state.messages,
                {
                    id: 'thinking-' + Date.now(),
                    content: '',
                    sender: SENDER_TYPES.ASSISTANT,
                    messageType: MESSAGE_SUBTYPES.MESSAGE,
                    className: 'thinking-completed',
                    traceId: null,
                    timestamp: new Date().toISOString(),
                    thinkingData: {
                        duration,
                        history: state.thinkingProcess.history,
                        isExpanded: false
                    }
                }
            ] : state.messages,
            thinkingProcess: {
                ...state.thinkingProcess,
                state: THINKING_STATES.COMPLETED,
                endTime,
                duration,
                isActive: false
            }
        };
    }),
    
    toggleThinkingExpanded: () => set((state) => ({
        thinkingProcess: {
            ...state.thinkingProcess,
            isExpanded: !state.thinkingProcess.isExpanded
        }
    })),
    
    toggleThinkingMessageExpanded: (messageId) => set((state) => ({
        messages: state.messages.map(msg => 
            msg.id === messageId && msg.thinkingData 
                ? { ...msg, thinkingData: { ...msg.thinkingData, isExpanded: !msg.thinkingData.isExpanded } }
                : msg
        )
    })),
    
    clearThinkingProcess: () => set((state) => ({
        thinkingProcess: {
            isActive: false,
            state: THINKING_STATES.THINKING,
            startTime: null,
            endTime: null,
            duration: 0,
            history: [],
            isExpanded: false
        }
    })),
    
    reset: () => set({
        threads: [],
        currentThreadId: null,
        messages: [],
        input: '',
        isLoading: false,
        isSending: false,
        connectionStatus: {
            status: STATUSES.DISCONNECTED,
            message: MESSAGES.READY
        },
        currentAssistantMessage: '',
        currentAssistantTraceId: null,
        thinkingProcess: {
            isActive: false,
            state: THINKING_STATES.THINKING,
            startTime: null,
            endTime: null,
            duration: 0,
            history: [],
            isExpanded: false
        }
    }),

    resetChatContext: () => set({
        messages: [],
        input: '',
        isLoading: false,
        isSending: false,
        connectionStatus: {
            status: STATUSES.DISCONNECTED,
            message: MESSAGES.READY
        },
        currentAssistantMessage: '',
        currentAssistantTraceId: null,
        thinkingProcess: {
            isActive: false,
            state: THINKING_STATES.THINKING,
            startTime: null,
            endTime: null,
            duration: 0,
            history: [],
            isExpanded: false
        }
    })
})); 