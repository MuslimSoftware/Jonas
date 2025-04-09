import React from 'react';
import {
  StyleSheet,
  FlatList,
  View,
} from 'react-native';
import { BgView, FgView } from '@/features/shared/components/layout';
import { TextBody, TextCaption } from '@/features/shared/components/text';
import { paddings, borderRadii, gaps } from '@/features/shared/theme/spacing';
import { useTheme } from '@/features/shared/context/ThemeContext';
import { useChat } from '../context'; // Import useChat
import { MessageData } from '../context'; // Import type from context
import { Brand } from '@/features/shared';

interface MessageListProps {}

export const MessageList: React.FC<MessageListProps> = ({}) => {
  const { theme } = useTheme();
  const { messages } = useChat(); 

  const renderMessageItem = ({ item, index }: { item: MessageData; index: number }) => {
    const previousMessage = messages[index + 1] ?? null;
    const showAgentLabel = 
        item.sender === 'other' && 
        (previousMessage === null || previousMessage.sender === 'user');

    const BubbleView = item.sender === 'user' ? BgView : FgView;
    return (
      <>
        <View 
          style={[
              styles.messageBubbleContainer, 
              item.sender === 'user' ? styles.userMessageContainer : styles.otherMessageContainer
          ]}
        >
          <BubbleView style={styles.messageBubble}>
            <TextBody color={theme.colors.text.primary}>
              {item.text}
            </TextBody>
          </BubbleView>
        </View>
        {/* Render label conditionally */}
        {showAgentLabel && (
          <View style={styles.agentLabelContainer}>
            <TextCaption color={theme.colors.text.secondary}>{Brand.name}</TextCaption>
          </View>
        )}
      </>
    );
  };

  return (
    <FlatList
        data={messages}
        renderItem={renderMessageItem}
        keyExtractor={(item) => item.id}
        style={styles.messageList}
        contentContainerStyle={styles.messageListContent}
        inverted
    />
  );
};

const styles = StyleSheet.create({
    messageList: {
        flex: 1,
    },
    messageListContent: {
        paddingHorizontal: paddings.large,
        paddingVertical: paddings.medium,
        flexGrow: 1,
        justifyContent: 'flex-end',
    },
    messageBubbleContainer: {
        marginBottom: gaps.medium,
        maxWidth: '80%',
    },
    messageBubble: {
        padding: paddings.medium,
        borderRadius: borderRadii.large,
    },
    userMessageContainer: {
        alignSelf: 'flex-end',
    },
    otherMessageContainer: { 
        alignSelf: 'flex-start',
    },
    agentLabelContainer: {
        alignItems: 'flex-start',
    },
}); 