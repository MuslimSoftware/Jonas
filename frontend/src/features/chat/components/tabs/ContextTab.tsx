import React from 'react';
import { StyleSheet, Pressable, View, ActivityIndicator, Text, Platform, FlatList } from 'react-native';
import { paddings } from '@/features/shared/theme/spacing';
import { useTheme } from '@/features/shared/context/ThemeContext';
import { ContextItemData } from '@/api/types/chat.types';
import { Theme } from '@/features/shared/context/ThemeContext';
import { ApiError } from '@/api/types/api.types';
import { ContextItem } from '../items/ContextItem';

interface ContextTabProps {
  contextItems: ContextItemData[];
  loadingContext: boolean;
  contextError: ApiError | null;
  hasMoreContext: boolean;
  loadingMoreContext: boolean;
  fetchMoreContextItems: () => void;
}

export const ContextTab: React.FC<ContextTabProps> = ({
  contextItems,
  loadingContext,
  contextError,
  hasMoreContext,
  loadingMoreContext,
  fetchMoreContextItems,
}) => {
  const { theme } = useTheme();
  const styles = getStyles(theme);

  const renderContextItem = ({ item }: { item: ContextItemData }) => (
    <ContextItem item={item} />
  );

  const renderListFooter = () => {
    if (!hasMoreContext) return null;
    return (
      <Pressable
        style={styles.loadMoreButton}
        onPress={fetchMoreContextItems}
        disabled={loadingMoreContext}
      >
        {loadingMoreContext ? (
          <ActivityIndicator color={theme.colors.text.secondary} />
        ) : (
          <Text style={styles.loadMoreText}>Load More</Text>
        )}
      </Pressable>
    );
  };

  const renderEmptyList = () => {
    // Initial loading state handled outside FlatList in RightChatPanel
    if (contextError) {
       return <Text style={styles.errorText}>Error loading context items.</Text>;
    }
    if (!loadingContext && contextItems.length === 0) {
      return <Text style={styles.emptyText}>No context items available.</Text>;
    }
    return null; // Don't show anything if loading but items exist, or if no error/empty
  };

  // Handle initial loading and error states before rendering FlatList
  if (loadingContext && contextItems.length === 0) {
    return <View style={styles.centeredContainer}><ActivityIndicator color={theme.colors.text.primary} /></View>;
  }

  if (contextError && contextItems.length === 0) {
    return <View style={styles.centeredContainer}><Text style={styles.errorText}>Error loading context items.</Text></View>;
  }


  return (
    <FlatList
      data={contextItems}
      renderItem={renderContextItem}
      keyExtractor={(item) => item._id}
      contentContainerStyle={styles.flatListContentContainer}
      ListEmptyComponent={renderEmptyList} // Handles empty state after initial load
      ListFooterComponent={renderListFooter}
      onEndReached={() => {
        if (hasMoreContext && !loadingMoreContext) {
          fetchMoreContextItems();
        }
      }}
      onEndReachedThreshold={0.5}
      style={styles.flatList} // Ensure FlatList takes up space
    />
  );
};

const getStyles = (theme: Theme) => StyleSheet.create({
  flatList: {
    flex: 1, // Ensure FlatList fills the available space
    width: '100%',
  },
  flatListContentContainer: {
    paddingBottom: paddings.small, // Ensure space for the load more button if needed
    paddingTop: paddings.small,
  },
  centeredContainer: { // For initial loading/error states
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: paddings.medium, // Consistent padding
  },
  errorText: {
    color: theme.colors.indicators.error,
    textAlign: 'center',
  },
  emptyText: {
    color: theme.colors.text.secondary,
    textAlign: 'center',
  },
  loadMoreButton: {
    paddingVertical: paddings.medium,
    alignItems: 'center',
  },
  loadMoreText: {
    color: theme.colors.text.primary,
    fontWeight: '500',
  },
}); 