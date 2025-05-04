import React, { useState } from 'react';
import { StyleSheet, View, Text, Platform, Pressable } from 'react-native';
import { paddings, borderRadii } from '@/features/shared/theme/spacing';
import { useTheme } from '@/features/shared/context/ThemeContext';
import { ContextItemData } from '@/api/types/chat.types';
import { Theme } from '@/features/shared/context/ThemeContext';
import { Ionicons } from '@expo/vector-icons';
import { iconSizes } from '@/features/shared/theme/sizes';

interface ContextItemProps {
  item: ContextItemData;
}

export const ContextItem: React.FC<ContextItemProps> = React.memo(({ item }) => {
  const { theme } = useTheme();
  const styles = getStyles(theme);
  const [isOpen, setIsOpen] = useState(false);

  const toggleOpen = () => setIsOpen(!isOpen);

  return (
    <View style={styles.contextItemContainer}>
      <View style={styles.headerContainer}>
        <View style={styles.headerTextContainer}>
          <Text style={styles.contextItemHeader}>
            {item.source_agent} - {item.content_type}
          </Text>
          <Text style={styles.contextItemTimestamp}>
            {new Date(item.created_at).toLocaleString()}
          </Text>
        </View>
        <Pressable onPress={toggleOpen} style={styles.toggleButton}>
          <Ionicons 
            name={isOpen ? 'chevron-up-outline' : 'chevron-down-outline'} 
            size={iconSizes.medium}
            color={theme.colors.text.secondary} 
          />
        </Pressable>
      </View>
      
      {isOpen && (
        <Text style={styles.contextItemData} selectable>
          {JSON.stringify(item.data, null, 2)}
        </Text>
      )}
    </View>
  );
});

const getStyles = (theme: Theme) => StyleSheet.create({
  contextItemContainer: {
    marginBottom: paddings.medium,
    padding: paddings.small,
    backgroundColor: theme.colors.layout.background,
    borderRadius: borderRadii.medium,
    borderWidth: 1,
    borderColor: theme.colors.layout.border,
  },
  headerContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: paddings.small,
  },
  headerTextContainer: {
     flex: 1,
     marginRight: paddings.small,
  },
  contextItemHeader: {
    color: theme.colors.text.primary,
    fontWeight: '600',
    marginBottom: paddings.xsmall,
  },
  contextItemTimestamp: {
    color: theme.colors.text.secondary,
  },
  toggleButton: {
    paddingLeft: paddings.small,
    paddingRight: paddings.small,
  },
  contextItemData: {
    color: theme.colors.text.primary,
    backgroundColor: theme.colors.layout.foreground,
    marginTop: paddings.xsmall,
  },
}); 