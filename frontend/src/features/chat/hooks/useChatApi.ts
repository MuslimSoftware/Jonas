import { useState, useCallback, useMemo } from 'react';
import { Platform } from 'react-native';
import { useRouter } from 'expo-router';

import { useApi } from '@/api/useApi';
import { useApiPaginated } from '@/api/useApiPaginated';
import {
  Message,
  Chat,
  CreateChatPayload,
  PaginatedResponseData,
  PaginationParams,
  ChatUpdatePayload,
  ScreenshotData
} from '@/api/types/chat.types';
import { ApiError } from '@/api/types/api.types';
import * as chatApi from '@/api/endpoints/chatApi';
import {
    GetChatMessagesData,
    CreateChatData,
    UpdateChatData,
    GetScreenshotsData
} from '@/api/endpoints/chatApi';

// Define the props the hook needs
interface UseChatApiProps {
    messageData: PaginatedResponseData<Message> | null;
    setMessageData: React.Dispatch<React.SetStateAction<PaginatedResponseData<Message> | null>>;
    setSelectedChatId: React.Dispatch<React.SetStateAction<string | null>>;
}

export const useChatApi = ({
    messageData,
    setMessageData,
    setSelectedChatId
}: UseChatApiProps) => {
    const router = useRouter();

    // --- State for API loading/error/pagination ---
    const [loadingMoreMessages, setLoadingMoreMessages] = useState<boolean>(false);
    const [updatingChat, setUpdatingChat] = useState<boolean>(false);
    const [updateChatError, setUpdateChatError] = useState<ApiError | null>(null);
    // --- State for Screenshots --- 
    const [screenshots, setScreenshots] = useState<ScreenshotData[]>([]);
    const [loadingScreenshots, setLoadingScreenshots] = useState<boolean>(false);
    const [screenshotsError, setScreenshotsError] = useState<ApiError | null>(null);

    // --- useApiPaginated Hook for Chats (Define BEFORE callbacks that use its methods) ---
    const { 
        data: chatListDataItems, 
        loading: loadingChats, 
        error: chatsError, 
        loadingMore: loadingMoreChats, 
        hasMore: hasMoreChats, 
        fetch: fetchChatList, 
        fetchMore: fetchMoreChats, 
        reset: resetChatList, 
        nextCursorTimestamp: chatListNextCursorTimestamp,
    } = useApiPaginated<Chat>(
        chatApi.getChats, 
        { 
            pageSize: 25, 
        }
    );

    // --- API Callbacks ---
    const handleGetMessagesSuccess = useCallback((data: GetChatMessagesData, args: any[]) => {
        const isFetchingMore = !!args?.[1]?.before_timestamp;
        setMessageData(prevData => {
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
          setLoadingMoreMessages(false);
        }
    }, [setMessageData]);

    const handleGetMessagesError = useCallback((error: ApiError, args: any[]) => {
         const isFetchingMore = !!args?.[1]?.before_timestamp;
         console.error(`Error fetching messages${isFetchingMore ? ' (more)' : ''} for chat ${args?.[0]}:`, error);
         if (isFetchingMore) {
           setLoadingMoreMessages(false);
         }
    }, []);

    // Keep create/update chat handlers (Now fetchChatList is defined)
    const handleCreateChatSuccess = useCallback((newChatData: CreateChatData) => {
        fetchChatList();
        setSelectedChatId(newChatData._id);
        if (Platform.OS !== 'web') {
            router.push(`/chat/${newChatData._id}` as any);
        }
    }, [fetchChatList, setSelectedChatId, router]);
    
    const handleCreateChatError = useCallback((error: ApiError) => {
        console.error("Error creating chat:", error);
    }, []);

    const handleUpdateChatSuccess = useCallback((updatedChatData: UpdateChatData) => {
        fetchChatList();
        setUpdatingChat(false);
        setUpdateChatError(null);
    }, [fetchChatList]);

    const handleUpdateChatError = useCallback((error: ApiError) => {
        console.error("Error updating chat:", error);
        setUpdateChatError(error);
        setUpdatingChat(false);
    }, []);

    // --- Screenshot API Callbacks --- 
    const handleGetScreenshotsSuccess = useCallback((data: GetScreenshotsData) => {
        setScreenshots(data);
        setLoadingScreenshots(false);
        setScreenshotsError(null);
    }, []);

    const handleGetScreenshotsError = useCallback((error: ApiError) => {
        console.error("Error fetching screenshots:", error);
        setScreenshots([]); // Clear screenshots on error
        setScreenshotsError(error);
        setLoadingScreenshots(false);
    }, []);

    // --- Other useApi Hooks Initialization ---
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

    // --- Screenshot API Hook --- 
    const { execute: fetchScreenshotsApi, reset: resetScreenshotsError } 
        = useApi<GetScreenshotsData, [string]>(chatApi.getChatScreenshots, {
        onSuccess: handleGetScreenshotsSuccess,
        onError: handleGetScreenshotsError,
    });

    // --- Actions ---
    const fetchMessages = useCallback((chatId: string) => {
        resetMessagesError();
        setMessageData(null);
        fetchMessagesApi(chatId, {});
    }, [fetchMessagesApi, resetMessagesError, setMessageData]);

    // Function to refresh the first page of messages for the current chat
    const refreshMessages = useCallback((chatId: string) => {
        if (!chatId) return;
        resetMessagesError(); // Reset errors
        // Re-fetch the first page, useApi will set loading state
        fetchMessagesApi(chatId, {}); 
    }, [fetchMessagesApi, resetMessagesError]);

    const fetchMoreMessages = useCallback((chatId: string) => {
        if (!chatId || loadingMessages || loadingMoreMessages || !messageData?.has_more || !messageData.next_cursor_timestamp) {
            return;
        }
        setLoadingMoreMessages(true);
        fetchMessagesApi(chatId, { before_timestamp: messageData.next_cursor_timestamp });
    }, [loadingMessages, loadingMoreMessages, messageData, fetchMessagesApi, setLoadingMoreMessages]);
   
    const startNewChat = useCallback(async () => {
        resetCreateChatError();
        try {
            await createChatApi({ name: 'New Chat' });
        } catch (e) {
            console.log("Create chat caught exception (already handled by useApi):", e)
        }
    }, [createChatApi, resetCreateChatError]);

    const updateChat = useCallback(async (chatId: string, payload: ChatUpdatePayload) => {
        setUpdatingChat(true);
        setUpdateChatError(null);
        resetUpdateChatError();
        try {
            await updateChatApi(chatId, payload);
        } catch (e) { 
            console.log("Update chat caught exception (already handled by useApi):", e)
        }
    }, [updateChatApi, resetUpdateChatError]);

    // --- Action to fetch screenshots --- 
    const fetchScreenshots = useCallback(async (chatId: string) => {
        if (!chatId) return;
        setScreenshots([]); // Clear previous screenshots
        setLoadingScreenshots(true);
        resetScreenshotsError();
        try {
            await fetchScreenshotsApi(chatId);
        } catch(e) {
            console.log("Fetch screenshots caught exception (already handled by useApi):", e)
        }
    }, [fetchScreenshotsApi, resetScreenshotsError]);

    // --- Memoize the chat list data object --- 
    const memoizedChatListData = useMemo(() => ({
        items: chatListDataItems || [],
        has_more: hasMoreChats,
        next_cursor_timestamp: chatListNextCursorTimestamp,
    }), [chatListDataItems, hasMoreChats, chatListNextCursorTimestamp]);

    // --- Return Values ---
    return {
        chatListData: memoizedChatListData, 
        loadingChats,
        chatsError,
        loadingMoreChats,
        fetchChatList,
        fetchMoreChats,
        resetChatList,
        loadingMessages,
        messagesError,
        fetchMessages,
        fetchMoreMessages,
        loadingMoreMessages,
        creatingChat,
        createChatError,
        startNewChat,
        updatingChat,
        updateChatError,
        updateChat,
        refreshMessages,
        screenshots,
        loadingScreenshots,
        screenshotsError,
        fetchScreenshots,
        resetScreenshotsError
    };
}; 