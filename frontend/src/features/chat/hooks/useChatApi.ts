import { useState, useCallback } from 'react';
import { Platform } from 'react-native';
import { useRouter } from 'expo-router';

import { useApi } from '@/api/useApi';
import {
  Message,
  Chat,
  CreateChatPayload,
  PaginatedResponseData,
  PaginationParams,
  ChatUpdatePayload,
} from '@/api/types/chat.types';
import { ApiError } from '@/api/types/api.types';
import * as chatApi from '@/api/endpoints/chatApi';
import {
    GetChatsData,
    GetChatMessagesData,
    CreateChatData,
    UpdateChatData
} from '@/api/endpoints/chatApi';

// Define the props the hook needs
interface UseChatApiProps {
    setChatListData: React.Dispatch<React.SetStateAction<PaginatedResponseData<Chat> | null>>;
    setMessageData: React.Dispatch<React.SetStateAction<PaginatedResponseData<Message> | null>>;
    setSelectedChatId: React.Dispatch<React.SetStateAction<string | null>>;
}

export const useChatApi = ({
    setChatListData,
    setMessageData,
    setSelectedChatId
}: UseChatApiProps) => {
    const router = useRouter();

    // --- State for API loading/error/pagination ---
    const [loadingMoreChats, setLoadingMoreChats] = useState<boolean>(false);
    const [loadingMoreMessages, setLoadingMoreMessages] = useState<boolean>(false);
    const [updatingChat, setUpdatingChat] = useState<boolean>(false);
    const [updateChatError, setUpdateChatError] = useState<ApiError | null>(null);

    // --- API Callbacks ---
    const handleGetChatsSuccess = useCallback((data: GetChatsData, args?: PaginationParams[]) => {
        const isFetchingMore = !!args?.[0]?.before_timestamp;
        setChatListData(prevData => {
            if (isFetchingMore && prevData) {
                return {
                    items: [...prevData.items, ...data.items],
                    next_cursor_timestamp: data.next_cursor_timestamp,
                    has_more: data.has_more,
                };
            } else {
                return data;
            }
        });
        if (isFetchingMore) {
            setLoadingMoreChats(false);
        }
    }, [setChatListData]);

    const handleGetChatsError = useCallback((error: ApiError, args?: PaginationParams[]) => {
        const isFetchingMore = !!args?.[0]?.before_timestamp;
        console.error(`Error fetching chats${isFetchingMore ? ' (more)' : ''}:`, error);
        if (isFetchingMore) {
            setLoadingMoreChats(false);
        }
    }, []);

    const handleGetMessagesSuccess = useCallback((data: GetChatMessagesData, args?: [string, PaginationParams]) => {
        const isFetchingMore = !!args?.[1]?.before_timestamp;
        setMessageData(prevData => {
            if (isFetchingMore && prevData) {
                return {
                    items: [...data.items, ...prevData.items],
                    next_cursor_timestamp: data.next_cursor_timestamp,
                    has_more: data.has_more,
                };
            } else {
                return data;
            }
        });
         if (isFetchingMore) {
          setLoadingMoreMessages(false);
        }
    }, [setMessageData]);

    const handleGetMessagesError = useCallback((error: ApiError, args?: [string, PaginationParams]) => {
         const isFetchingMore = !!args?.[1]?.before_timestamp;
         console.error(`Error fetching messages${isFetchingMore ? ' (more)' : ''} for chat ${args?.[0]}:`, error);
         if (isFetchingMore) {
           setLoadingMoreMessages(false);
         }
    }, []);

    const handleCreateChatSuccess = useCallback((newChatData: CreateChatData) => {
        setChatListData(prevData => {
            const completeNewItem: Chat = {
                ...newChatData,
                latest_message_content: newChatData.latest_message_content ?? undefined,
                latest_message_timestamp: newChatData.latest_message_timestamp ?? undefined,
            };
            return {
                items: [completeNewItem, ...(prevData?.items || [])],
                next_cursor_timestamp: prevData?.next_cursor_timestamp ?? null,
                has_more: prevData?.has_more ?? false
            };
        });
        setSelectedChatId(newChatData._id);
        if (Platform.OS !== 'web') {
            router.push(`/chat/${newChatData._id}` as any);
        }
    }, [setChatListData, setSelectedChatId, router]);

    const handleCreateChatError = useCallback((error: ApiError) => {
        console.error("Error creating chat:", error);
    }, []);

    const handleUpdateChatSuccess = useCallback((updatedChatData: UpdateChatData) => {
        setChatListData(prevData => {
            if (!prevData) return null;
            const completeUpdatedItem: Chat = {
                ...updatedChatData,
                latest_message_content: updatedChatData.latest_message_content ?? undefined,
                latest_message_timestamp: updatedChatData.latest_message_timestamp ?? undefined,
            };
            return {
                ...prevData,
                items: prevData.items.map(chat =>
                    chat._id === completeUpdatedItem._id ? completeUpdatedItem : chat
                ),
            };
        });
        setUpdatingChat(false);
        setUpdateChatError(null);
    }, [setChatListData]);

    const handleUpdateChatError = useCallback((error: ApiError) => {
        console.error("Error updating chat:", error);
        setUpdateChatError(error);
        setUpdatingChat(false);
    }, []);

    // --- useApi Hooks Initialization ---
    const { execute: fetchChatsApi, loading: loadingChats, error: chatsError, reset: resetChatsError }
        = useApi<GetChatsData, [PaginationParams?]>(chatApi.getChats, {
        onSuccess: handleGetChatsSuccess,
        onError: handleGetChatsError,
    });

    const { execute: fetchMessagesApi, loading: loadingMessages, error: messagesError, reset: resetMessagesError }
        = useApi<GetChatMessagesData, [string, PaginationParams?]>(chatApi.getChatMessages, {
        onSuccess: handleGetMessagesSuccess,
        onError: handleGetMessagesError,
    });

    const { execute: createChatApi, loading: creatingChat, error: createChatError, reset: resetCreateChatError }
        = useApi<CreateChatData, [CreateChatPayload]>(chatApi.createChat, {
        onSuccess: handleCreateChatSuccess,
        onError: handleCreateChatError,
    });

    const { execute: updateChatApi, reset: resetUpdateChatError }
        = useApi<UpdateChatData, [string, ChatUpdatePayload]>(chatApi.updateChat, {
        onSuccess: handleUpdateChatSuccess,
        onError: handleUpdateChatError,
    });

    // --- Actions ---
    const fetchChatList = useCallback(() => {
        resetChatsError();
        fetchChatsApi({});
    }, [fetchChatsApi, resetChatsError]);

    const fetchMoreChats = useCallback((currentChatListData: PaginatedResponseData<Chat> | null) => {
        if (loadingChats || loadingMoreChats || !currentChatListData?.has_more || !currentChatListData.next_cursor_timestamp) {
          return;
        }
        setLoadingMoreChats(true);
        fetchChatsApi({ before_timestamp: currentChatListData.next_cursor_timestamp });
    }, [loadingChats, loadingMoreChats, fetchChatsApi]);

    const fetchMessages = useCallback((chatId: string) => {
        resetMessagesError();
        setMessageData(null); // Clear previous messages when fetching new chat
        fetchMessagesApi(chatId, {});
    }, [fetchMessagesApi, resetMessagesError, setMessageData]);

    const fetchMoreMessages = useCallback((chatId: string, currentMessageData: PaginatedResponseData<Message> | null) => {
        if (!chatId || loadingMessages || loadingMoreMessages || !currentMessageData?.has_more || !currentMessageData.next_cursor_timestamp) {
            return;
        }
        // setLoadingMoreMessages(true);
        // fetchMessagesApi(chatId, { before_timestamp: currentMessageData.next_cursor_timestamp });
    }, [loadingMessages, loadingMoreMessages, fetchMessagesApi]);

    const startNewChat = useCallback(async () => {
        resetCreateChatError();
        try {
            await createChatApi({ name: 'New Chat' });
        } catch (error) {
            // Error handled by useApi hook onError
        }
    }, [createChatApi, resetCreateChatError]);

    const updateChat = useCallback(async (chatId: string, payload: ChatUpdatePayload) => {
        setUpdatingChat(true);
        resetUpdateChatError();
        try {
            await updateChatApi(chatId, payload);
        } catch (err) {
            console.log('updateChat caught error (should be handled by useApi)', err);
            // Error should be handled by useApi hook onError, but catch here just in case
            setUpdatingChat(false); // Ensure loading state is reset on unexpected error
        }
    }, [updateChatApi, resetUpdateChatError]);

    // --- Return Values ---
    return {
        // Loading States
        loadingChats,
        loadingMessages,
        creatingChat,
        updatingChat,
        loadingMoreChats,
        loadingMoreMessages,
        // Error States
        chatsError,
        messagesError,
        createChatError,
        updateChatError,
        // Actions
        fetchChatList,
        fetchMoreChats,
        fetchMessages,
        fetchMoreMessages,
        startNewChat,
        updateChat,
    };
}; 